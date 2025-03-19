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
	"github.com/minbzk/poc-machine-law/machine-v3/casemanager"
	"github.com/minbzk/poc-machine-law/machine-v3/dataframe"
	"github.com/minbzk/poc-machine-law/machine-v3/model"
	"github.com/minbzk/poc-machine-law/machine-v3/service"
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
	ctx.When(`^de ([^"]*) wordt uitgevoerd door ([^"]*)$`, deWetWordtUitgevoerdDoorService)
	ctx.When(`^de ([^"]*) wordt uitgevoerd door ([^"]*) met wijzigingen$`, deWetWordtUitgevoerdDoorServiceMetWijzigingen)
	ctx.When(`^de beoordelaar de aanvraag afwijst met reden "([^"]*)"$`, deBeoordelaarDeAanvraagAfwijstMetReden)
	ctx.When(`^de beoordelaar het bezwaar "([^"]*)" met reden "([^"]*)"$`, deBeoordelaarHetBezwaarBeoordeeldMetReden)
	ctx.When(`^de burger bezwaar maakt met reden "([^"]*)"$`, deBurgerBezwaarMaaktMetReden)
	ctx.When(`^de burger deze gegevens indient:$`, deBurgerDezeGegevensIndient)
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

	services, ok := ctx.Value(servicesCtxKey{}).(*service.Services)
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

	ctx = context.WithValue(ctx, serviceCtxKey{}, svc)
	ctx = context.WithValue(ctx, lawCtxKey{}, law)

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

	return ctx, services.CaseManager.CompleteManualReview(ctx, caseID, "BEOORDELAAR", false, reason, nil)
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

func deBurgerDezeGegevensIndient(ctx context.Context, table *godog.Table) (context.Context, error) {
	if len(table.Rows) <= 1 {
		return ctx, fmt.Errorf("table must have at least one data row")
	}

	// Process the table to get the input data
	testData := map[string]any{}
	for i := 1; i < len(table.Rows); i++ {
		row := table.Rows[i]
		key := table.Rows[0].Cells[0].Value
		value := row.Cells[0].Value

		// Try to parse JSON-like values
		if value[0] == '{' || value[0] == '[' {
			var jsonValue any
			if err := json.Unmarshal([]byte(value), &jsonValue); err == nil {
				testData[key] = jsonValue
				continue
			}
		}

		// Otherwise just use the string value
		testData[key] = value
	}

	return context.WithValue(ctx, inputCtxKey{}, testData), nil
}

// func deBurgerEenWijzigingIndient(ctx context.Context, table *godog.Table) (context.Context, error) {
// 	services, ok := ctx.Value(servicesCtxKey{}).(*service.Services)
// 	if !ok || services == nil {
// 		return ctx, fmt.Errorf("services not set")
// 	}

// 	params := ctx.Value(paramsCtxKey{}).(map[string]any)
// 	bsn, ok := params["BSN"].(string)
// 	if !ok {
// 		return ctx, fmt.Errorf("BSN not set in parameters")
// 	}

// 	// Process each row of the table as a claim
// 	claims := []string{}

// 	for i := 1; i < len(table.Rows); i++ {
// 		row := table.Rows[i]
// 		if len(row.Cells) < 4 {
// 			continue // Skip rows with insufficient columns
// 		}

// 		serviceKey := table.Rows[0].Cells[0].Value
// 		keyKey := table.Rows[0].Cells[1].Value
// 		valueKey := table.Rows[0].Cells[2].Value
// 		reasonKey := table.Rows[0].Cells[3].Value
// 		lawKey := ""

// 		if len(table.Rows[0].Cells) > 4 {
// 			lawKey = table.Rows[0].Cells[4].Value
// 		}

// 		service := row.Cells[0].Value
// 		key := row.Cells[1].Value
// 		newValue := row.Cells[2].Value
// 		reason := row.Cells[3].Value
// 		law := ""

// 		if len(row.Cells) > 4 {
// 			law = row.Cells[4].Value
// 		}

// 		// Try to parse new value as appropriate type
// 		var parsedValue any = newValue
// 		if newValue != "" {
// 			// Try to parse as int
// 			if intVal, err := strconv.Atoi(newValue); err == nil {
// 				parsedValue = intVal
// 			} else if newValue[0] == '{' || newValue[0] == '[' {
// 				// Try to parse as JSON
// 				var jsonValue any
// 				if err := json.Unmarshal([]byte(newValue), &jsonValue); err == nil {
// 					parsedValue = jsonValue
// 				}
// 			}
// 		}

// 		// Get the case ID from context if available
// 		var caseID string
// 		if id, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID); ok {
// 			caseID = id.String()
// 		}

// 		// Submit claim
// 		claimID, err := services.ClaimManager.SubmitClaim(service, key, parsedValue, reason, "BURGER", caseID, "", law, bsn)
// 		if err != nil {
// 			return ctx, fmt.Errorf("failed to submit claim: %w", err)
// 		}

// 		claims = append(claims, claimID)
// 	}

// 	return context.WithValue(ctx, "claims", claims), nil
// }

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

	c, err := services.CaseManager.GetCaseByID(caseID)
	if err != nil {
		return fmt.Errorf("failed to get case: %w", err)
	}

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

	c, err := services.CaseManager.GetCaseByID(caseID)
	if err != nil {
		return fmt.Errorf("failed to get case: %w", err)
	}

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

	c, err := services.CaseManager.GetCaseByID(caseID)
	if err != nil {
		return fmt.Errorf("failed to get case: %w", err)
	}

	assert.Equal(godog.T(ctx), casemanager.CaseStatus(expected), c.Status,
		fmt.Sprintf("Expected status to be %s, but was %s", expected, c.Status))

	return nil
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

func kanDeBurgerInBeroepGaanBij(ctx context.Context, competentCourt string) error {
	services, ok := ctx.Value(servicesCtxKey{}).(*service.Services)
	if !ok || services == nil {
		return fmt.Errorf("services not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	assert.True(godog.T(ctx), ok)

	c, err := services.CaseManager.GetCaseByID(caseID)
	if err != nil {
		return fmt.Errorf("failed to get case: %w", err)
	}

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

	c, err := services.CaseManager.GetCaseByID(caseID)
	if err != nil {
		return fmt.Errorf("failed to get case: %w", err)
	}

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

	c, err := services.CaseManager.GetCaseByID(caseID)
	if err != nil {
		return fmt.Errorf("failed to get case: %w", err)
	}

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

	c, err := services.CaseManager.GetCaseByID(caseID)
	if err != nil {
		return fmt.Errorf("failed to get case: %w", err)
	}

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
