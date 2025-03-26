package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strconv"
	"testing"
	"time"

	"github.com/cucumber/godog"
	"github.com/google/uuid"
	"github.com/minbzk/poc-machine-law/machinev2/casemanager"
	"github.com/minbzk/poc-machine-law/machinev2/dataframe"
	"github.com/minbzk/poc-machine-law/machinev2/model"
	"github.com/minbzk/poc-machine-law/machinev2/service"
	"github.com/sirupsen/logrus"
	"github.com/stretchr/testify/assert"
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
			Format:   "pretty",
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

	inputs := ctx.Value(inputCtxKey{}).([]input)
	for _, input := range inputs {
		services.SetSourceDataFrame(input.svc, input.Table, input.DF)
	}

	params := ctx.Value(paramsCtxKey{}).(map[string]any)

	result, err := services.Evaluate(ctx, svc, law, params, "", nil, "", approved)
	assert.NoError(godog.T(ctx), err)

	ctx = context.WithValue(ctx, serviceCtxKey{}, svc)
	ctx = context.WithValue(ctx, lawCtxKey{}, law)

	return context.WithValue(ctx, resultCtxKey{}, *result), nil
}

type input struct {
	svc   string
	Table string
	DF    model.DataFrame
}

func doParseValue(key string) bool {
	for _, v := range []string{"bsn", "partner_bsn", "jaar", "kind_bsn"} {
		if v == key {
			return false
		}
	}

	return true
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
		svc:   service,
		Table: table,
		DF:    dataframe.New(t),
	})

	return context.WithValue(ctx, inputCtxKey{}, v), nil
}

func deDatumIs(ctx context.Context, arg1 string) (context.Context, error) {
	t1, err := time.Parse("2006-01-02", arg1)
	if err != nil {
		return nil, fmt.Errorf("could not parse time: %w", err)
	}

	return context.WithValue(ctx, servicesCtxKey{}, service.NewServices(t1)), nil
}

func eenPersoonMetBSN(ctx context.Context, bsn string) (context.Context, error) {
	params, ok := ctx.Value(paramsCtxKey{}).(map[string]any)
	if !ok {
		params = map[string]any{}
	}

	params["BSN"] = bsn

	return context.WithValue(ctx, paramsCtxKey{}, params), nil
}

func deWetWordtUitgevoerdDoorService(ctx context.Context, law, svc string) (context.Context, error) {
	return evaluateLaw(ctx, svc, law, true)
}

func deWetWordtUitgevoerdDoorServiceMetWijzigingen(ctx context.Context, law, svc string) (context.Context, error) {
	return evaluateLaw(ctx, svc, law, false)
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

	time.Sleep(100 * time.Millisecond)

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
	assert.True(godog.T(ctx), ok)

	c, err := getCaseByID(ctx, services.CaseManager, caseID)
	assert.NoError(godog.T(ctx), err)

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
	assert.True(godog.T(ctx), ok)

	c, err := getCaseByID(ctx, services.CaseManager, caseID)
	assert.NoError(godog.T(ctx), err)

	assert.Equal(godog.T(ctx), casemanager.CaseStatusDecided, c.Status, "Expected case to be decided")
	assert.NotNil(godog.T(ctx), c.Approved, "Expected approved status to be set")
	assert.True(godog.T(ctx), *c.Approved, "Expected case to be approved")

	return nil
}

func isDeHuurtoeslagEuro(ctx context.Context, expected float64) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	assert.True(godog.T(ctx), ok)

	v, ok := result.Output["subsidy_amount"]
	assert.True(godog.T(ctx), ok)

	actual, ok := v.(int)
	assert.True(godog.T(ctx), ok)

	compareMonitaryValue(ctx, expected, actual)

	return nil
}

func isDeStatus(ctx context.Context, expected string) error {
	services, ok := ctx.Value(servicesCtxKey{}).(*service.Services)
	if !ok || services == nil {
		return fmt.Errorf("services not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	assert.True(godog.T(ctx), ok)

	c, err := getCaseByID(ctx, services.CaseManager, caseID)
	assert.NoError(godog.T(ctx), err)

	assert.Equal(godog.T(ctx), casemanager.CaseStatus(expected), c.Status,
		fmt.Sprintf("Expected status to be %s, but was %s", expected, c.Status))

	return nil
}

func isDeWoonkostentoeslagEuro(ctx context.Context, expected float64) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	assert.True(godog.T(ctx), ok)

	v, ok := result.Output["housing_assistance"]
	assert.True(godog.T(ctx), ok)

	actual, ok := v.(int)
	assert.True(godog.T(ctx), ok)

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
	assert.True(godog.T(ctx), ok)

	c, err := getCaseByID(ctx, services.CaseManager, caseID)
	assert.NoError(godog.T(ctx), err)

	assert.True(godog.T(ctx), c.CanAppeal(), "Expected to be able to appeal")

	courtValue, ok := c.AppealStatus["competent_court"]
	assert.True(godog.T(ctx), ok, "Expected competent court to be set")

	court, ok := courtValue.(string)
	assert.True(godog.T(ctx), ok, "Expected competent court to be a string")

	assert.Equal(godog.T(ctx), competentCourt, court, "Expected another competent court")

	return nil
}

func kanDeBurgerInBezwaarGaan(ctx context.Context) error {
	services, ok := ctx.Value(servicesCtxKey{}).(*service.Services)
	if !ok || services == nil {
		return fmt.Errorf("services not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	assert.True(godog.T(ctx), ok)

	c, err := getCaseByID(ctx, services.CaseManager, caseID)
	assert.NoError(godog.T(ctx), err)

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

	c, err := getCaseByID(ctx, services.CaseManager, caseID)
	assert.NoError(godog.T(ctx), err)

	assert.False(godog.T(ctx), c.CanObject(), "Expected case not to be objectable")

	reasonValue, ok := c.ObjectionStatus["not_possible_reason"]
	assert.True(godog.T(ctx), ok, "Expected reason to be set")

	reason, ok := reasonValue.(string)
	assert.True(godog.T(ctx), ok, "Expected reason to be a string")

	assert.Equal(godog.T(ctx), expectedReason, reason, "Expected reasons to match")

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

	c, err := getCaseByID(ctx, services.CaseManager, caseID)
	assert.NoError(godog.T(ctx), err)

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

func getCaseByID(ctx context.Context, cm *service.CaseManager, caseID uuid.UUID) (*casemanager.Case, error) {
	time.Sleep(50 * time.Millisecond)

	c, err := cm.GetCaseByID(ctx, caseID)
	if err != nil {
		return nil, fmt.Errorf("failed to get case: %w", err)
	}

	return c, nil
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
