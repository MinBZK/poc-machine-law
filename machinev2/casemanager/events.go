package casemanager

import (
	"github.com/google/uuid"
	eh "github.com/looplab/eventhorizon"
)

// Register event types with the EventHorizon ecosystem
func RegisterEvents() {
	eh.RegisterEventData(CaseSubmittedEvent, func() eh.EventData { return &CaseSubmitted{} })
	eh.RegisterEventData(CaseResetEvent, func() eh.EventData { return &CaseReset{} })
	eh.RegisterEventData(CaseAutomaticallyDecidedEvent, func() eh.EventData { return &CaseAutomaticallyDecided{} })
	eh.RegisterEventData(CaseAddedToManualReviewEvent, func() eh.EventData { return &CaseAddedToManualReview{} })
	eh.RegisterEventData(CaseDecidedEvent, func() eh.EventData { return &CaseDecided{} })
	eh.RegisterEventData(CaseObjectedEvent, func() eh.EventData { return &CaseObjected{} })
	eh.RegisterEventData(ObjectionStatusDeterminedEvent, func() eh.EventData { return &ObjectionStatusDetermined{} })
	eh.RegisterEventData(ObjectionAdmissibilityDeterminedEvent, func() eh.EventData { return &ObjectionAdmissibilityDetermined{} })
	eh.RegisterEventData(AppealStatusDeterminedEvent, func() eh.EventData { return &AppealStatusDetermined{} })
}

// CaseSubmitted is an event for when a case is submitted.
type CaseSubmitted struct {
	BSN                string         `json:"bsn"`
	ServiceType        string         `json:"service_type"`
	Law                string         `json:"law"`
	Parameters         map[string]any `json:"parameters"`
	ClaimedResult      map[string]any `json:"claimed_result"`
	VerifiedResult     map[string]any `json:"verified_result"`
	RulespecUUID       uuid.UUID      `json:"rulespec_uuid"`
	ApprovedClaimsOnly bool           `json:"approved_claims_only"`
}

// CaseReset is an event for when a case is reset.
type CaseReset struct {
	Parameters         map[string]any `json:"parameters"`
	ClaimedResult      map[string]any `json:"claimed_result"`
	VerifiedResult     map[string]any `json:"verified_result"`
	ApprovedClaimsOnly bool           `json:"approved_claims_only"`
}

// CaseAutomaticallyDecided is an event for when a case is automatically decided.
type CaseAutomaticallyDecided struct {
	VerifiedResult map[string]any `json:"verified_result"`
	Parameters     map[string]any `json:"parameters"`
	Approved       bool           `json:"approved"`
}

// CaseAddedToManualReview is an event for when a case is added to manual review.
type CaseAddedToManualReview struct {
	VerifierID     string         `json:"verifier_id"`
	Reason         string         `json:"reason"`
	ClaimedResult  map[string]any `json:"claimed_result"`
	VerifiedResult map[string]any `json:"verified_result"`
}

// CaseDecided is an event for when a case is decided.
type CaseDecided struct {
	VerifiedResult map[string]any `json:"verified_result"`
	Reason         string         `json:"reason"`
	VerifierID     string         `json:"verifier_id"`
	Approved       bool           `json:"approved"`
}

// CaseObjected is an event for when an objection is raised for a case.
type CaseObjected struct {
	Reason string `json:"reason"`
}

// ObjectionStatusDetermined is an event for when objection status is determined.
type ObjectionStatusDetermined struct {
	Possible          *bool   `json:"possible,omitempty"`
	NotPossibleReason *string `json:"not_possible_reason,omitempty"`
	ObjectionPeriod   *int    `json:"objection_period,omitempty"`
	DecisionPeriod    *int    `json:"decision_period,omitempty"`
	ExtensionPeriod   *int    `json:"extension_period,omitempty"`
}

// ObjectionAdmissibilityDetermined is an event for when objection admissibility is determined.
type ObjectionAdmissibilityDetermined struct {
	Admissible *bool `json:"admissible,omitempty"`
}

// AppealStatusDetermined is an event for when appeal status is determined.
type AppealStatusDetermined struct {
	Possible           *bool   `json:"possible,omitempty"`
	NotPossibleReason  *string `json:"not_possible_reason,omitempty"`
	AppealPeriod       *int    `json:"appeal_period,omitempty"`
	DirectAppeal       *bool   `json:"direct_appeal,omitempty"`
	DirectAppealReason *string `json:"direct_appeal_reason,omitempty"`
	CompetentCourt     *string `json:"competent_court,omitempty"`
	CourtType          *string `json:"court_type,omitempty"`
}
