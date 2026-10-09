package delivery

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"strconv"
	"time"
)

// Sign binds the timestamp and delivery metadata to the exact body bytes.
func Sign(secret []byte, eventID, eventType, attempt string, body []byte, timestamp time.Time) string {
	ts := strconv.FormatInt(timestamp.Unix(), 10)
	mac := hmac.New(sha256.New, secret)
	_, _ = mac.Write([]byte(ts + "\n" + eventID + "\n" + eventType + "\n" + attempt + "\n"))
	_, _ = mac.Write(body)
	return fmt.Sprintf("t=%s,v1=%s", ts, hex.EncodeToString(mac.Sum(nil)))
}

func Verify(secret, body []byte, eventID, eventType, attempt, timestampHeader, signature string, now time.Time, tolerance time.Duration) bool {
	ts, err := strconv.ParseInt(timestampHeader, 10, 64)
	if err != nil {
		return false
	}
	signedAt := time.Unix(ts, 0)
	if signedAt.Before(now.Add(-tolerance)) || signedAt.After(now.Add(tolerance)) {
		return false
	}
	expected := Sign(secret, eventID, eventType, attempt, body, signedAt)
	return hmac.Equal([]byte(expected), []byte(signature))
}
