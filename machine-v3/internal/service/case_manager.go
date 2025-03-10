package service

import (
	"encoding/json"
	"fmt"
	"math"
	"sync"
	"time"

	"context"
	"math/rand"

	"github.com/minbzk/poc-machine-law/machine-v3/internal/logging"
	"github.com/minbzk/poc-machine-law/machine-v3/internal/model"
)

// CaseManager manages service cases including submission, verification, decisions and objections
type CaseManager struct {
	Services   *Services
	caseIndex  map[string]string // (bsn:service:law) -> case_id
	cases      map[string]*model.Case
	events     []*model.Event
	SampleRate float64
	mu         sync.RWMutex
}

// NewCaseManager creates a new case manager
func NewCaseManager(services *Services) *CaseManager {
	return &CaseManager{
		Services:   services,
		caseIndex:  make(map[string]string),
		cases:      make(map[string]*model.Case),
		events:     make([]*model.Event, 0),
		SampleRate: 0.10, // 10% sample rate
	}
}

// indexKey generates a composite key for case indexing
func (cm *CaseManager) indexKey(bsn, service, law string) string {
	return fmt.Sprintf("%s:%s:%s", bsn, service, law)
}

// indexCase adds a case to the index
func (cm *CaseManager) indexCase(c *model.Case) {
	key := cm.indexKey(c.BSN, c.Service, c.Law)
	cm.caseIndex[key] = c.ID
}

// recordEvent records a new event
func (cm *CaseManager) recordEvent(caseID, eventType string, data map[string]interface{}) {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	event := &model.Event{
		CaseID:    caseID,
		Timestamp: time.Now(),
		EventType: eventType,
		Data:      data,
	}

	cm.events = append(cm.events, event)

	// Trigger rules in response to event
	go func() {
		if err := cm.Services.ApplyRules(event); err != nil {
			logging.GetLogger("case_manager").WithIndent().Errorf("Error applying rules: %v", err)
		}
	}()
}

// resultsMatch compares claimed and verified results to determine if they match
func (cm *CaseManager) resultsMatch(claimed, verified map[string]interface{}) bool {
	// First check that both maps have the same keys
	if len(claimed) != len(verified) {
		return false
	}

	for key, verifiedVal := range verified {
		claimedVal, exists := claimed[key]
		if !exists {
			return false
		}

		// For numeric values, compare with tolerance
		switch v := verifiedVal.(type) {
		case int, int32, int64, float32, float64:
			// Convert to float for comparison
			var vFloat, cFloat float64

			switch vt := v.(type) {
			case int:
				vFloat = float64(vt)
			case int32:
				vFloat = float64(vt)
			case int64:
				vFloat = float64(vt)
			case float32:
				vFloat = float64(vt)
			case float64:
				vFloat = vt
			}

			switch ct := claimedVal.(type) {
			case int:
				cFloat = float64(ct)
			case int32:
				cFloat = float64(ct)
			case int64:
				cFloat = float64(ct)
			case float32:
				cFloat = float64(ct)
			case float64:
				cFloat = ct
			default:
				return false // Type mismatch
			}

			// Handle zero values specially
			if vFloat == 0 {
				if cFloat != 0 {
					return false
				}
			} else {
				// Use relative difference for non-zero values
				if math.Abs((vFloat-cFloat)/vFloat) > 0.01 {
					return false
				}
			}
		default:
			// For other values, require exact match
			if !deepEqual(verifiedVal, claimedVal) {
				return false
			}
		}
	}

	return true
}

// todo: change Helper function for deep equality comparison
func deepEqual(a, b interface{}) bool {
	aJson, err := json.Marshal(a)
	if err != nil {
		return false
	}

	bJson, err := json.Marshal(b)
	if err != nil {
		return false
	}

	return string(aJson) == string(bJson)
}

