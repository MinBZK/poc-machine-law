package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"
	"maps"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
	"time"

	"slices"

	"github.com/cucumber/godog"
	"github.com/google/uuid"
	"github.com/minbzk/poc-machine-law/machinev2/machine/casemanager"
	"github.com/minbzk/poc-machine-law/machinev2/machine/casemanager/manager"
	"github.com/minbzk/poc-machine-law/machinev2/machine/claimmanager"
	"github.com/minbzk/poc-machine-law/machinev2/machine/claimmanager/inmemory"
	"github.com/minbzk/poc-machine-law/machinev2/machine/dataframe"
	"github.com/minbzk/poc-machine-law/machinev2/machine/logger"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
	"github.com/minbzk/poc-machine-law/machinev2/machine/service/serviceprovider"
	"github.com/sirupsen/logrus"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// Context keys for storing test state.
type paramsCtxKey struct{}
type resultCtxKey struct{}
type inputCtxKey struct{}
type servicesCtxKey struct{}
type serviceCtxKey struct{}
type caseManagerCtxKey struct{}
type claimManagerCtxKey struct{}
type lawCtxKey struct{}
type caseIDCtxKey struct{}

// getFeatureFiles returns .feature files recursively from the current directory.
func getFeatureFiles() []string {
	var features []string
	err := filepath.WalkDir(".", func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if !d.IsDir() && filepath.Ext(path) == ".feature" {
			features = append(features, path)
		}
		return nil
	})
	if err != nil || len(features) == 0 {
		return []string{"."}
	}
	return features
}

func TestFeatures(t *testing.T) {
	featurePaths := getFeatureFiles()

	suite := godog.TestSuite{
		ScenarioInitializer: InitializeScenario,
		Options: &godog.Options{
			Format:   "pretty",
			Paths:    featurePaths,
			Tags:     "~@skip-go",
			TestingT: t,
		},
	}

	if suite.Run() != 0 {
		t.Fatal("non-zero status returned, failed to run feature tests")
	}
}

// =============================================================================
// Helpers: output field access, assertions, currency parsing
// =============================================================================

// getResult extracts the RuleResult from context.
func getResult(ctx context.Context) model.RuleResult {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok, "Expected result to be present in context")
	return result
}

// getOutputField extracts a named field from the result output.
func getOutputField(ctx context.Context, field string) (any, bool) {
	result := getResult(ctx)
	v, ok := result.Output[field]
	return v, ok
}

// requireOutputInt extracts a named integer field from output, failing if not found.
func requireOutputInt(ctx context.Context, field string) int {
	v, ok := getOutputField(ctx, field)
	require.True(godog.T(ctx), ok, "Expected '%s' to be present in output", field)
	actual, ok := v.(int)
	require.True(godog.T(ctx), ok, "Expected '%s' to be an int, got %T", field, v)
	return actual
}

// requireOutputBool extracts a named boolean field from output, failing if not found.
func requireOutputBool(ctx context.Context, field string) bool {
	v, ok := getOutputField(ctx, field)
	require.True(godog.T(ctx), ok, "Expected '%s' to be present in output", field)
	actual, ok := v.(bool)
	require.True(godog.T(ctx), ok, "Expected '%s' to be a bool, got %T", field, v)
	return actual
}

// requireOutputString extracts a named string field from output, failing if not found.
func requireOutputString(ctx context.Context, field string) string {
	v, ok := getOutputField(ctx, field)
	require.True(godog.T(ctx), ok, "Expected '%s' to be present in output", field)
	actual, ok := v.(string)
	require.True(godog.T(ctx), ok, "Expected '%s' to be a string, got %T", field, v)
	return actual
}

// compareMonetaryValue compares an expected euro amount (float) against actual eurocent (int).
func compareMonetaryValue(ctx context.Context, expected float64, actual int) {
	assert.Equal(godog.T(ctx), int(expected*100), actual,
		"Expected €%.2f (%d eurocent), got €%.2f (%d eurocent)",
		expected, int(expected*100), float64(actual)/100.0, actual)
}

// compareMonetaryValueApproximately compares with tolerance in eurocents.
func compareMonetaryValueApproximately(ctx context.Context, expected float64, actual int, toleranceEurocents int) {
	expectedCents := int(expected * 100)
	assert.InDelta(godog.T(ctx), expectedCents, actual, float64(toleranceEurocents),
		"Expected approximately €%.2f (%d eurocent), got €%.2f (%d eurocent)",
		expected, expectedCents, float64(actual)/100.0, actual)
}

// parseDutchCurrency parses "€3.480,00" format to float64.
func parseDutchCurrency(ctx context.Context, amount string) float64 {
	cleaned := strings.ReplaceAll(amount, "€", "")
	cleaned = strings.ReplaceAll(cleaned, ".", "")
	cleaned = strings.ReplaceAll(cleaned, ",", ".")
	cleaned = strings.TrimSpace(cleaned)
	result, err := strconv.ParseFloat(cleaned, 64)
	require.NoError(godog.T(ctx), err, "Failed to parse currency amount: %s", amount)
	return result
}

func requirementsMet(ctx context.Context, msgAndArgs ...any) {
	result := getResult(ctx)
	assert.True(godog.T(ctx), result.RequirementsMet, msgAndArgs...)
}

func requirementsNotMet(ctx context.Context, msgAndArgs ...any) {
	result := getResult(ctx)
	assert.False(godog.T(ctx), result.RequirementsMet, msgAndArgs...)
}

// =============================================================================
// Generic step functions (reused by multiple step registrations)
// =============================================================================

// checkOutputEuro checks an output field value in euros (stored as eurocent).
func checkOutputEuro(ctx context.Context, field string, expected float64) error {
	actual := requireOutputInt(ctx, field)
	compareMonetaryValue(ctx, expected, actual)
	return nil
}

