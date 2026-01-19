package casemanager

import (
	"context"
	"fmt"
	"math/rand/v2"
	"time"

	"github.com/google/uuid"
	eh "github.com/looplab/eventhorizon"
	"github.com/looplab/eventhorizon/aggregatestore/events"
)

// CaseAggregateType is the aggregate type for cases.
const CaseAggregateType = eh.AggregateType("Case")

var _ eh.Aggregate = &CaseAggregate{}
var _ events.VersionedAggregate = &CaseAggregate{}

// CaseAggregate represents an aggregate for managing cases.
type CaseAggregate struct {
	*events.AggregateBase
	c              *Case
	sampleRate     float64
	resultsMatchFn func(map[string]any, map[string]any) bool
}

func RegisterAggregate() {
	eh.RegisterAggregate(func(id uuid.UUID) eh.Aggregate {
		return NewCaseAggregate(id)
	})
}

// NewCaseAggregate creates a new CaseAggregate.
func NewCaseAggregate(id uuid.UUID) *CaseAggregate {
	// Create a new aggregate with default values
	aggregate := &CaseAggregate{
		AggregateBase: events.NewAggregateBase(CaseAggregateType, id), // Set the aggregate ID
		sampleRate:    0.10,                                           // 10% sample rate
	}

	return aggregate
}

// HandleCommand implements the HandleCommand method of the Aggregate interface.
func (aggregate *CaseAggregate) HandleCommand(ctx context.Context, cmd eh.Command) error {
	switch cmd := cmd.(type) {
	case SubmitCaseCommand:
		if aggregate.c != nil {
			return fmt.Errorf("case already exists")
		}

		// Create a basic empty case - we'll fill it during event application
		aggregate.c = &Case{}

		// Emit a CaseSubmitted event
		aggregate.AppendEvent(
			CaseSubmittedEvent,
			&CaseSubmitted{
				BSN:                cmd.BSN,
				ServiceType:        cmd.ServiceType,
				Law:                cmd.Law,
				Parameters:         cmd.Parameters,
				ClaimedResult:      cmd.ClaimedResult,
				VerifiedResult:     cmd.VerifiedResult,
				RulespecUUID:       cmd.RulespecID,
				ApprovedClaimsOnly: cmd.ApprovedClaimsOnly,
				EffectiveDate:      cmd.EffectiveDate,
			},
			time.Now(),
		)

		return nil

	case ResetCaseCommand:
		if aggregate.c == nil {
			return fmt.Errorf("case does not exist")
		}

		// Emit a CaseReset event
		aggregate.AppendEvent(
			CaseResetEvent,
			&CaseReset{
				Parameters:         cmd.Parameters,
				ClaimedResult:      cmd.ClaimedResult,
				VerifiedResult:     cmd.VerifiedResult,
				ApprovedClaimsOnly: cmd.ApprovedClaimsOnly,
			},
			time.Now(),
		)

		return nil

	case DecideAutomaticallyCommand:
		if aggregate.c == nil {
			return fmt.Errorf("case does not exist")
		}

		if aggregate.c.Status != CaseStatusSubmitted && aggregate.c.Status != CaseStatusObjected {
			return fmt.Errorf("case incorrect state, can only decide on submitted or objections")
		}

		aggregate.AppendEvent(
			CaseAutomaticallyDecidedEvent,
			&CaseAutomaticallyDecided{
				VerifiedResult: cmd.VerifiedResult,
				Parameters:     cmd.Parameters,
				Approved:       cmd.Approved,
			},
			time.Now(),
		)

		return nil

	case AddToManualReviewCommand:
		if aggregate.c == nil {
			return fmt.Errorf("case does not exist")
		}

		if aggregate.c.Status != CaseStatusSubmitted && aggregate.c.Status != CaseStatusObjected {
			return fmt.Errorf("case incorrect state, can only add to review on submitted or objections")
		}

		aggregate.AppendEvent(
			CaseAddedToManualReviewEvent,
			&CaseAddedToManualReview{
				VerifierID:     cmd.VerifierID,
				Reason:         cmd.Reason,
				ClaimedResult:  cmd.ClaimedResult,
				VerifiedResult: cmd.VerifiedResult,
			},
			time.Now(),
		)
		return nil

	case CompleteManualReviewCommand:
		if aggregate.c == nil {
			return fmt.Errorf("case does not exist")
		}

		if aggregate.c.Status != CaseStatusInReview && aggregate.c.Status != CaseStatusObjected {
			return fmt.Errorf("can only complete review for cases in review or objections, current state: %s", aggregate.c.Status)
		}

		aggregate.AppendEvent(
			CaseDecidedEvent,
			&CaseDecided{
				VerifiedResult: cmd.VerifiedResult,
				Reason:         cmd.Reason,
				VerifierID:     cmd.VerifierID,
				Approved:       cmd.Approved,
			},
			time.Now(),
		)

		return nil

	case ObjectToCaseCommand:
		if aggregate.c == nil {
			return fmt.Errorf("case does not exist")
		}

		if aggregate.c.Status != CaseStatusDecided {
			return fmt.Errorf("can only object on decided cases")
		}

		aggregate.AppendEvent(
			CaseObjectedEvent,
			&CaseObjected{
				Reason: cmd.Reason,
			},
			time.Now(),
		)

		return nil
	case AddClaimToCaseCommand:
		if aggregate.c == nil {
			return fmt.Errorf("case does not exist")
		}

		if aggregate.c.Status == CaseStatusDecided {
			return fmt.Errorf("can not alter object on decided cases")
		}

		aggregate.AppendEvent(
			CaseAddClaimEvent,
			&CaseAddClaim{
				ClaimID: cmd.ClaimID,
			},
			time.Now(),
		)

		return nil
	case SetObjectionStatusCommand:
		if aggregate.c == nil {
			return fmt.Errorf("case does not exist")
		}

		aggregate.AppendEvent(
			ObjectionStatusDeterminedEvent,
			&ObjectionStatusDetermined{
				Possible:          cmd.Possible,
				NotPossibleReason: cmd.NotPossibleReason,
				ObjectionPeriod:   cmd.ObjectionPeriod,
				DecisionPeriod:    cmd.DecisionPeriod,
				ExtensionPeriod:   cmd.ExtensionPeriod,
			},
			time.Now(),
		)

		return nil

	case SetObjectionAdmissibilityCommand:
		if aggregate.c == nil {
			return fmt.Errorf("case does not exist")
		}

		aggregate.AppendEvent(
			ObjectionAdmissibilityDeterminedEvent,
			&ObjectionAdmissibilityDetermined{
				Admissible: cmd.Admissible,
			},
			time.Now(),
		)

		return nil

	case SetAppealStatusCommand:
		if aggregate.c == nil {
			return fmt.Errorf("case does not exist")
		}

		aggregate.AppendEvent(
			AppealStatusDeterminedEvent,
			&AppealStatusDetermined{
				Possible:           cmd.Possible,
				NotPossibleReason:  cmd.NotPossibleReason,
				AppealPeriod:       cmd.AppealPeriod,
				DirectAppeal:       cmd.DirectAppeal,
				DirectAppealReason: cmd.DirectAppealReason,
				CompetentCourt:     cmd.CompetentCourt,
				CourtType:          cmd.CourtType,
			},
			time.Now(),
		)

		return nil
	}

	return fmt.Errorf("couldn't handle command: %s", cmd.CommandType())
}

