package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"time"

	"github.com/minbzk/poc-machine-law/machine-v3/internal/logging"
	models "github.com/minbzk/poc-machine-law/machine-v3/internal/model"
	"github.com/minbzk/poc-machine-law/machine-v3/internal/service"
)

// SimpleDataFrame is a basic implementation of the DataFrame interface
type SimpleDataFrame struct {
	data    []map[string]interface{}
	columns map[string][]interface{}
}

// NewSimpleDataFrame creates a new simple dataframe from records
func NewSimpleDataFrame(records []map[string]interface{}) *SimpleDataFrame {
	df := &SimpleDataFrame{
		data:    records,
		columns: make(map[string][]interface{}),
	}

	// Extract columns
	if len(records) > 0 {
		for col := range records[0] {
			values := make([]interface{}, len(records))
			for i, record := range records {
				values[i] = record[col]
			}
			df.columns[col] = values
		}
	}

	return df
}

// Filter filters the DataFrame based on column, operator, and value
func (df *SimpleDataFrame) Filter(column, operator string, value interface{}) (models.DataFrame, error) {
	var filtered []map[string]interface{}

	for _, row := range df.data {
		colValue, exists := row[column]
		if !exists {
			continue
		}

		var match bool
		switch operator {
		case "=":
			match = colValue == value
		case "!=":
			match = colValue != value
		case ">":
			// For simplicity, handle only numeric comparisons
			fv1, ok1 := toFloat(colValue)
			fv2, ok2 := toFloat(value)
			match = ok1 && ok2 && fv1 > fv2
		case "<":
			fv1, ok1 := toFloat(colValue)
			fv2, ok2 := toFloat(value)
			match = ok1 && ok2 && fv1 < fv2
		case ">=":
			fv1, ok1 := toFloat(colValue)
			fv2, ok2 := toFloat(value)
			match = ok1 && ok2 && fv1 >= fv2
		case "<=":
			fv1, ok1 := toFloat(colValue)
			fv2, ok2 := toFloat(value)
			match = ok1 && ok2 && fv1 <= fv2
		case "in":
			// Check if value is in array
			if arr, ok := value.([]interface{}); ok {
				for _, v := range arr {
					if v == colValue {
						match = true
						break
					}
				}
			}
		default:
			return nil, fmt.Errorf("unsupported operator: %s", operator)
		}

		if match {
			filtered = append(filtered, row)
		}
	}

	return NewSimpleDataFrame(filtered), nil
}

// Helper to convert values to float
func toFloat(v interface{}) (float64, bool) {
	switch val := v.(type) {
	case int:
		return float64(val), true
	case int32:
		return float64(val), true
	case int64:
		return float64(val), true
	case float32:
		return float64(val), true
	case float64:
		return val, true
	default:
		return 0, false
	}
}

// Select returns a new DataFrame with only the specified columns
func (df *SimpleDataFrame) Select(columns []string) models.DataFrame {
	var filtered []map[string]interface{}

	for _, row := range df.data {
		newRow := make(map[string]interface{})
		for _, col := range columns {
			if val, exists := row[col]; exists {
				newRow[col] = val
			}
		}
		filtered = append(filtered, newRow)
	}

	return NewSimpleDataFrame(filtered)
}

// ToRecords converts the DataFrame to a slice of maps
func (df *SimpleDataFrame) ToRecords() []map[string]interface{} {
	return df.data
}

// HasColumn checks if the DataFrame has a column
func (df *SimpleDataFrame) HasColumn(column string) bool {
	_, exists := df.columns[column]
	return exists
}

// GetColumnValues returns all values from a column
func (df *SimpleDataFrame) GetColumnValues(column string) []interface{} {
	if values, exists := df.columns[column]; exists {
		return values
	}
	return nil
}

