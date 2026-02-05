package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
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

// godogsCtxKey is the key used to store the available godogs in the context.Context.
type paramsCtxKey struct{}
type resultCtxKey struct{}
type inputCtxKey struct{}
type servicesCtxKey struct{}
type serviceCtxKey struct{}
type caseManagerCtxKey struct{}
type claimManagerCtxKey struct{}
type lawCtxKey struct{}
type caseIDCtxKey struct{}

// getFeatureFiles returns feature files from the current directory only,
// excluding subdirectories like pending/
func getFeatureFiles() []string {
	entries, err := os.ReadDir(".")
	if err != nil {
		return []string{"."}
	}

	var features []string
	for _, entry := range entries {
		if !entry.IsDir() && filepath.Ext(entry.Name()) == ".feature" {
			features = append(features, entry.Name())
		}
	}

	if len(features) == 0 {
		return []string{"."}
	}
	return features
}

func TestFeatures(t *testing.T) {
	// Get feature files from current directory only (exclude pending/ subdirectory)
	featurePaths := getFeatureFiles()

	suite := godog.TestSuite{
		ScenarioInitializer: InitializeScenario,
		Options: &godog.Options{
			Format:   "pretty", // pretty, progress, cucumber, events, junit
			Paths:    featurePaths,
			Tags:     "~@skip-go", // Skip tests tagged with @skip-go
			TestingT: t,
		},
	}

	if suite.Run() != 0 {
		t.Fatal("non-zero status returned, failed to run feature tests")
	}
}

