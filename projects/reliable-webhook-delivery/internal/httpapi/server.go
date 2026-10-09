package httpapi

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"log/slog"
	"mime"
	"net/http"
	"regexp"
	"strings"
	"time"

	"github.com/artin-bahrampour/reliable-webhook-delivery/internal/delivery"
	"github.com/artin-bahrampour/reliable-webhook-delivery/internal/telemetry"
)

type Creator interface {
	Create(context.Context, string, string, string, json.RawMessage) (delivery.Delivery, bool, error)
}
type Reader interface {
	Get(context.Context, string) (delivery.Delivery, error)
	Ping(context.Context) error
}
type Server struct {
	creator Creator
	reader  Reader
	metrics *telemetry.Metrics
	logger  *slog.Logger
}

var requestIDPattern = regexp.MustCompile(`^[A-Za-z0-9._-]{1,64}$`)
var uuidPattern = regexp.MustCompile(`(?i)^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`)

type createRequest struct {
	TargetID  string          `json:"target_id"`
	EventType string          `json:"event_type"`
	Payload   json.RawMessage `json:"payload"`
}
type errorResponse struct {
	Error     string `json:"error"`
	RequestID string `json:"request_id,omitempty"`
}

func New(creator Creator, reader Reader, metrics *telemetry.Metrics, logger *slog.Logger) http.Handler {
	s := &Server{creator: creator, reader: reader, metrics: metrics, logger: logger}
	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", s.health)
	mux.HandleFunc("GET /readyz", s.ready)
	mux.Handle("GET /metrics", metrics)
	mux.HandleFunc("POST /v1/deliveries", s.create)
	mux.HandleFunc("GET /v1/deliveries/{id}", s.get)
	return s.middleware(mux)
}
func (s *Server) middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		s.metrics.Request()
		w.Header().Set("X-Content-Type-Options", "nosniff")
		id := r.Header.Get("X-Request-ID")
		if !requestIDPattern.MatchString(id) {
			id = randomRequestID()
		}
		r.Header.Set("X-Request-ID", id)
		w.Header().Set("X-Request-ID", id)
		started := time.Now()
		next.ServeHTTP(w, r)
		s.logger.Info("http request", "request_id", id, "method", r.Method, "path", r.URL.Path, "duration_ms", time.Since(started).Milliseconds())
	})
}
func (s *Server) health(w http.ResponseWriter, _ *http.Request) { w.WriteHeader(http.StatusNoContent) }
func (s *Server) ready(w http.ResponseWriter, r *http.Request) {
	if err := s.reader.Ping(r.Context()); err != nil {
		writeError(w, r, http.StatusServiceUnavailable, "not_ready")
		return
	}
	w.WriteHeader(http.StatusNoContent)
}
func (s *Server) create(w http.ResponseWriter, r *http.Request) {
	mediaType, _, mediaErr := mime.ParseMediaType(r.Header.Get("Content-Type"))
	if mediaErr != nil || mediaType != "application/json" {
		writeError(w, r, http.StatusUnsupportedMediaType, "content_type_must_be_application_json")
		return
	}
	key := r.Header.Get("Idempotency-Key")
	if key == "" {
		writeError(w, r, http.StatusBadRequest, "idempotency_key_required")
		return
	}
	r.Body = http.MaxBytesReader(w, r.Body, delivery.MaxPayloadBytes+(16<<10))
	dec := json.NewDecoder(r.Body)
	dec.DisallowUnknownFields()
	var req createRequest
	if err := dec.Decode(&req); err != nil {
		writeDecodeError(w, r, err)
		return
	}
	var extra any
	if err := dec.Decode(&extra); err != io.EOF {
		writeError(w, r, http.StatusBadRequest, "request_must_contain_one_json_object")
		return
	}
	result, created, err := s.creator.Create(r.Context(), req.TargetID, key, req.EventType, req.Payload)
	if err != nil {
		switch {
		case errors.Is(err, delivery.ErrInvalidInput):
			writeError(w, r, http.StatusBadRequest, err.Error())
		case errors.Is(err, delivery.ErrIdempotencyConflict):
			writeError(w, r, http.StatusConflict, "idempotency_key_conflict")
		default:
			s.logger.Error("delivery create failed", "request_id", requestID(r), "error", err)
			writeError(w, r, http.StatusInternalServerError, "internal_error")
		}
		return
	}
	w.Header().Set("Location", "/v1/deliveries/"+result.ID)
	status := http.StatusOK
	if created {
		status = http.StatusAccepted
		s.metrics.Created()
	}
	writeJSON(w, status, result)
}
func (s *Server) get(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	if !uuidPattern.MatchString(id) {
		writeError(w, r, http.StatusBadRequest, "invalid_delivery_id")
		return
	}
	result, err := s.reader.Get(r.Context(), id)
	if err != nil {
		if errors.Is(err, delivery.ErrNotFound) {
			writeError(w, r, http.StatusNotFound, "delivery_not_found")
			return
		}
		s.logger.Error("delivery lookup failed", "request_id", requestID(r), "error", err)
		writeError(w, r, http.StatusInternalServerError, "internal_error")
		return
	}
	writeJSON(w, http.StatusOK, result)
}
func writeDecodeError(w http.ResponseWriter, r *http.Request, err error) {
	var maxErr *http.MaxBytesError
	if errors.As(err, &maxErr) {
		writeError(w, r, http.StatusRequestEntityTooLarge, "request_too_large")
		return
	}
	writeError(w, r, http.StatusBadRequest, "invalid_json_request")
}
func writeError(w http.ResponseWriter, r *http.Request, status int, code string) {
	writeJSON(w, status, errorResponse{Error: code, RequestID: requestID(r)})
}
func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}
func requestID(r *http.Request) string { return r.Header.Get("X-Request-ID") }
func randomRequestID() string {
	b := make([]byte, 16)
	if _, err := io.ReadFull(rand.Reader, b); err == nil {
		return hex.EncodeToString(b)
	}
	return strings.ReplaceAll(time.Now().UTC().Format("20060102T150405.000000000"), ".", "-")
}
