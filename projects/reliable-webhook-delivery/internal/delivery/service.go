package delivery

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"regexp"
	"strings"
)

const MaxPayloadBytes = 256 << 10

var eventTypePattern = regexp.MustCompile(`^[a-z][a-z0-9]*(\.[a-z][a-z0-9_-]*){1,7}$`)

type Service struct {
	store   Store
	targets map[string]Target
}

func NewService(store Store, targets map[string]Target) *Service {
	return &Service{store: store, targets: targets}
}

func (s *Service) Create(ctx context.Context, targetID, key, eventType string, payload json.RawMessage) (Delivery, bool, error) {
	if _, ok := s.targets[targetID]; !ok {
		return Delivery{}, false, fmt.Errorf("%w: unknown target_id", ErrInvalidInput)
	}
	if len(key) < 1 || len(key) > 200 || strings.TrimSpace(key) != key {
		return Delivery{}, false, fmt.Errorf("%w: Idempotency-Key must contain 1-200 non-whitespace characters", ErrInvalidInput)
	}
	for _, r := range key {
		if r < 0x21 || r > 0x7e {
			return Delivery{}, false, fmt.Errorf("%w: Idempotency-Key must contain printable ASCII", ErrInvalidInput)
		}
	}
	if !eventTypePattern.MatchString(eventType) || len(eventType) > 128 {
		return Delivery{}, false, fmt.Errorf("%w: event_type must use dotted lowercase event notation", ErrInvalidInput)
	}
	if len(payload) == 0 || len(payload) > MaxPayloadBytes || !json.Valid(payload) {
		return Delivery{}, false, fmt.Errorf("%w: payload must be valid JSON no larger than 256 KiB", ErrInvalidInput)
	}
	decoder := json.NewDecoder(bytes.NewReader(payload))
	decoder.UseNumber()
	var value any
	if err := decoder.Decode(&value); err != nil {
		return Delivery{}, false, fmt.Errorf("%w: invalid payload", ErrInvalidInput)
	}
	if _, ok := value.(map[string]any); !ok {
		return Delivery{}, false, fmt.Errorf("%w: payload must be a JSON object", ErrInvalidInput)
	}
	canonical, err := json.Marshal(value)
	if err != nil {
		return Delivery{}, false, fmt.Errorf("%w: cannot normalize payload", ErrInvalidInput)
	}
	h := sha256.New()
	_, _ = io.WriteString(h, targetID+"\n"+eventType+"\n")
	_, _ = h.Write(canonical)
	input := NewDelivery{TargetID: targetID, IdempotencyKey: key, EventType: eventType, Payload: canonical, RequestHash: hex.EncodeToString(h.Sum(nil))}
	result, created, err := s.store.Create(ctx, input)
	if err != nil {
		return Delivery{}, false, err
	}
	return result, created, nil
}
