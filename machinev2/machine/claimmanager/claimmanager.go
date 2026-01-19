package claimmanager

import (
	"context"
	"time"

	"github.com/google/uuid"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
)

type ClaimManager interface {
	Submit(ctx context.Context, service, key string, newValue any, reason, claimant, law, bsn string, caseID uuid.UUID, oldValue any, evidencePath string, autoApprove bool, effectiveDate time.Time) (uuid.UUID, error)
	Approve(ctx context.Context, id uuid.UUID, verification model.ClaimVerification) error
	Reject(ctx context.Context, id uuid.UUID, rejection model.ClaimRejection) error
	AddEvidence(ctx context.Context, id uuid.UUID, evidence string) error
	LinkCase(ctx context.Context, claimID, caseID uuid.UUID) error
	Get(ctx context.Context, id uuid.UUID) (*model.Claim, error)
	GetClaimsByService(ctx context.Context, service string, approved, includeRejected bool) ([]model.Claim, error)
	GetClaimsByCase(ctx context.Context, caseID uuid.UUID, approved, includeRejected bool) ([]model.Claim, error)
	GetClaimsByClaimant(ctx context.Context, claimant string, approved, includeRejected bool) ([]model.Claim, error)
	GetClaimsByBSN(ctx context.Context, bsn string, approved, includeRejected bool) ([]model.Claim, error)
	GetClaimByBSNServiceLaw(ctx context.Context, bsn, service, law string, approved, includeRejected bool) (map[string]model.Claim, error)

	Reset(ctx context.Context) error
}
