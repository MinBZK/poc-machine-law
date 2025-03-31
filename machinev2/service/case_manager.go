package service

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"math"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/minbzk/poc-machine-law/machinev2/casemanager"
	"github.com/minbzk/poc-machine-law/machinev2/logging"
	"github.com/minbzk/poc-machine-law/machinev2/model"

	"maps"

	eh "github.com/looplab/eventhorizon"
	"github.com/looplab/eventhorizon/commandhandler/bus"
	localEventBus "github.com/looplab/eventhorizon/eventbus/local"
	memoryEventStore "github.com/looplab/eventhorizon/eventstore/memory"
	"github.com/looplab/eventhorizon/repo/memory"
)

// CaseManager manages service cases using the EventHorizon-based casemanager.
type CaseManager struct {
	logger      logging.Logger
	Services    *Services
	caseIndex   map[string]uuid.UUID // Maps (bsn:service:law) -> case_id
	events      []*model.Event
	SampleRate  float64
	mu          sync.RWMutex
	commandBus  eh.CommandHandler
	caseRepo    eh.ReadWriteRepo
	eventBus    eh.EventBus
	observerBus eh.EventBus
	wg          *sync.WaitGroup
}

// NewCaseManager creates a new case manager with EventHorizon components.
func NewCaseManager(logger logging.Logger, services *Services) *CaseManager {
	// Create the event buses
	eventBus := localEventBus.NewEventBus()
	observerBus := localEventBus.NewEventBus()

	// Handle errors from the event buses
	go func() {
		for e := range eventBus.Errors() {
			log.Printf("eventbus: %s", e.Error())
		}
	}()
	go func() {
		for e := range observerBus.Errors() {
			log.Printf("observerbus: %s", e.Error())
		}
	}()

	// Create the event store with the event bus as a handler
	eventStore, err := memoryEventStore.NewEventStore(
		memoryEventStore.WithEventHandler(eventBus),
	)
	if err != nil {
		log.Fatalf("could not create event store: %s", err)
	}

	// Create the command bus
	commandBus := bus.NewCommandHandler()

	// Create the read repository for cases
	caseRepo := memory.NewRepo()
	caseRepo.SetEntityFactory(func() eh.Entity { return &casemanager.Case{} })

	// Set up the case manager
	ctx := context.Background()
	if err := casemanager.Setup(ctx, eventStore, eventBus, eventBus, commandBus, caseRepo); err != nil {
		log.Fatalf("could not set up case manager: %s", err)
	}

	return &CaseManager{
		logger:      logger.WithName("case_manager"),
		Services:    services,
		caseIndex:   make(map[string]uuid.UUID),
		events:      make([]*model.Event, 0),
		SampleRate:  0.10, // 10% sample rate
		commandBus:  commandBus,
		caseRepo:    caseRepo,
		eventBus:    eventBus,
		observerBus: observerBus,
		wg:          &sync.WaitGroup{},
	}
}

// indexKey generates a composite key for case indexing
func (cm *CaseManager) indexKey(bsn, service, law string) string {
	return fmt.Sprintf("%s:%s:%s", bsn, service, law)
}

// indexCase adds a case to the index
func (cm *CaseManager) indexCase(caseID uuid.UUID, bsn, service, law string) {
	key := cm.indexKey(bsn, service, law)
	cm.SetCase(caseID, key)
}

// recordEvent records a new event
func (cm *CaseManager) recordEvent(caseID uuid.UUID, eventType string, data map[string]any) {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	event := &model.Event{
		CaseID:    caseID,
		Timestamp: time.Now(),
		EventType: eventType,
		Data:      data,
	}

	cm.events = append(cm.events, event)

	cm.wg.Add(1)
	// Trigger rules in response to event
	go func() {
		ctx := context.Background()
		if err := cm.Services.ApplyRules(ctx, event); err != nil {
			cm.logger.WithIndent().Errorf(ctx, "Error applying rules: %v", err)
		}

		cm.wg.Done()
	}()
}

