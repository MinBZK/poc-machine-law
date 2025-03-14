package model

// PathNode represents a node in the evaluation path
type PathNode struct {
	Type        string                 `json:"type"`
	Name        string                 `json:"name"`
	Result      interface{}            `json:"result"`
	ResolveType string                 `json:"resolve_type,omitempty"`
	Required    bool                   `json:"required"`
	Details     map[string]interface{} `json:"details,omitempty"`
	Children    []*PathNode            `json:"children,omitempty"`
}

// AddChild adds a child node to this node
func (p *PathNode) AddChild(child *PathNode) {
	if p.Children == nil {
		p.Children = make([]*PathNode, 0)
	}
	p.Children = append(p.Children, child)
}
