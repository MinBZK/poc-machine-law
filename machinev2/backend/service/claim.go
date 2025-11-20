package service

import (
	"context"
	"fmt"

	"github.com/looplab/eventhorizon/uuid"
	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
	machinemodel "github.com/minbzk/poc-machine-law/machinev2/machine/model"
)

func (service *Service) ClaimListBasedOnBSN(ctx context.Context, bsn string, filter ClaimListFilter) ([]model.Claim, error) {
	onlyApproved := false
	if filter.OnlyApproved != nil {
		onlyApproved = *filter.OnlyApproved
	}

	includeRejected := false
	if filter.IncludeRejected != nil {
		includeRejected = *filter.IncludeRejected
	}

	records, err := service.claimManager.GetClaimsByBSN(ctx, bsn, onlyApproved, includeRejected)
	if err != nil {
		return nil, fmt.Errorf("get claims by bsn: %w", err)
	}

	return ToClaims(records), nil
}

func (service *Service) ClaimListBasedOnBSNServiceLaw(ctx context.Context, bsn, svc, law string, filter ClaimListFilter) (map[string]model.Claim, error) {
	onlyApproved := false
	if filter.OnlyApproved != nil {
		onlyApproved = *filter.OnlyApproved
	}

	includeRejected := false
	if filter.IncludeRejected != nil {
		includeRejected = *filter.IncludeRejected
	}

	records, err := service.claimManager.GetClaimByBSNServiceLaw(ctx, bsn, svc, law, onlyApproved, includeRejected)
	if err != nil {
		return nil, fmt.Errorf("get claims by bsn: %w", err)
	}

	claims := make(map[string]model.Claim, len(records))

	for key, record := range records {
		claims[key] = ToClaim(record)
	}

	return claims, nil
}

// ClaimApprove implements Servicer.
func (service *Service) ClaimApprove(ctx context.Context, claim model.ClaimApprove) error {
	verification := machinemodel.ClaimVerification{
		By:    claim.VerifiedBy,
		Value: claim.VerifiedValue,
	}
	err := service.claimManager.Approve(ctx, claim.ID, verification)
	if err != nil {
		return fmt.Errorf("approve claim: %w", err)
	}

	return nil
}

// ClaimReject implements Servicer.
func (service *Service) ClaimReject(ctx context.Context, claim model.ClaimReject) error {
	rejection := machinemodel.ClaimRejection{
		By:     claim.RejectedBy,
		Reason: claim.RejectionReason,
	}
	err := service.claimManager.Reject(ctx, claim.ID, rejection)
	if err != nil {
		return fmt.Errorf("reject claim: %w", err)
	}

	return nil
}

// ClaimSubmit implements Servicer.
func (service *Service) ClaimSubmit(ctx context.Context, claim model.ClaimSubmit) (uuid.UUID, error) {
	var autoApprove bool
	if claim.AutoApprove != nil {
		autoApprove = *claim.AutoApprove
	}

	var caseID uuid.UUID = uuid.Nil
	if claim.CaseID != nil {
		caseID = *claim.CaseID
	}

	var oldValue any
	if claim.OldValue != nil {
		oldValue = *claim.OldValue
	}

	var evidencePath string
	if claim.EvidencePath != nil {
		evidencePath = *claim.EvidencePath
	}

	claimID, err := service.claimManager.Submit(
		ctx,
		claim.Service,
		claim.Key,
		claim.NewValue,
		claim.Reason,
		claim.Claimant,
		claim.Law,
		claim.BSN,
		caseID,
		oldValue,
		evidencePath,
		autoApprove,
		claim.EffectiveDate,
	)
	if err != nil {
		return uuid.Nil, fmt.Errorf("submit claim: %w", err)
	}

	return claimID, nil
}

func ToClaim(claim machinemodel.Claim) model.Claim {
	var caseID *uuid.UUID
	if claim.CaseID != uuid.Nil {
		caseID = &claim.CaseID
	}

	var evidencePath *string
	if claim.EvidencePath != "" {
		evidencePath = &claim.EvidencePath
	}

	var oldValue *any
	if claim.OldValue != nil {
		oldValue = &claim.OldValue
	}

	return model.Claim{
		ID:           claim.ID,
		Service:      claim.Service,
		Key:          claim.Key,
		CaseID:       caseID,
		Law:          claim.Law,
		BSN:          claim.BSN,
		Claimant:     claim.Claimant,
		EvidencePath: evidencePath,
		NewValue:     claim.NewValue,
		OldValue:     oldValue,
		Reason:       claim.Reason,
		Status:       string(claim.Status),
	}
}

func ToClaims(claims []machinemodel.Claim) []model.Claim {
	cs := make([]model.Claim, 0, len(claims))

	for idx := range claims {
		cs = append(cs, ToClaim(claims[idx]))
	}

	return cs
}