// checkOutputInt checks an output field value as integer.
func checkOutputInt(ctx context.Context, field, expected string) error {
	actual := requireOutputInt(ctx, field)
	expectedInt, err := strconv.Atoi(expected)
	require.NoError(godog.T(ctx), err)
	assert.Equal(godog.T(ctx), expectedInt, actual, "Expected %s to be %d, but was %d", field, expectedInt, actual)
	return nil
}

// checkOutputString checks an output field value as string.
func checkOutputString(ctx context.Context, field, expected string) error {
	actual := requireOutputString(ctx, field)
	assert.Equal(godog.T(ctx), expected, actual, "Expected %s to be %s, but was %s", field, expected, actual)
	return nil
}

// checkOutputBoolTrue checks that a boolean output field is true.
func checkOutputBoolTrue(ctx context.Context, field, msg string) error {
	actual := requireOutputBool(ctx, field)
	assert.True(godog.T(ctx), actual, msg)
	return nil
}

// checkOutputBoolFalse checks that a boolean output field is false.
// If the field is missing, it's treated as false (which passes).
func checkOutputBoolFalse(ctx context.Context, field, msg string) error {
	v, ok := getOutputField(ctx, field)
	if !ok {
		return nil
	}
	actual, ok := v.(bool)
	require.True(godog.T(ctx), ok, "Expected '%s' to be a bool", field)
	assert.False(godog.T(ctx), actual, msg)
	return nil
}

// checkDutchCurrencyExact parses Dutch-format currency and compares exactly.
func checkDutchCurrencyExact(ctx context.Context, field, expectedAmount string) error {
	actual := requireOutputInt(ctx, field)
	expected := parseDutchCurrency(ctx, expectedAmount)
	compareMonetaryValue(ctx, expected, actual)
	return nil
}

// checkDutchCurrencyApprox parses Dutch-format currency and compares approximately.
func checkDutchCurrencyApprox(ctx context.Context, field, expectedAmount string, toleranceCents int) error {
	actual := requireOutputInt(ctx, field)
	expected := parseDutchCurrency(ctx, expectedAmount)
	compareMonetaryValueApproximately(ctx, expected, actual, toleranceCents)
	return nil
}

// setParam sets a parameter in the context params map.
func setParam(ctx context.Context, key string, value any) context.Context {
	params, ok := ctx.Value(paramsCtxKey{}).(map[string]any)
	if !ok {
		params = map[string]any{}
	}
	params[key] = value
	return context.WithValue(ctx, paramsCtxKey{}, params)
}

// =============================================================================
// Scenario initialization
// =============================================================================

