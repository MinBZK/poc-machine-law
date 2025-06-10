package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"strconv"
	"testing"
	"time"

	"slices"

	"github.com/cucumber/godog"
	"github.com/google/uuid"
	"github.com/minbzk/poc-machine-law/machinev2/machine/casemanager"
	"github.com/minbzk/poc-machine-law/machinev2/machine/dataframe"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/service"
	"github.com/sirupsen/logrus"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// godogsCtxKey is the key used to store the available godogs in the context.Context.
type paramsCtxKey struct{}
type resultCtxKey struct{}
type inputCtxKey struct{}
type servicesCtxKey struct{}
type serviceCtxKey struct{}
type lawCtxKey struct{}
type caseIDCtxKey struct{}

func TestFeatures(t *testing.T) {
	suite := godog.TestSuite{
		ScenarioInitializer: InitializeScenario,
		Options: &godog.Options{
			Format: "pretty", // pretty, progress, cucumber, events, junit
			// ShowStepDefinitions: false,
			Paths:    []string{"."},
			TestingT: t, // Testing instance that will run subtests.
		},
	}

	if suite.Run() != 0 {
		t.Fatal("non-zero status returned, failed to run feature tests")
	}
}

func InitializeScenario(ctx *godog.ScenarioContext) {
	ctx.Given(`^de volgende ([^"]*) ([^"]*) gegevens:$`, DeVolgendeGegevens)
	ctx.Given(`^de datum is "([^"]*)"$`, deDatumIs)
	ctx.Given(`^een persoon met BSN "([^"]*)"$`, eenPersoonMetBSN)
	ctx.Given(`^alle aanvragen worden beoordeeld$`, alleAanvragenWordenBeoordeeld)
	ctx.When(`^de ([^"]*) wordt uitgevoerd door ([^"]*) met wijzigingen$`, deWetWordtUitgevoerdDoorServiceMetWijzigingen)
	ctx.When(`^de ([^"]*) wordt uitgevoerd door ([^"]*)$`, deWetWordtUitgevoerdDoorService)
	ctx.When(`^de beoordelaar de aanvraag afwijst met reden "([^"]*)"$`, deBeoordelaarDeAanvraagAfwijstMetReden)
	ctx.When(`^de beoordelaar het bezwaar ([^"]*) met reden "([^"]*)"$`, deBeoordelaarHetBezwaarBeoordeeldMetReden)
	ctx.When(`^de burger bezwaar maakt met reden "([^"]*)"$`, deBurgerBezwaarMaaktMetReden)
	ctx.When(`^de burger ([^"]*) indient:$`, deBurgerGegevensIndient)
	ctx.When(`^de persoon dit aanvraagt$`, dePersoonDitAanvraagt)

	ctx.Then(`^heeft de persoon geen stemrecht$`, heeftDePersoonGeenStemrecht)
	ctx.Then(`^heeft de persoon recht op huurtoeslag$`, heeftDePersoonRechtOpHuurtoeslag)
	ctx.Then(`^heeft de persoon recht op zorgtoeslag$`, heeftDePersoonRechtOpZorgtoeslag)
	ctx.Then(`^heeft de persoon stemrecht$`, heeftDePersoonStemrecht)
	ctx.Then(`^is de aanvraag afgewezen$`, isDeAanvraagAfgewezen)
	ctx.Then(`^is de aanvraag toegekend$`, isDeAanvraagToegekend)
	ctx.Then(`^is de huurtoeslag "(\-*\d+\.\d+)" euro$`, isDeHuurtoeslagEuro)
	ctx.Then(`^is de status "([^"]*)"$`, isDeStatus)
	ctx.Then(`^is de woonkostentoeslag "(\-*\d+\.\d+)" euro$`, isDeWoonkostentoeslagEuro)
	ctx.Then(`^is het bijstandsuitkeringsbedrag "(\-*\d+\.\d+)" euro$`, isHetBijstandsuitkeringsbedragEuro)
	ctx.Then(`^is het pensioen "(\-*\d+\.\d+)" euro$`, isHetPensioenEuro)
	ctx.Then(`^is het startkapitaal "(\-*\d+\.\d+)" euro$`, isHetStartkapitaalEuro)
	ctx.Then(`^is het toeslagbedrag "(\-*\d+\.\d+)" euro$`, isHetToeslagbedragEuro)
	ctx.Then(`^is niet voldaan aan de voorwaarden$`, isNietVoldaanAanDeVoorwaarden)
	ctx.Then(`^is voldaan aan de voorwaarden$`, isVoldaanAanDeVoorwaarden)
	ctx.Then(`^kan de burger in beroep gaan bij ([^"]*)$`, kanDeBurgerInBeroepGaanBij)
	ctx.Then(`^kan de burger in bezwaar gaan$`, kanDeBurgerInBezwaarGaan)
	ctx.Then(`^kan de burger niet in bezwaar gaan met reden "([^"]*)"$`, kanDeBurgerNietInBezwaarGaanMetReden)
	ctx.Then(`^ontbreken er geen verplichte gegevens$`, ontbrekenErGeenVerplichteGegevens)
	ctx.Then(`^ontbreken er verplichte gegevens$`, ontbrekenErVerplichteGegevens)
	ctx.Then(`^wordt de aanvraag toegevoegd aan handmatige beoordeling$`, wordtDeAanvraagToegevoegdAanHandmatigeBeoordeling)
	ctx.Step(`^is het ([^"]*) "(\d+)" eurocent$`, isHetBedragEurocent)
	ctx.Step(`^heeft de persoon geen recht op kinderopvangtoeslag$`, heeftDePersoonGeenRechtOpKinderopvangtoeslag)
	ctx.Step(`^heeft de persoon recht op kinderopvangtoeslag$`, heeftDePersoonRechtOpKinderopvangtoeslag)

	ctx.StepContext().After(func(ctx context.Context, st *godog.Step, status godog.StepResultStatus, err error) (context.Context, error) {
		services, ok := ctx.Value(servicesCtxKey{}).(*service.Services)
		if !ok || services == nil {
			return ctx, nil
		}

		// wait after every step to make sure the state machine is finished
		services.CaseManager.Wait()

		return ctx, nil
	})
}

