package adapter

import (
	"github.com/minbzk/poc-machine-law/machinev2/backend/interface/api"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
)

// FromRuleSpec converts ruleresolver.RuleSpec to api.RuleSpec
func FromRuleSpec(rulespec ruleresolver.RuleSpec) api.RuleSpec {
	var lawType *string
	if rulespec.LawType != nil {
		lawType = rulespec.LawType
	}

	var references *[]api.Reference
	// Convert References
	if rulespec.References != nil && len(rulespec.References) > 0 {
		refs := make([]api.Reference, 0, len(rulespec.References))
		for _, ref := range rulespec.References {
			refs = append(refs, FromReference(ref))
		}

		references = &refs
	}

	// Convert Requirements
	var requirements *[]api.Requirement
	if rulespec.Requirements != nil && len(rulespec.Requirements) > 0 {
		reqs := make([]api.Requirement, 0, len(rulespec.Requirements))
		for _, req := range rulespec.Requirements {
			reqs = append(reqs, FromRequirements(req))
		}
		requirements = &reqs
	}

	// Convert Actions
	var actions *[]api.Action
	if rulespec.Actions != nil && len(rulespec.Actions) > 0 {
		acts := make([]api.Action, 0, len(rulespec.Actions))
		for _, action := range rulespec.Actions {
			acts = append(acts, *FromAction(action))
		}
		actions = &acts
	}

	return api.RuleSpec{
		Actions:        actions,
		Uuid:           rulespec.UUID,
		Name:           rulespec.Name,
		Law:            rulespec.Law,
		LawType:        lawType,
		LegalCharacter: rulespec.LegalCharacter,
		DecisionType:   rulespec.DecisionType,
		Discoverable:   rulespec.Discoverable,
		Service:        rulespec.Service,
		Description:    rulespec.Description,
		ValidFrom:      rulespec.ValidFrom,
		References:     references,
		Requirements:   requirements,
		Properties:     FromProperties(rulespec.Properties),
	}
}

// FromProperties converts ruleresolver.Properties to api.Properties
func FromProperties(src ruleresolver.Properties) api.Properties {
	var applies *[]api.Apply
	if src.Applies != nil && len(src.Applies) > 0 {
		appls := make([]api.Apply, 0, len(src.Applies))
		for _, apply := range src.Applies {
			appls = append(appls, FromApply(apply))
		}

		applies = &appls
	}

	var inputs *[]api.InputField
	// Convert Input
	if src.Input != nil && len(src.Input) > 0 {
		inpts := make([]api.InputField, 0, len(src.Input))
		for _, input := range src.Input {
			inpts = append(inpts, FromInputField(input))
		}

		inputs = &inpts
	}

	var outputs *[]api.OutputField
	// Convert Output
	if src.Output != nil && len(src.Output) > 0 {
		outpts := make([]api.OutputField, 0, len(src.Output))
		for _, output := range src.Output {
			outpts = append(outpts, FromOutputField(output))
		}

		outputs = &outpts
	}

	var parameters *[]api.ParameterField
	// Convert Parameters
	if src.Parameters != nil && len(src.Parameters) > 0 {
		params := make([]api.ParameterField, 0, len(src.Parameters))
		for _, param := range src.Parameters {
			params = append(params, api.ParameterField(FromBaseField(param.BaseField)))
		}

		parameters = &params
	}

	var sources *[]api.SourceField
	// Convert Sources
	if src.Sources != nil && len(src.Sources) > 0 {
		srcs := make([]api.SourceField, 0, len(src.Sources))
		for _, source := range src.Sources {
			srcs = append(srcs, FromSourceField(source))
		}

		sources = &srcs
	}

	return api.Properties{
		Applies:     applies,
		Definitions: &src.Definitions,
		Input:       inputs,
		Output:      outputs,
		Parameters:  parameters,
		Sources:     sources,
	}
}

func FromOutputField(src ruleresolver.OutputField) api.OutputField {
	basefield := FromBaseField(src.BaseField)

	return api.OutputField{
		Name:             basefield.Name,
		Description:      basefield.Description,
		Type:             basefield.Type,
		Required:         basefield.Required,
		TypeSpec:         basefield.TypeSpec,
		Temporal:         basefield.Temporal,
		CitizenRelevance: src.CitizenRelevance,
	}
}

// FromBaseField converts ruleresolver.BaseField to api.BaseField
func FromBaseField(src ruleresolver.BaseField) api.BaseField {
	var typeSpec *api.TypeSpec
	if src.TypeSpec != nil {
		typeSpec = FromTypeSpec(*src.TypeSpec)
	}

	var temporal *api.Temporal
	if src.Temporal != nil {
		temporal = FromTemporal(*src.Temporal)
	}

	return api.BaseField{
		Name:        src.Name,
		Description: src.Description,
		Type:        src.Type,
		Required:    src.Required,
		TypeSpec:    typeSpec,
		Temporal:    temporal,
	}
}

