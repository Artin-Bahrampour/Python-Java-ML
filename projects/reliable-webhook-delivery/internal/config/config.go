package config

import (
	"fmt"
	"os"
	"strconv"
	"time"

	"github.com/artin-bahrampour/reliable-webhook-delivery/internal/worker"
)

type Config struct {
	DatabaseURL          string
	HTTPAddr             string
	WorkerMetricsAddr    string
	TargetsFile          string
	AllowInsecureTargets bool
	PollInterval         time.Duration
	LeaseDuration        time.Duration
	RequestTimeout       time.Duration
	MaxAttempts          int
	BaseBackoff          time.Duration
	MaxBackoff           time.Duration
}

func Load() (Config, error) {
	c := Config{
		DatabaseURL: os.Getenv("DB_URL"), HTTPAddr: envOr("HTTP_ADDR", ":8080"), WorkerMetricsAddr: envOr("WORKER_METRICS_ADDR", ":9090"),
		TargetsFile:  envOr("TARGETS_FILE", "config/targets.json"),
		PollInterval: 500 * time.Millisecond, LeaseDuration: 45 * time.Second,
		RequestTimeout: 10 * time.Second, MaxAttempts: 8,
		BaseBackoff: time.Second, MaxBackoff: 5 * time.Minute,
	}
	if c.DatabaseURL == "" {
		return Config{}, fmt.Errorf("DB_URL is required")
	}
	var err error
	if c.PollInterval, err = durationEnv("POLL_INTERVAL", c.PollInterval); err != nil {
		return Config{}, err
	}
	if c.LeaseDuration, err = durationEnv("LEASE_DURATION", c.LeaseDuration); err != nil {
		return Config{}, err
	}
	if c.RequestTimeout, err = durationEnv("REQUEST_TIMEOUT", c.RequestTimeout); err != nil {
		return Config{}, err
	}
	if c.BaseBackoff, err = durationEnv("BASE_BACKOFF", c.BaseBackoff); err != nil {
		return Config{}, err
	}
	if c.MaxBackoff, err = durationEnv("MAX_BACKOFF", c.MaxBackoff); err != nil {
		return Config{}, err
	}
	if c.MaxAttempts, err = intEnv("MAX_ATTEMPTS", c.MaxAttempts); err != nil {
		return Config{}, err
	}
	insecure, err := strconv.ParseBool(envOr("ALLOW_INSECURE_TARGETS", "false"))
	if err != nil {
		return Config{}, fmt.Errorf("ALLOW_INSECURE_TARGETS must be a boolean: %w", err)
	}
	c.AllowInsecureTargets = insecure
	if c.PollInterval <= 0 || c.RequestTimeout <= 0 || c.LeaseDuration <= 0 || c.BaseBackoff <= 0 || c.MaxBackoff <= 0 {
		return Config{}, fmt.Errorf("poll interval, timeouts, lease and backoff durations must be positive")
	}
	if c.MaxAttempts < 1 || c.MaxAttempts > 100 {
		return Config{}, fmt.Errorf("MAX_ATTEMPTS must be between 1 and 100")
	}
	if c.MaxBackoff < c.BaseBackoff {
		return Config{}, fmt.Errorf("MAX_BACKOFF must be greater than or equal to BASE_BACKOFF")
	}
	if c.LeaseDuration < c.RequestTimeout+5*time.Second {
		return Config{}, fmt.Errorf("LEASE_DURATION must exceed REQUEST_TIMEOUT by at least 5 seconds")
	}
	return c, nil
}

func (c Config) WorkerOptions() worker.Options {
	return worker.Options{PollInterval: c.PollInterval, LeaseDuration: c.LeaseDuration, RequestTimeout: c.RequestTimeout, MaxAttempts: c.MaxAttempts, BaseBackoff: c.BaseBackoff, MaxBackoff: c.MaxBackoff}
}
func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
func durationEnv(key string, fallback time.Duration) (time.Duration, error) {
	v := os.Getenv(key)
	if v == "" {
		return fallback, nil
	}
	d, err := time.ParseDuration(v)
	if err != nil {
		return 0, fmt.Errorf("%s must be a duration: %w", key, err)
	}
	return d, nil
}
func intEnv(key string, fallback int) (int, error) {
	v := os.Getenv(key)
	if v == "" {
		return fallback, nil
	}
	n, err := strconv.Atoi(v)
	if err != nil {
		return 0, fmt.Errorf("%s must be an integer: %w", key, err)
	}
	return n, nil
}