func evaluateLaw(ctx context.Context, svc, law string, approved bool) (context.Context, error) {
	// Configure logging
	logger := logrus.New()
	logger.SetOutput(os.Stdout)
	logger.SetLevel(logrus.DebugLevel)
	logger.SetFormatter(&logrus.TextFormatter{
		ForceColors:      true,
		DisableTimestamp: false,
		FullTimestamp:    true,
	})

	services, ok := ctx.Value(servicesCtxKey{}).(*service.Services)
	if !ok || services == nil {
		return ctx, fmt.Errorf("services not set")
	}

	services.Reset()

	inputs := ctx.Value(inputCtxKey{}).([]input)
	for _, input := range inputs {
		services.SetSourceDataFrame(input.Service, input.Table, input.DF)
	}

	params := ctx.Value(paramsCtxKey{}).(map[string]any)

	result, err := services.Evaluate(ctx, svc, law, params, "", nil, "", approved)
	require.NoError(godog.T(ctx), err)

	ctx = context.WithValue(ctx, serviceCtxKey{}, svc)
	ctx = context.WithValue(ctx, lawCtxKey{}, law)

	return context.WithValue(ctx, resultCtxKey{}, *result), nil
}

type input struct {
	Service string
	Table   string
	DF      model.DataFrame
}

func doParseValue(key string) bool {
	return !slices.Contains([]string{"bsn", "partner_bsn", "jaar", "kind_bsn"}, key)
}

func parseValue(value string) any {
	m := []map[string]any{}
	if err := json.Unmarshal([]byte(value), &m); err == nil {
		return m
	}

	v, err := strconv.Atoi(value)
	if err == nil {
		return v
	}

	return value
}

func DeVolgendeGegevens(ctx context.Context, service, table string, data *godog.Table) (context.Context, error) {
	t := []map[string]any{}

	for idx, row := range data.Rows {
		if idx == 0 {
			continue
		}

		d := map[string]any{}
		for idx, cell := range row.Cells {
			key := data.Rows[0].Cells[idx].Value

			var v any = cell.Value
			if doParseValue(key) {
				v = parseValue(cell.Value)
			}

			d[key] = v
		}

		t = append(t, d)
	}

	v, ok := ctx.Value(inputCtxKey{}).([]input)
	if !ok {
		v = []input{}
	}

	v = append(v, input{
		Service: service,
		Table:   table,
		DF:      dataframe.New(t),
	})

	return context.WithValue(ctx, inputCtxKey{}, v), nil
}