func InitializeScenario(ctx *godog.ScenarioContext) {
	// Setup steps
	ctx.Given(`^de volgende ([^"]*) ([^"]*) gegevens:?$`, DeVolgendeGegevens)
	ctx.Given(`^de datum is "([^"]*)"$`, deDatumIs)
	ctx.Given(`^een persoon met BSN "([^"]*)"$`, eenPersoonMetBSN)
	ctx.Given(`^alle aanvragen worden beoordeeld$`, alleAanvragenWordenBeoordeeld)

	// Law execution steps
	ctx.When(`^de ([^"]*) wordt uitgevoerd door ([^"]*) met wijzigingen$`, deWetWordtUitgevoerdDoorServiceMetWijzigingen)
	ctx.When(`^de ([^"]*) wordt uitgevoerd door ([^"]*) met$`, deWetWordtUitgevoerdDoorServiceMet)
	ctx.When(`^de ([^"]*) wordt uitgevoerd door ([^"]*)$`, deWetWordtUitgevoerdDoorService)

	// Case management steps
	ctx.When(`^de beoordelaar de aanvraag afwijst met reden "([^"]*)"$`, deBeoordelaarDeAanvraagAfwijstMetReden)
	ctx.When(`^de beoordelaar het bezwaar ([^"]*) met reden "([^"]*)"$`, deBeoordelaarHetBezwaarBeoordeeldMetReden)
	ctx.When(`^de burger bezwaar maakt met reden "([^"]*)"$`, deBurgerBezwaarMaaktMetReden)
	ctx.When(`^de burger ([^"]*) indient:$`, deBurgerGegevensIndient)
	ctx.When(`^de persoon dit aanvraagt$`, dePersoonDitAanvraagt)

	// Requirements assertions
	ctx.Then(`^is voldaan aan de voorwaarden$`, isVoldaanAanDeVoorwaarden)
	ctx.Then(`^is niet voldaan aan de voorwaarden$`, isNietVoldaanAanDeVoorwaarden)
	ctx.Then(`^ontbreken er geen verplichte gegevens$`, ontbrekenErGeenVerplichteGegevens)
	ctx.Then(`^ontbreken er verplichte gegevens$`, ontbrekenErVerplichteGegevens)

	// Case status assertions
	ctx.Then(`^is de aanvraag afgewezen$`, isDeAanvraagAfgewezen)
	ctx.Then(`^is de aanvraag toegekend$`, isDeAanvraagToegekend)
	ctx.Then(`^is de status "([^"]*)"$`, isDeStatus)
	ctx.Then(`^wordt de aanvraag toegevoegd aan handmatige beoordeling$`, wordtDeAanvraagToegevoegdAanHandmatigeBeoordeling)
	ctx.Then(`^kan de burger in bezwaar gaan$`, kanDeBurgerInBezwaarGaan)
	ctx.Then(`^kan de burger niet in bezwaar gaan met reden "([^"]*)"$`, kanDeBurgerNietInBezwaarGaanMetReden)
	ctx.Then(`^kan de burger in beroep gaan bij ([^"]*)$`, kanDeBurgerInBeroepGaanBij)

	// Euro amount assertions (stored as eurocent in output)
	ctx.Then(`^is het toeslagbedrag "(\-*\d+\.\d+)" euro$`, isHetToeslagbedragEuro)
	ctx.Then(`^is de huurtoeslag "(\-*\d+\.\d+)" euro$`, func(ctx context.Context, expected float64) error {
		return checkOutputEuro(ctx, "subsidiebedrag", expected)
	})
	ctx.Then(`^is de woonkostentoeslag "(\-*\d+\.\d+)" euro$`, func(ctx context.Context, expected float64) error {
		return checkOutputEuro(ctx, "woonkostentoeslag", expected)
	})
	ctx.Then(`^is het bijstandsuitkeringsbedrag "(\-*\d+\.\d+)" euro$`, func(ctx context.Context, expected float64) error {
		return checkOutputEuro(ctx, "uitkeringsbedrag", expected)
	})
	ctx.Then(`^is het pensioen "(\-*\d+\.\d+)" euro$`, func(ctx context.Context, expected float64) error {
		return checkOutputEuro(ctx, "pensioenbedrag", expected)
	})
	ctx.Then(`^is het startkapitaal "(\-*\d+\.\d+)" euro$`, func(ctx context.Context, expected float64) error {
		return checkOutputEuro(ctx, "startkapitaal", expected)
	})
	ctx.Then(`^is het bedrijfskapitaal_max "(\-*\d+\.\d+)" euro$`, func(ctx context.Context, expected float64) error {
		return checkOutputEuro(ctx, "bedrijfskapitaal_max", expected)
	})
	ctx.Then(`^zijn de project kosten "([^"]*)" euro$`, func(ctx context.Context, expected string) error {
		expectedFloat, err := strconv.ParseFloat(expected, 64)
		require.NoError(godog.T(ctx), err)
		return checkOutputEuro(ctx, "project_kosten", expectedFloat)
	})

	// Generic eurocent assertion (handles both "is het" and "is de" via regex)
	ctx.Step(`^is het ([^"]*) "(\d+)" eurocent$`, isHetBedragEurocent)
	ctx.Step(`^is de werkgeversbijdrage "([^"]*)" eurocent$`, isDeWerkgeversbijdrageEurocent)

	// Integer field assertions (generic pattern)
	ctx.Then(`^is het aantal_werknemers "([^"]*)"$`, func(ctx context.Context, v string) error { return checkOutputInt(ctx, "aantal_werknemers", v) })
	ctx.Then(`^is de co2_uitstoot_totaal "([^"]*)"$`, func(ctx context.Context, v string) error { return checkOutputInt(ctx, "co2_uitstoot_totaal", v) })
	ctx.Then(`^is de max_duur_maanden "([^"]*)"$`, func(ctx context.Context, v string) error { return checkOutputInt(ctx, "max_duur_maanden", v) })
	ctx.Then(`^is de woon_werk_auto_benzine "([^"]*)"$`, func(ctx context.Context, v string) error { return checkOutputInt(ctx, "woon_werk_auto_benzine", v) })
	ctx.Then(`^is de woon_werk_auto_diesel "([^"]*)"$`, func(ctx context.Context, v string) error { return checkOutputInt(ctx, "woon_werk_auto_diesel", v) })
	ctx.Then(`^is de woon_werk_openbaar_vervoer "([^"]*)"$`, func(ctx context.Context, v string) error { return checkOutputInt(ctx, "woon_werk_openbaar_vervoer", v) })
	ctx.Then(`^is de zakelijk_auto_benzine "([^"]*)"$`, func(ctx context.Context, v string) error { return checkOutputInt(ctx, "zakelijk_auto_benzine", v) })
	ctx.Then(`^is de zakelijk_auto_diesel "([^"]*)"$`, func(ctx context.Context, v string) error { return checkOutputInt(ctx, "zakelijk_auto_diesel", v) })

	// String field assertions
	ctx.Then(`^is de categorie_zelfstandige "([^"]*)"$`, func(ctx context.Context, v string) error { return checkOutputString(ctx, "categorie_zelfstandige", v) })
	ctx.Then(`^is het bedrijfskapitaal_type "([^"]*)"$`, func(ctx context.Context, v string) error { return checkOutputString(ctx, "bedrijfskapitaal_type", v) })

	// Boolean assertions: zorgtoeslag
	ctx.Then(`^heeft de persoon recht op zorgtoeslag$`, func(ctx context.Context) error {
		return checkOutputBoolTrue(ctx, "is_verzekerde_zorgtoeslag", "Expected person to be eligible for zorgtoeslag")
	})

	// Boolean assertions: kinderopvangtoeslag
	ctx.Step(`^heeft de persoon recht op kinderopvangtoeslag$`, func(ctx context.Context) error {
		return checkOutputBoolTrue(ctx, "is_gerechtigd", "Expected person to be eligible for kinderopvangtoeslag")
	})
	ctx.Step(`^heeft de persoon geen recht op kinderopvangtoeslag$`, func(ctx context.Context) error {
		return checkOutputBoolFalse(ctx, "is_gerechtigd", "Expected person to NOT be eligible for kinderopvangtoeslag")
	})

	// Boolean assertions: WW
	ctx.Step(`^heeft de persoon recht op WW$`, func(ctx context.Context) error {
		return checkOutputBoolTrue(ctx, "heeft_recht_op_ww", "Expected person to be eligible for WW")
	})
	ctx.Step(`^heeft de persoon geen recht op WW$`, heeftDePersoonGeenRechtOpWW)

	// WW-specific assertions
	ctx.Step(`^is de WW duur "([^"]*)" maanden$`, func(ctx context.Context, v string) error { return checkOutputInt(ctx, "ww_duur_maanden", v) })
	ctx.Step(`^is de WW uitkering per maand maximaal "([^"]*)"$`, func(ctx context.Context, amount string) error {
		return checkDutchCurrencyExact(ctx, "ww_uitkering_per_maand", amount)
	})
	ctx.Step(`^is de WW uitkering per maand ongeveer "([^"]*)"$`, func(ctx context.Context, amount string) error {
		return checkDutchCurrencyApprox(ctx, "ww_uitkering_per_maand", amount, 50)
	})
	ctx.Step(`^is de WW uitkering maximaal omdat het dagloon gemaximeerd is$`, isDeWWUitkeringMaximaal)

	// Kindgebonden budget assertions
	ctx.Step(`^is het ALO-kop bedrag "([^"]*)"$`, func(ctx context.Context, amount string) error {
		return checkDutchCurrencyExact(ctx, "alo_kop_bedrag", amount)
	})
	ctx.Step(`^is het kindgebonden budget ongeveer "([^"]*)" per jaar$`, func(ctx context.Context, amount string) error {
		return checkDutchCurrencyApprox(ctx, "kindgebonden_budget_jaar", amount, 50)
	})
	ctx.Step(`^is het totale kindgebonden budget ongeveer "([^"]*)" per jaar$`, isHetTotaleKindgebondenBudgetOngeveerPerJaar)
	ctx.Step(`^is het kindgebonden budget lager door hoog inkomen$`, isHetKindgebondenBudgetLagerDoorHoogInkomen)
	ctx.Step(`^ontvangt de persoon de ALO-kop omdat deze alleenstaand is$`, ontvangtDePersoonDeALOkopOmdatDezeAlleenstaandIs)
	ctx.Step(`^is het kindgebonden budget hoog door laag inkomen en meerdere kinderen$`, isHetKindgebondenBudgetHoogDoorLaagInkomenEnMeerdereKinderen)
	ctx.Step(`^ontvangt de persoon extra bedragen voor kinderen 12\+ en 16\+$`, ontvangtDePersoonExtraBedragenVoorKinderen12Plus)
	ctx.Step(`^is het kindgebonden budget maximaal door laag inkomen$`, isHetKindgebondenBudgetMaximaalDoorLaagInkomen)

	// Generic output assertions
	ctx.Step(`^heeft de output "([^"]*)" waarde "([^"]*)"$`, heeftDeOutputWaarde)
	ctx.Step(`^is de output "([^"]*)" waar$`, func(ctx context.Context, field string) error {
		return checkOutputBoolTrue(ctx, field, fmt.Sprintf("Expected '%s' to be true", field))
	})
	ctx.Step(`^is de output "([^"]*)" onwaar$`, func(ctx context.Context, field string) error {
		return checkOutputBoolFalse(ctx, field, fmt.Sprintf("Expected '%s' to be false", field))
	})
	ctx.Step(`^bevat de output "([^"]*)" waarde "(\[.+\])"$`, bevatDeOutputWaarde)
	ctx.Step(`^bevat de output "([^"]*)" waarde "([^"]*)"$`, bevatDeOutputWaarde)
	ctx.Step(`^bevat de output "([^"]*)" niet de waarde "([^"]*)"$`, bevatDeOutputNietDeWaarde)
	ctx.Step(`^is de output "([^"]*)" leeg$`, isDeOutputLeeg)

	// Aliases for generic output assertions (alternative phrasing)
	ctx.Step(`^is het veld "([^"]*)" gelijk aan "([^"]*)"$`, heeftDeOutputWaarde)
	ctx.Step(`^is het veld "([^"]*)" een lege lijst$`, isDeOutputLeeg)
	ctx.Step(`^bevat het veld "([^"]*)" de waarde "([^"]*)"$`, bevatDeOutputWaarde)

	// Entity setup steps
	ctx.Step(`^een organisatie met ID "([^"]*)"$`, func(ctx context.Context, id string) (context.Context, error) {
		return setParam(ctx, "ORGANISATIE_ID", id), nil
	})
	ctx.Step(`^een ICT-project met ID "([^"]*)"$`, func(ctx context.Context, id string) (context.Context, error) {
		return setParam(ctx, "PROJECT_ID", id), nil
	})
	ctx.Step(`^een organisatie met KVK-nummer "([^"]*)"$`, func(ctx context.Context, id string) (context.Context, error) {
		return setParam(ctx, "KVK_NUMMER", id), nil
	})
	ctx.Step(`^een werkgever met loonheffingennummer "([^"]*)"$`, func(ctx context.Context, id string) (context.Context, error) {
		return setParam(ctx, "LOONHEFFINGENNUMMER", id), nil
	})
	ctx.Step(`^een werknemer met bruto jaarloon "([^"]*)" euro$`, func(ctx context.Context, amount string) (context.Context, error) {
		f, err := strconv.ParseFloat(amount, 64)
		if err != nil {
			return ctx, fmt.Errorf("could not parse bruto jaarloon: %w", err)
		}
		return setParam(ctx, "BRUTO_LOON", f), nil
	})

	// Case manager wait after each step
	ctx.StepContext().After(func(ctx context.Context, _ *godog.Step, _ godog.StepResultStatus, _ error) (context.Context, error) {
		cm, ok := ctx.Value(caseManagerCtxKey{}).(casemanager.CaseManager)
		if !ok || cm == nil {
			return ctx, nil
		}
		cm.Wait()
		return ctx, nil
	})
}