// FromTypeSpec converts ruleresolver.TypeSpec to api.TypeSpec
func FromTypeSpec(src ruleresolver.TypeSpec) *api.TypeSpec {
	return &api.TypeSpec{
		Type:      src.Type,
		Unit:      src.Unit,
		Precision: src.Precision,
		Min:       src.Min,
		Max:       src.Max,
	}
}

// FromTemporal converts ruleresolver.Temporal to api.Temporal
func FromTemporal(src ruleresolver.Temporal) *api.Temporal {
	var reference *string
	if src.Reference != nil {
		// Handle the any type - convert to string if possible
		if refStr, ok := src.Reference.(string); ok {
			reference = &refStr
		}
	}

	return &api.Temporal{
		Type:           src.Type,
		PeriodType:     src.PeriodType,
		Reference:      reference,
		ImmutableAfter: src.ImmutableAfter,
	}
}

// FromSourceField converts ruleresolver.SourceField to api.SourceField
func FromSourceField(src ruleresolver.SourceField) api.SourceField {
	baseField := FromBaseField(src.BaseField)

	var sourceReference *api.SourceReference
	if src.SourceReference != nil {
		sourceReference = FromSourceReference(*src.SourceReference)
	}

	var serviceReference *api.ServiceReference
	if src.ServiceReference != nil {
		serviceRef := FromServiceReference(*src.ServiceReference)
		serviceReference = &serviceRef
	}

	return api.SourceField{
		Description:      baseField.Description,
		Name:             baseField.Name,
		Required:         baseField.Required,
		ServiceReference: serviceReference,
		SourceReference:  sourceReference,
		Temporal:         baseField.Temporal,
		Type:             baseField.Type,
		TypeSpec:         baseField.TypeSpec,
	}
}

// FromInputField converts ruleresolver.InputField to api.InputField
func FromInputField(src ruleresolver.InputField) api.InputField {
	baseField := FromBaseField(src.BaseField)

	return api.InputField{
		Description:      baseField.Description,
		Name:             baseField.Name,
		Required:         baseField.Required,
		ServiceReference: FromServiceReference(src.ServiceReference),
		Temporal:         baseField.Temporal,
		Type:             baseField.Type,
		TypeSpec:         baseField.TypeSpec,
	}
}

// FromSourceReference converts ruleresolver.SourceReference to api.SourceReference
func FromSourceReference(src ruleresolver.SourceReference) *api.SourceReference {
	var selectsOn *[]api.SelectField
	if src.SelectOn != nil && len(src.SelectOn) > 0 {
		selectOn := make([]api.SelectField, 0, len(src.SelectOn))
		for _, sel := range src.SelectOn {
			selectOn = append(selectOn, FromSelectField(sel))
		}

		selectsOn = &selectOn
	}

	return &api.SourceReference{
		SourceType: &src.SourceType,
		Table:      &src.Table,
		Field:      src.Field,
		Fields:     src.Fields,
		SelectOn:   selectsOn,
	}
}

// FromServiceReference converts ruleresolver.ServiceReference to api.ServiceReference
func FromServiceReference(src ruleresolver.ServiceReference) api.ServiceReference {
	return api.ServiceReference{
		Service:    src.Service,
		Field:      src.Field,
		Law:        src.Law,
		Parameters: FromParameters(src.Parameters),
	}
}

// FromParameter converts ruleresolver.Parameter to api.Parameter
func FromParameters(parameters []ruleresolver.Parameter) *[]api.Parameter {
	if parameters != nil && len(parameters) > 0 {
		params := make([]api.Parameter, 0, len(parameters))
		for _, param := range parameters {
			params = append(params, FromParameter(param))
		}

		return &params
	}

	return nil
}

// FromParameter converts ruleresolver.Parameter to api.Parameter
func FromParameter(src ruleresolver.Parameter) api.Parameter {
	return api.Parameter{
		Name:      src.Name,
		Reference: src.Reference,
	}
}

// FromSelectField converts ruleresolver.SelectField to api.SelectField
func FromSelectField(src ruleresolver.SelectField) api.SelectField {
	var actionValue api.ActionValue
	if src.Value.Action != nil {
		actionValue.FromAction(*FromAction(*src.Value.Action))
	} else {
		actionValue.FromActionValue1(*src.Value.Value)
	}

	return api.SelectField{
		Name:        src.Name,
		Description: src.Description,
		Type:        src.Type,
		Value:       actionValue,
	}
}

