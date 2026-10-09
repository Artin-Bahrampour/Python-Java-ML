// receiver is a local development sink for exercising signed webhook deliveries.
// Do not deploy it as an application endpoint.
package main

import (
	"io"
	"log/slog"
	"net/http"
	"os"
	"time"

	"github.com/artin-bahrampour/reliable-webhook-delivery/internal/delivery"
)

func main() {
	secret := os.Getenv("WEBHOOK_DEMO_SECRET")
	if len(secret) < 32 {
		slog.Error("WEBHOOK_DEMO_SECRET must contain at least 32 bytes")
		os.Exit(1)
	}
	mux := http.NewServeMux()
	mux.HandleFunc("POST /webhooks", func(w http.ResponseWriter, r *http.Request) {
		body, err := io.ReadAll(http.MaxBytesReader(w, r.Body, 256<<10))
		if err != nil {
			http.Error(w, "invalid body", http.StatusRequestEntityTooLarge)
			return
		}
		timestamp := r.Header.Get("X-Webhook-Timestamp")
		if !delivery.Verify([]byte(secret), body, r.Header.Get("X-Event-ID"), r.Header.Get("X-Event-Type"), r.Header.Get("X-Delivery-Attempt"), timestamp, r.Header.Get("X-Webhook-Signature"), time.Now(), 5*time.Minute) {
			http.Error(w, "invalid signature", http.StatusUnauthorized)
			return
		}
		slog.Info("verified webhook received", "event_id", r.Header.Get("X-Event-ID"), "event_type", r.Header.Get("X-Event-Type"), "attempt", r.Header.Get("X-Delivery-Attempt"), "bytes", len(body))
		w.WriteHeader(http.StatusNoContent)
	})
	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, _ *http.Request) { w.WriteHeader(http.StatusNoContent) })
	addr := os.Getenv("RECEIVER_ADDR")
	if addr == "" {
		addr = ":8081"
	}
	srv := &http.Server{Addr: addr, Handler: mux, ReadHeaderTimeout: 3 * time.Second, ReadTimeout: 5 * time.Second, WriteTimeout: 5 * time.Second, IdleTimeout: 30 * time.Second}
	slog.Info("local webhook receiver listening", "addr", addr, "warning", "development-only")
	if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		slog.Error("receiver failed", "error", err)
		os.Exit(1)
	}
}
