package store

import (
	"context"
	"crypto/rand"
	"embed"
	"encoding/hex"
	"errors"
	"fmt"
	"io/fs"
	"log/slog"
	"sort"
	"strings"
	"time"

	"github.com/artin-bahrampour/reliable-webhook-delivery/internal/delivery"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

//go:embed migrations/*.sql
var migrations embed.FS

type Postgres struct {
	pool   *pgxpool.Pool
	logger *slog.Logger
}

func NewPostgres(ctx context.Context, dsn string, logger *slog.Logger) (*Postgres, error) {
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		return nil, fmt.Errorf("parse DB_URL: invalid PostgreSQL connection string")
	}
	return newPostgresWithConfig(ctx, cfg, logger)
}

func newPostgresWithConfig(ctx context.Context, cfg *pgxpool.Config, logger *slog.Logger) (*Postgres, error) {
	cfg.MaxConns = 12
	cfg.MinConns = 1
	cfg.MaxConnLifetime = 45 * time.Minute
	cfg.MaxConnIdleTime = 5 * time.Minute
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		return nil, fmt.Errorf("create database pool: %w", err)
	}
	if err := pool.Ping(ctx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("connect to PostgreSQL: %w", err)
	}
	p := &Postgres{pool: pool, logger: logger}
	if err := p.migrate(ctx); err != nil {
		pool.Close()
		return nil, err
	}
	return p, nil
}
func (p *Postgres) Close()                         { p.pool.Close() }
func (p *Postgres) Ping(ctx context.Context) error { return p.pool.Ping(ctx) }
func (p *Postgres) migrate(ctx context.Context) error {
	if _, err := p.pool.Exec(ctx, `CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())`); err != nil {
		return fmt.Errorf("create migration table: %w", err)
	}
	entries, err := fs.Glob(migrations, "migrations/*.sql")
	if err != nil {
		return err
	}
	sort.Strings(entries)
	for _, name := range entries {
		version := strings.TrimPrefix(name, "migrations/")
		var exists bool
		if err := p.pool.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM schema_migrations WHERE version=$1)`, version).Scan(&exists); err != nil {
			return err
		}
		if exists {
			continue
		}
		body, err := migrations.ReadFile(name)
		if err != nil {
			return err
		}
		tx, err := p.pool.Begin(ctx)
		if err != nil {
			return err
		}
		if _, err = tx.Exec(ctx, string(body)); err == nil {
			_, err = tx.Exec(ctx, `INSERT INTO schema_migrations(version) VALUES($1) ON CONFLICT DO NOTHING`, version)
		}
		if err != nil {
			_ = tx.Rollback(ctx)
			return fmt.Errorf("apply migration %s: %w", version, err)
		}
		if err = tx.Commit(ctx); err != nil {
			return fmt.Errorf("commit migration %s: %w", version, err)
		}
		p.logger.Info("database migration applied", "version", version)
	}
	return nil
}

const deliveryColumns = `id::text,target_id,event_type,payload,status,attempts,last_http_status,last_error,next_attempt_at,created_at,updated_at,delivered_at`

func scanDelivery(row pgx.Row) (delivery.Delivery, error) {
	var d delivery.Delivery
	var payload []byte
	var status string
	err := row.Scan(&d.ID, &d.TargetID, &d.EventType, &payload, &status, &d.Attempts, &d.LastHTTPStatus, &d.LastError, &d.NextAttemptAt, &d.CreatedAt, &d.UpdatedAt, &d.DeliveredAt)
	if err != nil {
		return d, err
	}
	d.Payload = payload
	d.Status = delivery.Status(status)
	if d.Status != delivery.StatusQueued && d.Status != delivery.StatusRetrying {
		d.NextAttemptAt = nil
	}
	return d, nil
}
func (p *Postgres) Create(ctx context.Context, in delivery.NewDelivery) (delivery.Delivery, bool, error) {
	row := p.pool.QueryRow(ctx, `INSERT INTO deliveries(target_id,idempotency_key,request_hash,event_type,payload,status) VALUES($1,$2,$3,$4,$5::jsonb,'queued') ON CONFLICT(target_id,idempotency_key) DO NOTHING RETURNING `+deliveryColumns, in.TargetID, in.IdempotencyKey, in.RequestHash, in.EventType, string(in.Payload))
	d, err := scanDelivery(row)
	if err == nil {
		return d, true, nil
	}
	if !errors.Is(err, pgx.ErrNoRows) {
		return delivery.Delivery{}, false, fmt.Errorf("insert delivery: %w", err)
	}
	existing, err := scanDelivery(p.pool.QueryRow(ctx, `SELECT `+deliveryColumns+` FROM deliveries WHERE target_id=$1 AND idempotency_key=$2`, in.TargetID, in.IdempotencyKey))
	if err != nil {
		return delivery.Delivery{}, false, fmt.Errorf("read idempotent delivery: %w", err)
	}
	var requestHash string
	// Read the hash separately to keep the public delivery projection stable.
	if err := p.pool.QueryRow(ctx, `SELECT request_hash FROM deliveries WHERE id=$1::uuid`, existing.ID).Scan(&requestHash); err != nil {
		return delivery.Delivery{}, false, err
	}
	if requestHash != in.RequestHash {
		return delivery.Delivery{}, false, delivery.ErrIdempotencyConflict
	}
	return existing, false, nil
}
func (p *Postgres) Get(ctx context.Context, id string) (delivery.Delivery, error) {
	d, err := scanDelivery(p.pool.QueryRow(ctx, `SELECT `+deliveryColumns+` FROM deliveries WHERE id=$1::uuid`, id))
	if errors.Is(err, pgx.ErrNoRows) {
		return delivery.Delivery{}, delivery.ErrNotFound
	}
	if err != nil {
		return delivery.Delivery{}, fmt.Errorf("get delivery: %w", err)
	}
	return d, nil
}
func (p *Postgres) Claim(ctx context.Context, lease time.Duration, maxAttempts int) (*delivery.ClaimedDelivery, uint64, error) {
	tx, err := p.pool.Begin(ctx)
	if err != nil {
		return nil, 0, err
	}
	defer func() { _ = tx.Rollback(ctx) }()
	expiredTag, err := tx.Exec(ctx, `UPDATE deliveries SET status='dead_letter',last_error=COALESCE(NULLIF(last_error,''),'worker lease expired after final attempt'),lease_token=NULL,lease_until=NULL,updated_at=now() WHERE attempts >= $1 AND ((status IN ('queued','retrying') AND next_attempt_at <= now()) OR (status='in_flight' AND lease_until <= now()))`, maxAttempts)
	if err != nil {
		return nil, 0, fmt.Errorf("expire exhausted deliveries: %w", err)
	}
	expiredDeadLetters := uint64(expiredTag.RowsAffected())
	row := tx.QueryRow(ctx, `SELECT `+deliveryColumns+` FROM deliveries WHERE (status IN ('queued','retrying') AND next_attempt_at <= now()) OR (status='in_flight' AND lease_until <= now() AND attempts < $1) ORDER BY next_attempt_at,created_at LIMIT 1 FOR UPDATE SKIP LOCKED`, maxAttempts)
	d, err := scanDelivery(row)
	if errors.Is(err, pgx.ErrNoRows) {
		if err := tx.Commit(ctx); err != nil {
			return nil, 0, err
		}
		return nil, expiredDeadLetters, nil
	}
	if err != nil {
		return nil, 0, fmt.Errorf("select next delivery: %w", err)
	}
	token, err := newUUID()
	if err != nil {
		return nil, 0, err
	}
	claimed, err := scanDelivery(tx.QueryRow(ctx, `UPDATE deliveries SET status='in_flight',attempts=attempts+1,lease_token=$2::uuid,lease_until=now()+($3 * interval '1 second'),updated_at=now() WHERE id=$1::uuid RETURNING `+deliveryColumns, d.ID, token, lease.Seconds()))
	if err != nil {
		return nil, 0, fmt.Errorf("claim delivery: %w", err)
	}
	if err := tx.Commit(ctx); err != nil {
		return nil, 0, err
	}
	return &delivery.ClaimedDelivery{Delivery: claimed, LeaseToken: token}, expiredDeadLetters, nil
}
func (p *Postgres) Complete(ctx context.Context, id, token string, httpStatus int) error {
	tag, err := p.pool.Exec(ctx, `UPDATE deliveries SET status='delivered',last_http_status=$3,last_error='',delivered_at=now(),updated_at=now(),lease_token=NULL,lease_until=NULL WHERE id=$1::uuid AND lease_token=$2::uuid AND status='in_flight'`, id, token, httpStatus)
	if err != nil {
		return fmt.Errorf("complete delivery: %w", err)
	}
	if tag.RowsAffected() == 0 {
		return delivery.ErrLeaseLost
	}
	return nil
}
func (p *Postgres) Fail(ctx context.Context, id, token string, f delivery.Failure, maxAttempts int, delay time.Duration) (delivery.Status, error) {
	var status string
	err := p.pool.QueryRow(ctx, `UPDATE deliveries SET status=CASE WHEN NOT $3 OR attempts >= $4 THEN 'dead_letter' ELSE 'retrying' END,last_http_status=NULLIF($5,0),last_error=$6,next_attempt_at=now()+($7 * interval '1 second'),updated_at=now(),lease_token=NULL,lease_until=NULL WHERE id=$1::uuid AND lease_token=$2::uuid AND status='in_flight' RETURNING status`, id, token, f.Retryable, maxAttempts, f.HTTPStatus, truncate(f.Message, 240), delay.Seconds()).Scan(&status)
	if errors.Is(err, pgx.ErrNoRows) {
		return "", delivery.ErrLeaseLost
	}
	if err != nil {
		return "", fmt.Errorf("record delivery failure: %w", err)
	}
	return delivery.Status(status), nil
}
func newUUID() (string, error) {
	b := make([]byte, 16)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	b[6] = (b[6] & 0x0f) | 0x40
	b[8] = (b[8] & 0x3f) | 0x80
	h := hex.EncodeToString(b)
	return h[:8] + "-" + h[8:12] + "-" + h[12:16] + "-" + h[16:20] + "-" + h[20:], nil
}
func truncate(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n]
}