func main() {
	// Configure logging
	logging.ConfigureLogging("debug")
	logger := logging.GetLogger("main")

	// Set up context
	ctx := context.Background()

	// Initialize services with current date
	currentDate := time.Now().Format("2006-01-02")
	services := service.NewServices(currentDate)

	// Load sample data
	sampleRules := []map[string]interface{}{
		{
			"path":            "law/toeslagen/zorgtoeslagwet.yaml",
			"decision_type":   "automatisch",
			"law_type":        "wet",
			"legal_character": "publiek",
			"uuid":            "4d8c7237-b930-4f0f-aaa3-624ba035e449",
			"name":            "Zorgtoeslag",
			"law":             "zorgtoeslagwet",
			"valid_from":      "2023-01-01",
			"service":         "TOESLAGEN",
			"discoverable":    "CITIZEN",

			"bsn":           "123456789",
			"polis_status":  "ACTIEF",
			"start_date":    "2023-01-01",
			"end_date":      "2025-01-01",
			"registratie":   "INACTIEF",
			"geboortedatum": "2007-01-01",
		},
		{
			"path":            "law/toeslagen/huurtoeslag.yaml",
			"decision_type":   "automatisch",
			"law_type":        "wet",
			"legal_character": "publiek",
			"uuid":            "5e9d8346-c041-5a10-bbb4-735046dbb559",
			"name":            "Huurtoeslag",
			"law":             "huurtoeslag",
			"valid_from":      "2023-01-01",
			"service":         "TOESLAGEN",
			"discoverable":    "CITIZEN",

			"bsn":           "123456789",
			"polis_status":  "ACTIEF",
			"start_date":    "2023-01-01",
			"end_date":      "2025-01-01",
			"registratie":   "INACTIEF",
			"geboortedatum": "2007-01-01",
		},
	}

	rulesDF := NewSimpleDataFrame(sampleRules)
	services.SetSourceDataFrame("TOESLAGEN", "laws", rulesDF)
	services.SetSourceDataFrame("RVZ", "verzekeringen", rulesDF)
	services.SetSourceDataFrame("RVZ", "verdragsverzekeringen", rulesDF)
	services.SetSourceDataFrame("RVIG", "personen ", rulesDF)

	// Sample use case: Submit and process a case
	logger.WithIndent().Infof("Submitting sample case...")

	parameters := map[string]interface{}{
		"BSN":           "123456789",
		"income":        35000,
		"partner":       false,
		"housemates":    0,
		"health_issues": true,
	}

	claimedResult := map[string]interface{}{
		"eligible":     true,
		"amount":       1200,
		"start_date":   "2023-01-01",
		"payment_type": "monthly",
	}

	caseID, err := services.CaseManager.SubmitCase(
		ctx,
		"123456789",
		"TOESLAGEN",
		"zorgtoeslagwet",
		parameters,
		claimedResult,
		false,
	)
	if err != nil {
		logger.WithIndent().Errorf("Error submitting case: %v", err)
		os.Exit(1)
	}

	logger.WithIndent().Infof("Case submitted with ID: %s", caseID)

	// Get the case
	case_, err := services.CaseManager.GetCaseByID(caseID)
	if err != nil {
		logger.WithIndent().Errorf("Error getting case: %v", err)
		os.Exit(1)
	}

	// Display case details
	caseJSON, _ := json.MarshalIndent(case_, "", "  ")
	fmt.Printf("\nCase Details:\n%s\n", string(caseJSON))

	// Submit a claim
	claimID, err := services.ClaimManager.SubmitClaim(
		"TOESLAGEN",
		"health_issues",
		true,
		"I have documented medical condition",
		"123456789",
		"zorgtoeslagwet",
		"123456789",
		caseID,
		nil,
		"/path/to/evidence.pdf",
		true, // Auto-approve
	)
	if err != nil {
		logger.WithIndent().Errorf("Error submitting claim: %v", err)
		os.Exit(1)
	}

	logger.WithIndent().Infof("Claim submitted with ID: %s", claimID)

	// Get the claim
	claim, err := services.ClaimManager.GetClaim(claimID)
	if err != nil {
		logger.WithIndent().Errorf("Error getting claim: %v", err)
		os.Exit(1)
	}

	// Display claim details
	claimJSON, _ := json.MarshalIndent(claim, "", "  ")
	fmt.Printf("\nClaim Details:\n%s\n", string(claimJSON))

	// Complete manual review (if in review)
	if case_.Status == models.CaseStatusInReview {
		caseID, err = services.CaseManager.CompleteManualReview(
			caseID,
			"OFFICER123",
			true,
			"All documentation is correct and verified",
			nil,
		)
		if err != nil {
			logger.WithIndent().Errorf("Error completing review: %v", err)
			os.Exit(1)
		}

		logger.WithIndent().Infof("Manual review completed for case: %s", caseID)

		// Display updated case
		case_, _ = services.CaseManager.GetCaseByID(caseID)
		caseJSON, _ = json.MarshalIndent(case_, "", "  ")
		fmt.Printf("\nUpdated Case Details (after review):\n%s\n", string(caseJSON))
	}

	// List events for the case
	events := services.CaseManager.GetEvents(caseID)
	eventsJSON, _ := json.MarshalIndent(events, "", "  ")
	fmt.Printf("\nCase Events:\n%s\n", string(eventsJSON))

	// Example of using the rules engine directly
	logger.WithIndent().Infof("\nDirect rules engine evaluation example:")

	evalParams := map[string]interface{}{
		"BSN":            "987654321",
		"income":         42000,
		"partner":        true,
		"partner_income": 38000,
		"health_issues":  false,
	}

	evalResult, err := services.Evaluate(
		ctx,
		"TOESLAGEN",
		"zorgtoeslagwet",
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
		fmt.Printf("\nDirect Evaluation Result:\n%s\n", string(resultJSON))
	}

	logger.WithIndent().Infof("\nSuccessfully completed demo!")
}