// =============================================================================
// Core step implementations
// =============================================================================

func evaluateLaw(ctx context.Context, svc, law string, approved bool) (context.Context, error) {
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
		return ctx, errors.New("services not set")
	}

	err := services.Reset(ctx)
	require.NoError(godog.T(ctx), err)

	inputs, ok := ctx.Value(inputCtxKey{}).([]input)
	if ok {
		for _, input := range inputs {
			err := services.SetSourceDataFrame(ctx, input.Service, input.Table, input.DF)
			require.NoError(godog.T(ctx), err)
		}
	}

	params, ok := ctx.Value(paramsCtxKey{}).(map[string]any)
	if !ok {
		params = map[string]any{}
	}

	result, err := services.Evaluate(ctx, svc, law, params, nil, nil, nil, "", approved)
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

// =============================================================================
// Given steps
// =============================================================================

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

	logr := logger.New("godog_test", os.Stdout, logrus.DebugLevel)

	caseManager := manager.New(logr)
	claimManager := inmemory.New(logr, caseManager)
	ruleresolver, err := ruleresolver.New()
	if err != nil {
		return nil, fmt.Errorf("new ruleresolver: %w", err)
	}

	services, err := serviceprovider.New(logr, t1, caseManager, claimManager, ruleresolver, serviceprovider.WithRuleServiceInMemory())
	if err != nil {
		return nil, fmt.Errorf("new services: %w", err)
	}

	caseManager.SetService(services)

	ctx = context.WithValue(ctx, servicesCtxKey{}, services)
	ctx = context.WithValue(ctx, caseManagerCtxKey{}, caseManager)
	ctx = context.WithValue(ctx, claimManagerCtxKey{}, claimManager)

	return ctx, nil
}

