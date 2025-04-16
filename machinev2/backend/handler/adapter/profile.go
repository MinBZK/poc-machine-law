package adapter

import (
	"github.com/minbzk/poc-machine-law/machinev2/backend/interface/api"
	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
)

func FromProfile(profile model.Profile) api.Profile {
	return api.Profile{
		Bsn:         profile.BSN,
		Description: profile.Description,
		Name:        profile.Name,
		Sources:     FromSources(profile.Sources),
	}
}

func FromProfiles(profiles []model.Profile) []api.Profile {
	ps := make([]api.Profile, 0, len(profiles))

	for idx := range profiles {
		ps = append(ps, FromProfile(profiles[idx]))
	}

	return ps
}

func FromSource(source model.Source) api.Source {
	s := api.Source{}

	// fmt.Printf("source: %#v\n", source)
	for k, v := range source {
		s[k] = v
	}

	return s
}

func FromSources(sources map[string]model.Source) map[string]api.Source {
	ss := make(map[string]api.Source, len(sources))

	for k, v := range sources {
		ss[k] = FromSource(v)
	}

	return ss
}
