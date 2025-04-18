package adapter

import (
	"github.com/minbzk/poc-machine-law/machinev2/backend/interface/api"
	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
)

func FromClaim(claim model.Claim) api.Claim {
	return api.Claim{
		Bsn:     claim.BSN,
		Key:     claim.Key,
		Law:     claim.Law,
		Service: claim.Service,
	}
}

func FromClaims(claims []model.Claim) []api.Claim {
	cs := make([]api.Claim, 0, len(claims))

	for idx := range claims {
		cs = append(cs, FromClaim(claims[idx]))
	}

	return cs
}