func eenPersoonMetBSN(ctx context.Context, bsn string) (context.Context, error) {
	return setParam(ctx, "BSN", bsn), nil
}

type SampleRater interface {
	SetSampleRate(value float64)
}

func alleAanvragenWordenBeoordeeld(ctx context.Context) error {
	cm, ok := ctx.Value(caseManagerCtxKey{}).(casemanager.CaseManager)
	if !ok || cm == nil {
		return errors.New("casemanager not set")
	}
	if cm, ok := cm.(SampleRater); ok {
		cm.SetSampleRate(1.0)
	}
	return nil
}

// =============================================================================
// When steps
// =============================================================================

func deWetWordtUitgevoerdDoorService(ctx context.Context, law, service string) (context.Context, error) {
	return evaluateLaw(ctx, service, law, true)
}

func deWetWordtUitgevoerdDoorServiceMetWijzigingen(ctx context.Context, law, service string) (context.Context, error) {
	return evaluateLaw(ctx, service, law, false)
}

func deWetWordtUitgevoerdDoorServiceMet(ctx context.Context, law, service string, table *godog.Table) (context.Context, error) {
	if len(table.Rows) <= 1 {
		return ctx, errors.New("table must have at least one data row")
	}

	params, ok := ctx.Value(paramsCtxKey{}).(map[string]any)
	if !ok {
		params = map[string]any{}
	}

	headers := table.Rows[0].Cells
	for idx := 1; idx < len(table.Rows); idx++ {
		row := table.Rows[idx]
		if len(headers) == 0 || len(row.Cells) == 0 {
			continue
		}

		key := headers[0].Value
		value := row.Cells[0].Value

		var parsedValue any = value
		if strings.HasPrefix(value, "[") || strings.HasPrefix(value, "{") {
			if err := json.Unmarshal([]byte(value), &parsedValue); err != nil {
				parsedValue = value
			}
		}
		params[key] = parsedValue
	}

	ctx = context.WithValue(ctx, paramsCtxKey{}, params)
	return evaluateLaw(ctx, service, law, true)
}

