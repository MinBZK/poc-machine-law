package service_test

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"testing"
	"time"

	"github.com/minbzk/poc-machine-law/machinev2/machine/dataframe"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/logging"
	"github.com/minbzk/poc-machine-law/machinev2/machine/service"
	"github.com/sirupsen/logrus"
	"github.com/stretchr/testify/assert"
)

func TestService(t *testing.T) {

	start := time.Now()

	logger := logging.New("main", os.Stdout, logrus.DebugLevel)

	// Set up context
	ctx := context.Background()

	// Initialize services with current date
	currentDate := time.Now()
	services, err := service.NewServices(currentDate)
	assert.NoError(t, err)

	logger.Infof(ctx, "Direct rules engine evaluation example:")

	evalParams := map[string]any{
		"BSN": "999993653",
	}

	services.SetSourceDataFrame("CBS", "levensverwachting", dataframe.New([]map[string]any{
		{
			"jaar":           "2025",
			"verwachting_65": "20.5",
		},
	}))

	services.SetSourceDataFrame("IND", "verblijfsvergunningen", dataframe.New([]map[string]any{
		{
			"bsn":          "999993653",
			"type":         "ONBEPAALDE_TIJD_REGULIER",
			"status":       "VERLEEND",
			"ingangsdatum": "2015-01-01",
			"einddatum":    "null",
		},
	}))

	services.SetSourceDataFrame("RvIG", "personen", dataframe.New([]map[string]any{
		{
			"bsn":            "999993653",
			"geboortedatum":  "1990-01-01",
			"verblijfsadres": "Amsterdam",
		},
	}))

	services.SetSourceDataFrame("RvIG", "relaties", dataframe.New([]map[string]any{
		{
			"bsn":               "999993653",
			"partnerschap_type": "GEEN",
			"partner_bsn":       "null",
		},
	}))

	services.SetSourceDataFrame("BELASTINGDIENST", "box1", dataframe.New([]map[string]any{
		{
			"bsn":                             "999993653",
			"loon_uit_dienstbetrekking":       0,
			"uitkeringen_en_pensioenen":       0,
			"winst_uit_onderneming":           0,
			"resultaat_overige_werkzaamheden": 0,
			"eigen_woning":                    0,
		},
	}))

	services.SetSourceDataFrame("BELASTINGDIENST", "box3", dataframe.New([]map[string]any{
		{
			"bsn":            "999993653",
			"spaargeld":      "5000",
			"beleggingen":    "0",
			"onroerend_goed": "0",
			"schulden":       "0",
		},
	}))

	services.SetSourceDataFrame("RvIG", "verblijfplaats", dataframe.New([]map[string]any{
		{
			"bsn":        "999993653",
			"straat":     "Kalverstraat",
			"huisnummer": "1",
			"postcode":   "1012NX",
			"woonplaats": "Amsterdam",
			"type":       "WOONADRES",
		},
	}))

	services.SetSourceDataFrame("GEMEENTE_AMSTERDAM", "werk_en_re_integratie", dataframe.New([]map[string]any{
		{
			"bsn":                   "999993653",
			"arbeidsvermogen":       "VOLLEDIG",
			"re_integratie_traject": "Werkstage",
		},
	}))

	evalResult, err := services.Evaluate(
		ctx,
		"GEMEENTE_AMSTERDAM",
		"participatiewet/bijstand",
		evalParams,
		"",
		nil,
		"",
		true,
	)

	if err != nil {
		logger.WithIndent().Errorf(ctx, "Error evaluating rules: %v", err)
	} else {
		resultJSON, _ := json.MarshalIndent(evalResult.Output, "", "  ")
		fmt.Printf("Direct Evaluation Result:\n%s\n", string(resultJSON))
	}

	// caseID, err := services.CaseManager.SubmitCase(
	// 	ctx,
	// 	"999993653",
	// 	"GEMEENTE_AMSTERDAM",
	// 	"participatiewet/bijstand",
	// 	nil,
	// 	nil,
	// 	true,
	// )

	// if err != nil {
	// 	fmt.Printf("err: %v\n", err)
	// }

	// services.CaseManager.Wait()

	// c, err := services.CaseManager.GetCaseByID(ctx, caseID)
	// if err != nil {
	// 	fmt.Printf("err: %v\n", err)
	// }

	// fmt.Printf("c: %v\n", c)

	fmt.Printf("time.Since(start): %v\n", time.Since(start))

	logger.Infof(ctx, "Successfully completed demo!")
}

func BenchmarkService(b *testing.B) {
	// SETUP

	// Initialize services with current date
	currentDate := time.Now()
	services, err := service.NewServices(currentDate)
	if err != nil {
		b.Errorf("new services: %v", err)
	}

	evalParams := map[string]any{
		"BSN": "999993653",
	}

	services.SetSourceDataFrame("CBS", "levensverwachting", dataframe.New([]map[string]any{
		{
			"jaar":           "2025",
			"verwachting_65": "20.5",
		},
	}))

	services.SetSourceDataFrame("IND", "verblijfsvergunningen", dataframe.New([]map[string]any{
		{
			"bsn":          "999993653",
			"type":         "ONBEPAALDE_TIJD_REGULIER",
			"status":       "VERLEEND",
			"ingangsdatum": "2015-01-01",
			"einddatum":    "null",
		},
	}))

	services.SetSourceDataFrame("RvIG", "personen", dataframe.New([]map[string]any{
		{
			"bsn":            "999993653",
			"geboortedatum":  "1990-01-01",
			"verblijfsadres": "Amsterdam",
		},
	}))

	services.SetSourceDataFrame("RvIG", "relaties", dataframe.New([]map[string]any{
		{
			"bsn":               "999993653",
			"partnerschap_type": "GEEN",
			"partner_bsn":       "null",
		},
	}))

	services.SetSourceDataFrame("BELASTINGDIENST", "box1", dataframe.New([]map[string]any{
		{
			"bsn":                             "999993653",
			"loon_uit_dienstbetrekking":       0,
			"uitkeringen_en_pensioenen":       0,
			"winst_uit_onderneming":           0,
			"resultaat_overige_werkzaamheden": 0,
			"eigen_woning":                    0,
		},
	}))

	services.SetSourceDataFrame("BELASTINGDIENST", "box3", dataframe.New([]map[string]any{
		{
			"bsn":            "999993653",
			"spaargeld":      "5000",
			"beleggingen":    "0",
			"onroerend_goed": "0",
			"schulden":       "0",
		},
	}))

	services.SetSourceDataFrame("RvIG", "verblijfplaats", dataframe.New([]map[string]any{
		{
			"bsn":        "999993653",
			"straat":     "Kalverstraat",
			"huisnummer": "1",
			"postcode":   "1012NX",
			"woonplaats": "Amsterdam",
			"type":       "WOONADRES",
		},
	}))

	services.SetSourceDataFrame("GEMEENTE_AMSTERDAM", "werk_en_re_integratie", dataframe.New([]map[string]any{
		{
			"bsn":                   "999993653",
			"arbeidsvermogen":       "VOLLEDIG",
			"re_integratie_traject": "Werkstage",
		},
	}))

	// Reset timer after setup

	for b.Loop() {
		evalResult, _ := services.Evaluate(
			b.Context(),
			"GEMEENTE_AMSTERDAM",
			"participatiewet/bijstand",
			evalParams,
			"",
			nil,
			"",
			true,
		)

		abc, _ := json.MarshalIndent(evalResult.Output, "", "  ")
		_ = abc
		// fmt.Printf("Direct Evaluation Result:\n%s\n", string(resultJSON))
	}
}
