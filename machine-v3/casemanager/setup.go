package casemanager

import (
	"context"
	"fmt"
	"log"
	"math/rand"
	"sync"

	"github.com/google/uuid"
	eh "github.com/looplab/eventhorizon"
	"github.com/looplab/eventhorizon/aggregatestore/events"
	"github.com/looplab/eventhorizon/commandhandler/aggregate"
	"github.com/looplab/eventhorizon/commandhandler/bus"
	"github.com/looplab/eventhorizon/eventhandler/projector"
	"github.com/looplab/eventhorizon/middleware/eventhandler/observer"
)

var registerSync sync.Once

// HandlerAdder interface for handlers that can add event handlers.
type HandlerAdder interface {
	AddHandler(context.Context, eh.EventMatcher, eh.EventHandler) error
}

// Setup sets up the case manager with all required components.
func Setup(
	ctx context.Context,
	eventStore eh.EventStore,
	local, global HandlerAdder,
	commandBus *bus.CommandHandler,
	caseRepo eh.ReadWriteRepo,
) error {

	registerSync.Do(func() {
		// Register event types and data
		RegisterEvents()

		RegisterCommands()

		RegisterAggregate()
	})

	// Create the aggregate repository
	aggregateStore, err := events.NewAggregateStore(eventStore)
	if err != nil {
		return fmt.Errorf("could not create aggregate store: %w", err)
	}

	// Create the command handler for the Case aggregate
	caseHandler, err := aggregate.NewCommandHandler(CaseAggregateType, aggregateStore)
	if err != nil {
		return fmt.Errorf("could not create case command handler: %w", err)
	}

	// Apply logging middleware to the command handler
	commandHandler := eh.UseCommandHandlerMiddleware(caseHandler, LoggingMiddleware)

	// Register all commands with the command bus
	for _, cmd := range []eh.CommandType{
		CommandSubmitCase,
		CommandResetCase,
		CommandDecideAutomatically,
		CommandAddToManualReview,
		CommandCompleteManualReview,
		CommandObjectToCase,
		CommandSetObjectionStatus,
		CommandSetObjectionAdmissibility,
		CommandSetAppealStatus,
	} {
		if err := commandBus.SetHandler(commandHandler, cmd); err != nil {
			return fmt.Errorf("could not add command handler for '%s': %w", cmd, err)
		}
	}

	// Create and register a read model for individual invitations.
	caseProjector := projector.NewEventHandler(NewCaseProjector(), caseRepo)

	caseProjector.SetEntityFactory(func() eh.Entity { return &Case{} })
	if err := local.AddHandler(ctx, eh.MatchEvents{
		CaseSubmittedEvent,
		CaseResetEvent,
		CaseAutomaticallyDecidedEvent,
		CaseAddedToManualReviewEvent,
		CaseDecidedEvent,
		CaseObjectedEvent,
		ObjectionStatusDeterminedEvent,
		ObjectionAdmissibilityDeterminedEvent,
		AppealStatusDeterminedEvent,
	}, caseProjector); err != nil {
		return fmt.Errorf("could not add invitation projector: %w", err)
	}

	// Add a logger as an observer
	if err := local.AddHandler(ctx, eh.MatchAll{}, eh.UseEventHandlerMiddleware(&Logger{}, observer.Middleware)); err != nil {
		return fmt.Errorf("could not add logger to event bus: %w", err)
	}

	return nil
}

// SubmitCase is a helper function to submit a new case.
func SubmitCase(
	ctx context.Context,
	commandBus eh.CommandHandler,
	bsn string,
	serviceType string,
	law string,
	parameters map[string]any,
	claimedResult map[string]any,
	verifiedResult map[string]any,
	rulespecID uuid.UUID,
	approvedClaimsOnly bool,
) (uuid.UUID, error) {
	// Create a unique ID for the case
	id := uuid.New()

	// Create the command
	cmd := SubmitCaseCommand{
		ID:                 id,
		BSN:                bsn,
		ServiceType:        serviceType,
		Law:                law,
		Parameters:         parameters,
		ClaimedResult:      claimedResult,
		VerifiedResult:     verifiedResult,
		RulespecID:         rulespecID,
		ApprovedClaimsOnly: approvedClaimsOnly,
	}

	// Execute the command
	if err := commandBus.HandleCommand(ctx, cmd); err != nil {
		return uuid.Nil, fmt.Errorf("could not handle submit case command: %w", err)
	}

	log.Printf("Case submitted with ID: %s", id)
	return id, nil
}

