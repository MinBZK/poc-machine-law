package casemanager

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"

	eh "github.com/looplab/eventhorizon"
	"github.com/looplab/eventhorizon/eventhandler/projector"
)

// CaseProjector is a projector for cases.
type CaseProjector struct{}

// NewCaseProjector creates a new CaseProjector.
func NewCaseProjector() *CaseProjector {
	return &CaseProjector{}
}

// ProjectorType implements the ProjectorType method of the Projector interface.
func (p *CaseProjector) ProjectorType() projector.Type {
	return projector.Type(CaseAggregateType.String())
}

// Project implements the Project method of the Projector interface.
func (p *CaseProjector) Project(ctx context.Context, event eh.Event, entity eh.Entity) (eh.Entity, error) {
	c, ok := entity.(*Case)
	if !ok {
		return nil, errors.New("model is of incorrect type")
	}

	// Apply the changes for the event.
	switch event.EventType() {
	case CaseSubmittedEvent:
		data, ok := event.Data().(*CaseSubmitted)
		if !ok {
			return nil, fmt.Errorf("projector: invalid event data type: %v", event.Data())
		}
		c.ID = event.AggregateID()
		c.BSN = data.BSN
		c.Service = data.ServiceType
		c.Law = data.Law
		c.Parameters = data.Parameters
		c.ClaimedResult = data.ClaimedResult
		c.VerifiedResult = data.VerifiedResult
		c.RulespecID = data.RulespecUUID
		c.ApprovedClaimsOnly = data.ApprovedClaimsOnly
		c.Status = CaseStatusSubmitted
		c.CreatedAt = time.Now()
		c.UpdatedAt = time.Now()

	case CaseResetEvent:
		data, ok := event.Data().(*CaseReset)
		if !ok {
			return nil, fmt.Errorf("projector: invalid event data type: %v", event.Data())
		}

		c.Parameters = data.Parameters
		c.ClaimedResult = data.ClaimedResult
		c.VerifiedResult = data.VerifiedResult
		c.ApprovedClaimsOnly = data.ApprovedClaimsOnly
		c.DisputedParameters = nil
		c.Evidence = ""
		c.Reason = ""
		c.VerifierID = ""
		c.Status = CaseStatusSubmitted
		c.Approved = nil
		c.UpdatedAt = time.Now()

	case CaseAutomaticallyDecidedEvent:
		data, ok := event.Data().(*CaseAutomaticallyDecided)
		if !ok {
			return nil, fmt.Errorf("projector: invalid event data type: %v", event.Data())
		}

		c.VerifiedResult = data.VerifiedResult
		c.Parameters = data.Parameters
		c.Status = CaseStatusDecided
		c.Approved = &data.Approved
		c.UpdatedAt = time.Now()

	case CaseAddedToManualReviewEvent:
		data, ok := event.Data().(*CaseAddedToManualReview)
		if !ok {
			return nil, fmt.Errorf("projector: invalid event data type: %v", event.Data())
		}

		c.Status = CaseStatusInReview
		c.VerifierID = data.VerifierID
		c.Reason = data.Reason
		c.ClaimedResult = data.ClaimedResult
		c.VerifiedResult = data.VerifiedResult
		c.UpdatedAt = time.Now()

	case CaseDecidedEvent:
		data, ok := event.Data().(*CaseDecided)
		if !ok {
			return nil, fmt.Errorf("projector: invalid event data type: %v", event.Data())
		}

		c.Status = CaseStatusDecided
		c.VerifiedResult = data.VerifiedResult
		c.Reason = data.Reason
		c.VerifierID = data.VerifierID
		c.Approved = &data.Approved
		c.UpdatedAt = time.Now()

	case CaseObjectedEvent:
		data, ok := event.Data().(*CaseObjected)
		if !ok {
			return nil, fmt.Errorf("projector: invalid event data type: %v", event.Data())
		}
		c.Status = CaseStatusObjected
		c.Reason = data.Reason
		c.UpdatedAt = time.Now()

	case ObjectionStatusDeterminedEvent:
		data, ok := event.Data().(*ObjectionStatusDetermined)
		if !ok {
			return nil, fmt.Errorf("projector: invalid event data type: %v", event.Data())
		}
		if c.ObjectionStatus == nil {
			c.ObjectionStatus = make(map[string]any)
		}

		if data.Possible != nil {
			c.ObjectionStatus["possible"] = *data.Possible
		}

		if data.NotPossibleReason != nil {
			c.ObjectionStatus["not_possible_reason"] = *data.NotPossibleReason
		}

		if data.ObjectionPeriod != nil {
			c.ObjectionStatus["objection_period"] = *data.ObjectionPeriod
		}

		if data.DecisionPeriod != nil {
			c.ObjectionStatus["decision_period"] = *data.DecisionPeriod
		}

		if data.ExtensionPeriod != nil {
			c.ObjectionStatus["extension_period"] = *data.ExtensionPeriod
		}

		c.UpdatedAt = time.Now()

	case ObjectionAdmissibilityDeterminedEvent:
		data, ok := event.Data().(*ObjectionAdmissibilityDetermined)
		if !ok {
			return nil, fmt.Errorf("projector: invalid event data type: %v", event.Data())
		}
		if c.ObjectionStatus == nil {
			c.ObjectionStatus = make(map[string]any)
		}

		if data.Admissible != nil {
			c.ObjectionStatus["admissible"] = *data.Admissible
		}

		c.UpdatedAt = time.Now()

	case AppealStatusDeterminedEvent:
		data, ok := event.Data().(*AppealStatusDetermined)
		if !ok {
			return nil, fmt.Errorf("projector: invalid event data type: %v", event.Data())
		}
		if c.AppealStatus == nil {
			c.AppealStatus = make(map[string]any)
		}

		if data.Possible != nil {
			c.AppealStatus["possible"] = *data.Possible
		}

		if data.NotPossibleReason != nil {
			c.AppealStatus["not_possible_reason"] = *data.NotPossibleReason
		}

		if data.AppealPeriod != nil {
			c.AppealStatus["appeal_period"] = *data.AppealPeriod
		}

		if data.DirectAppeal != nil {
			c.AppealStatus["direct_appeal"] = *data.DirectAppeal
		}

		if data.DirectAppealReason != nil {
			c.AppealStatus["direct_appeal_reason"] = *data.DirectAppealReason
		}

		if data.CompetentCourt != nil {
			c.AppealStatus["competent_court"] = *data.CompetentCourt
		}

		if data.CourtType != nil {
			c.AppealStatus["court_type"] = *data.CourtType
		}

		c.UpdatedAt = time.Now()

	default:
		return nil, fmt.Errorf("could not handle event: %s", event)
	}

	// Update the version
	c.Version++

	return c, nil
}

