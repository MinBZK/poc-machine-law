package adapter

import (
	"fmt"

	"github.com/minbzk/poc-machine-law/machinev2/backend/interface/api"
	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
)

func FromPathNode(pathNode *model.PathNode) *api.PathNode {
	var details *map[string]any
	if pathNode.Details != nil {
		result := make(map[string]any)
		for k, v := range pathNode.Details {
			result[k] = convertMapInterfaceToMapString(v)
		}

		details = &result
	}

	var resolveType *string
	if pathNode.ResolveType != "" {
		resolveType = &pathNode.ResolveType
	}

	var result *any
	if pathNode.Result != nil {
		r := convertMapInterfaceToMapString(pathNode.Result)
		result = &r
	}

	return &api.PathNode{
		Children:    FromPathNodes(pathNode.Children),
		Details:     details,
		Name:        pathNode.Name,
		Required:    &pathNode.Required,
		ResolveType: resolveType,
		Result:      result,
		Type:        pathNode.Type,
	}
}

func FromPathNodes(pathNodes []*model.PathNode) *[]api.PathNode {
	nodes := make([]api.PathNode, 0, len(pathNodes))

	for idx := range pathNodes {
		nodes = append(nodes, *FromPathNode(pathNodes[idx]))
	}

	return &nodes
}

func convertMapInterfaceToMapString(input any) any {
	switch x := input.(type) {
	case map[string]any:
		result := make(map[string]any)
		for k, v := range x {
			result[k] = convertMapInterfaceToMapString(v)
		}
		return result
	case map[any]any:
		result := make(map[string]any)
		for k, v := range x {
			result[fmt.Sprintf("%v", k)] = convertMapInterfaceToMapString(v)
		}
		return result
	case []any:
		for i, v := range x {
			x[i] = convertMapInterfaceToMapString(v)
		}

		return x
	}

	return input
}