func deBeoordelaarDeAanvraagAfwijstMetReden(ctx context.Context, reason string) (context.Context, error) {
	cm, ok := ctx.Value(caseManagerCtxKey{}).(casemanager.CaseManager)
	if !ok || cm == nil {
		return ctx, errors.New("case manager not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)

	var verifiedResult map[string]any
	if result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult); ok {
		verifiedResult = result.Output
	}

	return ctx, cm.CompleteManualReview(ctx, caseID, "BEOORDELAAR", false, reason, verifiedResult)
}

func deBeoordelaarHetBezwaarBeoordeeldMetReden(ctx context.Context, approve string, reason string) (context.Context, error) {
	approved := approve == "toewijst"

	cm, ok := ctx.Value(caseManagerCtxKey{}).(casemanager.CaseManager)
	if !ok || cm == nil {
		return ctx, errors.New("case manager not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)

	var verifiedResult map[string]any
	if result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult); ok {
		verifiedResult = result.Output
	}

	return ctx, cm.CompleteManualReview(ctx, caseID, "BEOORDELAAR", approved, reason, verifiedResult)
}

func deBurgerBezwaarMaaktMetReden(ctx context.Context, reason string) (context.Context, error) {
	cm, ok := ctx.Value(caseManagerCtxKey{}).(casemanager.CaseManager)
	if !ok || cm == nil {
		return ctx, errors.New("case manager not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)

	err := cm.ObjectCase(ctx, caseID, reason)
	return ctx, err
}

func deBurgerGegevensIndient(ctx context.Context, chance string, table *godog.Table) (context.Context, error) {
	if len(table.Rows) <= 1 {
		return ctx, errors.New("table must have at least one data row")
	}

	type claim struct {
		Service, Law, Key, Evidence string
		NewValue                    any
		Reason                      string
	}

	lookup := map[string]int{}
	for k, v := range table.Rows[0].Cells {
		lookup[v.Value] = k
	}

	claims := make([]claim, 0, len(table.Rows)-1)
	for idx := 1; idx < len(table.Rows); idx++ {
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
		return ctx, errors.New("BSN not set in parameters")
	}

	claimManager, ok := ctx.Value(claimManagerCtxKey{}).(claimmanager.ClaimManager)
	if !ok || claimManager == nil {
		return ctx, errors.New("claim manager not set")
	}

	for _, v := range claims {
		_, err := claimManager.Submit(ctx, v.Service, v.Key, v.NewValue, v.Reason, "BURGER", v.Law, bsn, uuid.Nil, nil, v.Evidence, false, time.Now())
		if err != nil {
			return ctx, err
		}
	}

	return ctx, nil
}

func dePersoonDitAanvraagt(ctx context.Context) (context.Context, error) {
	cm, ok := ctx.Value(caseManagerCtxKey{}).(casemanager.CaseManager)
	if !ok || cm == nil {
		return ctx, errors.New("case manager not set")
	}

	params := ctx.Value(paramsCtxKey{}).(map[string]any)
	svc := ctx.Value(serviceCtxKey{}).(string)
	law := ctx.Value(lawCtxKey{}).(string)
	result := ctx.Value(resultCtxKey{}).(model.RuleResult)

	maps.Copy(params, result.Input)

	caseID, err := cm.SubmitCase(ctx, params["BSN"].(string), svc, law, params, result.Output, true, nil)
	if err != nil {
		return ctx, err
	}

	return context.WithValue(ctx, caseIDCtxKey{}, caseID), nil
}

// =============================================================================
// Then steps: requirements & missing data
// =============================================================================

func isVoldaanAanDeVoorwaarden(ctx context.Context) error {
	requirementsMet(ctx, "Expected requirements to be met, but they were not")
	return nil
}

func isNietVoldaanAanDeVoorwaarden(ctx context.Context) error {
	requirementsNotMet(ctx, "Expected requirements to not be met, but they were")
	return nil
}

func ontbrekenErGeenVerplichteGegevens(ctx context.Context) error {
	result := getResult(ctx)
	assert.False(godog.T(ctx), result.MissingRequired, "Expected no missing required fields")
	return nil
}

func ontbrekenErVerplichteGegevens(ctx context.Context) error {
	result := getResult(ctx)
	assert.True(godog.T(ctx), result.MissingRequired, "Expected missing required fields")
	return nil
}

// =============================================================================
// Then steps: toeslagbedrag (special case with field fallback)
// =============================================================================

func isHetToeslagbedragEuro(ctx context.Context, expected float64) error {
	result := getResult(ctx)
	v, ok := result.Output["hoogte_toeslag"]
	if !ok {
		v, ok = result.Output["jaarbedrag"]
	}
	require.True(godog.T(ctx), ok, "No toeslag amount found in output")
	actual, ok := v.(int)
	require.True(godog.T(ctx), ok)
	compareMonetaryValue(ctx, expected, actual)
	return nil
}

// =============================================================================
// Then steps: eurocent assertions
// =============================================================================

func isHetBedragEurocent(ctx context.Context, field string, amount int) error {
	actual := requireOutputInt(ctx, field)
	assert.Equal(godog.T(ctx), amount, actual, "Expected %s to be %d eurocent, but was %d", field, amount, actual)
	return nil
}

func isDeWerkgeversbijdrageEurocent(ctx context.Context, expected string) error {
	result := getResult(ctx)
	fieldNames := []string{"werkgeversbijdrage_awf", "zvw_werkgeversbijdrage", "werkgeversbijdrage"}
	var v any
	var found bool
	for _, name := range fieldNames {
		if v, found = result.Output[name]; found {
			break
		}
	}
	require.True(godog.T(ctx), found, "Expected werkgeversbijdrage field to be present in output")
	actual, ok := v.(int)
	require.True(godog.T(ctx), ok)
	expectedInt, err := strconv.Atoi(expected)
	require.NoError(godog.T(ctx), err)
	assert.Equal(godog.T(ctx), expectedInt, actual, "Expected werkgeversbijdrage to be %d eurocent, but was %d", expectedInt, actual)
	return nil
}

// =============================================================================
// Then steps: WW special
// =============================================================================

func heeftDePersoonGeenRechtOpWW(ctx context.Context) error {
	result := getResult(ctx)
	v, ok := result.Output["heeft_recht_op_ww"]
	if !ok {
		assert.False(godog.T(ctx), result.RequirementsMet, "Expected person to NOT be eligible for WW")
		return nil
	}
	actual, ok := v.(bool)
	require.True(godog.T(ctx), ok)
	assert.False(godog.T(ctx), actual, "Expected person to NOT be eligible for WW, but they were")
	return nil
}

func isDeWWUitkeringMaximaal(ctx context.Context) error {
	dagloonValue := requireOutputInt(ctx, "ww_dagloon")
	maxDagloon := 29067
	assert.GreaterOrEqual(godog.T(ctx), dagloonValue, maxDagloon, "Expected dagloon to be at maximum")
	return nil
}

// =============================================================================
// Then steps: kindgebonden budget (narrative assertions)
// =============================================================================

func isHetTotaleKindgebondenBudgetOngeveerPerJaar(ctx context.Context, expectedAmount string) error {
	actual := requireOutputInt(ctx, "kindgebonden_budget_jaar")
	expected := parseDutchCurrency(ctx, expectedAmount)
	expectedCents := int(expected * 100)
	tolerance := float64(expectedCents) * 0.02
	assert.InDelta(godog.T(ctx), expectedCents, actual, tolerance,
		"Expected total kindgebonden budget approximately €%.2f, got €%.2f",
		expected, float64(actual)/100.0)
	return nil
}

func isHetKindgebondenBudgetLagerDoorHoogInkomen(ctx context.Context) error {
	actual := requireOutputInt(ctx, "kindgebonden_budget_jaar")
	maxBudget := 850200
	assert.Less(godog.T(ctx), actual, maxBudget,
		"Expected budget to be reduced from maximum €8,502, but was €%.2f", float64(actual)/100)
	return nil
}

func ontvangtDePersoonDeALOkopOmdatDezeAlleenstaandIs(ctx context.Context) error {
	actual := requireOutputInt(ctx, "alo_kop_bedrag")
	assert.Positive(godog.T(ctx), actual, "Expected ALO-kop to be greater than 0 for single parent")
	return nil
}

func isHetKindgebondenBudgetHoogDoorLaagInkomenEnMeerdereKinderen(ctx context.Context) error {
	actual := requireOutputInt(ctx, "kindgebonden_budget_jaar")
	assert.GreaterOrEqual(godog.T(ctx), actual, 700000,
		"Expected budget to be high due to low income and multiple children, but was €%.2f", float64(actual)/100)
	return nil
}

func ontvangtDePersoonExtraBedragenVoorKinderen12Plus(ctx context.Context) error {
	_, ok := getOutputField(ctx, "kindgebonden_budget_jaar")
	require.True(godog.T(ctx), ok, "Expected 'kindgebonden_budget_jaar' to be present in output")
	return nil
}

func isHetKindgebondenBudgetMaximaalDoorLaagInkomen(ctx context.Context) error {
	actual := requireOutputInt(ctx, "kindgebonden_budget_jaar")
	assert.InDelta(godog.T(ctx), 599100, actual, 10000, "Expected budget to be near maximum for low income")
	return nil
}

// =============================================================================
// Then steps: case management assertions
// =============================================================================

func isDeAanvraagAfgewezen(ctx context.Context) error {
	cm, ok := ctx.Value(caseManagerCtxKey{}).(casemanager.CaseManager)
	if !ok || cm == nil {
		return errors.New("case manager not set")
	}
	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)
	c, err := getCaseByID(ctx, cm, caseID, compareCaseStatus(casemanager.CaseStatusDecided))
	require.NoError(godog.T(ctx), err)
	assert.Equal(godog.T(ctx), casemanager.CaseStatusDecided, c.Status, "Expected case to be decided")
	require.NotNil(godog.T(ctx), c.Approved, "Expected approved status to be set")
	assert.False(godog.T(ctx), *c.Approved, "Expected case to be rejected")
	return nil
}

func isDeAanvraagToegekend(ctx context.Context) error {
	cm, ok := ctx.Value(caseManagerCtxKey{}).(casemanager.CaseManager)
	if !ok || cm == nil {
		return errors.New("case manager not set")
	}
	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)
	c, err := getCaseByID(ctx, cm, caseID, compareCaseStatus(casemanager.CaseStatusDecided))
	require.NoError(godog.T(ctx), err)
	assert.Equal(godog.T(ctx), casemanager.CaseStatusDecided, c.Status, "Expected case to be decided")
	require.NotNil(godog.T(ctx), c.Approved, "Expected approved status to be set")
	assert.True(godog.T(ctx), *c.Approved, "Expected case to be approved")
	return nil
}

func isDeStatus(ctx context.Context, expected string) error {
	cm, ok := ctx.Value(caseManagerCtxKey{}).(casemanager.CaseManager)
	if !ok || cm == nil {
		return errors.New("case manager not set")
	}
	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)
	c, err := getCaseByID(ctx, cm, caseID, compareCaseStatus(casemanager.CaseStatus(expected)))
	require.NoError(godog.T(ctx), err)
	assert.Equal(godog.T(ctx), casemanager.CaseStatus(expected), c.Status)
	return nil
}

func wordtDeAanvraagToegevoegdAanHandmatigeBeoordeling(ctx context.Context) error {
	cm, ok := ctx.Value(caseManagerCtxKey{}).(casemanager.CaseManager)
	if !ok || cm == nil {
		return errors.New("case manager not set")
	}
	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)
	c, err := getCaseByID(ctx, cm, caseID, compareCaseStatus(casemanager.CaseStatusInReview))
	require.NoError(godog.T(ctx), err)
	assert.Equal(godog.T(ctx), casemanager.CaseStatusInReview, c.Status, "Expected case to be in review")
	return nil
}

