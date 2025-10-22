package service

import (
	"context"

	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
	"github.com/minbzk/poc-machine-law/machinev2/machine/serviceresolver"
)

// ServiceProvider interface defines what a service provider needs to implement
type ServiceProvider interface {
	Evaluate(ctx context.Context, service, law string, parameters map[string]any, referenceDate string,
		overwriteInput map[string]any, requestedOutput string, approved bool) (*model.RuleResult, error)
	GetRuleResolver() *ruleresolver.RuleResolver
	GetServiceResolver() *serviceresolver.ServiceResolver
	GetCaseManager() CaseManagerAccessor
	GetClaimManager() ClaimManagerAccessor
	RuleServicesInMemory() bool
	HasOrganizationName() bool
	GetOrganizationName() string
	InStandAloneMode() bool
	HasExternalClaimResolverEndpoint() bool
	GetExternalClaimResolverEndpoint() string
}

// CaseManagerAccessor interface for accessing case manager events
type CaseManagerAccessor interface {
	GetEvents(caseID any) []model.Event
}

// ClaimManagerAccessor interface for accessing claim manager functionality
type ClaimManagerAccessor interface {
	GetClaimsByBSN(bsn string, approved bool, includeRejected bool) ([]model.Claim, error)
	GetClaimByBSNServiceLaw(bsn string, service string, law string, approved bool, includeRejected bool) (map[string]model.Claim, error)
}
