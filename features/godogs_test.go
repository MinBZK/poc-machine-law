package main

import (
	"context"
	"fmt"
	"os"
	"testing"
	"time"

	"github.com/cucumber/godog"
	// "github.com/minbzk/poc-machine-law/machine-v2/rules"
	"github.com/sirupsen/logrus"
	"github.com/stretchr/testify/assert"
)

// godogsCtxKey is the key used to store the available godogs in the context.Context.
type dateCtxKey struct{}
type bsnCtxKey struct{}
type resultCtxKey struct{}
type inputCtxKey struct{}

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
	ctx.Then(`^is de huurtoeslag "([^"]*)" euro$`, isDeHuurtoeslagEuro)
	ctx.Then(`^is de status "([^"]*)"$`, isDeStatus)
	ctx.Then(`^is de woonkostentoeslag "([^"]*)" euro$`, isDeWoonkostentoeslagEuro)
	ctx.Then(`^is het bijstandsuitkeringsbedrag "([^"]*)" euro$`, isHetBijstandsuitkeringsbedragEuro)
	ctx.Then(`^is het pensioen "([^"]*)" euro$`, isHetPensioenEuro)
	ctx.Then(`^is het startkapitaal "([^"]*)" euro$`, isHetStartkapitaalEuro)
	ctx.Then(`^is het toeslagbedrag "(\-*\d+\.\d+)" euro$`, isHetToeslagbedragEuro)
	ctx.Then(`^is niet voldaan aan de voorwaarden$`, isNietVoldaanAanDeVoorwaarden)
	ctx.Then(`^is voldaan aan de voorwaarden$`, isVoldaanAanDeVoorwaarden)
	ctx.Then(`^kan de burger in beroep gaan bij RECHTBANK_AMSTERDAM$`, kanDeBurgerInBeroepGaanBijRECHTBANK_AMSTERDAM)
	ctx.Then(`^kan de burger in bezwaar gaan$`, kanDeBurgerInBezwaarGaan)
	ctx.Then(`^kan de burger niet in bezwaar gaan met reden "([^"]*)"$`, kanDeBurgerNietInBezwaarGaanMetReden)
	ctx.Then(`^ontbreken er geen verplichte gegevens$`, ontbrekenErGeenVerplichteGegevens)
	ctx.Then(`^ontbreken er verplichte gegevens$`, ontbrekenErVerplichteGegevens)
	ctx.Then(`^wordt de aanvraag toegevoegd aan handmatige beoordeling$`, wordtDeAanvraagToegevoegdAanHandmatigeBeoordeling)
}

func evaluate_law(ctx context.Context, service, law string, approved bool) (context.Context, error) {
	// Configure logging
	logger := logrus.New()
	logger.SetOutput(os.Stdout)
	logger.SetLevel(logrus.DebugLevel)
	logger.SetFormatter(&logrus.TextFormatter{
		ForceColors:      true,
		DisableTimestamp: false,
		FullTimestamp:    true,
	})

	// Create indent logger
	return context.WithValue(ctx, resultCtxKey{}, 0), nil
}

func DeVolgendeGegevens(ctx context.Context, service, table string, data *godog.Table) (context.Context, error) {
	t := []map[string]any{}

	for idx, row := range data.Rows {
		if idx == 0 {
			continue
		}

		v := map[string]any{}
		for idx, cell := range row.Cells {
			v[data.Rows[0].Cells[idx].Value] = cell.Value
		}

		t = append(t, v)
	}

	return context.WithValue(ctx, inputCtxKey{}, t), nil
}

func deDatumIs(ctx context.Context, arg1 string) (context.Context, error) {
	t1, err := time.Parse("2006-01-02", arg1)
	if err != nil {
		return nil, fmt.Errorf("could not parse time: %w", err)
	}

	return context.WithValue(ctx, dateCtxKey{}, t1), nil
}

func eenPersoonMetBSN(ctx context.Context, arg1 string) (context.Context, error) {
	return context.WithValue(ctx, bsnCtxKey{}, arg1), nil
}

func deWetWordtUitgevoerdDoorService(ctx context.Context, law, service string) (context.Context, error) {
	return evaluate_law(ctx, service, law, true)
}

func deWetWordtUitgevoerdDoorServiceMetWijzigingen(ctx context.Context, law, service string) (context.Context, error) {
	return evaluate_law(ctx, service, law, false)
}

func isNietVoldaanAanDeVoorwaarden() error {
	return nil
}

func heeftDePersoonRechtOpZorgtoeslag(ctx context.Context) error {
	result, ok := ctx.Value(resultCtxKey{}).(map[string]any)
	assert.True(godog.T(ctx), ok)

	v, ok := result["is_verzekerde_zorgtoeslag"]
	assert.True(godog.T(ctx), ok)

	v1, ok := v.(bool)
	assert.True(godog.T(ctx), ok)

	assert.True(godog.T(ctx), v1)

	return nil
}

func isHetToeslagbedragEuro(ctx context.Context, expected float64) error {
	result, ok := ctx.Value(resultCtxKey{}).(map[string]any)
	assert.True(godog.T(ctx), ok)

	v, ok := result["hoogte_toeslag"]
	assert.True(godog.T(ctx), ok)

	actual, ok := v.(int)
	assert.True(godog.T(ctx), ok)

	assert.Equal(godog.T(ctx), int(expected*100), actual)

	return nil
}

func alleAanvragenWordenBeoordeeld() error {
	return godog.ErrPending
}

func deBeoordelaarDeAanvraagAfwijstMetReden(arg1 string) error {
	return godog.ErrPending
}

func deBeoordelaarHetBezwaarAfwijstMetReden(arg1 string) error {
	return godog.ErrPending
}

func deBeoordelaarHetBezwaarToewijstMetReden(arg1 string) error {
	return godog.ErrPending
}

func deBurgerBezwaarMaaktMetReden(arg1 string) error {
	return godog.ErrPending
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

func heeftDePersoonGeenStemrecht() error {
	return godog.ErrPending
}

func heeftDePersoonRechtOpHuurtoeslag() error {
	return godog.ErrPending
}

func heeftDePersoonStemrecht() error {
	return godog.ErrPending
}

func isDeAanvraagAfgewezen() error {
	return godog.ErrPending
}

func isDeAanvraagToegekend() error {
	return godog.ErrPending
}

func isDeHuurtoeslagEuro(arg1 string) error {
	return godog.ErrPending
}

func isDeStatus(arg1 string) error {
	return godog.ErrPending
}

func isDeWoonkostentoeslagEuro(arg1 string) error {
	return godog.ErrPending
}

func isHetBijstandsuitkeringsbedragEuro(arg1 string) error {
	return godog.ErrPending
}

func isHetPensioenEuro(arg1 string) error {
	return godog.ErrPending
}

func isHetStartkapitaalEuro(arg1 string) error {
	return godog.ErrPending
}

func isVoldaanAanDeVoorwaarden() error {
	return godog.ErrPending
}

func kanDeBurgerInBeroepGaanBijRECHTBANK_AMSTERDAM() error {
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
