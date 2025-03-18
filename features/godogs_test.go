package main

import (
	"context"
	"fmt"
	"os"
	"strconv"
	"testing"
	"time"

	"github.com/cucumber/godog"
	"github.com/minbzk/poc-machine-law/machine-v3/dataframe"
	"github.com/minbzk/poc-machine-law/machine-v3/model"
	"github.com/minbzk/poc-machine-law/machine-v3/service"
	"github.com/sirupsen/logrus"
	"github.com/stretchr/testify/assert"
)

// godogsCtxKey is the key used to store the available godogs in the context.Context.
type dateCtxKey struct{}
type paramsCtxKey struct{}
type resultCtxKey struct{}
type inputCtxKey struct{}
type serviceCtxKey struct{}

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
	ctx.When(`^de ([^"]*) wordt uitgevoerd door ([^"]*)$`, deWetWordtUitgevoerdDoorService)
	ctx.When(`^de ([^"]*) wordt uitgevoerd door ([^"]*) met wijzigingen$`, deWetWordtUitgevoerdDoorServiceMetWijzigingen)
	ctx.When(`^de beoordelaar de aanvraag afwijst met reden "([^"]*)"$`, deBeoordelaarDeAanvraagAfwijstMetReden)
	ctx.When(`^de beoordelaar het bezwaar afwijst met reden "([^"]*)"$`, deBeoordelaarHetBezwaarAfwijstMetReden)
	ctx.When(`^de beoordelaar het bezwaar toewijst met reden "([^"]*)"$`, deBeoordelaarHetBezwaarToewijstMetReden)
	ctx.When(`^de burger bezwaar maakt met reden "([^"]*)"$`, deBurgerBezwaarMaaktMetReden)
	ctx.When(`^de burger deze gegevens indient:$`, deBurgerDezeGegevensIndient)
	ctx.When(`^de burger een wijziging indient$`, deBurgerEenWijzigingIndient)
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
}

func evaluate_law(ctx context.Context, svc, law string, approved bool) (context.Context, error) {
	// Configure logging
	logger := logrus.New()
	logger.SetOutput(os.Stdout)
	logger.SetLevel(logrus.DebugLevel)
	logger.SetFormatter(&logrus.TextFormatter{
		ForceColors:      true,
		DisableTimestamp: false,
		FullTimestamp:    true,
	})

	services, ok := ctx.Value(serviceCtxKey{}).(*service.Services)
	if !ok || services == nil {
		return ctx, fmt.Errorf("services not set")
	}

	inputs := ctx.Value(inputCtxKey{}).([]input)
	for _, input := range inputs {
		services.SetSourceDataFrame(input.Service, input.Table, input.DF)
	}

	params := ctx.Value(paramsCtxKey{}).(map[string]any)

	result, err := services.Evaluate(ctx, svc, law, params, "", nil, "", approved)
	assert.NoError(godog.T(ctx), err)

	return context.WithValue(ctx, resultCtxKey{}, *result), nil
}

type input struct {
	Service string
	Table   string
	DF      model.DataFrame
}

func parseValue(key string) bool {
	for _, v := range []string{"bsn", "partner_bsn", "jaar", "kind_bsn"} {
		if v == key {
			return false
		}
	}

	return true
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

			var v any
			var err error
			v = cell.Value

			if parseValue(key) {
				v, err = strconv.Atoi(cell.Value)
				if err != nil {
					v = cell.Value
				}
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

	return context.WithValue(ctx, serviceCtxKey{}, service.NewServices(t1)), nil
}

func eenPersoonMetBSN(ctx context.Context, arg1 string) (context.Context, error) {
	v, ok := ctx.Value(paramsCtxKey{}).(map[string]any)
	if !ok {
		v = map[string]any{}
	}

	v["BSN"] = arg1

	return context.WithValue(ctx, paramsCtxKey{}, v), nil
}

func deWetWordtUitgevoerdDoorService(ctx context.Context, law, service string) (context.Context, error) {
	return evaluate_law(ctx, service, law, true)
}

func deWetWordtUitgevoerdDoorServiceMetWijzigingen(ctx context.Context, law, service string) (context.Context, error) {
	return evaluate_law(ctx, service, law, false)
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
	assert.True(godog.T(ctx), ok)

	actual, ok := v.(int)
	assert.True(godog.T(ctx), ok)

	compareMonitaryValue(ctx, expected, actual)

	return nil
}

func alleAanvragenWordenBeoordeeld(ctx context.Context) error {
	services, ok := ctx.Value(serviceCtxKey{}).(*service.Services)
	if !ok || services == nil {
		return fmt.Errorf("services not set")
	}

	services.CaseManager.SampleRate = 1.0

	return nil
}

func deBeoordelaarDeAanvraagAfwijstMetReden(ctx context.Context, reason string) (context.Context, error) {
	services, ok := ctx.Value(serviceCtxKey{}).(*service.Services)
	if !ok || services == nil {
		return ctx, fmt.Errorf("services not set")
	}

	c, err := services.CaseManager.GetCaseByID(arg1)
	if err != nil {
		return ctx, fmt.Errorf("get case by id: %w", err)
	}

	c.Decide(nil, reason, "BEOORDELAAR", false)

	services.CaseManager.SubmitCase()

	return ctx, godog.ErrPending
}

func deBeoordelaarHetBezwaarAfwijstMetReden(ctx context.Context, arg1 string) (context.Context, error) {
	return ctx, godog.ErrPending
}

func deBeoordelaarHetBezwaarToewijstMetReden(ctx context.Context, arg1 string) (context.Context, error) {
	return ctx, godog.ErrPending
}

func deBurgerBezwaarMaaktMetReden(ctx context.Context, arg1 string) (context.Context, error) {
	return ctx, godog.ErrPending
}

func deBurgerDezeGegevensIndient(arg1 *godog.Table) error {
	return godog.ErrPending
}

func deBurgerEenWijzigingIndient(arg1 *godog.Table) error {
	return godog.ErrPending
}

func dePersoonDitAanvraagt() error {
	return godog.ErrPending
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

func isDeAanvraagAfgewezen() error {
	return godog.ErrPending
}

func isDeAanvraagToegekend() error {
	return godog.ErrPending
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

func isDeStatus(arg1 string) error {
	return godog.ErrPending
}

func isDeWoonkostentoeslagEuro(ctx context.Context, expected float64) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	assert.True(godog.T(ctx), ok)

	v, ok := result.Output["subsidy_amount"]
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

func kanDeBurgerInBeroepGaanBij(arg1 string) error {
	return godog.ErrPending
}

func kanDeBurgerInBezwaarGaan() error {
	return godog.ErrPending
}

func kanDeBurgerNietInBezwaarGaanMetReden(arg1 string) error {
	return godog.ErrPending
}

func ontbrekenErGeenVerplichteGegevens() error {
	return godog.ErrPending
}

func ontbrekenErVerplichteGegevens() error {
	return godog.ErrPending
}

func wordtDeAanvraagToegevoegdAanHandmatigeBeoordeling() error {
	return godog.ErrPending
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