func kanDeBurgerInBezwaarGaan(ctx context.Context) error {
	cm, ok := ctx.Value(caseManagerCtxKey{}).(casemanager.CaseManager)
	if !ok || cm == nil {
		return errors.New("case manager not set")
	}
	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)
	c, err := getCaseByID(ctx, cm, caseID, compareCaseCanObject)
	require.NoError(godog.T(ctx), err)
	assert.True(godog.T(ctx), c.CanObject(), "Expected case to be objectable")
	return nil
}

func kanDeBurgerNietInBezwaarGaanMetReden(ctx context.Context, expectedReason string) error {
	cm, ok := ctx.Value(caseManagerCtxKey{}).(casemanager.CaseManager)
	if !ok || cm == nil {
		return errors.New("case manager not set")
	}
	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)
	c, err := getCaseByID(ctx, cm, caseID, compareCaseCanNotObject)
	require.NoError(godog.T(ctx), err)
	require.NotNil(godog.T(ctx), c)
	assert.False(godog.T(ctx), c.CanObject(), "Expected case not to be objectable")
	reason := c.ObjectionStatus.NotPossibleReason
	require.NotNil(godog.T(ctx), reason, "Expected reason to be set")
	assert.Equal(godog.T(ctx), expectedReason, *reason, "Expected reasons to match")
	return nil
}

