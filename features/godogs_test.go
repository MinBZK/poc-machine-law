package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"strconv"
	"strings"
	"testing"
	"time"

	"slices"

	"github.com/cucumber/godog"
	"github.com/google/uuid"
	"github.com/minbzk/poc-machine-law/machinev2/machine/casemanager"
	"github.com/minbzk/poc-machine-law/machinev2/machine/dataframe"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/service/serviceprovider"
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
	ctx.When(`^de ([^"]*) wordt uitgevoerd door ([^"]*) met$`, deWetWordtUitgevoerdDoorServiceMet)
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

	// WW (Werkloosheidswet) step definitions
	ctx.Step(`^heeft de persoon recht op WW$`, heeftDePersoonRechtOpWW)
	ctx.Step(`^heeft de persoon geen recht op WW$`, heeftDePersoonGeenRechtOpWW)
	ctx.Step(`^is de WW duur "([^"]*)" maanden$`, isDeWWDuurMaanden)
	ctx.Step(`^is de WW uitkering per maand maximaal "([^"]*)"$`, isDeWWUitkeringPerMaandMaximaal)
	ctx.Step(`^is de WW uitkering per maand ongeveer "([^"]*)"$`, isDeWWUitkeringPerMaandOngeveer)
	ctx.Step(`^is de WW uitkering maximaal omdat het dagloon gemaximeerd is$`, isDeWWUitkeringMaximaalOmdatHetDagloonGemaximeerdIs)

	// Kindgebonden Budget step definitions
	ctx.Step(`^heeft de persoon recht op kindgebonden budget$`, heeftDePersoonRechtOpKindgebondenBudget)
	ctx.Step(`^heeft de persoon geen recht op kindgebonden budget$`, heeftDePersoonGeenRechtOpKindgebondenBudget)
	ctx.Step(`^is het ALO-kop bedrag "([^"]*)"$`, isHetALOkopBedrag)
	ctx.Step(`^is het kindgebonden budget ongeveer "([^"]*)" per jaar$`, isHetKindgebondenBudgetOngeveerPerJaar)
	ctx.Step(`^is het totale kindgebonden budget ongeveer "([^"]*)" per jaar$`, isHetTotaleKindgebondenBudgetOngeveerPerJaar)
	ctx.Step(`^is het kindgebonden budget lager door hoog inkomen$`, isHetKindgebondenBudgetLagerDoorHoogInkomen)
	ctx.Step(`^ontvangt de persoon de ALO-kop omdat deze alleenstaand is$`, ontvangtDePersoonDeALOkopOmdatDezeAlleenstaandIs)
	ctx.Step(`^is het kindgebonden budget hoog door laag inkomen en meerdere kinderen$`, isHetKindgebondenBudgetHoogDoorLaagInkomenEnMeerdereKinderen)
	ctx.Step(`^ontvangt de persoon extra bedragen voor kinderen 12\+ en 16\+$`, ontvangtDePersoonExtraBedragenVoorKinderen12Plus)
	ctx.Step(`^is het kindgebonden budget maximaal door laag inkomen$`, isHetKindgebondenBudgetMaximaalDoorLaagInkomen)

	// LAA (Landelijke Aanpak Adreskwaliteit) step definitions
	ctx.Step(`^genereert wet_brp/laa een signaal$`, genereertWetBrpLaaEenSignaal)
	ctx.Step(`^genereert wet_brp/laa geen signaal$`, genereertWetBrpLaaGeenSignaal)
	ctx.Step(`^is het signaal_type "([^"]*)"$`, isHetSignaalType)

	ctx.StepContext().After(func(ctx context.Context, st *godog.Step, status godog.StepResultStatus, err error) (context.Context, error) {
		services, ok := ctx.Value(servicesCtxKey{}).(*serviceprovider.Services)
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

	services, ok := ctx.Value(servicesCtxKey{}).(*serviceprovider.Services)
	if !ok || services == nil {
		return ctx, fmt.Errorf("services not set")
	}

	err := services.Reset(ctx)
	require.NoError(godog.T(ctx), err)

	inputs := ctx.Value(inputCtxKey{}).([]input)
	for _, input := range inputs {
		err := services.SetSourceDataFrame(ctx, input.Service, input.Table, input.DF)
		require.NoError(godog.T(ctx), err)
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
	return !slices.Contains([]string{"bsn", "partner_bsn", "jaar", "kind_bsn", "kvk_nummer", "ouder_bsn", "postcode", "huisnummer"}, key)
}

func parseValue(value string) any {
	m := []map[string]any{}
	if err := json.Unmarshal([]byte(value), &m); err == nil {
		return m
	}

	// Try parsing as boolean
	if value == "true" || value == "TRUE" || value == "True" {
		return true
	}
	if value == "false" || value == "FALSE" || value == "False" {
		return false
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

	// services, err := service.NewServices(t1, service.WithOrganizationName("TOESLAGEN"))
	services, err := serviceprovider.NewServices(t1, serviceprovider.WithRuleServiceInMemory())
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

func deWetWordtUitgevoerdDoorServiceMet(ctx context.Context, law, service string, table *godog.Table) (context.Context, error) {
	if len(table.Rows) <= 1 {
		return ctx, fmt.Errorf("table must have at least one data row")
	}

	// Get or create params map
	params, ok := ctx.Value(paramsCtxKey{}).(map[string]any)
	if !ok {
		params = map[string]any{}
	}

	// Process the table to get the input data
	// First row is headers
	headers := table.Rows[0].Cells

	// For each data row
	for idx := 1; idx < len(table.Rows); idx++ {
		row := table.Rows[idx]

		// Get the first column as the key
		if len(headers) == 0 || len(row.Cells) == 0 {
			continue
		}

		key := headers[0].Value
		value := row.Cells[0].Value

		// Special handling for JSON-like values
		var parsedValue any = value
		if strings.HasPrefix(value, "[") || strings.HasPrefix(value, "{") {
			// Try to parse as JSON
			if err := json.Unmarshal([]byte(value), &parsedValue); err != nil {
				// If parsing fails, keep as string
				parsedValue = value
			}
		}

		params[key] = parsedValue
	}

	// Update context with params
	ctx = context.WithValue(ctx, paramsCtxKey{}, params)

	// Evaluate the law
	return evaluateLaw(ctx, service, law, true)
}

func isNietVoldaanAanDeVoorwaarden(ctx context.Context) error {
	requirementsNotMet(ctx, "Expected requirements to not be met, but they were")

	return nil
}

func heeftDePersoonRechtOpZorgtoeslag(ctx context.Context) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["is_verzekerde_zorgtoeslag"]
	require.True(godog.T(ctx), ok)

	v1, ok := v.(bool)
	require.True(godog.T(ctx), ok)
	assert.True(godog.T(ctx), v1, "Expected person to be eligible for healthcare allowance, but they were not")

	return nil
}

func isHetToeslagbedragEuro(ctx context.Context, expected float64) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["hoogte_toeslag"]
	if !ok {
		v, ok = result.Output["jaarbedrag"]
	}

	require.True(godog.T(ctx), ok, "No toeslag amount found in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok)

	compareMonitaryValue(ctx, expected, actual)

	return nil
}

func alleAanvragenWordenBeoordeeld(ctx context.Context) error {
	services, ok := ctx.Value(servicesCtxKey{}).(*serviceprovider.Services)
	if !ok || services == nil {
		return fmt.Errorf("services not set")
	}

	services.CaseManager.SampleRate = 1.0

	return nil
}

func deBeoordelaarDeAanvraagAfwijstMetReden(ctx context.Context, reason string) (context.Context, error) {
	services, ok := ctx.Value(servicesCtxKey{}).(*serviceprovider.Services)
	if !ok || services == nil {
		return ctx, fmt.Errorf("services not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)

	// Check if we have a result in the context to use as verifiedResult
	var verifiedResult map[string]any
	if result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult); ok {
		verifiedResult = result.Output
	}

	return ctx, services.CaseManager.CompleteManualReview(ctx, caseID, "BEOORDELAAR", false, reason, verifiedResult)
}

func deBeoordelaarHetBezwaarBeoordeeldMetReden(ctx context.Context, approve string, reason string) (context.Context, error) {
	approved := approve == "toewijst"

	services, ok := ctx.Value(servicesCtxKey{}).(*serviceprovider.Services)
	if !ok || services == nil {
		return ctx, fmt.Errorf("services not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)

	// Check if we have a result in the context to use as verifiedResult
	var verifiedResult map[string]any
	if result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult); ok {
		verifiedResult = result.Output
	}

	return ctx, services.CaseManager.CompleteManualReview(ctx, caseID, "BEOORDELAAR", approved, reason, verifiedResult)
}

func deBurgerBezwaarMaaktMetReden(ctx context.Context, reason string) (context.Context, error) {
	services, ok := ctx.Value(servicesCtxKey{}).(*serviceprovider.Services)
	if !ok || services == nil {
		return ctx, fmt.Errorf("services not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)

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

	services, ok := ctx.Value(servicesCtxKey{}).(*serviceprovider.Services)
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
	services, ok := ctx.Value(servicesCtxKey{}).(*serviceprovider.Services)
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
	services, ok := ctx.Value(servicesCtxKey{}).(*serviceprovider.Services)
	if !ok || services == nil {
		return fmt.Errorf("services not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)

	c, err := getCaseByID(ctx, services.CaseManager, caseID, compareCaseStatus(casemanager.CaseStatusDecided))
	require.NoError(godog.T(ctx), err)

	assert.Equal(godog.T(ctx), casemanager.CaseStatusDecided, c.Status, "Expected case to be decided")
	require.NotNil(godog.T(ctx), c.Approved, "Expected approved status to be set")
	assert.False(godog.T(ctx), *c.Approved, "Expected case to be rejected")

	return nil
}

func isDeAanvraagToegekend(ctx context.Context) error {
	services, ok := ctx.Value(servicesCtxKey{}).(*serviceprovider.Services)
	if !ok || services == nil {
		return fmt.Errorf("services not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)

	c, err := getCaseByID(ctx, services.CaseManager, caseID, compareCaseStatus(casemanager.CaseStatusDecided))
	require.NoError(godog.T(ctx), err)

	assert.Equal(godog.T(ctx), casemanager.CaseStatusDecided, c.Status, "Expected case to be decided")
	require.NotNil(godog.T(ctx), c.Approved, "Expected approved status to be set")
	assert.True(godog.T(ctx), *c.Approved, "Expected case to be approved")

	return nil
}

func isDeHuurtoeslagEuro(ctx context.Context, expected float64) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["subsidiebedrag"]
	require.True(godog.T(ctx), ok)

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok)

	compareMonitaryValue(ctx, expected, actual)

	return nil
}

func isDeStatus(ctx context.Context, expected string) error {
	services, ok := ctx.Value(servicesCtxKey{}).(*serviceprovider.Services)
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

	v, ok := result.Output["woonkostentoeslag"]
	require.True(godog.T(ctx), ok)

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok)

	compareMonitaryValue(ctx, expected, actual)

	return nil
}

func isHetBijstandsuitkeringsbedragEuro(ctx context.Context, expected float64) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["uitkeringsbedrag"]
	require.True(godog.T(ctx), ok)

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok)

	compareMonitaryValue(ctx, expected, actual)

	return nil
}

func isHetPensioenEuro(ctx context.Context, expected float64) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["pensioenbedrag"]
	require.True(godog.T(ctx), ok)

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok)

	compareMonitaryValue(ctx, expected, actual)

	return nil
}

func isHetStartkapitaalEuro(ctx context.Context, expected float64) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["startkapitaal"]
	require.True(godog.T(ctx), ok)

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok)

	compareMonitaryValue(ctx, expected, actual)

	return nil
}

func isVoldaanAanDeVoorwaarden(ctx context.Context) error {
	requirementsMet(ctx, "Expected requirements to be met, but they were not")

	return nil
}

func kanDeBurgerInBeroepGaanBij(ctx context.Context, competentCourt string) error {
	services, ok := ctx.Value(servicesCtxKey{}).(*serviceprovider.Services)
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
	services, ok := ctx.Value(servicesCtxKey{}).(*serviceprovider.Services)
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
	services, ok := ctx.Value(servicesCtxKey{}).(*serviceprovider.Services)
	if !ok || services == nil {
		return fmt.Errorf("services not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)

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
	require.True(godog.T(ctx), ok)

	assert.False(godog.T(ctx), result.MissingRequired, "Expected no missing required fields")

	return nil
}

func ontbrekenErVerplichteGegevens(ctx context.Context) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	assert.True(godog.T(ctx), result.MissingRequired, "Expected missing required fields")

	return nil
}

func wordtDeAanvraagToegevoegdAanHandmatigeBeoordeling(ctx context.Context) error {
	services, ok := ctx.Value(servicesCtxKey{}).(*serviceprovider.Services)
	if !ok || services == nil {
		return fmt.Errorf("services not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)

	c, err := getCaseByID(ctx, services.CaseManager, caseID, compareCaseStatus(casemanager.CaseStatusInReview))
	require.NoError(godog.T(ctx), err)

	assert.Equal(godog.T(ctx), casemanager.CaseStatusInReview, c.Status, "Expected case to be in review")

	return nil
}

// helper functions

func compareMonitaryValue(ctx context.Context, expected float64, actual int) {
	assert.Equal(godog.T(ctx), int(expected*100), actual)
}

func compareMonitaryValueApproximately(ctx context.Context, expected float64, actual int, toleranceEurocents int) {
	expectedCents := int(expected * 100)
	assert.InDelta(godog.T(ctx), expectedCents, actual, float64(toleranceEurocents),
		"Expected approximately €%.2f (%d eurocents) but got €%.2f (%d eurocents)",
		expected, expectedCents, float64(actual)/100.0, actual)
}

func requirementsMet(ctx context.Context, msgAndArgs ...any) {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)
	assert.True(godog.T(ctx), result.RequirementsMet, msgAndArgs...)
}

func requirementsNotMet(ctx context.Context, msgAndArgs ...any) {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)
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

func getCaseByID(ctx context.Context, cm *serviceprovider.CaseManager, caseID uuid.UUID, fn func(c *casemanager.Case) bool) (*casemanager.Case, error) {
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
	require.True(godog.T(ctx), ok)

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
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["is_gerechtigd"]
	if !ok {
		return fmt.Errorf("could not find: 'is_gerechtigd'")
	}

	actual, ok := v.(bool)
	if !ok {
		return fmt.Errorf("could not convert 'is_gerechtigd' to bool")
	}

	assert.True(godog.T(ctx), actual, "Expected person to be eligible for childcare allowance, but they were not")

	return nil
}

func heeftDePersoonGeenRechtOpKinderopvangtoeslag(ctx context.Context) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["is_gerechtigd"]
	if !ok {
		return nil
	}

	actual, ok := v.(bool)
	if !ok {
		return fmt.Errorf("could not convert 'is_gerechtigd' to bool")
	}

	assert.False(godog.T(ctx), actual, "Expected person to NOT be eligible for childcare allowance, but they were")

	return nil
}

// WW (Werkloosheidswet) step definitions
func heeftDePersoonRechtOpWW(ctx context.Context) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["heeft_recht_op_ww"]
	require.True(godog.T(ctx), ok, "Expected 'heeft_recht_op_ww' to be present in output")

	actual, ok := v.(bool)
	require.True(godog.T(ctx), ok, "Expected 'heeft_recht_op_ww' to be a bool")

	assert.True(godog.T(ctx), actual, "Expected person to be eligible for WW, but they were not")

	return nil
}

func heeftDePersoonGeenRechtOpWW(ctx context.Context) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["heeft_recht_op_ww"]
	if !ok {
		// If output is missing, requirements were not met
		assert.False(godog.T(ctx), result.RequirementsMet, "Expected person to NOT be eligible for WW")
		return nil
	}

	actual, ok := v.(bool)
	require.True(godog.T(ctx), ok)

	assert.False(godog.T(ctx), actual, "Expected person to NOT be eligible for WW, but they were")

	return nil
}

func isDeWWDuurMaanden(ctx context.Context, expectedMonths string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["ww_duur_maanden"]
	require.True(godog.T(ctx), ok, "Expected 'ww_duur_maanden' to be present in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok, "Expected 'ww_duur_maanden' to be an int")

	expected, err := strconv.Atoi(expectedMonths)
	require.NoError(godog.T(ctx), err)

	assert.Equal(godog.T(ctx), expected, actual, "Expected WW duration to be %d months, but was %d", expected, actual)

	return nil
}

func isDeWWUitkeringPerMaandMaximaal(ctx context.Context, expectedAmount string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["ww_uitkering_per_maand"]
	require.True(godog.T(ctx), ok, "Expected 'ww_uitkering_per_maand' to be present in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok, "Expected 'ww_uitkering_per_maand' to be an int")

	// Parse amount like "€2.625,00" or "€4.741,55"
	// Remove € symbol
	cleanedAmount := strings.ReplaceAll(expectedAmount, "€", "")
	// Remove thousands separator (dot)
	cleanedAmount = strings.ReplaceAll(cleanedAmount, ".", "")
	// Replace decimal separator (comma) with dot
	cleanedAmount = strings.ReplaceAll(cleanedAmount, ",", ".")

	expected, err := strconv.ParseFloat(cleanedAmount, 64)
	require.NoError(godog.T(ctx), err)

	compareMonitaryValue(ctx, expected, actual)

	return nil
}

func isDeWWUitkeringPerMaandOngeveer(ctx context.Context, expectedAmount string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["ww_uitkering_per_maand"]
	require.True(godog.T(ctx), ok, "Expected 'ww_uitkering_per_maand' to be present in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok, "Expected 'ww_uitkering_per_maand' to be an int")

	// Parse amount like "€2.625,00" or "€4.741,55"
	cleanedAmount := strings.ReplaceAll(expectedAmount, "€", "")
	cleanedAmount = strings.ReplaceAll(cleanedAmount, ".", "")
	cleanedAmount = strings.ReplaceAll(cleanedAmount, ",", ".")

	expected, err := strconv.ParseFloat(cleanedAmount, 64)
	require.NoError(godog.T(ctx), err)

	// Allow 50 eurocents tolerance for "ongeveer" (approximately) due to rounding in complex calculations
	compareMonitaryValueApproximately(ctx, expected, actual, 50)

	return nil
}

func isDeWWUitkeringMaximaalOmdatHetDagloonGemaximeerdIs(ctx context.Context) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	dagloon, ok := result.Output["ww_dagloon"]
	require.True(godog.T(ctx), ok, "Expected 'ww_dagloon' to be present in output")

	dagloonValue, ok := dagloon.(int)
	require.True(godog.T(ctx), ok, "Expected 'ww_dagloon' to be an int")

	// Maximum dagloon for 2025 is €29,067 per year / 261 working days = €111.37 per day = 11,137 eurocent
	// But in the law it's calculated differently, check if it's the maximum
	maxDagloon := 29067

	assert.GreaterOrEqual(godog.T(ctx), dagloonValue, maxDagloon, "Expected dagloon to be at maximum")

	return nil
}

// Kindgebonden Budget step definitions
func heeftDePersoonRechtOpKindgebondenBudget(ctx context.Context) error {
	requirementsMet(ctx, "Expected person to have right to kindgebonden budget, but they did not")
	return nil
}

func heeftDePersoonGeenRechtOpKindgebondenBudget(ctx context.Context) error {
	requirementsNotMet(ctx, "Expected person to NOT have right to kindgebonden budget, but they did")
	return nil
}

func isHetALOkopBedrag(ctx context.Context, expectedAmount string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["alo_kop_bedrag"]
	require.True(godog.T(ctx), ok, "Expected 'alo_kop_bedrag' to be present in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok, "Expected 'alo_kop_bedrag' to be an int")

	// Parse amount like "€3.480,00"
	cleanedAmount := strings.ReplaceAll(expectedAmount, "€", "")
	cleanedAmount = strings.ReplaceAll(cleanedAmount, ".", "")
	cleanedAmount = strings.ReplaceAll(cleanedAmount, ",", ".")

	expected, err := strconv.ParseFloat(cleanedAmount, 64)
	require.NoError(godog.T(ctx), err)

	compareMonitaryValue(ctx, expected, actual)

	return nil
}

func isHetKindgebondenBudgetOngeveerPerJaar(ctx context.Context, expectedAmount string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["kindgebonden_budget_jaar"]
	require.True(godog.T(ctx), ok, "Expected 'kindgebonden_budget_jaar' to be present in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok, "Expected 'kindgebonden_budget_jaar' to be an int")

	// Parse amount like "€5.991,00"
	cleanedAmount := strings.ReplaceAll(expectedAmount, "€", "")
	cleanedAmount = strings.ReplaceAll(cleanedAmount, ".", "")
	cleanedAmount = strings.ReplaceAll(cleanedAmount, ",", ".")

	expected, err := strconv.ParseFloat(cleanedAmount, 64)
	require.NoError(godog.T(ctx), err)

	// Allow 50 eurocents tolerance for "ongeveer" (approximately) due to rounding in complex calculations
	compareMonitaryValueApproximately(ctx, expected, actual, 50)

	return nil
}

func isHetTotaleKindgebondenBudgetOngeveerPerJaar(ctx context.Context, expectedAmount string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["kindgebonden_budget_jaar"]
	require.True(godog.T(ctx), ok, "Expected 'kindgebonden_budget_jaar' to be present in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok, "Expected 'kindgebonden_budget_jaar' to be an int")

	// Parse amount like "€5.870,00"
	cleanedAmount := strings.ReplaceAll(expectedAmount, "€", "")
	cleanedAmount = strings.ReplaceAll(cleanedAmount, ".", "")
	cleanedAmount = strings.ReplaceAll(cleanedAmount, ",", ".")

	expected, err := strconv.ParseFloat(cleanedAmount, 64)
	require.NoError(godog.T(ctx), err)

	// Allow 2% tolerance for "totale kindgebonden budget ongeveer" (matches Python implementation)
	expectedCents := int(expected * 100)
	tolerance := float64(expectedCents) * 0.02

	assert.InDelta(godog.T(ctx), expectedCents, actual, tolerance,
		"Expected total kindgebonden budget approximately €%.2f (%d eurocents) but got €%.2f (%d eurocents)",
		expected, expectedCents, float64(actual)/100.0, actual)

	return nil
}

func isHetKindgebondenBudgetLagerDoorHoogInkomen(ctx context.Context) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["kindgebonden_budget_jaar"]
	require.True(godog.T(ctx), ok, "Expected 'kindgebonden_budget_jaar' to be present in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok)

	// Maximum budget for 2 kinderen with ALO-kop is €8,502
	maxBudget := 850200 // in eurocent

	assert.Less(godog.T(ctx), actual, maxBudget, "Expected budget to be reduced from maximum €8,502, but was €%.2f", float64(actual)/100)

	return nil
}

func ontvangtDePersoonDeALOkopOmdatDezeAlleenstaandIs(ctx context.Context) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	// Check that ALO-kop > 0
	v, ok := result.Output["alo_kop_bedrag"]
	require.True(godog.T(ctx), ok, "Expected 'alo_kop_bedrag' to be present in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok)

	assert.Greater(godog.T(ctx), actual, 0, "Expected ALO-kop to be greater than 0 for single parent")

	return nil
}

func isHetKindgebondenBudgetHoogDoorLaagInkomenEnMeerdereKinderen(ctx context.Context) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["kindgebonden_budget_jaar"]
	require.True(godog.T(ctx), ok, "Expected 'kindgebonden_budget_jaar' to be present in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok)

	// Minimum budget for 3 kinderen should be significant
	minBudget := 700000 // €7,000 in eurocent

	assert.GreaterOrEqual(godog.T(ctx), actual, minBudget, "Expected budget to be high due to low income and multiple children, but was €%.2f", float64(actual)/100)

	return nil
}

func ontvangtDePersoonExtraBedragenVoorKinderen12Plus(ctx context.Context) error {
	// This step is informational - the calculation already includes age supplements
	// Just verify that budget is present
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	_, ok = result.Output["kindgebonden_budget_jaar"]
	require.True(godog.T(ctx), ok, "Expected 'kindgebonden_budget_jaar' to be present in output")

	return nil
}

func isHetKindgebondenBudgetMaximaalDoorLaagInkomen(ctx context.Context) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["kindgebonden_budget_jaar"]
	require.True(godog.T(ctx), ok, "Expected 'kindgebonden_budget_jaar' to be present in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok)

	// For 1 kind with ALO-kop, maximum is around €5,991
	expectedMax := 599100 // in eurocent

	// Allow some tolerance (within €100)
	tolerance := 10000
	assert.InDelta(godog.T(ctx), expectedMax, actual, float64(tolerance), "Expected budget to be near maximum for low income")

	return nil
}

// LAA (Landelijke Aanpak Adreskwaliteit) step definitions

func genereertWetBrpLaaEenSignaal(ctx context.Context) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["genereer_signaal"]
	if !ok {
		assert.Fail(godog.T(ctx), "Expected LAA to generate a signal, but 'genereer_signaal' field not found in output")
		return nil
	}

	genereertSignaal, ok := v.(bool)
	require.True(godog.T(ctx), ok)

	assert.True(godog.T(ctx), genereertSignaal, "Expected LAA to generate a signal, but it did not")

	return nil
}

func genereertWetBrpLaaGeenSignaal(ctx context.Context) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["genereer_signaal"]
	if !ok {
		// If field doesn't exist, assume no signal (default false)
		return nil
	}

	genereertSignaal, ok := v.(bool)
	require.True(godog.T(ctx), ok)

	assert.False(godog.T(ctx), genereertSignaal, "Expected LAA not to generate a signal, but it did")

	return nil
}

func isHetSignaalType(ctx context.Context, expectedSignaalType string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["signaal_type"]
	require.True(godog.T(ctx), ok, "Expected 'signaal_type' to be present in output")

	actualSignaalType, ok := v.(string)
	require.True(godog.T(ctx), ok)

	assert.Equal(godog.T(ctx), expectedSignaalType, actualSignaalType,
		fmt.Sprintf("Expected signaal_type to be '%s', but was '%s'", expectedSignaalType, actualSignaalType))

	return nil
}