// SubmitCase submits a new case and automatically processes it if possible
func (cm *CaseManager) SubmitCase(
	ctx context.Context,
	bsn string,
	serviceType string,
	law string,
	parameters map[string]interface{},
	claimedResult map[string]interface{},
	approvedClaimsOnly bool,
) (string, error) {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	// Verify using rules engine
	result, err := cm.Services.Evaluate(
		ctx,
		serviceType,
		law,
		parameters,
		"", // Use default reference date
		nil,
		"",
		true,
	)
	if err != nil {
		return "", err
	}

	verifiedResult := result.Output

	// Check if a case already exists
	existingCase := cm.GetCase(bsn, serviceType, law)

	var c *model.Case
	var eventType string
	var eventData map[string]interface{}

	if existingCase == nil {
		// Create new case
		c = model.NewCase(
			bsn,
			serviceType,
			law,
			parameters,
			claimedResult,
			verifiedResult,
			result.RulespecUUID,
			approvedClaimsOnly,
		)

		eventType = "Submitted"
		eventData = map[string]interface{}{
			"bsn":                  bsn,
			"service_type":         serviceType,
			"law":                  law,
			"parameters":           parameters,
			"claimed_result":       claimedResult,
			"verified_result":      verifiedResult,
			"rulespec_uuid":        result.RulespecUUID,
			"approved_claims_only": approvedClaimsOnly,
		}
	} else {
		// Reset existing case
		c = existingCase
		err := c.Reset(
			parameters,
			claimedResult,
			verifiedResult,
			approvedClaimsOnly,
		)
		if err != nil {
			return "", err
		}

		eventType = "Reset"
		eventData = map[string]interface{}{
			"parameters":           parameters,
			"claimed_result":       claimedResult,
			"verified_result":      verifiedResult,
			"approved_claims_only": approvedClaimsOnly,
		}
	}

	// Check if results match and if manual review is needed
	resultsMatch := cm.resultsMatch(claimedResult, verifiedResult)
	needsManualReview := rand.Float64() < cm.SampleRate

	if resultsMatch && !needsManualReview {
		// Automatic approval
		err := c.DecideAutomatically(
			verifiedResult,
			parameters,
			true,
		)
		if err != nil {
			return "", err
		}

		cm.recordEvent(c.ID, "AutomaticallyDecided", map[string]interface{}{
			"verified_result": verifiedResult,
			"parameters":      parameters,
			"approved":        true,
		})
	} else {
		// Route to manual review with reason
		reason := "Selected for manual review - "
		if !resultsMatch {
			reason += "results differ"
		} else {
			reason += "random sample check"
		}

		err := c.SelectForManualReview(
			"SYSTEM",
			reason,
			claimedResult,
			verifiedResult,
		)
		if err != nil {
			return "", err
		}

		cm.recordEvent(c.ID, "AddedToManualReview", map[string]interface{}{
			"verifier_id":     "SYSTEM",
			"reason":          reason,
			"claimed_result":  claimedResult,
			"verified_result": verifiedResult,
		})
	}

	// Save case and record initial event
	cm.cases[c.ID] = c
	cm.indexCase(c)

	// Record initial event if new case
	if eventType == "Submitted" {
		cm.recordEvent(c.ID, eventType, eventData)
	}

	return c.ID, nil
}

// CompleteManualReview completes manual review of a case
func (cm *CaseManager) CompleteManualReview(
	caseID string,
	verifierID string,
	approved bool,
	reason string,
	overrideResult map[string]interface{},
) (string, error) {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	case_, err := cm.GetCaseByID(caseID)
	if err != nil {
		return "", err
	}

	if case_.Status != model.CaseStatusInReview && case_.Status != model.CaseStatusObjected {
		return "", fmt.Errorf("can only complete review for cases in review or objections")
	}

	// Use current verified_result or override if provided
	verifiedResult := case_.VerifiedResult
	if overrideResult != nil {
		verifiedResult = overrideResult
	}

	err = case_.Decide(
		verifiedResult,
		reason,
		verifierID,
		approved,
	)
	if err != nil {
		return "", err
	}

	cm.recordEvent(caseID, "Decided", map[string]interface{}{
		"verified_result": verifiedResult,
		"reason":          reason,
		"verifier_id":     verifierID,
		"approved":        approved,
	})

	return caseID, nil
}

// ObjectCase submits an objection for a case
func (cm *CaseManager) ObjectCase(caseID string, reason string) (string, error) {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	case_, err := cm.GetCaseByID(caseID)
	if err != nil {
		return "", err
	}

	err = case_.Object(reason)
	if err != nil {
		return "", err
	}

	cm.recordEvent(caseID, "Objected", map[string]interface{}{
		"reason": reason,
	})

	return caseID, nil
}

// DetermineObjectionStatus determines objection status and periods
func (cm *CaseManager) DetermineObjectionStatus(
	caseID string,
	possible *bool,
	notPossibleReason string,
	objectionPeriod *int,
	decisionPeriod *int,
	extensionPeriod *int,
) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	case_, err := cm.GetCaseByID(caseID)
	if err != nil {
		return err
	}

	err = case_.DetermineObjectionStatus(
		possible,
		notPossibleReason,
		objectionPeriod,
		decisionPeriod,
		extensionPeriod,
	)
	if err != nil {
		return err
	}

	eventData := make(map[string]interface{})
	if possible != nil {
		eventData["possible"] = *possible
	}
	if notPossibleReason != "" {
		eventData["not_possible_reason"] = notPossibleReason
	}
	if objectionPeriod != nil {
		eventData["objection_period"] = *objectionPeriod
	}
	if decisionPeriod != nil {
		eventData["decision_period"] = *decisionPeriod
	}
	if extensionPeriod != nil {
		eventData["extension_period"] = *extensionPeriod
	}

	cm.recordEvent(caseID, "ObjectionStatusDetermined", eventData)

	return nil
}