// CasesProjector is a projector that manages a list of cases.
type CasesProjector struct {
	repo   eh.ReadWriteRepo
	repoMu sync.Mutex
}

// NewCasesProjector creates a new CaseListProjector.
func NewCasesProjector(repo eh.ReadWriteRepo) *CasesProjector {
	return &CasesProjector{
		repo: repo,
	}
}

// HandlerType implements the HandlerType method of the eventhorizon.EventHandler interface.
func (p *CasesProjector) HandlerType() eh.EventHandlerType {
	return eh.EventHandlerType("projector_CaseList")
}

// HandleEvent implements the HandleEvent method of the EventHandler interface.
func (p *CasesProjector) HandleEvent(ctx context.Context, event eh.Event) error {
	// Lock to ensure atomic operations on the repo
	p.repoMu.Lock()
	defer p.repoMu.Unlock()

	// Only handle case-related events
	switch event.EventType() {
	case CaseSubmittedEvent, CaseResetEvent, CaseAutomaticallyDecidedEvent,
		CaseAddedToManualReviewEvent, CaseDecidedEvent, CaseObjectedEvent,
		ObjectionStatusDeterminedEvent, ObjectionAdmissibilityDeterminedEvent,
		AppealStatusDeterminedEvent:
		// Continue handling
	default:
		// Skip other event types
		return nil
	}

	// Find the case
	entity, err := p.repo.Find(ctx, event.AggregateID())
	if errors.Is(err, eh.ErrEntityNotFound) {
		// If this is a CaseSubmitted event, create a new case
		if event.EventType() == CaseSubmittedEvent {
			data, ok := event.Data().(*CaseSubmitted)
			if !ok {
				return fmt.Errorf("projector: invalid event data type: %v", event.Data())
			}

			now := time.Now()
			c := &Case{
				ID:                 event.AggregateID(),
				Version:            event.Version(),
				BSN:                data.BSN,
				Service:            data.ServiceType,
				Law:                data.Law,
				Parameters:         data.Parameters,
				ClaimedResult:      data.ClaimedResult,
				VerifiedResult:     data.VerifiedResult,
				RulespecID:         data.RulespecUUID,
				ApprovedClaimsOnly: data.ApprovedClaimsOnly,
				Status:             CaseStatusSubmitted,
				CreatedAt:          now,
				UpdatedAt:          now,
			}

			if err := p.repo.Save(ctx, c); err != nil {
				return fmt.Errorf("projector: could not save new case: %w", err)
			}
			return nil
		}

		// For other events, if the case doesn't exist, it's an error
		return fmt.Errorf("case not found for event %s: %w", event.EventType(), err)
	} else if err != nil {
		return fmt.Errorf("projector: could not find case: %w", err)
	}

	// Apply projections using the CaseProjector
	projector := NewCaseProjector()
	updatedEntity, err := projector.Project(ctx, event, entity)
	if err != nil {
		return fmt.Errorf("projector: failed to project event: %w", err)
	}

	// Save the updated case
	if err := p.repo.Save(ctx, updatedEntity); err != nil {
		return fmt.Errorf("projector: could not save case: %w", err)
	}

	return nil
}
