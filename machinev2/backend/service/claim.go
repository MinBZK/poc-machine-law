package service

import (
	"context"
	"fmt"

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

	records, err := service.service.ClaimManager.GetClaimsByBSN(bsn, onlyApproved, includeRejected)
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

	records, err := service.service.ClaimManager.GetClaimByBSNServiceLaw(bsn, svc, law, onlyApproved, includeRejected)
	if err != nil {
		return nil, fmt.Errorf("get claims by bsn: %w", err)
	}

	claims := make(map[string]model.Claim, len(records))

	for key, record := range records {
		claims[key] = ToClaim(record)
	}

	return claims, nil
}

func ToClaim(claim machinemodel.Claim) model.Claim {
	return model.Claim{
		ID:      claim.ID,
		Service: claim.Service,
		Key:     claim.Key,
		CaseID:  claim.CaseID,
		Law:     claim.Law,
		BSN:     claim.BSN,
	}
}

func ToClaims(claims []machinemodel.Claim) []model.Claim {
	cs := make([]model.Claim, 0, len(claims))

	for idx := range claims {
		cs = append(cs, ToClaim(claims[idx]))
	}

	return cs
}