// ProcessCase automatically decides or routes a case to manual review.
func ProcessCase(
	ctx context.Context,
	commandBus eh.CommandHandler,
	caseID uuid.UUID,
	verifiedResult map[string]any,
	parameters map[string]any,
	resultsMatch bool,
	sampleRate float64,
) error {
	// Determine if manual review is needed
	needsManualReview := !resultsMatch

	// If results match, check if we should sample for manual review
	if resultsMatch && rand.Float64() < sampleRate {
		needsManualReview = true
	}

	if needsManualReview {
		// Route to manual review with reason
		reason := "Selected for manual review - "
		if !resultsMatch {
			reason += "results differ"
		} else {
			reason += "random sample check"
		}

		cmd := AddToManualReviewCommand{
			ID:             caseID,
			VerifierID:     "SYSTEM",
			Reason:         reason,
			VerifiedResult: verifiedResult,
		}

		if err := commandBus.HandleCommand(ctx, cmd); err != nil {
			return fmt.Errorf("could not add case to manual review: %w", err)
		}
	} else {
		// Automatically approve the case
		cmd := DecideAutomaticallyCommand{
			ID:             caseID,
			VerifiedResult: verifiedResult,
			Parameters:     parameters,
			Approved:       true,
		}

		if err := commandBus.HandleCommand(ctx, cmd); err != nil {
			return fmt.Errorf("could not automatically decide case: %w", err)
		}
	}

	return nil
}

// CompleteManualReview completes a manual review.
func CompleteManualReview(
	ctx context.Context,
	commandBus eh.CommandHandler,
	caseID uuid.UUID,
	verifierID string,
	approved bool,
	reason string,
	verifiedResult map[string]any,
) error {
	cmd := CompleteManualReviewCommand{
		ID:             caseID,
		VerifierID:     verifierID,
		Approved:       approved,
		Reason:         reason,
		VerifiedResult: verifiedResult,
	}

	if err := commandBus.HandleCommand(ctx, cmd); err != nil {
		return fmt.Errorf("could not complete manual review: %w", err)
	}

	return nil
}

// ObjectToCase files an objection to a case.
func ObjectToCase(
	ctx context.Context,
	commandBus eh.CommandHandler,
	caseID uuid.UUID,
	reason string,
) error {
	cmd := ObjectToCaseCommand{
		ID:     caseID,
		Reason: reason,
	}

	if err := commandBus.HandleCommand(ctx, cmd); err != nil {
		return fmt.Errorf("could not object to case: %w", err)
	}

	return nil
}

// DetermineObjectionStatus sets the objection status.
func DetermineObjectionStatus(
	ctx context.Context,
	commandBus eh.CommandHandler,
	caseID uuid.UUID,
	possible *bool,
	notPossibleReason *string,
	objectionPeriod *int,
	decisionPeriod *int,
	extensionPeriod *int,
) error {
	cmd := SetObjectionStatusCommand{
		ID:                caseID,
		Possible:          possible,
		NotPossibleReason: notPossibleReason,
		ObjectionPeriod:   objectionPeriod,
		DecisionPeriod:    decisionPeriod,
		ExtensionPeriod:   extensionPeriod,
	}

	if err := commandBus.HandleCommand(ctx, cmd); err != nil {
		return fmt.Errorf("could not determine objection status: %w", err)
	}

	return nil
}

// DetermineObjectionAdmissibility sets the objection admissibility.
func DetermineObjectionAdmissibility(
	ctx context.Context,
	commandBus eh.CommandHandler,
	caseID uuid.UUID,
	admissible *bool,
) error {
	cmd := SetObjectionAdmissibilityCommand{
		ID:         caseID,
		Admissible: admissible,
	}

	if err := commandBus.HandleCommand(ctx, cmd); err != nil {
		return fmt.Errorf("could not determine objection admissibility: %w", err)
	}

	return nil
}

// DetermineAppealStatus sets the appeal status.
func DetermineAppealStatus(
	ctx context.Context,
	commandBus eh.CommandHandler,
	caseID uuid.UUID,
	possible *bool,
	notPossibleReason *string,
	appealPeriod *int,
	directAppeal *bool,
	directAppealReason *string,
	competentCourt *string,
	courtType *string,
) error {
	cmd := SetAppealStatusCommand{
		ID:                 caseID,
		Possible:           possible,
		NotPossibleReason:  notPossibleReason,
		AppealPeriod:       appealPeriod,
		DirectAppeal:       directAppeal,
		DirectAppealReason: directAppealReason,
		CompetentCourt:     competentCourt,
		CourtType:          courtType,
	}

	if err := commandBus.HandleCommand(ctx, cmd); err != nil {
		return fmt.Errorf("could not determine appeal status: %w", err)
	}

	return nil
}

// FindCase finds a case in the repository.
func FindCase(
	ctx context.Context,
	repo eh.ReadRepo,
	id uuid.UUID,
) (*Case, error) {
	entity, err := repo.Find(ctx, id)
	if err != nil {
		return nil, fmt.Errorf("could not find case: %w", err)
	}

	case_, ok := entity.(*Case)
	if !ok {
		return nil, fmt.Errorf("invalid entity type: %T", entity)
	}

	return case_, nil
}
