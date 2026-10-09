package delivery

import (
	"context"
	"encoding/json"
	"errors"
	"strconv"
	"strings"
	"testing"
	"time"
)

type memoryStore struct {
	input NewDelivery
	err   error
}

func (m *memoryStore) Create(_ context.Context, in NewDelivery) (Delivery, bool, error) {
	m.input = in
	if m.err != nil {
		return Delivery{}, false, m.err
	}
	return Delivery{ID: "new-id", TargetID: in.TargetID, EventType: in.EventType, Payload: in.Payload, Status: StatusQueued, CreatedAt: time.Now()}, true, nil
}
func (m *memoryStore) Get(context.Context, string) (Delivery, error) { return Delivery{}, ErrNotFound }
func (m *memoryStore) Ping(context.Context) error                    { return nil }
func (m *memoryStore) Claim(context.Context, time.Duration, int) (*ClaimedDelivery, uint64, error) {
	return nil, 0, nil
}
func (m *memoryStore) Complete(context.Context, string, string, int) error { return nil }
func (m *memoryStore) Fail(context.Context, string, string, Failure, int, time.Duration) (Status, error) {
	return StatusRetrying, nil
}

func TestCreateCanonicalizesPayload(t *testing.T) {
	m := &memoryStore{}
	s := NewService(m, map[string]Target{"t": {ID: "t"}})
	_, created, err := s.Create(context.Background(), "t", "key-1", "invoice.paid", json.RawMessage(`{ "z": 2, "a": 1 }`))
	if err != nil || !created {
		t.Fatalf("created=%v err=%v", created, err)
	}
	if string(m.input.Payload) != `{"a":1,"z":2}` {
		t.Fatalf("payload=%s", m.input.Payload)
	}
}
func TestCreateRejectsUnknownTarget(t *testing.T) {
	s := NewService(&memoryStore{}, map[string]Target{})
	_, _, err := s.Create(context.Background(), "missing", "k", "invoice.paid", json.RawMessage(`{}`))
	if !errors.Is(err, ErrInvalidInput) {
		t.Fatalf("err=%v", err)
	}
}
func TestCreateRejectsNonObjectPayload(t *testing.T) {
	s := NewService(&memoryStore{}, map[string]Target{"t": {ID: "t"}})
	_, _, err := s.Create(context.Background(), "t", "k", "invoice.paid", json.RawMessage(`[1,2]`))
	if !errors.Is(err, ErrInvalidInput) {
		t.Fatalf("err=%v", err)
	}
}
func TestCreateRejectsBadEventType(t *testing.T) {
	s := NewService(&memoryStore{}, map[string]Target{"t": {ID: "t"}})
	_, _, err := s.Create(context.Background(), "t", "k", "Invoice Paid", json.RawMessage(`{}`))
	if !errors.Is(err, ErrInvalidInput) {
		t.Fatalf("err=%v", err)
	}
}
func TestCreateRejectsPayloadOverLimit(t *testing.T) {
	s := NewService(&memoryStore{}, map[string]Target{"t": {ID: "t"}})
	_, _, err := s.Create(context.Background(), "t", "k", "invoice.paid", json.RawMessage(`{"x":"`+strings.Repeat("a", MaxPayloadBytes)+`"}`))
	if !errors.Is(err, ErrInvalidInput) {
		t.Fatalf("err=%v", err)
	}
}
func TestBackoffCappedAndNonNegative(t *testing.T) {
	base, max := time.Second, 16*time.Second
	for a := 1; a < 20; a++ {
		d := Backoff(a, base, max)
		if d < 0 || d > max {
			t.Fatalf("attempt=%d delay=%s", a, d)
		}
	}
}
func TestSignatureVerification(t *testing.T) {
	secret := []byte(strings.Repeat("s", 32))
	body := []byte(`{"event":"ok"}`)
	now := time.Now()
	sig := Sign(secret, "event-1", "invoice.paid", "1", body, now)
	if !Verify(secret, body, "event-1", "invoice.paid", "1", fmtInt(now.Unix()), sig, now, time.Minute) {
		t.Fatal("valid signature rejected")
	}
	if Verify(secret, []byte(`{"event":"tampered"}`), "event-1", "invoice.paid", "1", fmtInt(now.Unix()), sig, now, time.Minute) {
		t.Fatal("tampered payload accepted")
	}
	if Verify(secret, body, "event-1", "invoice.paid", "1", fmtInt(now.Add(-time.Hour).Unix()), sig, now, time.Minute) {
		t.Fatal("stale signature accepted")
	}
	if Verify(secret, body, "event-1", "invoice.refunded", "1", fmtInt(now.Unix()), sig, now, time.Minute) {
		t.Fatal("tampered event metadata accepted")
	}
}
func fmtInt(n int64) string { return strconv.FormatInt(n, 10) }

func TestCanonicalPayloadHashIgnoresObjectKeyOrder(t *testing.T) {
	m := &memoryStore{}
	s := NewService(m, map[string]Target{"t": {ID: "t"}})
	_, _, err := s.Create(context.Background(), "t", "key", "invoice.paid", json.RawMessage(`{"z":2,"a":1}`))
	if err != nil {
		t.Fatal(err)
	}
	first := m.input.RequestHash
	_, _, err = s.Create(context.Background(), "t", "key", "invoice.paid", json.RawMessage(`{ "a": 1, "z": 2 }`))
	if err != nil {
		t.Fatal(err)
	}
	if first != m.input.RequestHash {
		t.Fatalf("hash changed for semantically equivalent JSON: %s != %s", first, m.input.RequestHash)
	}
}
