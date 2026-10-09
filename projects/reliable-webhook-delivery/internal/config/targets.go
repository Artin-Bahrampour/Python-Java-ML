package config

import (
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/url"
	"os"
	"strings"

	"github.com/artin-bahrampour/reliable-webhook-delivery/internal/delivery"
)

type targetFile struct {
	Targets []targetEntry `json:"targets"`
}
type targetEntry struct {
	ID        string `json:"id"`
	URL       string `json:"url"`
	SecretEnv string `json:"secret_env"`
}

// LoadTargets resolves secrets from the environment and validates destinations before the API accepts work.
func LoadTargets(path string, allowInsecure bool, lookup func(string) (string, bool)) (map[string]delivery.Target, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read targets file: %w", err)
	}
	if len(raw) > 1<<20 {
		return nil, fmt.Errorf("targets file exceeds 1 MiB")
	}
	var cfg targetFile
	dec := json.NewDecoder(strings.NewReader(string(raw)))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&cfg); err != nil {
		return nil, fmt.Errorf("parse targets file: %w", err)
	}
	var extra any
	if err := dec.Decode(&extra); err != io.EOF {
		return nil, fmt.Errorf("parse targets file: expected exactly one JSON object")
	}
	if len(cfg.Targets) == 0 {
		return nil, fmt.Errorf("targets file must define at least one target")
	}
	out := make(map[string]delivery.Target, len(cfg.Targets))
	for _, item := range cfg.Targets {
		if !validTargetID(item.ID) {
			return nil, fmt.Errorf("invalid target id %q", item.ID)
		}
		if _, exists := out[item.ID]; exists {
			return nil, fmt.Errorf("duplicate target id %q", item.ID)
		}
		u, err := url.ParseRequestURI(item.URL)
		if err != nil || u.Hostname() == "" || u.User != nil || u.RawQuery != "" || u.Fragment != "" {
			return nil, fmt.Errorf("target %q has an invalid URL", item.ID)
		}
		if u.Scheme != "https" && !(allowInsecure && u.Scheme == "http") {
			return nil, fmt.Errorf("target %q must use HTTPS (HTTP is permitted only when ALLOW_INSECURE_TARGETS=true)", item.ID)
		}
		ipHost := strings.Split(u.Hostname(), "%")[0]
		if net.ParseIP(ipHost) != nil && !allowInsecure {
			return nil, fmt.Errorf("target %q must use a DNS hostname, not an IP literal", item.ID)
		}
		if item.SecretEnv == "" {
			return nil, fmt.Errorf("target %q must name a secret_env variable", item.ID)
		}
		secret, ok := lookup(item.SecretEnv)
		if !ok || len(secret) < 32 {
			return nil, fmt.Errorf("secret environment variable %s for target %q must contain at least 32 bytes", item.SecretEnv, item.ID)
		}
		out[item.ID] = delivery.Target{ID: item.ID, URL: u.String(), Secret: []byte(secret)}
	}
	return out, nil
}
func validTargetID(s string) bool {
	if len(s) < 1 || len(s) > 64 {
		return false
	}
	for _, r := range s {
		if !(r >= 'a' && r <= 'z' || r >= '0' && r <= '9' || r == '-' || r == '_') {
			return false
		}
	}
	return true
}
