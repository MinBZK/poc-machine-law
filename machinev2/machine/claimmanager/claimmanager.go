package claimmanager

import (
	"context"

	"github.com/google/uuid"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
)

type Claimmanager interface {
	Submit(ctx context.Context) (uuid.UUID, error)
	Approve(ctx context.Context, id uuid.UUID, verification model.ClaimVerification) error
	Reject(ctx context.Context, id uuid.UUID, rejection model.ClaimRejection) error
	AddEvidence(ctx context.Context, id uuid.UUID, evidence string) error
	Get(ctx context.Context, id uuid.UUID) (model.Claim, error)
	GetClaimsByCase(ctx context.Context, caseID uuid.UUID, approved, includeRejected bool) ([]model.Claim, error)
	GetClaimsByClaimant(ctx context.Context, claimant string, approved, includeRejected bool) ([]model.Claim, error)
	GetClaimsByBSN(ctx context.Context, bsn string, approved, includeRejected bool) ([]model.Claim, error)
	GetClaimByBSNServiceLaw(ctx context.Context, bsn, service, law string, approved, includeRejected bool) ([]model.Claim, error)
}