// FromApply converts ruleresolver.Apply to api.Apply
func FromApply(src ruleresolver.Apply) api.Apply {
	events := make([]api.ApplyEvent, 0, len(src.Events))
	for _, event := range src.Events {
		events = append(events, FromApplyEvent(event))
	}

	updates := make([]api.Update, 0, len(src.Update))
	for _, update := range src.Update {
		updates = append(updates, FromUpdate(update))
	}

	return api.Apply{
		Name:      src.Name,
		Aggregate: src.Aggregate,
		Events:    events,
		Update:    updates,
	}
}

func FromApplyEvent(event ruleresolver.Event) api.ApplyEvent {
	return api.ApplyEvent{
		Type:   event.Type,
		Filter: event.Filter,
	}
}

func FromUpdate(update ruleresolver.Update) api.Update {
	return api.Update{
		Method:  update.Method,
		Mapping: update.Mapping,
	}
}

// FromReference converts ruleresolver.Reference to api.Reference
func FromReference(src ruleresolver.Reference) api.Reference {
	return api.Reference{
		Law:     src.Law,
		Article: src.Article,
		Url:     src.URL,
	}
}

// FromRequirements converts ruleresolver.Requirement to api.Requirement
func FromRequirements(src ruleresolver.Requirement) api.Requirement {
	return api.Requirement{
		All: fromActionRequirements(src.All),
		Or:  fromActionRequirements(src.Or),
	}

}

func fromActionRequirements(actions *[]ruleresolver.ActionRequirement) *[]api.ActionRequirement {
	if actions == nil {
		return nil
	}

	all := make([]api.ActionRequirement, 0, len(*actions))
	for _, action := range *actions {
		all = append(all, FromActionRequirement(action))
	}

	return &all
}

// FromActionRequirement converts ruleresolver.ActionRequirement to api.ActionRequirement
func FromActionRequirement(src ruleresolver.ActionRequirement) api.ActionRequirement {
	var dst api.ActionRequirement
	if src.Requirement != nil {
		dst.FromRequirement(FromRequirements(*src.Requirement))
	} else if src.Action != nil {
		dst.FromAction(*FromAction(*src.Action))
	}

	return dst
}

func FromActionValue(av ruleresolver.ActionValue) api.ActionValue {
	var actionvalue api.ActionValue
	if av.Action != nil {
		actionvalue.FromAction(*FromAction(*av.Action))
	} else if av.Value != nil {
		actionvalue.FromActionValue1(*av.Value)
	}

	return actionvalue
}

func FromActionValues(av ruleresolver.ActionValues) api.ActionValues {
	var actionvalue api.ActionValues
	if av.ActionValues != nil {
		avs := make([]api.ActionValue, 0, len(*av.ActionValues))

		for _, av := range *av.ActionValues {
			avs = append(avs, FromActionValue(av))
		}

		actionvalue.FromActionValues0(avs)
	} else if av.Value != nil {
		actionvalue.FromActionValues1(*av.Value)
	}

	return actionvalue
}

// FromAction converts ruleresolver.Action to api.Action
func FromAction(action ruleresolver.Action) *api.Action {
	var value *api.ActionValue
	if action.Value != nil {
		v := FromActionValue(*action.Value)
		value = &v
	}

	var values *api.ActionValues
	if action.Values != nil {
		v := FromActionValues(*action.Values)
		values = &v
	}

	var conditions *[]api.Condition
	if action.Conditions != nil && len(action.Conditions) > 0 {
		conds := make([]api.Condition, 0, len(action.Conditions))
		for _, cond := range action.Conditions {
			conds = append(conds, ConditionToAPI(cond))
		}

		conditions = &conds
	}

	return &api.Action{
		Output:     action.Output,
		Operation:  action.Operation,
		Subject:    action.Subject,
		Unit:       action.Unit,
		Combine:    action.Combine,
		Conditions: conditions,
		Values:     values,
		Value:      value,
	}
}

// ConditionToAPI converts ruleresolver.Condition to api.Condition
func ConditionToAPI(src ruleresolver.Condition) api.Condition {
	var test *api.Action
	if src.Test != nil {
		test = FromAction(*src.Test)
	}

	var thenAV *api.ActionValue
	if src.Then != nil {
		av := FromActionValue(*src.Then)
		thenAV = &av
	}

	var elseAV *api.ActionValue
	if src.Else != nil {
		av := FromActionValue(*src.Else)
		elseAV = &av
	}

	return api.Condition{
		Else: elseAV,
		Test: test,
		Then: thenAV,
	}
}
