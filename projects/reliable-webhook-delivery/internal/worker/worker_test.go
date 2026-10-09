package worker

import (
	"context"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/artin-bahrampour/reliable-webhook-delivery/internal/delivery"
	"github.com/artin-bahrampour/reliable-webhook-delivery/internal/telemetry"
)

type noStore struct{}

func (noStore) Create(context.Context, delivery.NewDelivery) (delivery.Delivery, bool, error) {
	return delivery.Delivery{}, false, nil
}
func (noStore) Get(context.Context, string) (delivery.Delivery, error) {
	return delivery.Delivery{}, delivery.ErrNotFound
}
func (noStore) Ping(context.Context) error { return nil }
func (noStore) Claim(context.Context, time.Duration, int) (*delivery.ClaimedDelivery, uint64, error) {
	return nil, 0, nil
}
func (noStore) Complete(context.Context, string, string, int) error { return nil }
func (noStore) Fail(context.Context, string, string, delivery.Failure, int, time.Duration) (delivery.Status, error) {
	return delivery.StatusRetrying, nil
}
func testWorker(target delivery.Target) *Worker {
	return New(noStore{}, map[string]delivery.Target{target.ID: target}, telemetry.NewMetrics(), slog.New(slog.NewTextHandler(io.Discard, nil)), Options{PollInterval: time.Millisecond, LeaseDuration: time.Minute, RequestTimeout: time.Second, MaxAttempts: 4, BaseBackoff: time.Second, MaxBackoff: time.Minute})
}
func claimed(url string) *delivery.ClaimedDelivery {
	return &delivery.ClaimedDelivery{Delivery: delivery.Delivery{ID: "delivery-1", TargetID: "target", EventType: "invoice.paid", Payload: []byte(`{"invoice_id":"i-1"}`), Attempts: 1}, LeaseToken: "lease"}
}
func TestSendSignsRequestAndAccepts204(t *testing.T) {
	secret := []byte(strings.Repeat("s", 32))
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		body, _ := io.ReadAll(r.Body)
		if !delivery.Verify(secret, body, r.Header.Get("X-Event-ID"), r.Header.Get("X-Event-Type"), r.Header.Get("X-Delivery-Attempt"), r.Header.Get("X-Webhook-Timestamp"), r.Header.Get("X-Webhook-Signature"), time.Now(), time.Minute) {
			t.Error("signature did not verify")
		}
		if r.Header.Get("X-Event-Type") != "invoice.paid" {
			t.Error("event type missing")
		}
		w.WriteHeader(http.StatusNoContent)
	}))
	defer srv.Close()
	w := testWorker(delivery.Target{ID: "target", URL: srv.URL, Secret: secret})
	result := w.send(context.Background(), delivery.Target{ID: "target", URL: srv.URL, Secret: secret}, claimed(srv.URL))
	if result.status != 204 || result.retryable {
		t.Fatalf("result=%+v", result)
	}
}
func TestSendMarks429Retryable(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Retry-After", "3")
		w.WriteHeader(http.StatusTooManyRequests)
	}))
	defer srv.Close()
	secret := []byte(strings.Repeat("s", 32))
	w := testWorker(delivery.Target{ID: "target", URL: srv.URL, Secret: secret})
	result := w.send(context.Background(), delivery.Target{ID: "target", URL: srv.URL, Secret: secret}, claimed(srv.URL))
	if !result.retryable || result.status != 429 || result.retryAfter < 2*time.Second {
		t.Fatalf("result=%+v", result)
	}
}
func TestSendDoesNotFollowRedirects(t *testing.T) {
	targetCalls := 0
	target := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		targetCalls++
		w.Header().Set("Location", "http://127.0.0.1:1/steal")
		w.WriteHeader(http.StatusFound)
	}))
	defer target.Close()
	secret := []byte(strings.Repeat("s", 32))
	w := testWorker(delivery.Target{ID: "target", URL: target.URL, Secret: secret})
	result := w.send(context.Background(), delivery.Target{ID: "target", URL: target.URL, Secret: secret}, claimed(target.URL))
	if result.status != 302 || result.retryable {
		t.Fatalf("result=%+v", result)
	}
	if targetCalls != 1 {
		t.Fatalf("calls=%d", targetCalls)
	}
}

func TestParseRetryAfterCapsUntrustedValues(t *testing.T) {
	now := time.Now().UTC()
	maximum := 5 * time.Minute
	if got := parseRetryAfter("9223372036854775807", now, maximum); got != maximum {
		t.Fatalf("expected cap %s, got %s", maximum, got)
	}
	if got := parseRetryAfter(now.Add(time.Hour).Format(http.TimeFormat), now, maximum); got != maximum {
		t.Fatalf("expected date cap %s, got %s", maximum, got)
	}
}