func kanDeBurgerInBeroepGaanBij(ctx context.Context, competentCourt string) error {
	cm, ok := ctx.Value(caseManagerCtxKey{}).(casemanager.CaseManager)
	if !ok || cm == nil {
		return errors.New("case manager not set")
	}
	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)
	c, err := getCaseByID(ctx, cm, caseID, compareCaseCanAppeal)
	require.NoError(godog.T(ctx), err)
	assert.True(godog.T(ctx), c.CanAppeal(), "Expected to be able to appeal")
	require.NotNil(godog.T(ctx), c.AppealStatus.CompetentCourt, "Expected competent court to be set")
	assert.Equal(godog.T(ctx), competentCourt, *c.AppealStatus.CompetentCourt, "Expected another competent court")
	return nil
}

// =============================================================================
// Then steps: generic output assertions
// =============================================================================

func heeftDeOutputWaarde(ctx context.Context, field, expectedValue string) error {
	result := getResult(ctx)
	v, ok := result.Output[field]
	require.True(godog.T(ctx), ok, "Expected '%s' to be present in output", field)
	expected := parseValue(expectedValue)

	if expectedInt, ok := expected.(int); ok {
		if actualFloat, ok := v.(float64); ok {
			assert.Equal(godog.T(ctx), float64(expectedInt), actualFloat, "Expected %s to be %v, but was %v", field, expected, v)
			return nil
		}
	}

	assert.Equal(godog.T(ctx), expected, v, "Expected %s to be %v, but was %v", field, expected, v)
	return nil
}

func bevatDeOutputWaarde(ctx context.Context, field, expectedValue string) error {
	result := getResult(ctx)
	v, ok := result.Output[field]
	require.True(godog.T(ctx), ok, "Expected '%s' to be present in output", field)

	// Handle Python-style list comparison (e.g., "['LEZEN', 'CLAIMS_INDIENEN']")
	if strings.HasPrefix(expectedValue, "['") && strings.HasSuffix(expectedValue, "']") {
		switch arr := v.(type) {
		case []any:
			items := make([]string, len(arr))
			for i, item := range arr {
				items[i] = fmt.Sprintf("'%v'", item)
			}
			actualList := "[" + strings.Join(items, ", ") + "]"
			assert.Equal(godog.T(ctx), expectedValue, actualList)
		case []string:
			items := make([]string, len(arr))
			for i, item := range arr {
				items[i] = fmt.Sprintf("'%s'", item)
			}
			actualList := "[" + strings.Join(items, ", ") + "]"
			assert.Equal(godog.T(ctx), expectedValue, actualList)
		default:
			assert.Fail(godog.T(ctx), fmt.Sprintf("Expected %s to be a list, but was %T", field, v))
		}
		return nil
	}

	switch arr := v.(type) {
	case []any:
		found := false
		for _, item := range arr {
			if fmt.Sprintf("%v", item) == expectedValue {
				found = true
				break
			}
		}
		assert.True(godog.T(ctx), found, "Expected %s to contain %s, but it did not. Values: %v", field, expectedValue, arr)
	case []string:
		assert.True(godog.T(ctx), slices.Contains(arr, expectedValue), "Expected %s to contain %s", field, expectedValue)
	case string:
		assert.Contains(godog.T(ctx), arr, expectedValue)
	default:
		assert.Equal(godog.T(ctx), expectedValue, fmt.Sprintf("%v", v))
	}
	return nil
}

func bevatDeOutputNietDeWaarde(ctx context.Context, field, expectedValue string) error {
	v, ok := getOutputField(ctx, field)
	if !ok {
		return nil
	}

	switch arr := v.(type) {
	case []any:
		for _, item := range arr {
			assert.NotEqual(godog.T(ctx), expectedValue, fmt.Sprintf("%v", item),
				"Expected %s to NOT contain %s", field, expectedValue)
		}
	case []string:
		assert.False(godog.T(ctx), slices.Contains(arr, expectedValue),
			"Expected %s to NOT contain %s", field, expectedValue)
	case string:
		assert.NotContains(godog.T(ctx), arr, expectedValue)
	default:
		assert.NotEqual(godog.T(ctx), expectedValue, fmt.Sprintf("%v", v))
	}
	return nil
}

func isDeOutputLeeg(ctx context.Context, field string) error {
	v, ok := getOutputField(ctx, field)
	if !ok {
		return nil
	}

	switch arr := v.(type) {
	case []any:
		assert.Empty(godog.T(ctx), arr, "Expected %s to be empty", field)
	case []string:
		assert.Empty(godog.T(ctx), arr, "Expected %s to be empty", field)
	case string:
		assert.Empty(godog.T(ctx), arr, "Expected %s to be empty", field)
	case nil:
		// nil is empty
	default:
		assert.Fail(godog.T(ctx), fmt.Sprintf("Expected %s to be empty, but was %v", field, v))
	}
	return nil
}

// =============================================================================
// Case management helpers
// =============================================================================

func compareCaseStatus(status casemanager.CaseStatus) func(c *casemanager.Case) bool {
	return func(c *casemanager.Case) bool { return c.Status == status }
}

func compareCaseCanObject(c *casemanager.Case) bool    { return c.CanObject() }
func compareCaseCanNotObject(c *casemanager.Case) bool  { return !c.CanObject() }
func compareCaseCanAppeal(c *casemanager.Case) bool     { return c.CanAppeal() }

func getCaseByID(ctx context.Context, cm casemanager.CaseManager, caseID uuid.UUID, fn func(c *casemanager.Case) bool) (*casemanager.Case, error) {
	var err error
	var c *casemanager.Case
	for range 300 {
		c, err = cm.GetCaseByID(ctx, caseID)
		if err == nil && c != nil && fn(c) {
			return c, nil
		}
		time.Sleep(10 * time.Millisecond)
	}
	return nil, fmt.Errorf("failed to get case: %w: %w", errors.New("timeout"), err)
}