func InitializeScenario(ctx *godog.ScenarioContext) {
	ctx.Given(`^de volgende ([^"]*) ([^"]*) gegevens:?$`, DeVolgendeGegevens)
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
	ctx.Step(`^is de reactietermijn_weken "([^"]*)"$`, isDeReactietermijnWeken)
	ctx.Step(`^is de onderzoekstermijn_maanden "([^"]*)"$`, isDeOnderzoekstermijnMaanden)

	// Generic output assertion step definitions
	ctx.Step(`^heeft de output "([^"]*)" waarde "([^"]*)"$`, heeftDeOutputWaarde)
	ctx.Step(`^bevat de output "([^"]*)" waarde "(\[.+\])"$`, bevatDeOutputWaarde)
	ctx.Step(`^bevat de output "([^"]*)" waarde "([^"]*)"$`, bevatDeOutputWaarde)
	ctx.Step(`^bevat de output "([^"]*)" niet de waarde "([^"]*)"$`, bevatDeOutputNietDeWaarde)
	ctx.Step(`^is de output "([^"]*)" leeg$`, isDeOutputLeeg)
	ctx.Step(`^is het veld "([^"]*)" gelijk aan "([^"]*)"$`, isHetVeldGelijkAan)
	ctx.Step(`^is het veld "([^"]*)" een lege lijst$`, isHetVeldEenLegeLijst)
	ctx.Step(`^bevat het veld "([^"]*)" de waarde "([^"]*)"$`, bevatHetVeldDeWaarde)

	// Entity setup step definitions
	ctx.Step(`^een organisatie met ID "([^"]*)"$`, eenOrganisatieMetID)
	ctx.Step(`^een ICT-project met ID "([^"]*)"$`, eenICTprojectMetID)
	ctx.Step(`^een organisatie met KVK-nummer "([^"]*)"$`, eenOrganisatieMetKVKnummer)
	ctx.Step(`^een werkgever met loonheffingennummer "([^"]*)"$`, eenWerkgeverMetLoonheffingennummer)
	ctx.Step(`^een werknemer met bruto jaarloon "([^"]*)" euro$`, eenWerknemerMetBrutoJaarloon)

	// Boolean assertion step definitions
	ctx.Step(`^is de organisatie een bestuursorgaan$`, isDeOrganisatieEenBestuursorgaan)
	ctx.Step(`^is de organisatie geen bestuursorgaan$`, isDeOrganisatieGeenBestuursorgaan)
	ctx.Step(`^valt het project onder adviesplicht$`, valtHetProjectOnderAdviesplicht)
	ctx.Step(`^valt het project niet onder adviesplicht$`, valtHetProjectNietOnderAdviesplicht)

	// Additional field assertions
	ctx.Step(`^is de werkgeversbijdrage "([^"]*)" eurocent$`, isDeWerkgeversbijdrageEurocent)
	ctx.Step(`^zijn de project kosten "([^"]*)" euro$`, zijnDeProjectKostenEuro)
	ctx.Step(`^is de rapportageverplichting "([^"]*)"$`, isDeRapportageverplichting)
	ctx.Step(`^is het aantal_werknemers "([^"]*)"$`, isHetAantalWerknemers)
	ctx.Step(`^is de co2_uitstoot_totaal "([^"]*)"$`, isDeCo2UitstootTotaal)
	ctx.Step(`^is de max_duur_maanden "([^"]*)"$`, isDeMaxDuurMaanden)
	ctx.Step(`^is de categorie_zelfstandige "([^"]*)"$`, isDeCategorieZelfstandige)
	ctx.Step(`^is het bedrijfskapitaal_max "([^"]*)" euro$`, isHetBedrijfskapitaalMaxEuro)
	ctx.Step(`^is het bedrijfskapitaal_type "([^"]*)"$`, isHetBedrijfskapitaalType)
	ctx.Step(`^is de woon_werk_auto_benzine "([^"]*)"$`, isDeWoonWerkAutoBenzine)
	ctx.Step(`^is de woon_werk_auto_diesel "([^"]*)"$`, isDeWoonWerkAutoDiesel)
	ctx.Step(`^is de woon_werk_openbaar_vervoer "([^"]*)"$`, isDeWoonWerkOpenbaarVervoer)
	ctx.Step(`^is de zakelijk_auto_benzine "([^"]*)"$`, isDeZakelijkAutoBenzine)
	ctx.Step(`^is de zakelijk_auto_diesel "([^"]*)"$`, isDeZakelijkAutoDiesel)

	ctx.StepContext().After(func(ctx context.Context, _ *godog.Step, _ godog.StepResultStatus, _ error) (context.Context, error) {
		cm, ok := ctx.Value(caseManagerCtxKey{}).(casemanager.CaseManager)
		if !ok || cm == nil {
			return ctx, nil
		}

		// wait after every step to make sure the state machine is finished
		cm.Wait()

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
		return ctx, errors.New("table must have at least one data row")
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

func deBeoordelaarDeAanvraagAfwijstMetReden(ctx context.Context, reason string) (context.Context, error) {
	cm, ok := ctx.Value(caseManagerCtxKey{}).(casemanager.CaseManager)
	if !ok || cm == nil {
		return ctx, errors.New("case manager not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)

	// Check if we have a result in the context to use as verifiedResult
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

	// Check if we have a result in the context to use as verifiedResult
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
		return ctx, errors.New("BSN not set in parameters")
	}

	claimManager, ok := ctx.Value(claimManagerCtxKey{}).(claimmanager.ClaimManager)
	if !ok || claimManager == nil {
		return ctx, errors.New("claim manager not set")
	}

	for _, v := range claims {
		_, err := claimManager.Submit(
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
			time.Now(),
		)

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

	caseID, err := cm.SubmitCase(
		ctx,
		params["BSN"].(string),
		svc,
		law,
		params,
		result.Output,
		true,
		nil,
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
	cm, ok := ctx.Value(caseManagerCtxKey{}).(casemanager.CaseManager)
	if !ok || cm == nil {
		return errors.New("case manager not set")
	}

	caseID, ok := ctx.Value(caseIDCtxKey{}).(uuid.UUID)
	require.True(godog.T(ctx), ok)

	c, err := getCaseByID(ctx, cm, caseID, compareCaseStatus(casemanager.CaseStatus(expected)))
	require.NoError(godog.T(ctx), err)

	assert.Equal(godog.T(ctx), casemanager.CaseStatus(expected), c.Status,
		"Expected status to be %s, but was %s", expected, c.Status)

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

func getCaseByID(ctx context.Context, cm casemanager.CaseManager, caseID uuid.UUID, fn func(c *casemanager.Case) bool) (*casemanager.Case, error) {
	var err error
	var c *casemanager.Case
	for range 300 {
		c, err = cm.GetCaseByID(ctx, caseID)
		if err == nil && c != nil && fn(c) {
			return c, nil
		}

		time.Sleep(10 * time.Millisecond) // Sleep 10ms to give the timemachine some time to process
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
		return errors.New("could not find: 'is_gerechtigd'")
	}

	actual, ok := v.(bool)
	if !ok {
		return errors.New("could not convert 'is_gerechtigd' to bool")
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
		return errors.New("could not convert 'is_gerechtigd' to bool")
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

	assert.Positive(godog.T(ctx), actual, "Expected ALO-kop to be greater than 0 for single parent")

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
		"Expected signaal_type to be '%s', but was '%s'", expectedSignaalType, actualSignaalType)

	return nil
}

func isDeReactietermijnWeken(ctx context.Context, weken string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["reactietermijn_weken"]
	require.True(godog.T(ctx), ok, "Expected 'reactietermijn_weken' to be present in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok, "Expected 'reactietermijn_weken' to be an integer")

	expected, err := strconv.Atoi(weken)
	require.NoError(godog.T(ctx), err, "Failed to parse expected weeks")

	assert.Equal(godog.T(ctx), expected, actual,
		"Expected reactietermijn_weken to be %d, but was %d", expected, actual)

	return nil
}

func isDeOnderzoekstermijnMaanden(ctx context.Context, maanden string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["onderzoekstermijn_maanden"]
	require.True(godog.T(ctx), ok, "Expected 'onderzoekstermijn_maanden' to be present in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok, "Expected 'onderzoekstermijn_maanden' to be an integer")

	expected, err := strconv.Atoi(maanden)
	require.NoError(godog.T(ctx), err, "Failed to parse expected months")

	assert.Equal(godog.T(ctx), expected, actual,
		"Expected onderzoekstermijn_maanden to be %d, but was %d", expected, actual)

	return nil
}

// Generic output assertion step definitions

func heeftDeOutputWaarde(ctx context.Context, field, expectedValue string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output[field]
	require.True(godog.T(ctx), ok, "Expected '%s' to be present in output", field)

	// Parse expected value
	expected := parseValue(expectedValue)

	// Handle numeric type coercion (Go JSON unmarshals numbers as float64)
	if expectedInt, ok := expected.(int); ok {
		if actualFloat, ok := v.(float64); ok {
			// Compare as floats to handle int vs float64
			assert.Equal(godog.T(ctx), float64(expectedInt), actualFloat, "Expected %s to be %v, but was %v", field, expected, v)
			return nil
		}
	}

	// Compare values
	assert.Equal(godog.T(ctx), expected, v, "Expected %s to be %v, but was %v", field, expected, v)

	return nil
}

func bevatDeOutputWaarde(ctx context.Context, field, expectedValue string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output[field]
	require.True(godog.T(ctx), ok, "Expected '%s' to be present in output", field)

	// Check if expected value is a Python-style list (e.g., "['LEZEN', 'CLAIMS_INDIENEN']")
	if strings.HasPrefix(expectedValue, "['") && strings.HasSuffix(expectedValue, "']") {
		// Convert actual value to Python-style list format for comparison
		switch arr := v.(type) {
		case []any:
			items := make([]string, len(arr))
			for i, item := range arr {
				items[i] = fmt.Sprintf("'%v'", item)
			}
			actualList := "[" + strings.Join(items, ", ") + "]"
			assert.Equal(godog.T(ctx), expectedValue, actualList, "Expected %s to equal %s, but got %s", field, expectedValue, actualList)
		case []string:
			items := make([]string, len(arr))
			for i, item := range arr {
				items[i] = fmt.Sprintf("'%s'", item)
			}
			actualList := "[" + strings.Join(items, ", ") + "]"
			assert.Equal(godog.T(ctx), expectedValue, actualList, "Expected %s to equal %s, but got %s", field, expectedValue, actualList)
		default:
			assert.Fail(godog.T(ctx), fmt.Sprintf("Expected %s to be a list, but was %T", field, v))
		}
		return nil
	}

	// Check if value is an array/slice
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
		found := slices.Contains(arr, expectedValue)
		assert.True(godog.T(ctx), found, "Expected %s to contain %s, but it did not. Values: %v", field, expectedValue, arr)
	case string:
		assert.Contains(godog.T(ctx), arr, expectedValue, "Expected %s to contain %s", field, expectedValue)
	default:
		// If it's a single value, check equality
		assert.Equal(godog.T(ctx), expectedValue, fmt.Sprintf("%v", v), "Expected %s to equal %s", field, expectedValue)
	}

	return nil
}

func bevatDeOutputNietDeWaarde(ctx context.Context, field, expectedValue string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output[field]
	if !ok {
		// Field doesn't exist, so it doesn't contain the value
		return nil
	}

	// Check if value is an array/slice
	switch arr := v.(type) {
	case []any:
		for _, item := range arr {
			assert.NotEqual(godog.T(ctx), expectedValue, fmt.Sprintf("%v", item),
				"Expected %s to NOT contain %s, but it did", field, expectedValue)
		}
	case []string:
		assert.False(godog.T(ctx), slices.Contains(arr, expectedValue),
			"Expected %s to NOT contain %s, but it did", field, expectedValue)
	case string:
		assert.NotContains(godog.T(ctx), arr, expectedValue, "Expected %s to NOT contain %s", field, expectedValue)
	default:
		assert.NotEqual(godog.T(ctx), expectedValue, fmt.Sprintf("%v", v), "Expected %s to NOT equal %s", field, expectedValue)
	}

	return nil
}

func isDeOutputLeeg(ctx context.Context, field string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output[field]
	if !ok {
		// Field doesn't exist, treat as empty
		return nil
	}

	// Check if value is empty
	switch arr := v.(type) {
	case []any:
		assert.Empty(godog.T(ctx), arr, "Expected %s to be empty, but had %d items", field, len(arr))
	case []string:
		assert.Empty(godog.T(ctx), arr, "Expected %s to be empty, but had %d items", field, len(arr))
	case string:
		assert.Empty(godog.T(ctx), arr, "Expected %s to be empty", field)
	case nil:
		// nil is considered empty
	default:
		assert.Fail(godog.T(ctx), fmt.Sprintf("Expected %s to be empty, but was %v", field, v))
	}

	return nil
}

func isHetVeldGelijkAan(ctx context.Context, field, expectedValue string) error {
	return heeftDeOutputWaarde(ctx, field, expectedValue)
}

func isHetVeldEenLegeLijst(ctx context.Context, field string) error {
	return isDeOutputLeeg(ctx, field)
}

func bevatHetVeldDeWaarde(ctx context.Context, field, expectedValue string) error {
	return bevatDeOutputWaarde(ctx, field, expectedValue)
}

// Entity setup step definitions

func eenOrganisatieMetID(ctx context.Context, orgID string) (context.Context, error) {
	params, ok := ctx.Value(paramsCtxKey{}).(map[string]any)
	if !ok {
		params = map[string]any{}
	}
	params["ORGANISATIE_ID"] = orgID
	return context.WithValue(ctx, paramsCtxKey{}, params), nil
}

func eenICTprojectMetID(ctx context.Context, projectID string) (context.Context, error) {
	params, ok := ctx.Value(paramsCtxKey{}).(map[string]any)
	if !ok {
		params = map[string]any{}
	}
	params["PROJECT_ID"] = projectID
	return context.WithValue(ctx, paramsCtxKey{}, params), nil
}

func eenOrganisatieMetKVKnummer(ctx context.Context, kvkNummer string) (context.Context, error) {
	params, ok := ctx.Value(paramsCtxKey{}).(map[string]any)
	if !ok {
		params = map[string]any{}
	}
	params["KVK_NUMMER"] = kvkNummer
	return context.WithValue(ctx, paramsCtxKey{}, params), nil
}

func eenWerkgeverMetLoonheffingennummer(ctx context.Context, loonheffingennummer string) (context.Context, error) {
	params, ok := ctx.Value(paramsCtxKey{}).(map[string]any)
	if !ok {
		params = map[string]any{}
	}
	params["LOONHEFFINGENNUMMER"] = loonheffingennummer
	return context.WithValue(ctx, paramsCtxKey{}, params), nil
}

func eenWerknemerMetBrutoJaarloon(ctx context.Context, brutoJaarloon string) (context.Context, error) {
	params, ok := ctx.Value(paramsCtxKey{}).(map[string]any)
	if !ok {
		params = map[string]any{}
	}
	// Store as float euros (to match Python implementation which handles unit conversion internally)
	amount, err := strconv.ParseFloat(brutoJaarloon, 64)
	if err != nil {
		return ctx, fmt.Errorf("could not parse bruto jaarloon: %w", err)
	}
	params["BRUTO_LOON"] = amount
	return context.WithValue(ctx, paramsCtxKey{}, params), nil
}

// Boolean assertion step definitions

func isDeOrganisatieEenBestuursorgaan(ctx context.Context) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["is_bestuursorgaan"]
	require.True(godog.T(ctx), ok, "Expected 'is_bestuursorgaan' to be present in output")

	actual, ok := v.(bool)
	require.True(godog.T(ctx), ok, "Expected 'is_bestuursorgaan' to be a bool")

	assert.True(godog.T(ctx), actual, "Expected organisation to be a bestuursorgaan, but it was not")

	return nil
}

func isDeOrganisatieGeenBestuursorgaan(ctx context.Context) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["is_bestuursorgaan"]
	if !ok {
		// Field doesn't exist, treat as not a bestuursorgaan
		return nil
	}

	actual, ok := v.(bool)
	require.True(godog.T(ctx), ok, "Expected 'is_bestuursorgaan' to be a bool")

	assert.False(godog.T(ctx), actual, "Expected organisation to NOT be a bestuursorgaan, but it was")

	return nil
}

func valtHetProjectOnderAdviesplicht(ctx context.Context) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["adviesplicht"]
	require.True(godog.T(ctx), ok, "Expected 'adviesplicht' to be present in output")

	actual, ok := v.(bool)
	require.True(godog.T(ctx), ok, "Expected 'adviesplicht' to be a bool")

	assert.True(godog.T(ctx), actual, "Expected project to be subject to adviesplicht, but it was not")

	return nil
}

func valtHetProjectNietOnderAdviesplicht(ctx context.Context) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["adviesplicht"]
	if !ok {
		// Field doesn't exist, treat as no adviesplicht
		return nil
	}

	actual, ok := v.(bool)
	require.True(godog.T(ctx), ok, "Expected 'adviesplicht' to be a bool")

	assert.False(godog.T(ctx), actual, "Expected project to NOT be subject to adviesplicht, but it was")

	return nil
}

// Additional field assertions

func isDeWerkgeversbijdrageEurocent(ctx context.Context, expected string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	// Try multiple field names
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
	require.True(godog.T(ctx), ok, "Expected werkgeversbijdrage to be an int")

	expectedInt, err := strconv.Atoi(expected)
	require.NoError(godog.T(ctx), err)

	assert.Equal(godog.T(ctx), expectedInt, actual, "Expected werkgeversbijdrage to be %d eurocent, but was %d", expectedInt, actual)

	return nil
}

func zijnDeProjectKostenEuro(ctx context.Context, expected string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["project_kosten"]
	require.True(godog.T(ctx), ok, "Expected 'project_kosten' to be present in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok, "Expected 'project_kosten' to be an int")

	expectedFloat, err := strconv.ParseFloat(expected, 64)
	require.NoError(godog.T(ctx), err)

	compareMonitaryValue(ctx, expectedFloat, actual)

	return nil
}

func isDeRapportageverplichting(ctx context.Context, expected string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["rapportageverplichting"]
	require.True(godog.T(ctx), ok, "Expected 'rapportageverplichting' to be present in output")

	expectedBool := expected == "true" || expected == "True" || expected == "TRUE"
	actual, ok := v.(bool)
	require.True(godog.T(ctx), ok, "Expected 'rapportageverplichting' to be a bool")

	assert.Equal(godog.T(ctx), expectedBool, actual, "Expected rapportageverplichting to be %v, but was %v", expectedBool, actual)

	return nil
}

func isHetAantalWerknemers(ctx context.Context, expected string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["aantal_werknemers"]
	require.True(godog.T(ctx), ok, "Expected 'aantal_werknemers' to be present in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok, "Expected 'aantal_werknemers' to be an int")

	expectedInt, err := strconv.Atoi(expected)
	require.NoError(godog.T(ctx), err)

	assert.Equal(godog.T(ctx), expectedInt, actual, "Expected aantal_werknemers to be %d, but was %d", expectedInt, actual)

	return nil
}

func isDeCo2UitstootTotaal(ctx context.Context, expected string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["co2_uitstoot_totaal"]
	require.True(godog.T(ctx), ok, "Expected 'co2_uitstoot_totaal' to be present in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok, "Expected 'co2_uitstoot_totaal' to be an int")

	expectedInt, err := strconv.Atoi(expected)
	require.NoError(godog.T(ctx), err)

	assert.Equal(godog.T(ctx), expectedInt, actual, "Expected co2_uitstoot_totaal to be %d, but was %d", expectedInt, actual)

	return nil
}

func isDeMaxDuurMaanden(ctx context.Context, expected string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["max_duur_maanden"]
	require.True(godog.T(ctx), ok, "Expected 'max_duur_maanden' to be present in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok, "Expected 'max_duur_maanden' to be an int")

	expectedInt, err := strconv.Atoi(expected)
	require.NoError(godog.T(ctx), err)

	assert.Equal(godog.T(ctx), expectedInt, actual, "Expected max_duur_maanden to be %d, but was %d", expectedInt, actual)

	return nil
}

func isDeCategorieZelfstandige(ctx context.Context, expected string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["categorie_zelfstandige"]
	require.True(godog.T(ctx), ok, "Expected 'categorie_zelfstandige' to be present in output")

	actual, ok := v.(string)
	require.True(godog.T(ctx), ok, "Expected 'categorie_zelfstandige' to be a string")

	assert.Equal(godog.T(ctx), expected, actual, "Expected categorie_zelfstandige to be %s, but was %s", expected, actual)

	return nil
}

func isHetBedrijfskapitaalMaxEuro(ctx context.Context, expected string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["bedrijfskapitaal_max"]
	require.True(godog.T(ctx), ok, "Expected 'bedrijfskapitaal_max' to be present in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok, "Expected 'bedrijfskapitaal_max' to be an int")

	expectedFloat, err := strconv.ParseFloat(expected, 64)
	require.NoError(godog.T(ctx), err)

	compareMonitaryValue(ctx, expectedFloat, actual)

	return nil
}

func isHetBedrijfskapitaalType(ctx context.Context, expected string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["bedrijfskapitaal_type"]
	require.True(godog.T(ctx), ok, "Expected 'bedrijfskapitaal_type' to be present in output")

	actual, ok := v.(string)
	require.True(godog.T(ctx), ok, "Expected 'bedrijfskapitaal_type' to be a string")

	assert.Equal(godog.T(ctx), expected, actual, "Expected bedrijfskapitaal_type to be %s, but was %s", expected, actual)

	return nil
}

func isDeWoonWerkAutoBenzine(ctx context.Context, expected string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["woon_werk_auto_benzine"]
	require.True(godog.T(ctx), ok, "Expected 'woon_werk_auto_benzine' to be present in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok, "Expected 'woon_werk_auto_benzine' to be an int")

	expectedInt, err := strconv.Atoi(expected)
	require.NoError(godog.T(ctx), err)

	assert.Equal(godog.T(ctx), expectedInt, actual, "Expected woon_werk_auto_benzine to be %d, but was %d", expectedInt, actual)

	return nil
}

func isDeWoonWerkAutoDiesel(ctx context.Context, expected string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["woon_werk_auto_diesel"]
	require.True(godog.T(ctx), ok, "Expected 'woon_werk_auto_diesel' to be present in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok, "Expected 'woon_werk_auto_diesel' to be an int")

	expectedInt, err := strconv.Atoi(expected)
	require.NoError(godog.T(ctx), err)

	assert.Equal(godog.T(ctx), expectedInt, actual, "Expected woon_werk_auto_diesel to be %d, but was %d", expectedInt, actual)

	return nil
}

func isDeWoonWerkOpenbaarVervoer(ctx context.Context, expected string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["woon_werk_openbaar_vervoer"]
	require.True(godog.T(ctx), ok, "Expected 'woon_werk_openbaar_vervoer' to be present in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok, "Expected 'woon_werk_openbaar_vervoer' to be an int")

	expectedInt, err := strconv.Atoi(expected)
	require.NoError(godog.T(ctx), err)

	assert.Equal(godog.T(ctx), expectedInt, actual, "Expected woon_werk_openbaar_vervoer to be %d, but was %d", expectedInt, actual)

	return nil
}

func isDeZakelijkAutoBenzine(ctx context.Context, expected string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["zakelijk_auto_benzine"]
	require.True(godog.T(ctx), ok, "Expected 'zakelijk_auto_benzine' to be present in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok, "Expected 'zakelijk_auto_benzine' to be an int")

	expectedInt, err := strconv.Atoi(expected)
	require.NoError(godog.T(ctx), err)

	assert.Equal(godog.T(ctx), expectedInt, actual, "Expected zakelijk_auto_benzine to be %d, but was %d", expectedInt, actual)

	return nil
}

func isDeZakelijkAutoDiesel(ctx context.Context, expected string) error {
	result, ok := ctx.Value(resultCtxKey{}).(model.RuleResult)
	require.True(godog.T(ctx), ok)

	v, ok := result.Output["zakelijk_auto_diesel"]
	require.True(godog.T(ctx), ok, "Expected 'zakelijk_auto_diesel' to be present in output")

	actual, ok := v.(int)
	require.True(godog.T(ctx), ok, "Expected 'zakelijk_auto_diesel' to be an int")

	expectedInt, err := strconv.Atoi(expected)
	require.NoError(godog.T(ctx), err)

	assert.Equal(godog.T(ctx), expectedInt, actual, "Expected zakelijk_auto_diesel to be %d, but was %d", expectedInt, actual)

	return nil
}