func deDatumIs(ctx context.Context, arg1 string) (context.Context, error) {
	t1, err := time.Parse("2006-01-02", arg1)
	if err != nil {
		return nil, fmt.Errorf("could not parse time: %w", err)
	}

	services, err := service.NewServices(t1)
	if err != nil {
		return nil, fmt.Errorf("new services: %w", err)
	}

	return context.WithValue(ctx, servicesCtxKey{}, services), nil
}

func eenPersoonMetBSN(ctx context.Context, bsn string) (context.Context, error) {
	params, ok := ctx.Value(paramsCtxKey{}).(map[string]any)
	if !ok {
		params = map[string]any{}
	}

	params["BSN"] = bsn

	return context.WithValue(ctx, paramsCtxKey{}, params), nil
}

func deWetWordtUitgevoerdDoorService(ctx context.Context, law, service string) (context.Context, error) {
	return evaluateLaw(ctx, service, law, true)
}

func deWetWordtUitgevoerdDoorServiceMetWijzigingen(ctx context.Context, law, service string) (context.Context, error) {
	return evaluateLaw(ctx, service, law, false)
}

func isNietVoldaanAanDeVoorwaarden(ctx context.Context) error {
	requirementsNotMet(ctx, "Expected requirements to not be met, but they were")

	return nil
}

func heeftDePersoonRechtOpZorgtoeslag(ctx context.Context) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	assert.True(godog.T(ctx), ok)

	v, ok := result.Output["is_verzekerde_zorgtoeslag"]
	assert.True(godog.T(ctx), ok)

	v1, ok := v.(bool)
	assert.True(godog.T(ctx), ok)
	assert.True(godog.T(ctx), v1, "Expected person to be eligible for healthcare allowance, but they were not")

	return nil
}

func isHetToeslagbedragEuro(ctx context.Context, expected float64) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	assert.True(godog.T(ctx), ok)

	v, ok := result.Output["hoogte_toeslag"]
	if !ok {
		v, ok = result.Output["yearly_amount"]
	}

	assert.True(godog.T(ctx), ok, "No toeslag amount found in output")

	actual, ok := v.(int)
	assert.True(godog.T(ctx), ok)

	compareMonitaryValue(ctx, expected, actual)

	return nil
}

func alleAanvragenWordenBeoordeeld(ctx context.Context) error {
	services, ok := ctx.Value(servicesCtxKey{}).(*service.Services)
	if !ok || services == nil {
		return fmt.Errorf("services not set")
	}

	services.CaseManager.SampleRate = 1.0

	return nil
}