type recordingStore struct {
	claimed         *delivery.ClaimedDelivery
	completed       bool
	completedStatus int
	failure         *delivery.Failure
	failureDelay    time.Duration
	failureStatus   delivery.Status
}

func (s *recordingStore) Create(context.Context, delivery.NewDelivery) (delivery.Delivery, bool, error) {
	return delivery.Delivery{}, false, nil
}
func (s *recordingStore) Get(context.Context, string) (delivery.Delivery, error) {
	return delivery.Delivery{}, delivery.ErrNotFound
}
func (s *recordingStore) Ping(context.Context) error { return nil }
func (s *recordingStore) Claim(context.Context, time.Duration, int) (*delivery.ClaimedDelivery, uint64, error) {
	return s.claimed, 0, nil
}
func (s *recordingStore) Complete(_ context.Context, _, _ string, status int) error {
	s.completed = true
	s.completedStatus = status
	return nil
}
func (s *recordingStore) Fail(_ context.Context, _, _ string, failure delivery.Failure, _ int, delay time.Duration) (delivery.Status, error) {
	s.failure = &failure
	s.failureDelay = delay
	return s.failureStatus, nil
}

func TestProcessOnePersistsSuccessfulDelivery(t *testing.T) {
	secret := []byte(strings.Repeat("s", 32))
	sink := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) { w.WriteHeader(http.StatusAccepted) }))
	defer sink.Close()
	queue := &recordingStore{claimed: claimed(sink.URL)}
	metrics := telemetry.NewMetrics()
	runner := New(queue, map[string]delivery.Target{"target": {ID: "target", URL: sink.URL, Secret: secret}}, metrics, slog.New(slog.NewTextHandler(io.Discard, nil)), Options{PollInterval: time.Millisecond, LeaseDuration: time.Minute, RequestTimeout: time.Second, MaxAttempts: 4, BaseBackoff: time.Second, MaxBackoff: time.Minute})
	worked, err := runner.ProcessOne(context.Background())
	if err != nil || !worked {
		t.Fatalf("worked=%v err=%v", worked, err)
	}
	if !queue.completed || queue.completedStatus != http.StatusAccepted || queue.failure != nil {
		t.Fatalf("unexpected queue updates: %+v", queue)
	}
}

func TestProcessOneSchedulesTransientFailure(t *testing.T) {
	secret := []byte(strings.Repeat("s", 32))
	sink := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Retry-After", "1")
		w.WriteHeader(http.StatusServiceUnavailable)
	}))
	defer sink.Close()
	queue := &recordingStore{claimed: claimed(sink.URL), failureStatus: delivery.StatusRetrying}
	runner := New(queue, map[string]delivery.Target{"target": {ID: "target", URL: sink.URL, Secret: secret}}, telemetry.NewMetrics(), slog.New(slog.NewTextHandler(io.Discard, nil)), Options{PollInterval: time.Millisecond, LeaseDuration: time.Minute, RequestTimeout: time.Second, MaxAttempts: 4, BaseBackoff: time.Second, MaxBackoff: time.Minute})
	worked, err := runner.ProcessOne(context.Background())
	if err != nil || !worked {
		t.Fatalf("worked=%v err=%v", worked, err)
	}
	if queue.failure == nil || !queue.failure.Retryable || queue.failure.HTTPStatus != http.StatusServiceUnavailable {
		t.Fatalf("unexpected failure: %+v", queue.failure)
	}
	if queue.failureDelay < time.Second || queue.failureDelay > time.Minute {
		t.Fatalf("unexpected retry delay: %s", queue.failureDelay)
	}
}

func TestProcessOneDeadLettersPermanentFailure(t *testing.T) {
	secret := []byte(strings.Repeat("s", 32))
	sink := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) { w.WriteHeader(http.StatusBadRequest) }))
	defer sink.Close()
	queue := &recordingStore{claimed: claimed(sink.URL), failureStatus: delivery.StatusDeadLetter}
	runner := New(queue, map[string]delivery.Target{"target": {ID: "target", URL: sink.URL, Secret: secret}}, telemetry.NewMetrics(), slog.New(slog.NewTextHandler(io.Discard, nil)), Options{PollInterval: time.Millisecond, LeaseDuration: time.Minute, RequestTimeout: time.Second, MaxAttempts: 4, BaseBackoff: time.Second, MaxBackoff: time.Minute})
	worked, err := runner.ProcessOne(context.Background())
	if err != nil || !worked {
		t.Fatalf("worked=%v err=%v", worked, err)
	}
	if queue.failure == nil || queue.failure.Retryable || queue.failure.HTTPStatus != http.StatusBadRequest {
		t.Fatalf("unexpected permanent failure: %+v", queue.failure)
	}
}
