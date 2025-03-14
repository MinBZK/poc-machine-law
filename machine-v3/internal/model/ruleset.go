package model

// RuleResult contains the results of a rule evaluation
type RuleResult struct {
	Output          map[string]interface{} `json:"output"`
	RequirementsMet bool                   `json:"requirements_met"`
	Input           map[string]interface{} `json:"input"`
	RulespecUUID    string                 `json:"rulespec_uuid"`
	Path            *PathNode              `json:"path,omitempty"`
	MissingRequired bool                   `json:"missing_required"`
}

// NewRuleResult creates a new RuleResult from engine result
func NewRuleResult(result map[string]interface{}, rulespecUUID string) *RuleResult {
	// Extract output
	output := make(map[string]interface{})
	if outputMap, ok := result["output"].(map[string]interface{}); ok {
		for name, data := range outputMap {
			if dataMap, ok := data.(map[string]interface{}); ok {
				output[name] = dataMap["value"]
			}
		}
	}

	// Extract path
	var path *PathNode
	if pathObj, ok := result["path"]; ok {
		if pathNode, ok := pathObj.(*PathNode); ok {
			path = pathNode
		}
	}

	return &RuleResult{
		Output:          output,
		RequirementsMet: result["requirements_met"].(bool),
		Input:           result["input"].(map[string]interface{}),
		RulespecUUID:    rulespecUUID,
		Path:            path,
		MissingRequired: result["missing_required"].(bool),
	}
}
