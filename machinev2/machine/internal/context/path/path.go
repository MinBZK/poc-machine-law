package path

import (
	"context"

	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
)

type Path struct {
	paths []*model.PathNode
}

func New() *Path {
	return &Path{
		paths: make([]*model.PathNode, 0),
	}
}

func NewWith(node *model.PathNode) *Path {
	return &Path{
		paths: []*model.PathNode{node},
	}
}

// Add adds node to evaluation path
func (rc *Path) Add(node *model.PathNode) {
	if len(rc.paths) > 0 {
		rc.paths[len(rc.paths)-1].AddChild(node)
	}
	rc.paths = append(rc.paths, node)
}

// PopPath removes the last node from path
func (rc *Path) Pop() {
	if len(rc.paths) > 0 {
		rc.paths = rc.paths[:len(rc.paths)-1]
	}
}

type pathCtxKey struct{}

func FromContext(ctx context.Context) *Path {
	path, ok := ctx.Value(pathCtxKey{}).(*Path)
	if !ok {
		return New()
	}

	return path
}

func WithPath(ctx context.Context, path *Path) context.Context {
	return context.WithValue(ctx, pathCtxKey{}, path)
}

// Helper functions to add to your path package
func WithPathNode(ctx context.Context, node *model.PathNode) context.Context {
	p := FromContext(ctx)
	p.Add(node)
	return WithPath(ctx, p)
}