// resultsMatch compares claimed and verified results to determine if they match
func (cm *CaseManager) resultsMatch(claimed, verified map[string]any) bool {
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

// Helper function for deep equality comparison
func deepEqual(a, b any) bool {
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

func (cm *CaseManager) SetCase(caseID uuid.UUID, key string) {
	cm.mu.Lock()

	cm.caseIndex[key] = caseID

	cm.mu.Unlock()

}

func (cm *CaseManager) GetCaseByKey(key string) (uuid.UUID, bool) {
	cm.mu.RLock()

	caseID, exists := cm.caseIndex[key]

	cm.mu.RUnlock()

	return caseID, exists
}

// SubmitCase submits a new case and automatically processes it
func (cm *CaseManager) SubmitCase(
	ctx context.Context,
	bsn string,
	serviceType string,
	law string,
	parameters map[string]any,
	claimedResult map[string]any,
	approvedClaimsOnly bool,
) (uuid.UUID, error) {

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
		return uuid.Nil, err
	}

	verifiedResult := result.Output
	rulespecUUID, err := uuid.Parse(result.RulespecUUID)
	if err != nil {
		return uuid.Nil, fmt.Errorf("invalid rulespec UUID: %w", err)
	}

	// Check if a case already exists
	key := cm.indexKey(bsn, serviceType, law)
	existingCaseID, exists := cm.GetCaseByKey(key)

	var caseID uuid.UUID
	var eventType string
	var eventData map[string]any

	if !exists {
		// Submit a new case
		caseID, err = casemanager.SubmitCase(
			ctx,
			cm.commandBus,
			bsn,
			serviceType,
			law,
			parameters,
			claimedResult,
			verifiedResult,
			rulespecUUID,
			approvedClaimsOnly,
		)
		if err != nil {
			return uuid.Nil, fmt.Errorf("failed to submit case: %w", err)
		}

		// Add to index
		cm.indexCase(caseID, bsn, serviceType, law)

		eventType = "Submitted"
		eventData = map[string]any{
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
		caseID = existingCaseID
		cmd := casemanager.ResetCaseCommand{
			ID:                 caseID,
			Parameters:         parameters,
			ClaimedResult:      claimedResult,
			VerifiedResult:     verifiedResult,
			ApprovedClaimsOnly: approvedClaimsOnly,
		}

		if err := cm.commandBus.HandleCommand(ctx, cmd); err != nil {
			return uuid.Nil, fmt.Errorf("failed to reset case: %w", err)
		}

		eventType = "Reset"
		eventData = map[string]any{
			"parameters":           parameters,
			"claimed_result":       claimedResult,
			"verified_result":      verifiedResult,
			"approved_claims_only": approvedClaimsOnly,
		}
	}

	// Check if results match
	resultsMatch := cm.resultsMatch(claimedResult, verifiedResult)

	// Process the case automatically
	err = casemanager.ProcessCase(
		ctx,
		cm.commandBus,
		caseID,
		verifiedResult,
		parameters,
		resultsMatch,
		cm.SampleRate,
	)
	if err != nil {
		return uuid.Nil, fmt.Errorf("failed to process case: %w", err)
	}

	// Record the initial event
	if eventType == "Submitted" {
		cm.recordEvent(caseID, eventType, eventData)
	}

	return caseID, nil
}

// CompleteManualReview completes manual review of a case
func (cm *CaseManager) CompleteManualReview(
	ctx context.Context,
	caseID uuid.UUID,
	verifierID string,
	approved bool,
	reason string,
	overrideResult map[string]any,
) error {
	// Get the case from the repository
	c, err := casemanager.FindCase(ctx, cm.caseRepo, caseID)
	if err != nil {
		return fmt.Errorf("failed to find case: %w", err)
	}

	// Use current verified_result or override if provided
	verifiedResult := c.VerifiedResult
	if overrideResult != nil {
		verifiedResult = overrideResult
	}

	// Complete the manual review
	if err := casemanager.CompleteManualReview(
		ctx,
		cm.commandBus,
		caseID,
		verifierID,
		approved,
		reason,
		verifiedResult,
	); err != nil {
		return fmt.Errorf("failed to complete manual review: %w", err)
	}

	// Record the event
	cm.recordEvent(caseID, "Decided", map[string]any{
		"verified_result": verifiedResult,
		"reason":          reason,
		"verifier_id":     verifierID,
		"approved":        approved,
	})

	return nil
}

// ObjectCase submits an objection for a case
func (cm *CaseManager) ObjectCase(ctx context.Context, caseID uuid.UUID, reason string) error {
	// Object to the case
	err := casemanager.ObjectToCase(ctx, cm.commandBus, caseID, reason)
	if err != nil {
		return fmt.Errorf("failed to object to case: %w", err)
	}

	// Record the event
	cm.recordEvent(caseID, "Objected", map[string]any{
		"reason": reason,
	})

	return nil
}

// DetermineObjectionStatus determines objection status and periods
func (cm *CaseManager) DetermineObjectionStatus(
	caseID uuid.UUID,
	possible *bool,
	notPossibleReason string,
	objectionPeriod *int,
	decisionPeriod *int,
	extensionPeriod *int,
) error {
	ctx := context.Background()

	// Convert string to pointer if not empty
	var notPossibleReasonPtr *string
	if notPossibleReason != "" {
		notPossibleReasonPtr = &notPossibleReason
	}

	// Determine objection status
	if err := casemanager.DetermineObjectionStatus(
		ctx,
		cm.commandBus,
		caseID,
		possible,
		notPossibleReasonPtr,
		objectionPeriod,
		decisionPeriod,
		extensionPeriod,
	); err != nil {
		return fmt.Errorf("failed to determine objection status: %w", err)
	}

	// Record the event
	eventData := make(map[string]any)
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
func (cm *CaseManager) DetermineObjectionAdmissibility(caseID uuid.UUID, admissible *bool) error {
	ctx := context.Background()

	// Determine objection admissibility
	if err := casemanager.DetermineObjectionAdmissibility(ctx, cm.commandBus, caseID, admissible); err != nil {
		return fmt.Errorf("failed to determine objection admissibility: %w", err)
	}

	// Record the event
	eventData := make(map[string]any)
	if admissible != nil {
		eventData["admissible"] = *admissible
	}

	cm.recordEvent(caseID, "ObjectionAdmissibilityDetermined", eventData)

	return nil
}

// DetermineAppealStatus determines appeal status and parameters
func (cm *CaseManager) DetermineAppealStatus(
	caseID uuid.UUID,
	possible *bool,
	notPossibleReason string,
	appealPeriod *int,
	directAppeal *bool,
	directAppealReason string,
	competentCourt string,
	courtType string,
) error {
	ctx := context.Background()

	// Convert strings to pointers if not empty
	var notPossibleReasonPtr, directAppealReasonPtr, competentCourtPtr, courtTypePtr *string

	if notPossibleReason != "" {
		notPossibleReasonPtr = &notPossibleReason
	}

	if directAppealReason != "" {
		directAppealReasonPtr = &directAppealReason
	}

	if competentCourt != "" {
		competentCourtPtr = &competentCourt
	}

	if courtType != "" {
		courtTypePtr = &courtType
	}

	// Determine appeal status
	if err := casemanager.DetermineAppealStatus(
		ctx,
		cm.commandBus,
		caseID,
		possible,
		notPossibleReasonPtr,
		appealPeriod,
		directAppeal,
		directAppealReasonPtr,
		competentCourtPtr,
		courtTypePtr,
	); err != nil {
		return fmt.Errorf("failed to determine appeal status: %w", err)
	}

	// Record the event
	eventData := make(map[string]any)
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
func (cm *CaseManager) CanAppeal(caseID uuid.UUID) (bool, error) {
	ctx := context.Background()

	// Find the case
	c, err := casemanager.FindCase(ctx, cm.caseRepo, caseID)
	if err != nil {
		return false, fmt.Errorf("failed to find case: %w", err)
	}

	return c.CanAppeal(), nil
}

// CanObject checks if objection is possible for a case
func (cm *CaseManager) CanObject(caseID uuid.UUID) (bool, error) {
	ctx := context.Background()

	// Find the case
	c, err := casemanager.FindCase(ctx, cm.caseRepo, caseID)
	if err != nil {
		return false, fmt.Errorf("failed to find case: %w", err)
	}

	return c.CanObject(), nil
}

// GetCase gets a case for a specific bsn, service and law combination
func (cm *CaseManager) GetCase(bsn, serviceType, law string) *casemanager.Case {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	key := cm.indexKey(bsn, serviceType, law)

	caseID, exists := cm.GetCaseByKey(key)
	if !exists {
		return nil
	}

	// Find the case in the repository
	ctx := context.Background()
	c, err := casemanager.FindCase(ctx, cm.caseRepo, caseID)
	if err != nil {
		return nil
	}

	// Convert from casemanager.Case to model.Case
	return c
}

// GetCaseByID gets a case by ID
func (cm *CaseManager) GetCaseByID(ctx context.Context, id uuid.UUID) (*casemanager.Case, error) {
	if id == uuid.Nil {
		return nil, fmt.Errorf("case ID cannot be empty")
	}

	// Find the case in the repository
	c, err := casemanager.FindCase(ctx, cm.caseRepo, id)
	if err != nil {
		return nil, fmt.Errorf("case not found: %s", id)
	}

	return c, nil
}

// GetCasesByStatus gets all cases for a service in a particular status
func (cm *CaseManager) GetCasesByStatus(serviceType string, status casemanager.CaseStatus) []*casemanager.Case {
	// This would normally involve a more efficient query to the repository
	// For now, we'll scan through all cases in the index
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	var result []*casemanager.Case
	ctx := context.Background()

	for _, caseID := range cm.caseIndex {
		c, err := casemanager.FindCase(ctx, cm.caseRepo, caseID)
		if err != nil {
			continue
		}

		if c.Service == serviceType && c.Status == status {
			result = append(result, c)
		}
	}

	return result
}

// GetCasesByLaw gets all cases for a specific law and service combination
func (cm *CaseManager) GetCasesByLaw(law, serviceType string) []*casemanager.Case {
	// This would normally involve a more efficient query to the repository
	// For now, we'll scan through all cases in the index
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	var result []*casemanager.Case
	ctx := context.Background()

	for _, caseID := range cm.caseIndex {
		c, err := casemanager.FindCase(ctx, cm.caseRepo, caseID)
		if err != nil {
			continue
		}

		if c.Law == law && c.Service == serviceType {
			result = append(result, c)
		}
	}

	return result
}

// GetEventsByUUID gets events, optionally filtered by case ID
func (cm *CaseManager) GetEventsByUUID(caseID uuid.UUID) []*model.Event {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if caseID == uuid.Nil {
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

// GetEvents implements the CaseManagerAccessor interface
// Converts internal event model to map format for use by dataframe
func (cm *CaseManager) GetEvents(caseID any) []map[string]any {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	var events []*model.Event

	// Convert any case ID to UUID if provided
	if caseID != nil {
		var id uuid.UUID
		switch v := caseID.(type) {
		case uuid.UUID:
			id = v
		case string:
			parsed, err := uuid.Parse(v)
			if err == nil {
				id = parsed
			}
		}

		// Filter events by case ID
		if id != uuid.Nil {
			for _, event := range cm.events {
				if event.CaseID == id {
					events = append(events, event)
				}
			}
		}
	} else {
		// Return all events
		events = cm.events
	}

	// Convert to map format
	result := make([]map[string]any, len(events))
	for i, event := range events {
		eventMap := map[string]any{
			"case_id":    event.CaseID.String(),
			"event_type": event.EventType,
			"timestamp":  event.Timestamp.Format(time.RFC3339),
		}

		// Add data fields
		maps.Copy(eventMap, event.Data)

		result[i] = eventMap
	}

	return result
}

func (cm *CaseManager) Save(ctx context.Context, c *casemanager.Case) error {
	return nil
}

func (cm *CaseManager) Wait() {
	cm.wg.Wait()
}

func (cm *CaseManager) Close() {
	cm.wg.Wait()
	cm.eventBus.Close()
	cm.observerBus.Close()
}
