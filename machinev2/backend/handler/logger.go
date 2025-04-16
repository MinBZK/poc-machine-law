package handler

import (
	"bytes"
	"io"
	"log/slog"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5/middleware"
)

// StructuredLogger is a simple, but powerful implementation of a custom structured
// logger backed by Go's standard library slog.
type StructuredLogger struct {
	Logger *slog.Logger
}

// NewStructuredLogger creates a new structured logger
func NewStructuredLogger(logger *slog.Logger) func(next http.Handler) http.Handler {
	return middleware.RequestLogger(&StructuredLogger{logger})
}

// NewLogEntry creates a new log entry for the request
func (l *StructuredLogger) NewLogEntry(r *http.Request) middleware.LogEntry {
	// Read the body
	bodyBytes, _ := readBody(r)

	entry := &StructuredLoggerEntry{
		Logger:    l.Logger,
		Request:   r,
		RequestID: middleware.GetReqID(r.Context()),
		Body:      string(bodyBytes),
	}

	// Log the request
	entry.Logger.Info("request started",
		"request_id", entry.RequestID,
		"method", r.Method,
		"path", r.URL.Path,
		"query", r.URL.Query(),
		"remote_addr", r.RemoteAddr,
		"user_agent", r.UserAgent(),
		"request_body", entry.Body,
	)

	return entry
}

// StructuredLoggerEntry holds data for a request log entry
type StructuredLoggerEntry struct {
	Logger    *slog.Logger
	Request   *http.Request
	RequestID string
	Body      string
}

// Write writes the final log entry when the request is complete
func (l *StructuredLoggerEntry) Write(status, bytes int, header http.Header, elapsed time.Duration, extra any) {
	l.Logger.Info("request complete",
		"request_id", l.RequestID,
		"method", l.Request.Method,
		"path", l.Request.URL.Path,
		"status", status,
		"bytes", bytes,
		"elapsed_ms", float64(elapsed.Nanoseconds())/1000000.0,
		"request_body", l.Body,
	)
}

// Panic writes a log entry for a panic
func (l *StructuredLoggerEntry) Panic(v any, stack []byte) {
	l.Logger.Error("request panic",
		"request_id", l.RequestID,
		"method", l.Request.Method,
		"path", l.Request.URL.Path,
		"panic", v,
		"stack", string(stack),
		"request_body", l.Body,
	)
}

// Helper function to read the request body without consuming it
func readBody(r *http.Request) ([]byte, error) {
	if r.Body == nil {
		return []byte{}, nil
	}

	bodyBytes, err := io.ReadAll(r.Body)
	if err != nil {
		return nil, err
	}

	// Restore the body to be read again
	r.Body = io.NopCloser(bytes.NewBuffer(bodyBytes))

	return bodyBytes, nil
}

// BodyLogMiddleware is a middleware that logs request bodies
// Use this as a standalone middleware if you just want body logging
func BodyLogMiddleware(logger *slog.Logger) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Get request ID from context
			requestID := middleware.GetReqID(r.Context())

			// Read and restore the body
			bodyBytes, err := readBody(r)
			if err != nil {
				logger.Error("failed to read request body",
					"request_id", requestID,
					"error", err,
				)
				http.Error(w, "Internal Server Error", http.StatusInternalServerError)
				return
			}

			// Log the request with body
			logger.Info("incoming request",
				"request_id", requestID,
				"method", r.Method,
				"path", r.URL.Path,
				"remote_addr", r.RemoteAddr,
				"body", string(bodyBytes),
			)

			// Call the next handler
			next.ServeHTTP(w, r)
		})
	}
}
