package source

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httputil"
	"net/url"

	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/logger"
)

type defaultResolver struct {
	endpoint string
	client   *http.Client
}

func newDefaultResolver(endpoint string) defaultResolver {
	return defaultResolver{
		endpoint: endpoint,
		client:   http.DefaultClient,
	}
}

// Resolve implements Resolver.
func (c defaultResolver) do(ctx context.Context, key string, table string, field string, filters Filters) (any, error) {
	logr := logger.FromContext(ctx).WithName("resolver")
	logr = logr.WithField("resolver", "external_claim").
		WithField("resolver_type", "default").
		WithField("table", table).
		WithField("field", field).
		WithField("filters", filters)

	endpoint, err := url.Parse(fmt.Sprintf("%s%s", c.endpoint, table))
	if err != nil {
		return nil, fmt.Errorf("url parse: %w", err)
	}

	b := &bytes.Buffer{}
	if err := json.NewEncoder(b).Encode(filters); err != nil {
		return nil, fmt.Errorf("encode: %w", err)
	}

	values := url.Values{}
	values.Add("fields", field)
	values.Add("filter", b.String())

	endpoint.RawQuery = values.Encode()

	logr.Debug("url parse", logger.NewField("endpoint", endpoint))

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint.String(), nil)
	if err != nil {
		return nil, fmt.Errorf("new request with context: %w", err)
	}
	logr.Debug("do request")

	response, err := c.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("do: %w", err)
	}

	logr.Debug("request done")

	defer response.Body.Close()

	if response.StatusCode != http.StatusOK {
		dump, _ := httputil.DumpResponse(response, true)
		return nil, fmt.Errorf("invalid http status: %d %v", response.StatusCode, string(dump))
	}

	body := []map[string]any{}
	if err := json.NewDecoder(response.Body).Decode(&body); err != nil {
		return nil, fmt.Errorf("json decode: %w", err)
	}

	switch len(body) {
	case 0:
		return nil, fmt.Errorf("field not found")
	case 1:
		return body[0][field], nil
	default:
		panic("unimplemented, multiple returns")
	}
}