// DetermineObjectionAdmissibility determines whether an objection is admissible
func (cm *CaseManager) DetermineObjectionAdmissibility(caseID string, admissible *bool) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	case_, err := cm.GetCaseByID(caseID)
	if err != nil {
		return err
	}

	err = case_.DetermineObjectionAdmissibility(admissible)
	if err != nil {
		return err
	}

	eventData := make(map[string]interface{})
	if admissible != nil {
		eventData["admissible"] = *admissible
	}

	cm.recordEvent(caseID, "ObjectionAdmissibilityDetermined", eventData)

	return nil
}

// DetermineAppealStatus determines appeal status and parameters
func (cm *CaseManager) DetermineAppealStatus(
	caseID string,
	possible *bool,
	notPossibleReason string,
	appealPeriod *int,
	directAppeal *bool,
	directAppealReason string,
	competentCourt string,
	courtType string,
) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	case_, err := cm.GetCaseByID(caseID)
	if err != nil {
		return err
	}

	err = case_.DetermineAppealStatus(
		possible,
		notPossibleReason,
		appealPeriod,
		directAppeal,
		directAppealReason,
		competentCourt,
		courtType,
	)
	if err != nil {
		return err
	}

	eventData := make(map[string]interface{})
	if possible != nil {
		eventData["possible"] = *possible
	}
	if notPossibleReason != "" {
		eventData["not_possible_reason"] = notPossibleReason
	}
	if appealPeriod != nil {
		eventData["appeal_period"] = *appealPeriod
	}
	if directAppeal != nil {
		eventData["direct_appeal"] = *directAppeal
	}
	if directAppealReason != "" {
		eventData["direct_appeal_reason"] = directAppealReason
	}
	if competentCourt != "" {
		eventData["competent_court"] = competentCourt
	}
	if courtType != "" {
		eventData["court_type"] = courtType
	}

	cm.recordEvent(caseID, "AppealStatusDetermined", eventData)

	return nil
}

// CanAppeal checks if appeal is possible for a case
func (cm *CaseManager) CanAppeal(caseID string) (bool, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	case_, err := cm.GetCaseByID(caseID)
	if err != nil {
		return false, err
	}

	return case_.CanAppeal(), nil
}

// CanObject checks if objection is possible for a case
func (cm *CaseManager) CanObject(caseID string) (bool, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	case_, err := cm.GetCaseByID(caseID)
	if err != nil {
		return false, err
	}

	return case_.CanObject(), nil
}

// GetCase gets a case for a specific bsn, service and law combination
func (cm *CaseManager) GetCase(bsn, serviceType, law string) *model.Case {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	key := cm.indexKey(bsn, serviceType, law)
	caseID, exists := cm.caseIndex[key]
	if !exists {
		return nil
	}

	return cm.cases[caseID]
}

// GetCaseByID gets a case by ID
func (cm *CaseManager) GetCaseByID(caseID string) (*model.Case, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if caseID == "" {
		return nil, fmt.Errorf("case ID cannot be empty")
	}

	case_, exists := cm.cases[caseID]
	if !exists {
		return nil, fmt.Errorf("case not found: %s", caseID)
	}

	return case_, nil
}

// GetCasesByStatus gets all cases for a service in a particular status
func (cm *CaseManager) GetCasesByStatus(serviceType string, status model.CaseStatus) []*model.Case {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	var result []*model.Case

	for _, case_ := range cm.cases {
		if case_.Service == serviceType && case_.Status == status {
			result = append(result, case_)
		}
	}

	return result
}

// GetCasesByLaw gets all cases for a specific law and service combination
func (cm *CaseManager) GetCasesByLaw(law, serviceType string) []*model.Case {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	var result []*model.Case

	for _, case_ := range cm.cases {
		if case_.Law == law && case_.Service == serviceType {
			result = append(result, case_)
		}
	}

	return result
}

// GetEvents gets events, optionally filtered by case ID
func (cm *CaseManager) GetEvents(caseID string) []*model.Event {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if caseID == "" {
		// Return all events
		return cm.events
	}

	// Filter events by case ID
	var filteredEvents []*model.Event

	for _, event := range cm.events {
		if event.CaseID == caseID {
			filteredEvents = append(filteredEvents, event)
		}
	}

	return filteredEvents
}
