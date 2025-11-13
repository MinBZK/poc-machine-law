package service

import (
	"context"
	"fmt"
	"log/slog"
	"os"
	"time"

	"github.com/google/uuid"
	"github.com/minbzk/poc-machine-law/machinev2/backend/config"
	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/casemanager"
	"github.com/minbzk/poc-machine-law/machinev2/machine/casemanager/manager"
	"github.com/minbzk/poc-machine-law/machinev2/machine/claimmanager"
	"github.com/minbzk/poc-machine-law/machinev2/machine/claimmanager/ace"
	"github.com/minbzk/poc-machine-law/machinev2/machine/dataframe"
	"github.com/minbzk/poc-machine-law/machinev2/machine/logger"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
	machine "github.com/minbzk/poc-machine-law/machinev2/machine/service/serviceprovider"
	"github.com/sirupsen/logrus"
)

var _ Servicer = &Service{}

type Service struct {
	logger       *slog.Logger
	cfg          *config.Config
	service      *machine.Services
	claimManager claimmanager.ClaimManager
	casemanager  casemanager.CaseManager
	profiles     map[string]model.Profile
	input        model.Input
}

func New(logr *slog.Logger, cfg *config.Config) (*Service, error) {
	options := []machine.Option{
		machine.WithOrganizationName(cfg.Organization),
	}

	if cfg.StandaloneMode {
		options = append(options, machine.SetStandaloneMode())
	}

	if cfg.WithRuleServiceInMemory {
		options = append(options, machine.WithRuleServiceInMemory())
	}

	if cfg.LDV.Enabled {
		options = append(options, machine.WithLogboekDataVerwerking(cfg.LDV.Endpoint, cfg.Organization))
	}

	if cfg.ExternalClaimResolverEndpoint != "" {
		options = append(options, machine.WithExternalClaimResolverUBB(cfg.ExternalClaimResolverEndpoint))
	}

	logr2 := logger.New("service", os.Stdout, logrus.DebugLevel)

	caseManager := manager.New(logr2)
	// claimManager := inmemory.New(logr2, caseManager)
	claimManager, err := ace.New(cfg.ExternalClaimResolverEndpoint, logr2)
	if err != nil {
		return nil, fmt.Errorf("claim manager new: %w", err)
	}

	services, err := machine.New(logr2, time.Now(), caseManager, claimManager, options...)
	if err != nil {
		return nil, fmt.Errorf("new services: %w", err)
	}

	caseManager.SetService(services)

	return &Service{
		logger:       logr,
		cfg:          cfg,
		service:      services,
		claimManager: claimManager,
		casemanager:  caseManager,
		profiles:     make(map[string]model.Profile),
	}, nil
}

func (service *Service) Shutdown(ctx context.Context) error {
	return nil
}

func (service *Service) Status(ctx context.Context) error {
	return nil
}

func (service *Service) AppendInput(ctx context.Context, input model.Input) error {
	service.input = input
	if err := service.setInput(ctx); err != nil {
		return fmt.Errorf("set input: %w", err)
	}

	return nil
}

func (service *Service) setInput(ctx context.Context) error {
	for svc, tables := range service.input.GlobalServices {
		for table, data := range tables {
			if err := service.service.SetSourceDataFrame(ctx, svc, table, dataframe.New(data)); err != nil {
				return fmt.Errorf("set source dataframe: %w", err)
			}
		}
	}

	for bsn, profile := range service.input.Profiles {
		for svc, tables := range profile.Sources {
			for table, data := range tables {
				if err := service.service.SetSourceDataFrame(ctx, svc, table, dataframe.New(data)); err != nil {
					return fmt.Errorf("set source dataframe: %w", err)
				}
			}
		}

		service.profiles[bsn] = model.Profile{
			BSN:         bsn,
			Name:        profile.Name,
			Description: profile.Description,
			Sources:     profile.Sources,
		}
	}

	return nil
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
	GetRuleSpec(service, law string, referenceDate time.Time) (ruleresolver.RuleSpec, error)

	ClaimListBasedOnBSN(ctx context.Context, bsn string, filter ClaimListFilter) ([]model.Claim, error)
	ClaimListBasedOnBSNServiceLaw(ctx context.Context, bsn, service, law string, filter ClaimListFilter) (map[string]model.Claim, error)
	ClaimSubmit(ctx context.Context, claim model.ClaimSubmit) (uuid.UUID, error)
	ClaimApprove(ctx context.Context, claim model.ClaimApprove) error
	ClaimReject(ctx context.Context, claim model.ClaimReject) error

	CaseGet(ctx context.Context, caseID uuid.UUID) (model.Case, error)
	CaseGetBasedOnBSNServiceLaw(ctx context.Context, bsn, service, law string) (model.Case, error)
	CaseListBasedOnServiceLaw(ctx context.Context, service, law string) ([]model.Case, error)
	CaseListBasedOnBSN(ctx context.Context, bsn string) ([]model.Case, error)
	CaseSubmit(ctx context.Context, case_ model.CaseSubmit) (uuid.UUID, error)
	CaseReview(ctx context.Context, case_ model.CaseReview) (uuid.UUID, error)
	CaseObject(ctx context.Context, case_ model.CaseObject) (uuid.UUID, error)

	EventList(ctx context.Context) ([]model.Event, error)
	CaseEventList(ctx context.Context, caseID uuid.UUID) ([]model.Event, error)

	SetSourceDataFrame(ctx context.Context, df model.DataFrame) error
	ResetEngine(ctx context.Context) error
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

func (service *Service) GetRuleSpec(svc, law string, referenceDate time.Time) (ruleresolver.RuleSpec, error) {
	rule, err := service.service.RuleResolver.GetRuleSpec(law, referenceDate, svc)
	if err != nil {
		return ruleresolver.RuleSpec{}, fmt.Errorf("get rule spec: %w", err)
	}

	return rule, nil
}
