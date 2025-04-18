package handler

import (
	"fmt"
	"log/slog"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	cache "github.com/victorspringer/http-cache"
	"github.com/victorspringer/http-cache/adapter/memory"

	"github.com/minbzk/poc-machine-law/machinev2/backend/config"
	"github.com/minbzk/poc-machine-law/machinev2/backend/interface/api"
	"github.com/minbzk/poc-machine-law/machinev2/backend/service"
)

var _ api.StrictServerInterface = &Handler{}

type Handler struct {
	*http.Server
	cfg      *config.Config
	logger   *slog.Logger
	servicer service.Servicer
}

func New(logger *slog.Logger, cfg *config.Config, servicer service.Servicer) (*Handler, error) {
	h := &Handler{
		Server: &http.Server{
			Addr: cfg.BackendListenAddress,
		},
		cfg:      cfg,
		logger:   logger,
		servicer: servicer,
	}

	handler, err := router(h)
	if err != nil {
		return nil, err
	}

	h.Handler = handler

	return h, nil
}

func router(handler *Handler) (http.Handler, error) {
	memcached, err := memory.NewAdapter(
		memory.AdapterWithAlgorithm(memory.LRU),
		memory.AdapterWithCapacity(10000000),
	)
	if err != nil {
		return nil, fmt.Errorf("memory new adapter: %w", err)
	}

	cacheClient, err := cache.NewClient(
		cache.ClientWithAdapter(memcached),
		cache.ClientWithTTL(1*time.Minute),
		cache.ClientWithRefreshKey("opn"),
	)
	if err != nil {
		return nil, fmt.Errorf("cache new client: %w", err)
	}

	r := chi.NewRouter()
	r.Use(middleware.RequestID)
	r.Use(NewStructuredLogger(handler.logger))
	r.Use(middleware.Recoverer)
	r.Use(handler.Heartbeat("/healthz"))

	// Metrics middleware example
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ww := middleware.NewWrapResponseWriter(w, r.ProtoMajor)
			start := time.Now()
			next.ServeHTTP(ww, r)
			duration := time.Since(start).Seconds()
			status := ww.Status()
			responseTime.WithLabelValues(r.Method, r.URL.Path).Observe(duration)
			requestsCount.WithLabelValues(r.Method, r.URL.Path, strconv.Itoa(status)).Inc()

		})
	})

	r.Group(func(r chi.Router) {
		r.Use(middleware.SetHeader("Content-Type", "application/json"))
		r.Use(cacheClient.Middleware)
		r.Mount("/v0", api.Handler(api.NewStrictHandler(handler, nil)))
	})

	r.Handle("/metrics", promhttp.Handler())

	return r, nil
}

func (handler *Handler) Heartbeat(endpoint string) func(http.Handler) http.Handler {
	return func(h http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if (r.Method == "GET" || r.Method == "HEAD") && strings.EqualFold(r.URL.Path, endpoint) {
				w.Header().Set("Content-Type", "text/plain")
				w.WriteHeader(http.StatusOK)
				w.Write([]byte("."))
				return
			}

			h.ServeHTTP(w, r)
		})
	}
}

var (
	responseTime = prometheus.NewHistogramVec(prometheus.HistogramOpts{
		Name:    "http_response_time_seconds",
		Help:    "Response time distribution",
		Buckets: prometheus.DefBuckets,
	}, []string{"method", "path"})

	requestsCount = prometheus.NewCounterVec(prometheus.CounterOpts{
		Name: "http_requests_total",
		Help: "Total number of HTTP requests",
	}, []string{"method", "path", "status"})
)

func init() {
	prometheus.MustRegister(responseTime)
	prometheus.MustRegister(requestsCount)
}

func NewBadRequestErrorResponseObject(err error) api.BadRequestErrorResponseJSONResponse {
	return api.BadRequestErrorResponseJSONResponse{
		Errors: []api.Error{{Message: err.Error()}},
	}
}

func NewResourceNotFoundErrorResponseObject(err error) api.ResourceNotFoundErrorResponseJSONResponse {
	return api.ResourceNotFoundErrorResponseJSONResponse{
		Errors: &[]api.Error{{Message: err.Error()}},
	}
}
