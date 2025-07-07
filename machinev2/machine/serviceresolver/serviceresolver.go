package serviceresolver

import (
	"fmt"
	"sync"
	// "github.com/goccy/go-yaml"
)

type ServiceSpec struct {
	ID       string `json:"uuid" yaml:"uuid"`
	Name     string `json:"name" yaml:"name"`
	Endpoint string `json:"endpoint" yaml:"endpoint"`
}

var (
	serviceResolver *ServiceResolver
	mu              sync.Mutex
)

type ServiceResolver struct {
	Services []ServiceSpec
	mu       sync.RWMutex
}

type ServiceResolverConfig struct {
	Provider RuleSpecProvider
	URL      *string
	DIR      *string
}

func New(cfg ServiceResolverConfig) (*ServiceResolver, error) {
	mu.Lock()
	defer mu.Unlock()

	if serviceResolver == nil {
		provider, err := ProviderFactory(cfg)
		if err != nil {
			return nil, fmt.Errorf("provider factory: %w", err)
		}

		services, err := provider.Fetch()
		if err != nil {
			return nil, fmt.Errorf("provider fetch: %w", err)
		}

		serviceResolver = &ServiceResolver{
			Services: services,
		}
	}

	return serviceResolver, nil
}

func ptr[T any](a T) *T {
	return &a
}
