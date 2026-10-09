package store

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"os"
	"testing"
	"time"

	"github.com/artin-bahrampour/reliable-webhook-delivery/internal/delivery"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

func TestPostgresDeliveryLifecycle(t *testing.T) {
	dsn := os.Getenv("TEST_DATABASE_URL")
	if dsn == "" {
		t.Skip("TEST_DATABASE_URL not set; PostgreSQL integration test skipped")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	admin, err := pgx.Connect(ctx, dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer func() { _ = admin.Close(context.Background()) }()
	schema := fmt.Sprintf("rwd_test_%d", time.Now().UnixNano())
	if _, err := admin.Exec(ctx, "CREATE SCHEMA "+schema); err != nil {
		t.Fatal(err)
	}
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		_, _ = admin.Exec(context.Background(), "DROP SCHEMA "+schema+" CASCADE")
		t.Fatal(err)
	}
	if cfg.ConnConfig.RuntimeParams == nil {
		cfg.ConnConfig.RuntimeParams = make(map[string]string)
	}
	cfg.ConnConfig.RuntimeParams["search_path"] = schema
	p, err := newPostgresWithConfig(ctx, cfg, slog.New(slog.NewTextHandler(os.Stderr, nil)))
	if err != nil {
		_, _ = admin.Exec(context.Background(), "DROP SCHEMA "+schema+" CASCADE")
		t.Fatal(err)
	}
	defer func() {
		p.Close()
		cleanupCtx, cleanupCancel := context.WithTimeout(context.Background(), 3*time.Second)
		defer cleanupCancel()
		_, _ = admin.Exec(cleanupCtx, "DROP SCHEMA "+schema+" CASCADE")
	}()
	in := delivery.NewDelivery{TargetID: "integration-target", IdempotencyKey: "integration-" + time.Now().Format("150405.000000000"), RequestHash: "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef", EventType: "invoice.paid", Payload: []byte(`{"invoice_id":"inv-1"}`)}
	first, created, err := p.Create(ctx, in)
	if err != nil || !created {
		t.Fatalf("create: created=%v err=%v", created, err)
	}
	second, created, err := p.Create(ctx, in)
	if err != nil || created || second.ID != first.ID {
		t.Fatalf("idempotency failed: created=%v id=%s err=%v", created, second.ID, err)
	}
	conflicting := in
	conflicting.RequestHash = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
	_, _, err = p.Create(ctx, conflicting)
	if !errors.Is(err, delivery.ErrIdempotencyConflict) {
		t.Fatalf("expected idempotency conflict, got %v", err)
	}
	claim, _, err := p.Claim(ctx, 30*time.Second, 4)
	if err != nil || claim == nil {
		t.Fatalf("claim: claim=%v err=%v", claim, err)
	}
	if claim.Attempts != 1 || claim.Status != delivery.StatusInFlight {
		t.Fatalf("unexpected claim: %+v", claim)
	}
	if err := p.Complete(ctx, claim.ID, claim.LeaseToken, 204); err != nil {
		t.Fatal(err)
	}
	got, err := p.Get(ctx, first.ID)
	if err != nil {
		t.Fatal(err)
	}
	if got.Status != delivery.StatusDelivered || got.DeliveredAt == nil {
		t.Fatalf("unexpected final state: %+v", got)
	}
	if err := p.Complete(ctx, claim.ID, claim.LeaseToken, 204); err != delivery.ErrLeaseLost {
		t.Fatalf("stale lease should fail, got %v", err)
	}

	in2 := delivery.NewDelivery{TargetID: "integration-target", IdempotencyKey: in.IdempotencyKey + "-retry", RequestHash: "1123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef", EventType: "invoice.failed", Payload: []byte(`{"invoice_id":"inv-2"}`)}
	if _, _, err := p.Create(ctx, in2); err != nil {
		t.Fatal(err)
	}
	retryClaim, _, err := p.Claim(ctx, 30*time.Second, 2)
	if err != nil || retryClaim == nil {
		t.Fatalf("first retry claim: claim=%v err=%v", retryClaim, err)
	}
	status, err := p.Fail(ctx, retryClaim.ID, retryClaim.LeaseToken, delivery.Failure{Message: "temporary", Retryable: true}, 2, 0)
	if err != nil || status != delivery.StatusRetrying {
		t.Fatalf("expected retrying, status=%s err=%v", status, err)
	}
	retryClaim, _, err = p.Claim(ctx, 30*time.Second, 2)
	if err != nil || retryClaim == nil {
		t.Fatalf("second retry claim: claim=%v err=%v", retryClaim, err)
	}
	status, err = p.Fail(ctx, retryClaim.ID, retryClaim.LeaseToken, delivery.Failure{Message: "still failing", Retryable: true}, 2, 0)
	if err != nil || status != delivery.StatusDeadLetter {
		t.Fatalf("expected dead letter, status=%s err=%v", status, err)
	}
}
