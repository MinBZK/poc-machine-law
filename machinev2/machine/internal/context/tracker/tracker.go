package tracker

import (
	"context"
)

type Tracker struct {
	resolvedPaths map[string]any
}

func New() *Tracker {
	return &Tracker{
		resolvedPaths: make(map[string]any),
	}
}

func (t *Tracker) Track(path string, value any) {
	t.resolvedPaths[path] = value
}

func (t *Tracker) ResolvedPaths() map[string]any {
	return t.resolvedPaths
}

type trackerCtxKey struct{}

func FromContext(ctx context.Context) *Tracker {
	path, ok := ctx.Value(trackerCtxKey{}).(*Tracker)
	if !ok {
		return New()
	}

	return path
}

func WithTracker(ctx context.Context, path *Tracker) context.Context {
	return context.WithValue(ctx, trackerCtxKey{}, path)
}

// Helper functions to add to your path package
func WithResolvedPath(ctx context.Context, path string, value any) context.Context {
	p := FromContext(ctx)
	p.Track(path, value)
	return WithTracker(ctx, p)
}
