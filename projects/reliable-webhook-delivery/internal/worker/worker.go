package worker

import (
	"context"
	"crypto/tls"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/artin-bahrampour/reliable-webhook-delivery/internal/delivery"
	"github.com/artin-bahrampour/reliable-webhook-delivery/internal/telemetry"
)

type Options struct {
	PollInterval, LeaseDuration, RequestTimeout, BaseBackoff, MaxBackoff time.Duration
	MaxAttempts                                                          int
}
type Worker struct {
	store   delivery.Store
	targets map[string]delivery.Target
	metrics *telemetry.Metrics
	logger  *slog.Logger
	opts    Options
	client  *http.Client
}
type sendResult struct {
	status     int
	retryable  bool
	message    string
	retryAfter time.Duration
}

func New(store delivery.Store, targets map[string]delivery.Target, metrics *telemetry.Metrics, logger *slog.Logger, opts Options) *Worker {
	transport := &http.Transport{Proxy: nil, DialContext: (&net.Dialer{Timeout: 3 * time.Second, KeepAlive: 30 * time.Second}).DialContext, TLSClientConfig: &tls.Config{MinVersion: tls.VersionTLS12}, MaxIdleConns: 64, MaxIdleConnsPerHost: 8, IdleConnTimeout: 60 * time.Second, ResponseHeaderTimeout: opts.RequestTimeout}
	client := &http.Client{Transport: transport, Timeout: opts.RequestTimeout, CheckRedirect: func(_ *http.Request, _ []*http.Request) error { return http.ErrUseLastResponse }}
	return &Worker{store: store, targets: targets, metrics: metrics, logger: logger, opts: opts, client: client}
}
func (w *Worker) Run(ctx context.Context) error {
	ticker := time.NewTicker(w.opts.PollInterval)
	defer ticker.Stop()
	for {
		if err := ctx.Err(); err != nil {
			return nil
		}
		worked, err := w.ProcessOne(ctx)
		if err != nil {
			w.logger.Error("worker iteration failed", "error", err)
		}
		if worked {
			continue
		}
		select {
		case <-ctx.Done():
			return nil
		case <-ticker.C:
		}
	}
}
func (w *Worker) ProcessOne(ctx context.Context) (bool, error) {
	claimed, expiredDeadLetters, err := w.store.Claim(ctx, w.opts.LeaseDuration, w.opts.MaxAttempts)
	if err != nil {
		return false, err
	}
	if expiredDeadLetters > 0 {
		w.metrics.DeadLetteredN(expiredDeadLetters)
	}
	if claimed == nil {
		return expiredDeadLetters > 0, nil
	}
	target, ok := w.targets[claimed.TargetID]
	if !ok {
		_, err := w.store.Fail(ctx, claimed.ID, claimed.LeaseToken, delivery.Failure{Message: "target is not configured", Retryable: false}, w.opts.MaxAttempts, 0)
		if err == nil {
			w.metrics.DeadLettered()
		}
		return true, err
	}
	w.metrics.Attempt()
	result := w.send(ctx, target, claimed)
	if result.status >= 200 && result.status < 300 {
		if err := w.store.Complete(ctx, claimed.ID, claimed.LeaseToken, result.status); err != nil {
			if errors.Is(err, delivery.ErrLeaseLost) {
				w.logger.Warn("completion ignored after lease loss", "delivery_id", claimed.ID)
				return true, nil
			}
			return true, err
		}
		w.metrics.Succeeded()
		w.logger.Info("webhook delivered", "delivery_id", claimed.ID, "target_id", claimed.TargetID, "attempt", claimed.Attempts, "http_status", result.status)
		return true, nil
	}
	delay := delivery.Backoff(claimed.Attempts, w.opts.BaseBackoff, w.opts.MaxBackoff)
	if result.retryAfter > delay {
		delay = result.retryAfter
	}
	if delay > w.opts.MaxBackoff {
		delay = w.opts.MaxBackoff
	}
	status, err := w.store.Fail(ctx, claimed.ID, claimed.LeaseToken, delivery.Failure{Message: result.message, HTTPStatus: result.status, Retryable: result.retryable}, w.opts.MaxAttempts, delay)
	if err != nil {
		if errors.Is(err, delivery.ErrLeaseLost) {
			w.logger.Warn("failure ignored after lease loss", "delivery_id", claimed.ID)
			return true, nil
		}
		return true, err
	}
	if status == delivery.StatusRetrying {
		w.metrics.Retried()
		w.logger.Warn("webhook scheduled for retry", "delivery_id", claimed.ID, "target_id", claimed.TargetID, "attempt", claimed.Attempts, "delay_ms", delay.Milliseconds(), "reason", result.message)
	} else {
		w.metrics.DeadLettered()
		if !result.retryable {
			w.metrics.PermanentFailure()
		}
		w.logger.Error("webhook moved to dead letter", "delivery_id", claimed.ID, "target_id", claimed.TargetID, "attempt", claimed.Attempts, "reason", result.message)
	}
	return true, nil
}
func (w *Worker) send(ctx context.Context, target delivery.Target, d *delivery.ClaimedDelivery) sendResult {
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, target.URL, strings.NewReader(string(d.Payload)))
	if err != nil {
		return sendResult{retryable: false, message: "invalid configured target request"}
	}
	now := time.Now().UTC()
	timestamp := strconv.FormatInt(now.Unix(), 10)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("User-Agent", "ReliableWebhookDelivery/1.0")
	attempt := strconv.Itoa(d.Attempts)
	req.Header.Set("X-Event-ID", d.ID)
	req.Header.Set("X-Event-Type", d.EventType)
	req.Header.Set("X-Delivery-Attempt", attempt)
	req.Header.Set("X-Webhook-Timestamp", timestamp)
	req.Header.Set("X-Webhook-Signature", delivery.Sign(target.Secret, d.ID, d.EventType, attempt, d.Payload, now))
	resp, err := w.client.Do(req)
	if err != nil {
		if errors.Is(err, context.Canceled) && ctx.Err() != nil {
			return sendResult{retryable: true, message: "worker shutdown interrupted delivery"}
		}
		if errors.Is(err, context.DeadlineExceeded) {
			return sendResult{retryable: true, message: "target request timed out"}
		}
		return sendResult{retryable: true, message: "network delivery failed"}
	}
	defer resp.Body.Close()
	_, _ = io.Copy(io.Discard, io.LimitReader(resp.Body, 4096))
	if resp.StatusCode >= 200 && resp.StatusCode < 300 {
		return sendResult{status: resp.StatusCode}
	}
	retryable := resp.StatusCode == 408 || resp.StatusCode == 425 || resp.StatusCode == 429 || resp.StatusCode >= 500
	return sendResult{status: resp.StatusCode, retryable: retryable, message: fmt.Sprintf("target returned HTTP %d", resp.StatusCode), retryAfter: parseRetryAfter(resp.Header.Get("Retry-After"), now, w.opts.MaxBackoff)}
}
func parseRetryAfter(value string, now time.Time, maximum time.Duration) time.Duration {
	if value == "" || maximum <= 0 {
		return 0
	}
	if seconds, err := strconv.ParseInt(value, 10, 64); err == nil && seconds >= 0 {
		if seconds > int64(maximum/time.Second) {
			return maximum
		}
		delay := time.Duration(seconds) * time.Second
		if delay > maximum {
			return maximum
		}
		return delay
	}
	if when, err := http.ParseTime(value); err == nil && when.After(now) {
		delay := when.Sub(now)
		if delay > maximum {
			return maximum
		}
		return delay
	}
	return 0
}
