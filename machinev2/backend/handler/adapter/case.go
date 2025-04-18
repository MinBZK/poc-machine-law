package adapter

import (
	"github.com/minbzk/poc-machine-law/machinev2/backend/interface/api"
	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
)

func FromCase(case_ model.Case) api.Case {
	return api.Case{
		Approved: case_.Approved,
		Bsn:      case_.BSN,
		Service:  case_.Service,
		Law:      case_.Law,
		Status:   api.CaseStatus(case_.Status),
	}
}

func FromCases(cases []model.Case) []api.Case {
	cs := make([]api.Case, 0, len(cases))

	for idx := range cases {
		cs = append(cs, FromCase(cases[idx]))
	}

	return cs
}
