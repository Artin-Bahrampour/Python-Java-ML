package delivery

import (
	"context"
	"encoding/json"
	"errors"
	"time"
)

type Status string

const (
	StatusQueued     Status = "queued"
	StatusInFlight   Status = "in_flight"
	StatusRetrying   Status = "retrying"
	StatusDelivered  Status = "delivered"
	StatusDeadLetter Status = "dead_letter"
)

var (
	ErrNotFound            = errors.New("delivery not found")
	ErrIdempotencyConflict = errors.New("idempotency key was already used with a different request")
	ErrInvalidInput        = errors.New("invalid delivery input")
	ErrLeaseLost           = errors.New("delivery lease is no longer owned by this worker")
)

type Target struct {
	ID     string
	URL    string
	Secret []byte
}
type Delivery struct {
	ID             string          `json:"id"`
	TargetID       string          `json:"target_id"`
	EventType      string          `json:"event_type"`
	Payload        json.RawMessage `json:"-"`
	Status         Status          `json:"status"`
	Attempts       int             `json:"attempts"`
	LastHTTPStatus *int            `json:"last_http_status,omitempty"`
	LastError      string          `json:"last_error,omitempty"`
	NextAttemptAt  *time.Time      `json:"next_attempt_at,omitempty"`
	CreatedAt      time.Time       `json:"created_at"`
	UpdatedAt      time.Time       `json:"updated_at"`
	DeliveredAt    *time.Time      `json:"delivered_at,omitempty"`
}
type NewDelivery struct {
	TargetID, IdempotencyKey, EventType, RequestHash string
	Payload                                          []byte
}
type ClaimedDelivery struct {
	Delivery
	LeaseToken string
}
type Failure struct {
	Message    string
	HTTPStatus int
	Retryable  bool
	RetryAfter time.Duration
}

type Store interface {
	Create(context.Context, NewDelivery) (Delivery, bool, error)
	Get(context.Context, string) (Delivery, error)
	Ping(context.Context) error
	Claim(context.Context, time.Duration, int) (*ClaimedDelivery, uint64, error)
	Complete(context.Context, string, string, int) error
	Fail(context.Context, string, string, Failure, int, time.Duration) (Status, error)
}
