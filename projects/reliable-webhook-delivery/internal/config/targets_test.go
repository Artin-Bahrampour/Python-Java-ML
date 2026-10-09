package config

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func writeTargets(t *testing.T, body string) string {
	t.Helper()
	p := filepath.Join(t.TempDir(), "targets.json")
	if err := os.WriteFile(p, []byte(body), 0600); err != nil {
		t.Fatal(err)
	}
	return p
}
func TestLoadTargetsResolvesSecret(t *testing.T) {
	p := writeTargets(t, `{"targets":[{"id":"billing","url":"https://hooks.example.test/events","secret_env":"HOOK_SECRET"}]}`)
	got, err := LoadTargets(p, false, func(k string) (string, bool) { return strings.Repeat("s", 32), k == "HOOK_SECRET" })
	if err != nil {
		t.Fatal(err)
	}
	if got["billing"].URL != "https://hooks.example.test/events" {
		t.Fatal(got)
	}
}
func TestLoadTargetsRejectsHTTPByDefault(t *testing.T) {
	p := writeTargets(t, `{"targets":[{"id":"billing","url":"http://localhost/events","secret_env":"HOOK_SECRET"}]}`)
	_, err := LoadTargets(p, false, func(string) (string, bool) { return strings.Repeat("s", 32), true })
	if err == nil {
		t.Fatal("expected HTTP target rejection")
	}
}
func TestLoadTargetsRejectsWeakSecret(t *testing.T) {
	p := writeTargets(t, `{"targets":[{"id":"billing","url":"https://hooks.example.test/events","secret_env":"HOOK_SECRET"}]}`)
	_, err := LoadTargets(p, false, func(string) (string, bool) { return "short", true })
	if err == nil {
		t.Fatal("expected weak secret rejection")
	}
}
func TestLoadTargetsAllowsHTTPOnlyInDevelopmentMode(t *testing.T) {
	p := writeTargets(t, `{"targets":[{"id":"local","url":"http://receiver:8081/webhooks","secret_env":"HOOK_SECRET"}]}`)
	_, err := LoadTargets(p, true, func(string) (string, bool) { return strings.Repeat("s", 32), true })
	if err != nil {
		t.Fatal(err)
	}
}
