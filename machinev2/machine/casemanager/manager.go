package casemanager

import (
	"context"

	"github.com/google/uuid"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
)

// CaseManager interface defines the contract for case management operations.
type CaseManager interface {
	// Case lifecycle operations
	SubmitCase(ctx context.Context, bsn, serviceType, law string, parameters, claimedResult map[string]any, approvedClaimsOnly bool) (uuid.UUID, error)
	CompleteManualReview(ctx context.Context, caseID uuid.UUID, verifierID string, approved bool, reason string, overrideResult map[string]any) error
	ObjectCase(ctx context.Context, caseID uuid.UUID, reason string) error
	DetermineObjectionStatus(caseID uuid.UUID, possible *bool, notPossibleReason string, objectionPeriod, decisionPeriod, extensionPeriod *int) error
	DetermineObjectionAdmissibility(caseID uuid.UUID, admissible *bool) error
	DetermineAppealStatus(caseID uuid.UUID, possible *bool, notPossibleReason string, appealPeriod *int, directAppeal *bool, directAppealReason, competentCourt, courtType string) error

	// Case queries
	GetCase(ctx context.Context, bsn, serviceType, law string) (*Case, error)
	GetCaseByID(ctx context.Context, id uuid.UUID) (*Case, error)
	GetCasesByStatus(serviceType string, status CaseStatus) []*Case
	GetCasesByLaw(ctx context.Context, service, law string) ([]*Case, error)
	GetCasesByBSN(ctx context.Context, bsn string) ([]*Case, error)

	// Case validation
	CanAppeal(caseID uuid.UUID) (bool, error)
	CanObject(caseID uuid.UUID) (bool, error)

	// Event operations
	GetEvents(caseID any) []model.Event
	GetEventsByUUID(caseID uuid.UUID) []model.Event

	// Index operations
	SetCase(caseID uuid.UUID, key string)
	GetCaseByKey(key string) (uuid.UUID, bool)

	// Lifecycle
	Wait()
	Close()
}