// ApplyEvent implements the ApplyEvent method of the Aggregate interface.
func (aggregate *CaseAggregate) ApplyEvent(ctx context.Context, event eh.Event) error {
	switch data := event.Data().(type) {
	case *CaseSubmitted:
		// Determine effective date - use provided date or default to now
		effectiveDate := time.Now()
		if data.EffectiveDate != nil {
			effectiveDate = *data.EffectiveDate
		}

		// Create a new case with the data from the event
		aggregate.c = NewCase(
			data.BSN,
			data.ServiceType,
			data.Law,
			data.Parameters,
			data.ClaimedResult,
			data.VerifiedResult,
			data.RulespecUUID,
			data.ApprovedClaimsOnly,
			effectiveDate,
		)

		// After case creation, we would normally check if results match and decide if manual review is needed
		// This would be done in a separate command handler that processes the submitted case

		return nil

	case *CaseReset:
		// Reset the case
		return aggregate.c.Reset(
			data.Parameters,
			data.ClaimedResult,
			data.VerifiedResult,
			data.ApprovedClaimsOnly,
		)

	case *CaseAutomaticallyDecided:
		// Decide the case automatically
		return aggregate.c.DecideAutomatically(
			data.VerifiedResult,
			data.Parameters,
			data.Approved,
		)

	case *CaseAddedToManualReview:
		// Add the case to manual review
		return aggregate.c.SelectForManualReview(
			data.VerifierID,
			data.Reason,
			data.ClaimedResult,
			data.VerifiedResult,
		)

	case *CaseDecided:
		// Decide the case
		return aggregate.c.Decide(
			data.VerifiedResult,
			data.Reason,
			data.VerifierID,
			data.Approved,
		)

	case *CaseObjected:
		return aggregate.c.Object(data.Reason)
	case *CaseAddClaim:
		return aggregate.c.AddClaim(data.ClaimID)
	case *ObjectionStatusDetermined:
		// Set objection status
		return aggregate.c.DetermineObjectionStatus(
			data.Possible,
			data.NotPossibleReason,
			data.ObjectionPeriod,
			data.DecisionPeriod,
			data.ExtensionPeriod,
		)

	case *ObjectionAdmissibilityDetermined:
		// Set objection admissibility
		return aggregate.c.DetermineObjectionAdmissibility(data.Admissible)

	case *AppealStatusDetermined:
		// Set appeal status
		return aggregate.c.DetermineAppealStatus(
			data.Possible,
			data.NotPossibleReason,
			data.AppealPeriod,
			data.DirectAppeal,
			data.DirectAppealReason,
			data.CompetentCourt,
			data.CourtType,
		)
	}

	return fmt.Errorf("couldn't apply event: %s", event.EventType())
}

// SetSampleRate sets the sample rate for random manual reviews
func (aggregate *CaseAggregate) SetSampleRate(rate float64) {
	aggregate.sampleRate = rate
}

// ShouldSelectForManualReview determines if a case should be selected for manual review
func (aggregate *CaseAggregate) ShouldSelectForManualReview(claimedResult, verifiedResult map[string]any) (bool, string) {
	// Check if results match
	if !aggregate.resultsMatchFn(claimedResult, verifiedResult) {
		return true, "Results differ"
	}

	// Determine if manual review is needed based on random sampling
	if rand.Float64() < aggregate.sampleRate {
		return true, "Random sample check"
	}

	return false, ""
}
