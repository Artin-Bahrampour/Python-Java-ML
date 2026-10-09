package delivery

import (
	"math/rand"
	"time"
)

// Backoff returns full-jitter exponential backoff, capped to max. Attempts are one-based.
func Backoff(attempt int, base, max time.Duration) time.Duration {
	if attempt < 1 {
		attempt = 1
	}
	capDelay := base
	for i := 1; i < attempt && capDelay < max; i++ {
		if capDelay > max/2 {
			capDelay = max
			break
		}
		capDelay *= 2
	}
	if capDelay > max {
		capDelay = max
	}
	if capDelay <= 1 {
		return capDelay
	}
	return time.Duration(rand.Int63n(int64(capDelay)))
}
