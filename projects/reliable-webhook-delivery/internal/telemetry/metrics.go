package telemetry

import (
	"fmt"
	"net/http"
	"sync/atomic"
)

type Metrics struct {
	requests          atomic.Uint64
	created           atomic.Uint64
	attempts          atomic.Uint64
	succeeded         atomic.Uint64
	retried           atomic.Uint64
	deadLettered      atomic.Uint64
	permanentFailures atomic.Uint64
}

func NewMetrics() *Metrics                { return &Metrics{} }
func (m *Metrics) Request()               { m.requests.Add(1) }
func (m *Metrics) Created()               { m.created.Add(1) }
func (m *Metrics) Attempt()               { m.attempts.Add(1) }
func (m *Metrics) Succeeded()             { m.succeeded.Add(1) }
func (m *Metrics) Retried()               { m.retried.Add(1) }
func (m *Metrics) DeadLettered()          { m.deadLettered.Add(1) }
func (m *Metrics) DeadLetteredN(n uint64) { m.deadLettered.Add(n) }
func (m *Metrics) PermanentFailure()      { m.permanentFailures.Add(1) }

func (m *Metrics) ServeHTTP(w http.ResponseWriter, _ *http.Request) {
	w.Header().Set("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
	_, _ = fmt.Fprintf(w, "# HELP webhook_http_requests_total HTTP requests handled by this process.\n# TYPE webhook_http_requests_total counter\nwebhook_http_requests_total %d\n", m.requests.Load())
	_, _ = fmt.Fprintf(w, "# HELP webhook_deliveries_created_total New idempotent deliveries accepted by this process.\n# TYPE webhook_deliveries_created_total counter\nwebhook_deliveries_created_total %d\n", m.created.Load())
	_, _ = fmt.Fprintf(w, "# HELP webhook_delivery_attempts_total Outbound delivery attempts made by this process.\n# TYPE webhook_delivery_attempts_total counter\nwebhook_delivery_attempts_total %d\n", m.attempts.Load())
	_, _ = fmt.Fprintf(w, "# HELP webhook_deliveries_succeeded_total Deliveries successfully acknowledged by targets.\n# TYPE webhook_deliveries_succeeded_total counter\nwebhook_deliveries_succeeded_total %d\n", m.succeeded.Load())
	_, _ = fmt.Fprintf(w, "# HELP webhook_deliveries_retried_total Deliveries scheduled for another attempt.\n# TYPE webhook_deliveries_retried_total counter\nwebhook_deliveries_retried_total %d\n", m.retried.Load())
	_, _ = fmt.Fprintf(w, "# HELP webhook_deliveries_dead_lettered_total Deliveries moved to the dead-letter state.\n# TYPE webhook_deliveries_dead_lettered_total counter\nwebhook_deliveries_dead_lettered_total %d\n", m.deadLettered.Load())
	_, _ = fmt.Fprintf(w, "# HELP webhook_delivery_permanent_failures_total Permanent target failures observed.\n# TYPE webhook_delivery_permanent_failures_total counter\nwebhook_delivery_permanent_failures_total %d\n", m.permanentFailures.Load())
}