func deBeoordelaarDeAanvraagAfwijstMetReden(ctx context.Context, reason string) (context.Context, error) {
	services, ok := ctx.Value(servicesCtxKey{}).(*service.Services)
	if !ok || services == nil {
		return ctx, fmt.Errorf("services not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	assert.True(godog.T(ctx), ok)

	// Check if we have a result in the context to use as verifiedResult
	var verifiedResult map[string]any
	if result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult); ok {
		verifiedResult = result.Output
	}

	return ctx, services.CaseManager.CompleteManualReview(ctx, caseID, "BEOORDELAAR", false, reason, verifiedResult)
}

func deBeoordelaarHetBezwaarBeoordeeldMetReden(ctx context.Context, approve string, reason string) (context.Context, error) {
	approved := approve == "toewijst"

	services, ok := ctx.Value(servicesCtxKey{}).(*service.Services)
	if !ok || services == nil {
		return ctx, fmt.Errorf("services not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	assert.True(godog.T(ctx), ok)

	// Check if we have a result in the context to use as verifiedResult
	var verifiedResult map[string]any
	if result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult); ok {
		verifiedResult = result.Output
	}

	return ctx, services.CaseManager.CompleteManualReview(ctx, caseID, "BEOORDELAAR", approved, reason, verifiedResult)
}

func deBurgerBezwaarMaaktMetReden(ctx context.Context, reason string) (context.Context, error) {
	services, ok := ctx.Value(servicesCtxKey{}).(*service.Services)
	if !ok || services == nil {
		return ctx, fmt.Errorf("services not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	assert.True(godog.T(ctx), ok)

	err := services.CaseManager.ObjectCase(ctx, caseID, reason)
	return ctx, err
}

func deBurgerGegevensIndient(ctx context.Context, chance string, table *godog.Table) (context.Context, error) {
	if len(table.Rows) <= 1 {
		return ctx, fmt.Errorf("table must have at least one data row")
	}

	type claim struct {
		Service  string
		Law      string
		Key      string
		NewValue any
		Reason   string
		Evidence string
	}

	claims := make([]claim, 0, len(table.Rows)-1)

	// lookup table to map keywords to cell location
	lookup := map[string]int{}

	for k, v := range table.Rows[0].Cells {
		lookup[v.Value] = k
	}

	for idx := range table.Rows {
		if idx == 0 {
			continue
		}

		claims = append(claims, claim{
			Service:  table.Rows[idx].Cells[lookup["service"]].Value,
			Law:      table.Rows[idx].Cells[lookup["law"]].Value,
			Key:      table.Rows[idx].Cells[lookup["key"]].Value,
			NewValue: parseValue(table.Rows[idx].Cells[lookup["nieuwe_waarde"]].Value),
			Reason:   table.Rows[idx].Cells[lookup["reden"]].Value,
			Evidence: table.Rows[idx].Cells[lookup["bewijs"]].Value,
		})
	}

	params := ctx.Value(paramsCtxKey{}).(map[string]any)
	bsn, ok := params["BSN"].(string)
	if !ok {
		return ctx, fmt.Errorf("BSN not set in parameters")
	}

	services, ok := ctx.Value(servicesCtxKey{}).(*service.Services)
	if !ok || services == nil {
		return ctx, fmt.Errorf("services not set")
	}

	for _, v := range claims {
		_, err := services.ClaimManager.SubmitClaim(
			ctx,
			v.Service,
			v.Key,
			v.NewValue,
			v.Reason,
			"BURGER",
			v.Law,
			bsn,
			uuid.Nil,
			nil,
			v.Evidence,
			false,
		)

		if err != nil {
			return ctx, err
		}
	}

	return ctx, nil
}

func dePersoonDitAanvraagt(ctx context.Context) (context.Context, error) {
	services, ok := ctx.Value(servicesCtxKey{}).(*service.Services)
	if !ok || services == nil {
		return ctx, fmt.Errorf("services not set")
	}

	params := ctx.Value(paramsCtxKey{}).(map[string]any)
	svc := ctx.Value(serviceCtxKey{}).(string)
	law := ctx.Value(lawCtxKey{}).(string)
	result := ctx.Value(resultCtxKey{}).(model.RuleResult)

	caseID, err := services.CaseManager.SubmitCase(
		ctx,
		params["BSN"].(string),
		svc,
		law,
		result.Input,
		result.Output,
		true,
	)

	if err != nil {
		return ctx, err
	}

	return context.WithValue(ctx, caseIDCtxKey{}, caseID), nil
}

func heeftDePersoonRechtOpHuurtoeslag(ctx context.Context) error {
	requirementsMet(ctx, "Persoon heeft toch geen recht op huurtoeslag")

	return nil
}

func heeftDePersoonStemrecht(ctx context.Context) error {
	requirementsMet(ctx, "Expected the person to have voting rights")

	return nil
}

func heeftDePersoonGeenStemrecht(ctx context.Context) error {
	requirementsNotMet(ctx, "Expected the person to not have voting rights")

	return nil
}

func isDeAanvraagAfgewezen(ctx context.Context) error {
	services, ok := ctx.Value(servicesCtxKey{}).(*service.Services)
	if !ok || services == nil {
		return fmt.Errorf("services not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)

	c, err := getCaseByID(ctx, services.CaseManager, caseID, compareCaseStatus(casemanager.CaseStatusDecided))
	require.NoError(godog.T(ctx), err)

	assert.Equal(godog.T(ctx), casemanager.CaseStatusDecided, c.Status, "Expected case to be decided")
	assert.NotNil(godog.T(ctx), c.Approved, "Expected approved status to be set")
	assert.False(godog.T(ctx), *c.Approved, "Expected case to be rejected")

	return nil
}

func isDeAanvraagToegekend(ctx context.Context) error {
	services, ok := ctx.Value(servicesCtxKey{}).(*service.Services)
	if !ok || services == nil {
		return fmt.Errorf("services not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)

	c, err := getCaseByID(ctx, services.CaseManager, caseID, compareCaseStatus(casemanager.CaseStatusDecided))
	require.NoError(godog.T(ctx), err)

	assert.Equal(godog.T(ctx), casemanager.CaseStatusDecided, c.Status, "Expected case to be decided")
	assert.NotNil(godog.T(ctx), c.Approved, "Expected approved status to be set")
	assert.True(godog.T(ctx), *c.Approved, "Expected case to be approved")

	return nil
}

func isDeHuurtoeslagEuro(ctx context.Context, expected float64) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["subsidy_amount"]
	require.True(godog.T(ctx), ok)

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok)

	compareMonitaryValue(ctx, expected, actual)

	return nil
}

func isDeStatus(ctx context.Context, expected string) error {
	services, ok := ctx.Value(servicesCtxKey{}).(*service.Services)
	if !ok || services == nil {
		return fmt.Errorf("services not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)

	c, err := getCaseByID(ctx, services.CaseManager, caseID, compareCaseStatus(casemanager.CaseStatus(expected)))
	require.NoError(godog.T(ctx), err)

	assert.Equal(godog.T(ctx), casemanager.CaseStatus(expected), c.Status,
		fmt.Sprintf("Expected status to be %s, but was %s", expected, c.Status))

	return nil
}

func isDeWoonkostentoeslagEuro(ctx context.Context, expected float64) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["housing_assistance"]
	require.True(godog.T(ctx), ok)

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok)

	compareMonitaryValue(ctx, expected, actual)

	return nil
}

func isHetBijstandsuitkeringsbedragEuro(ctx context.Context, expected float64) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	assert.True(godog.T(ctx), ok)

	v, ok := result.Output["benefit_amount"]
	assert.True(godog.T(ctx), ok)

	actual, ok := v.(int)
	assert.True(godog.T(ctx), ok)

	compareMonitaryValue(ctx, expected, actual)

	return nil
}

func isHetPensioenEuro(ctx context.Context, expected float64) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	assert.True(godog.T(ctx), ok)

	v, ok := result.Output["pension_amount"]
	assert.True(godog.T(ctx), ok)

	actual, ok := v.(int)
	assert.True(godog.T(ctx), ok)

	compareMonitaryValue(ctx, expected, actual)

	return nil
}

func isHetStartkapitaalEuro(ctx context.Context, expected float64) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	assert.True(godog.T(ctx), ok)

	v, ok := result.Output["startup_assistance"]
	assert.True(godog.T(ctx), ok)

	actual, ok := v.(int)
	assert.True(godog.T(ctx), ok)

	compareMonitaryValue(ctx, expected, actual)

	return nil
}

func isVoldaanAanDeVoorwaarden(ctx context.Context) error {
	requirementsMet(ctx, "Expected requirements to be met, but they were not")

	return nil
}

func kanDeBurgerInBeroepGaanBij(ctx context.Context, competentCourt string) error {
	services, ok := ctx.Value(servicesCtxKey{}).(*service.Services)
	if !ok || services == nil {
		return fmt.Errorf("services not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)

	c, err := getCaseByID(ctx, services.CaseManager, caseID, compareCaseCanAppeal)
	require.NoError(godog.T(ctx), err)

	assert.True(godog.T(ctx), c.CanAppeal(), "Expected to be able to appeal")

	require.True(godog.T(ctx), c.AppealStatus.CompetentCourt != nil, "Expected competent court to be set")

	assert.Equal(godog.T(ctx), competentCourt, *c.AppealStatus.CompetentCourt, "Expected another competent court")

	return nil
}

func kanDeBurgerInBezwaarGaan(ctx context.Context) error {
	services, ok := ctx.Value(servicesCtxKey{}).(*service.Services)
	if !ok || services == nil {
		return fmt.Errorf("services not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)

	c, err := getCaseByID(ctx, services.CaseManager, caseID, compareCaseCanObject)
	require.NoError(godog.T(ctx), err)

	assert.True(godog.T(ctx), c.CanObject(), "Expected case to be objectable")

	return nil
}

func kanDeBurgerNietInBezwaarGaanMetReden(ctx context.Context, expectedReason string) error {
	services, ok := ctx.Value(servicesCtxKey{}).(*service.Services)
	if !ok || services == nil {
		return fmt.Errorf("services not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	assert.True(godog.T(ctx), ok)

	c, err := getCaseByID(ctx, services.CaseManager, caseID, compareCaseCanNotObject)
	require.NoError(godog.T(ctx), err)
	require.NotNil(godog.T(ctx), c)

	assert.False(godog.T(ctx), c.CanObject(), "Expected case not to be objectable")

	reason := c.ObjectionStatus.NotPossibleReason
	require.True(godog.T(ctx), reason != nil, "Expected reason to be set")

	assert.Equal(godog.T(ctx), expectedReason, *reason, "Expected reasons to match")

	return nil
}

func ontbrekenErGeenVerplichteGegevens(ctx context.Context) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	assert.True(godog.T(ctx), ok)

	assert.False(godog.T(ctx), result.MissingRequired, "Expected no missing required fields")

	return nil
}

func ontbrekenErVerplichteGegevens(ctx context.Context) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	assert.True(godog.T(ctx), ok)

	assert.True(godog.T(ctx), result.MissingRequired, "Expected missing required fields")

	return nil
}

func wordtDeAanvraagToegevoegdAanHandmatigeBeoordeling(ctx context.Context) error {
	services, ok := ctx.Value(servicesCtxKey{}).(*service.Services)
	if !ok || services == nil {
		return fmt.Errorf("services not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	assert.True(godog.T(ctx), ok)

	c, err := getCaseByID(ctx, services.CaseManager, caseID, compareCaseStatus(casemanager.CaseStatusInReview))
	require.NoError(godog.T(ctx), err)

	assert.Equal(godog.T(ctx), casemanager.CaseStatusInReview, c.Status, "Expected case to be in review")

	return nil
}

// helper functions

func compareMonitaryValue(ctx context.Context, expected float64, actual int) {
	assert.Equal(godog.T(ctx), int(expected*100), actual)
}

func requirementsMet(ctx context.Context, msgAndArgs ...any) {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	assert.True(godog.T(ctx), ok)
	assert.True(godog.T(ctx), result.RequirementsMet, msgAndArgs...)
}

func requirementsNotMet(ctx context.Context, msgAndArgs ...any) {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	assert.True(godog.T(ctx), ok)
	assert.False(godog.T(ctx), result.RequirementsMet, msgAndArgs...)
}

func compareCaseStatus(status casemanager.CaseStatus) func(c *casemanager.Case) bool {
	return func(c *casemanager.Case) bool {
		return c.Status == status
	}
}

func compareCaseCanObject(c *casemanager.Case) bool {
	return c.CanObject()
}

func compareCaseCanNotObject(c *casemanager.Case) bool {
	return !c.CanObject()
}

func compareCaseCanAppeal(c *casemanager.Case) bool {
	return c.CanAppeal()
}

func getCaseByID(ctx context.Context, cm *service.CaseManager, caseID uuid.UUID, fn func(c *casemanager.Case) bool) (*casemanager.Case, error) {
	var err error
	var c *casemanager.Case
	for range 500 {
		c, err = cm.GetCaseByID(ctx, caseID)
		if err == nil && c != nil && fn(c) {
			return c, nil
		}

		time.Sleep(time.Microsecond) // Sleep a micro second to give the timemachine some time to process
	}

	return nil, fmt.Errorf("failed to get case: %w: %w", errors.New("timeout"), err)
}

func isHetBedragEurocent(ctx context.Context, field string, amount int) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	assert.True(godog.T(ctx), ok)

	v, ok := result.Output[field]
	if !ok {
		return fmt.Errorf("could not find: %s", field)
	}

	actual, ok := v.(int)
	if !ok {
		return fmt.Errorf("could not convert '%s' to int", field)
	}

	assert.Equal(godog.T(ctx), amount, actual, "Expected %s to be %d eurocent, but was %d", field, amount, actual)

	return nil
}

func heeftDePersoonRechtOpKinderopvangtoeslag(ctx context.Context) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	assert.True(godog.T(ctx), ok)

	v, ok := result.Output["is_eligible"]
	if !ok {
		return fmt.Errorf("could not find: 'is_eligible'")
	}

	actual, ok := v.(bool)
	if !ok {
		return fmt.Errorf("could not convert 'is_eligible' to bool")
	}

	assert.True(godog.T(ctx), actual, "Expected person to be eligible for childcare allowance, but they were not")

	return nil
}

func heeftDePersoonGeenRechtOpKinderopvangtoeslag(ctx context.Context) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	assert.True(godog.T(ctx), ok)

	v, ok := result.Output["is_eligible"]
	if !ok {
		return nil
	}

	actual, ok := v.(bool)
	if !ok {
		return fmt.Errorf("could not convert 'is_eligible' to bool")
	}

	assert.False(godog.T(ctx), actual, "Expected person to NOT be eligible for childcare allowance, but they were")

	return nil
}
