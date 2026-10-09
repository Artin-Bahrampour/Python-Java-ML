package httpapi

import (
	"context"
	"encoding/json"
	"errors"
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

type fakeStore struct {
	delivery delivery.Delivery
	getErr   error
	pingErr  error
}

func (f *fakeStore) Get(context.Context, string) (delivery.Delivery, error) {
	return f.delivery, f.getErr
}
func (f *fakeStore) Ping(context.Context) error { return f.pingErr }
func (f *fakeStore) Create(context.Context, delivery.NewDelivery) (delivery.Delivery, bool, error) {
	return f.delivery, true, nil
}
func (f *fakeStore) Claim(context.Context, time.Duration, int) (*delivery.ClaimedDelivery, uint64, error) {
	return nil, 0, nil
}
func (f *fakeStore) Complete(context.Context, string, string, int) error { return nil }
func (f *fakeStore) Fail(context.Context, string, string, delivery.Failure, int, time.Duration) (delivery.Status, error) {
	return delivery.StatusRetrying, nil
}

func testHandler() http.Handler {
	st := &fakeStore{delivery: delivery.Delivery{ID: "d-1", TargetID: "target", EventType: "invoice.paid", Payload: json.RawMessage(`{"id":1}`), Status: delivery.StatusQueued, CreatedAt: time.Now(), UpdatedAt: time.Now()}}
	svc := delivery.NewService(st, map[string]delivery.Target{"target": {ID: "target", URL: "https://example.com", Secret: []byte(strings.Repeat("x", 32))}})
	return New(svc, st, telemetry.NewMetrics(), slog.New(slog.NewTextHandler(io.Discard, nil)))
}
func TestCreateAcceptsNewDelivery(t *testing.T) {
	r := httptest.NewRequest(http.MethodPost, "/v1/deliveries", strings.NewReader(`{"target_id":"target","event_type":"invoice.paid","payload":{"id":1}}`))
	r.Header.Set("Content-Type", "application/json")
	r.Header.Set("Idempotency-Key", "invoice-1")
	w := httptest.NewRecorder()
	testHandler().ServeHTTP(w, r)
	if w.Code != http.StatusAccepted {
		t.Fatalf("status=%d body=%s", w.Code, w.Body.String())
	}
	if w.Header().Get("X-Request-ID") == "" {
		t.Fatal("request id missing")
	}
	if w.Header().Get("Location") != "/v1/deliveries/d-1" {
		t.Fatalf("unexpected Location: %q", w.Header().Get("Location"))
	}
	if strings.Contains(w.Body.String(), "payload") {
		t.Fatal("event payload must not be returned in API response")
	}
}
func TestCreateRequiresIdempotencyKey(t *testing.T) {
	r := httptest.NewRequest(http.MethodPost, "/v1/deliveries", strings.NewReader(`{}`))
	r.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	testHandler().ServeHTTP(w, r)
	if w.Code != http.StatusBadRequest {
		t.Fatalf("status=%d", w.Code)
	}
}
func TestCreateRejectsUnknownFields(t *testing.T) {
	r := httptest.NewRequest(http.MethodPost, "/v1/deliveries", strings.NewReader(`{"target_id":"target","event_type":"invoice.paid","payload":{},"admin":true}`))
	r.Header.Set("Content-Type", "application/json")
	r.Header.Set("Idempotency-Key", "k1")
	w := httptest.NewRecorder()
	testHandler().ServeHTTP(w, r)
	if w.Code != http.StatusBadRequest {
		t.Fatalf("status=%d", w.Code)
	}
}
func TestGetNotFound(t *testing.T) {
	st := &fakeStore{getErr: delivery.ErrNotFound}
	svc := delivery.NewService(st, map[string]delivery.Target{})
	h := New(svc, st, telemetry.NewMetrics(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	w := httptest.NewRecorder()
	h.ServeHTTP(w, httptest.NewRequest(http.MethodGet, "/v1/deliveries/00000000-0000-4000-8000-000000000000", nil))
	if w.Code != http.StatusNotFound {
		t.Fatalf("status=%d", w.Code)
	}
}
func TestReadinessFailsWhenDatabaseUnavailable(t *testing.T) {
	st := &fakeStore{pingErr: errors.New("offline")}
	h := New(delivery.NewService(st, map[string]delivery.Target{}), st, telemetry.NewMetrics(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	w := httptest.NewRecorder()
	h.ServeHTTP(w, httptest.NewRequest(http.MethodGet, "/readyz", nil))
	if w.Code != http.StatusServiceUnavailable {
		t.Fatalf("status=%d", w.Code)
	}
}

func TestGetRejectsMalformedUUID(t *testing.T) {
	w := httptest.NewRecorder()
	testHandler().ServeHTTP(w, httptest.NewRequest(http.MethodGet, "/v1/deliveries/not-a-uuid", nil))
	if w.Code != http.StatusBadRequest {
		t.Fatalf("status=%d", w.Code)
	}
}
