package main

import (
	"context"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/artin-bahrampour/reliable-webhook-delivery/internal/config"
	"github.com/artin-bahrampour/reliable-webhook-delivery/internal/store"
	"github.com/artin-bahrampour/reliable-webhook-delivery/internal/telemetry"
	"github.com/artin-bahrampour/reliable-webhook-delivery/internal/worker"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
	cfg, err := config.Load()
	if err != nil {
		logger.Error("invalid configuration", "error", err)
		os.Exit(1)
	}
	targets, err := config.LoadTargets(cfg.TargetsFile, cfg.AllowInsecureTargets, os.LookupEnv)
	if err != nil {
		logger.Error("invalid target configuration", "error", err)
		os.Exit(1)
	}
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()
	db, err := store.NewPostgres(ctx, cfg.DatabaseURL, logger)
	if err != nil {
		logger.Error("database initialization failed", "error", err)
		os.Exit(1)
	}
	defer db.Close()
	metrics := telemetry.NewMetrics()
	mux := http.NewServeMux()
	mux.HandleFunc("GET /metrics", func(w http.ResponseWriter, r *http.Request) { metrics.Request(); metrics.ServeHTTP(w, r) })
	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, _ *http.Request) { metrics.Request(); w.WriteHeader(http.StatusNoContent) })
	mux.HandleFunc("GET /readyz", func(w http.ResponseWriter, r *http.Request) {
		metrics.Request()
		if err := db.Ping(r.Context()); err != nil {
			http.Error(w, "not ready", http.StatusServiceUnavailable)
			return
		}
		w.WriteHeader(http.StatusNoContent)
	})
	metricsServer := &http.Server{Addr: cfg.WorkerMetricsAddr, Handler: mux, ReadHeaderTimeout: 3 * time.Second, ReadTimeout: 5 * time.Second, WriteTimeout: 5 * time.Second, IdleTimeout: 30 * time.Second}
	metricsErr := make(chan error, 1)
	go func() {
		logger.Info("worker metrics listening", "addr", cfg.WorkerMetricsAddr)
		metricsErr <- metricsServer.ListenAndServe()
	}()
	runner := worker.New(db, targets, metrics, logger, cfg.WorkerOptions())
	done := make(chan struct{})
	go func() {
		defer close(done)
		if err := runner.Run(ctx); err != nil {
			logger.Error("worker stopped", "error", err)
			stop()
		}
	}()
	select {
	case <-ctx.Done():
	case err := <-metricsErr:
		if err != nil && !errors.Is(err, http.ErrServerClosed) {
			logger.Error("metrics server failed", "error", err)
			stop()
		}
	}
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := metricsServer.Shutdown(shutdownCtx); err != nil {
		logger.Error("metrics shutdown failed", "error", err)
	}
	<-done
}
