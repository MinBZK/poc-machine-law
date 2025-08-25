package resolvermap

import (
	"context"
	"sync"

	"github.com/minbzk/poc-machine-law/machinev2/machine/resolver"
)

var _ resolver.Resolver = &MapResolver{}

type MapResolver struct {
	data         map[string]any
	resolverType string
	mu           sync.RWMutex
}

func New(data map[string]any, rt string) *MapResolver {
	return &MapResolver{
		data:         data,
		resolverType: rt,
		mu:           sync.RWMutex{},
	}
}

// Resolve implements Resolver.
func (l *MapResolver) Resolve(_ context.Context, key string) (*resolver.Resolved, bool) {
	v, ok := l.Get(key)
	return &resolver.Resolved{Value: v}, ok
}

func (l *MapResolver) Set(key string, data any) {
	l.mu.Lock()
	defer l.mu.Unlock()

	l.data[key] = data
}

func (l *MapResolver) Get(key string) (any, bool) {
	l.mu.RLock()
	value, ok := l.data[key]
	l.mu.RUnlock()

	return value, ok
}

// ResolveType implements Resolver.
func (l *MapResolver) ResolveType() string {
	return l.resolverType
}
