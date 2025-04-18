package service

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"github.com/minbzk/poc-machine-law/machinev2/backend/config"
	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/dataframe"
	machine "github.com/minbzk/poc-machine-law/machinev2/machine/service"
)

var _ Servicer = &Service{}

type Service struct {
	logger   *slog.Logger
	cfg      *config.Config
	service  *machine.Services
	profiles map[string]model.Profile
}

func New(logger *slog.Logger, cfg *config.Config) *Service {
	return &Service{
		logger:   logger,
		cfg:      cfg,
		service:  machine.NewServices(time.Now()),
		profiles: make(map[string]model.Profile),
	}
}

func (service *Service) Shutdown(ctx context.Context) error {
	return nil
}

func (service *Service) Status(ctx context.Context) error {
	return nil
}

func (service *Service) AppendInput(input model.Input) {
	for svc, tables := range input.GlobalServices {
		for table, data := range tables {
			service.service.SetSourceDataFrame(svc, table, dataframe.New(data))
		}
	}

	for bsn, profile := range input.Profiles {
		for svc, tables := range profile.Sources {
			for table, data := range tables {
				service.service.SetSourceDataFrame(svc, table, dataframe.New(data))
			}
		}

		service.profiles[bsn] = model.Profile{
			BSN:         bsn,
			Name:        profile.Name,
			Description: profile.Description,
			Sources:     profile.Sources,
		}
	}
}

type ClaimListFilter struct {
	OnlyApproved    *bool
	IncludeRejected *bool
}

type Servicer interface {
	Evaluate(ctx context.Context, evaluate model.Evaluate) (model.EvaluateResponse, error)

	ProfileList(ctx context.Context) ([]model.Profile, error)
	Profile(ctx context.Context, bsn string) (model.Profile, error)

	ServiceLawsDiscoverableList(ctx context.Context, discoverableBy string) ([]model.Service, error)
	GetRuleSpec(service, law string, referenceDate string) (map[string]any, error)

	ClaimListBasedOnBSN(ctx context.Context, bsn string, filter ClaimListFilter) ([]model.Claim, error)
	ClaimListBasedOnBSNServiceLaw(ctx context.Context, bsn, service, law string, filter ClaimListFilter) (map[string]model.Claim, error)

	CaseGetBasedOnBSNServiceLaw(ctx context.Context, bsn, service, law string) (model.Case, error)
	CaseListBasedOnServiceLaw(ctx context.Context, service, law string) ([]model.Case, error)
}

// ServiceLawsDiscoverableList implements Servicer.
func (service *Service) ServiceLawsDiscoverableList(ctx context.Context, discoverableBy string) ([]model.Service, error) {
	items := service.service.GetDiscoverableServiceLaws(discoverableBy)

	services := make([]model.Service, 0, len(items))
	for service, laws := range items {
		laws2 := make([]model.Law, 0, len(laws))

		for _, law := range laws {
			laws2 = append(laws2, model.Law{
				Name: law,
				Discoverableby: []string{
					discoverableBy,
				},
			})
		}

		services = append(services, model.Service{
			Name: service,
			Laws: laws2,
		})
	}

	return services, nil
}

func (service *Service) GetRuleSpec(svc, law string, referenceDate string) (map[string]any, error) {
	rule, err := service.service.Resolver.GetRuleSpec(law, referenceDate, svc)
	if err != nil {
		return nil, fmt.Errorf("get rule spec: %w", err)
	}

	return rule, nil
}
