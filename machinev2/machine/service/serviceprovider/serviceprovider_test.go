package serviceprovider_test

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"testing"
	"time"

	"github.com/minbzk/poc-machine-law/machinev2/machine/casemanager/manager"
	"github.com/minbzk/poc-machine-law/machinev2/machine/claimmanager/inmemory"
	"github.com/minbzk/poc-machine-law/machinev2/machine/dataframe"
	"github.com/minbzk/poc-machine-law/machinev2/machine/logger"
	"github.com/minbzk/poc-machine-law/machinev2/machine/service/serviceprovider"
	"github.com/sirupsen/logrus"
	"github.com/stretchr/testify/require"
)

func TestService(t *testing.T) {

	start := time.Now()

	logger := logger.New("main", os.Stdout, logrus.DebugLevel)

	// Set up context
	ctx := context.Background()

	caseManager := manager.New(logger)
	claimManager := inmemory.New(logger, caseManager)

	// Initialize services with current date
	services, err := serviceprovider.New(logger, time.Now(), caseManager, claimManager, serviceprovider.WithRuleServiceInMemory())
	require.NoError(t, err)

	caseManager.SetService(services)

	logger.Infof("Direct rules engine evaluation example:")

	evalParams := map[string]any{
		"BSN": "999993653",
	}

	services.SetSourceDataFrame(ctx, "CBS", "levensverwachting", dataframe.New([]map[string]any{
		{
			"jaar":           "2025",
			"verwachting_65": "20.5",
		},
	}))

	services.SetSourceDataFrame(ctx, "IND", "verblijfsvergunningen", dataframe.New([]map[string]any{
		{
			"bsn":          "999993653",
			"type":         "ONBEPAALDE_TIJD_REGULIER",
			"status":       "VERLEEND",
			"ingangsdatum": "2015-01-01",
			"einddatum":    "null",
		},
	}))

	services.SetSourceDataFrame(ctx, "RvIG", "personen", dataframe.New([]map[string]any{
		{
			"bsn":            "999993653",
			"geboortedatum":  "1990-01-01",
			"verblijfsadres": "Amsterdam",
		},
	}))

	services.SetSourceDataFrame(ctx, "RvIG", "relaties", dataframe.New([]map[string]any{
		{
			"bsn":               "999993653",
			"partnerschap_type": "GEEN",
			"partner_bsn":       "null",
		},
	}))

	services.SetSourceDataFrame(ctx, "BELASTINGDIENST", "box1", dataframe.New([]map[string]any{
		{
			"bsn":                             "999993653",
			"loon_uit_dienstbetrekking":       0,
			"uitkeringen_en_pensioenen":       0,
			"winst_uit_onderneming":           0,
			"resultaat_overige_werkzaamheden": 0,
			"eigen_woning":                    0,
		},
	}))

	services.SetSourceDataFrame(ctx, "BELASTINGDIENST", "box3", dataframe.New([]map[string]any{
		{
			"bsn":            "999993653",
			"spaargeld":      "5000",
			"beleggingen":    "0",
			"onroerend_goed": "0",
			"schulden":       "0",
		},
	}))

	services.SetSourceDataFrame(ctx, "RvIG", "verblijfplaats", dataframe.New([]map[string]any{
		{
			"bsn":        "999993653",
			"straat":     "Kalverstraat",
			"huisnummer": "1",
			"postcode":   "1012NX",
			"woonplaats": "Amsterdam",
			"type":       "WOONADRES",
		},
	}))

	services.SetSourceDataFrame(ctx, "GEMEENTE_AMSTERDAM", "werk_en_re_integratie", dataframe.New([]map[string]any{
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
		logger.WithIndent().Errorf("Error evaluating rules: %v", err)
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

	logger.Infof("Successfully completed demo!")
}

func BenchmarkService(b *testing.B) {
	// SETUP
	logger := logger.New("main", os.Stdout, logrus.DebugLevel)

	caseManager := manager.New(logger)
	claimManager := inmemory.New(logger, caseManager)

	// Initialize services with current date
	services, err := serviceprovider.New(logger, time.Now(), caseManager, claimManager, serviceprovider.WithRuleServiceInMemory())
	if err != nil {
		b.Errorf("new services: %v", err)
	}

	caseManager.SetService(services)

	evalParams := map[string]any{
		"BSN": "999993653",
	}

	ctx := b.Context()

	services.SetSourceDataFrame(ctx, "CBS", "levensverwachting", dataframe.New([]map[string]any{
		{
			"jaar":           "2025",
			"verwachting_65": "20.5",
		},
	}))

	services.SetSourceDataFrame(ctx, "IND", "verblijfsvergunningen", dataframe.New([]map[string]any{
		{
			"bsn":          "999993653",
			"type":         "ONBEPAALDE_TIJD_REGULIER",
			"status":       "VERLEEND",
			"ingangsdatum": "2015-01-01",
			"einddatum":    "null",
		},
	}))

	services.SetSourceDataFrame(ctx, "RvIG", "personen", dataframe.New([]map[string]any{
		{
			"bsn":            "999993653",
			"geboortedatum":  "1990-01-01",
			"verblijfsadres": "Amsterdam",
		},
	}))

	services.SetSourceDataFrame(ctx, "RvIG", "relaties", dataframe.New([]map[string]any{
		{
			"bsn":               "999993653",
			"partnerschap_type": "GEEN",
			"partner_bsn":       "null",
		},
	}))

	services.SetSourceDataFrame(ctx, "BELASTINGDIENST", "box1", dataframe.New([]map[string]any{
		{
			"bsn":                             "999993653",
			"loon_uit_dienstbetrekking":       0,
			"uitkeringen_en_pensioenen":       0,
			"winst_uit_onderneming":           0,
			"resultaat_overige_werkzaamheden": 0,
			"eigen_woning":                    0,
		},
	}))

	services.SetSourceDataFrame(ctx, "BELASTINGDIENST", "box3", dataframe.New([]map[string]any{
		{
			"bsn":            "999993653",
			"spaargeld":      "5000",
			"beleggingen":    "0",
			"onroerend_goed": "0",
			"schulden":       "0",
		},
	}))

	services.SetSourceDataFrame(ctx, "RvIG", "verblijfplaats", dataframe.New([]map[string]any{
		{
			"bsn":        "999993653",
			"straat":     "Kalverstraat",
			"huisnummer": "1",
			"postcode":   "1012NX",
			"woonplaats": "Amsterdam",
			"type":       "WOONADRES",
		},
	}))

	services.SetSourceDataFrame(ctx, "GEMEENTE_AMSTERDAM", "werk_en_re_integratie", dataframe.New([]map[string]any{
		{
			"bsn":                   "999993653",
			"arbeidsvermogen":       "VOLLEDIG",
			"re_integratie_traject": "Werkstage",
		},
	}))

	// Reset timer after setup

	for b.Loop() {
		evalResult, _ := services.Evaluate(
			ctx,
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
