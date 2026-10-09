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
	"github.com/artin-bahrampour/reliable-webhook-delivery/internal/delivery"
	"github.com/artin-bahrampour/reliable-webhook-delivery/internal/httpapi"
	"github.com/artin-bahrampour/reliable-webhook-delivery/internal/store"
	"github.com/artin-bahrampour/reliable-webhook-delivery/internal/telemetry"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
	if err := run(logger); err != nil {
		logger.Error("api stopped", "error", err)
		os.Exit(1)
	}
}

func run(logger *slog.Logger) error {
	cfg, err := config.Load()
	if err != nil {
		return err
	}
	targets, err := config.LoadTargets(cfg.TargetsFile, cfg.AllowInsecureTargets, os.LookupEnv)
	if err != nil {
		return err
	}

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()
	db, err := store.NewPostgres(ctx, cfg.DatabaseURL, logger)
	if err != nil {
		return err
	}
	defer db.Close()

	service := delivery.NewService(db, targets)
	metrics := telemetry.NewMetrics()
	handler := httpapi.New(service, db, metrics, logger)
	server := &http.Server{
		Addr: cfg.HTTPAddr, Handler: handler,
		ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 10 * time.Second,
		WriteTimeout: 15 * time.Second, IdleTimeout: 60 * time.Second,
	}
	errCh := make(chan error, 1)
	go func() {
		logger.Info("api listening", "addr", cfg.HTTPAddr, "target_count", len(targets))
		errCh <- server.ListenAndServe()
	}()
	select {
	case <-ctx.Done():
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		if err := server.Shutdown(shutdownCtx); err != nil {
			return err
		}
		err := <-errCh
		if errors.Is(err, http.ErrServerClosed) {
			return nil
		}
		return err
	case err := <-errCh:
		if errors.Is(err, http.ErrServerClosed) {
			return nil
		}
		return err
	}
}
