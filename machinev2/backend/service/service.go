package service

import (
	"context"
	"fmt"
	"log/slog"
	"os"
	"strings"
	"time"

	"github.com/google/uuid"
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
	input    model.Input
}

func New(logger *slog.Logger, cfg *config.Config) *Service {
	svc := &Service{
		logger:   logger,
		cfg:      cfg,
		service:  machine.NewServices(time.Now()),
		profiles: make(map[string]model.Profile),
	}

	// Check if vertegenwoordiging feature is enabled
	if isFeatureEnabled("VERTEGENWOORDIGING") {
		svc.LoadTestProfiles()
	}

	return svc
}

// isFeatureEnabled checks if a feature flag is enabled via environment variables
func isFeatureEnabled(flagName string) bool {
	envKey := "FEATURE_" + flagName
	value := getEnvOr(envKey, "0")

	lowerValue := strings.ToLower(value)
	return value == "1" || lowerValue == "true" || lowerValue == "yes" || lowerValue == "y"
}

// getEnvOr gets an environment variable value or returns a default
func getEnvOr(key, defaultValue string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultValue
}

func (service *Service) Shutdown(ctx context.Context) error {
	return nil
}

func (service *Service) Status(ctx context.Context) error {
	return nil
}

func (service *Service) AppendInput(input model.Input) {
	service.input = input
	service.setInput()
}

func (service *Service) setInput() {
	for svc, tables := range service.input.GlobalServices {
		for table, data := range tables {
			service.service.SetSourceDataFrame(svc, table, dataframe.New(data))
		}
	}

	for bsn, profile := range service.input.Profiles {
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

func (service *Service) GetRuleSpec(svc, law string, referenceDate string) (map[string]any, error) {
	rule, err := service.service.Resolver.GetRuleSpec(law, referenceDate, svc)
	if err != nil {
		return nil, fmt.Errorf("get rule spec: %w", err)
	}

	return rule, nil
}
