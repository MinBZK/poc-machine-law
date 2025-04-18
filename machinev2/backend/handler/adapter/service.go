package adapter

import (
	"github.com/minbzk/poc-machine-law/machinev2/backend/interface/api"
	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
)

func FromService(service model.Service) api.Service {
	return api.Service{
		Name: service.Name,
		Laws: FromLaws(service.Laws),
	}

}

func FromServices(services []model.Service) []api.Service {
	items := make([]api.Service, 0, len(services))

	for idx := range services {
		items = append(items, FromService(services[idx]))
	}

	return items
}
func FromLaw(law model.Law) api.Law {
	return api.Law{
		Name:           law.Name,
		DiscoverableBy: law.Discoverableby,
	}

}

func FromLaws(laws []model.Law) []api.Law {
	items := make([]api.Law, 0, len(laws))

	for idx := range laws {
		items = append(items, FromLaw(laws[idx]))
	}

	return items
}
