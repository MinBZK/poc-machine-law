package casemanager

import (
	"time"

	"github.com/google/uuid"
	eh "github.com/looplab/eventhorizon"
)

func RegisterCommands() {
	eh.RegisterCommand(func() eh.Command { return &SubmitCaseCommand{} })
	eh.RegisterCommand(func() eh.Command { return &ResetCaseCommand{} })
	eh.RegisterCommand(func() eh.Command { return &DecideAutomaticallyCommand{} })
	eh.RegisterCommand(func() eh.Command { return &AddToManualReviewCommand{} })
	eh.RegisterCommand(func() eh.Command { return &CompleteManualReviewCommand{} })
	eh.RegisterCommand(func() eh.Command { return &ObjectToCaseCommand{} })
	eh.RegisterCommand(func() eh.Command { return &SetObjectionStatusCommand{} })
	eh.RegisterCommand(func() eh.Command { return &SetObjectionAdmissibilityCommand{} })
	eh.RegisterCommand(func() eh.Command { return &SetAppealStatusCommand{} })
}

// Command types for the case manager.
const (
	CommandSubmitCase                eh.CommandType = "SubmitCase"
	CommandResetCase                 eh.CommandType = "ResetCase"
	CommandDecideAutomatically       eh.CommandType = "DecideAutomatically"
	CommandAddToManualReview         eh.CommandType = "AddToManualReview"
	CommandCompleteManualReview      eh.CommandType = "CompleteManualReview"
	CommandObjectToCase              eh.CommandType = "ObjectToCase"
	CommandAddClaimToCase            eh.CommandType = "AddClaimToCase"
	CommandSetObjectionStatus        eh.CommandType = "SetObjectionStatus"
	CommandSetObjectionAdmissibility eh.CommandType = "SetObjectionAdmissibility"
	CommandSetAppealStatus           eh.CommandType = "SetAppealStatus"
)

// Event types for the case manager.
const (
	CaseSubmittedEvent                    eh.EventType = "Submitted"
	CaseResetEvent                        eh.EventType = "Reset"
	CaseAutomaticallyDecidedEvent         eh.EventType = "AutomaticallyDecided"
	CaseAddedToManualReviewEvent          eh.EventType = "AddedToManualReview"
	CaseDecidedEvent                      eh.EventType = "Decided"
	CaseObjectedEvent                     eh.EventType = "Objected"
	CaseAddClaimEvent                     eh.EventType = "AddClaim"
	ObjectionStatusDeterminedEvent        eh.EventType = "ObjectionStatusDetermined"
	ObjectionAdmissibilityDeterminedEvent eh.EventType = "ObjectionAdmissibilityDetermined"
	AppealStatusDeterminedEvent           eh.EventType = "AppealStatusDetermined"
)

// SubmitCaseCommand is a command for submitting a new case.
type SubmitCaseCommand struct {
	ID                 uuid.UUID      `json:"id"`
	BSN                string         `json:"bsn"`
	ServiceType        string         `json:"service_type"`
	Law                string         `json:"law"`
	Parameters         map[string]any `json:"parameters" eh:"optional"`
	ClaimedResult      map[string]any `json:"claimed_result" eh:"optional"`
	VerifiedResult     map[string]any `json:"verified_result" eh:"optional"`
	RulespecID         uuid.UUID      `json:"rulespec_uuid"`
	ApprovedClaimsOnly bool           `json:"approved_claims_only"`
	EffectiveDate      *time.Time     `json:"effective_date,omitempty" eh:"optional"`
}

// CommandType returns the type of the command.
func (c SubmitCaseCommand) CommandType() eh.CommandType {
	return CommandSubmitCase
}

// AggregateID returns the ID of the aggregate that the command should be handled by.
func (c SubmitCaseCommand) AggregateID() uuid.UUID {
	return c.ID
}

// AggregateType returns the type of the aggregate that the command can be handled by.
func (c SubmitCaseCommand) AggregateType() eh.AggregateType {
	return "Case"
}

// ResetCaseCommand is a command for resetting an existing case.
type ResetCaseCommand struct {
	ID                 uuid.UUID      `json:"id"`
	Parameters         map[string]any `json:"parameters" eh:"optional"`
	ClaimedResult      map[string]any `json:"claimed_result" eh:"optional"`
	VerifiedResult     map[string]any `json:"verified_result" eh:"optional"`
	ApprovedClaimsOnly bool           `json:"approved_claims_only"`
}

// CommandType returns the type of the command.
func (c ResetCaseCommand) CommandType() eh.CommandType {
	return CommandResetCase
}

// AggregateID returns the ID of the aggregate that the command should be handled by.
func (c ResetCaseCommand) AggregateID() uuid.UUID {
	return c.ID
}

// AggregateType returns the type of the aggregate that the command can be handled by.
func (c ResetCaseCommand) AggregateType() eh.AggregateType {
	return "Case"
}

// DecideAutomaticallyCommand is a command for automatically deciding a case.
type DecideAutomaticallyCommand struct {
	ID             uuid.UUID      `json:"id"`
	VerifiedResult map[string]any `json:"verified_result"`
	Parameters     map[string]any `json:"parameters" eh:"optional"`
	Approved       bool           `json:"approved"`
}

// CommandType returns the type of the command.
func (c DecideAutomaticallyCommand) CommandType() eh.CommandType {
	return CommandDecideAutomatically
}

// AggregateID returns the ID of the aggregate that the command should be handled by.
func (c DecideAutomaticallyCommand) AggregateID() uuid.UUID {
	return c.ID
}

// AggregateType returns the type of the aggregate that the command can be handled by.
func (c DecideAutomaticallyCommand) AggregateType() eh.AggregateType {
	return "Case"
}

// AddToManualReviewCommand is a command for adding a case to manual review.
type AddToManualReviewCommand struct {
	ID             uuid.UUID      `json:"id"`
	VerifierID     string         `json:"verifier_id"`
	Reason         string         `json:"reason"`
	ClaimedResult  map[string]any `json:"claimed_result" eh:"optional"`
	VerifiedResult map[string]any `json:"verified_result" eh:"optional"`
}

// CommandType returns the type of the command.
func (c AddToManualReviewCommand) CommandType() eh.CommandType {
	return CommandAddToManualReview
}

// AggregateID returns the ID of the aggregate that the command should be handled by.
func (c AddToManualReviewCommand) AggregateID() uuid.UUID {
	return c.ID
}

// AggregateType returns the type of the aggregate that the command can be handled by.
func (c AddToManualReviewCommand) AggregateType() eh.AggregateType {
	return "Case"
}

// CompleteManualReviewCommand is a command for completing a manual review.
type CompleteManualReviewCommand struct {
	ID             uuid.UUID      `json:"id"`
	VerifierID     string         `json:"verifier_id"`
	Approved       bool           `json:"approved"`
	Reason         string         `json:"reason"`
	VerifiedResult map[string]any `json:"verified_result"`
}

// CommandType returns the type of the command.
func (c CompleteManualReviewCommand) CommandType() eh.CommandType {
	return CommandCompleteManualReview
}

// AggregateID returns the ID of the aggregate that the command should be handled by.
func (c CompleteManualReviewCommand) AggregateID() uuid.UUID {
	return c.ID
}

// AggregateType returns the type of the aggregate that the command can be handled by.
func (c CompleteManualReviewCommand) AggregateType() eh.AggregateType {
	return "Case"
}

// ObjectToCaseCommand is a command for objecting to a case.
type ObjectToCaseCommand struct {
	ID     uuid.UUID `json:"id"`
	Reason string    `json:"reason"`
}

// CommandType returns the type of the command.
func (c ObjectToCaseCommand) CommandType() eh.CommandType {
	return CommandObjectToCase
}

// AggregateID returns the ID of the aggregate that the command should be handled by.
func (c ObjectToCaseCommand) AggregateID() uuid.UUID {
	return c.ID
}

// AggregateType returns the type of the aggregate that the command can be handled by.
func (c ObjectToCaseCommand) AggregateType() eh.AggregateType {
	return "Case"
}

type AddClaimToCaseCommand struct {
	ID      uuid.UUID `json:"id"`
	ClaimID uuid.UUID `json:"claimId"`
}

// CommandType returns the type of the command.
func (c AddClaimToCaseCommand) CommandType() eh.CommandType {
	return CommandAddClaimToCase
}

// AggregateID returns the ID of the aggregate that the command should be handled by.
func (c AddClaimToCaseCommand) AggregateID() uuid.UUID {
	return c.ID
}

// AggregateType returns the type of the aggregate that the command can be handled by.
func (c AddClaimToCaseCommand) AggregateType() eh.AggregateType {
	return "Case"
}

// SetObjectionStatusCommand is a command for setting objection status.
type SetObjectionStatusCommand struct {
	ID                uuid.UUID `json:"id"`
	Possible          *bool     `json:"possible,omitempty" eh:"optional"`
	NotPossibleReason *string   `json:"not_possible_reason,omitempty" eh:"optional"`
	ObjectionPeriod   *int      `json:"objection_period,omitempty" eh:"optional"`
	DecisionPeriod    *int      `json:"decision_period,omitempty" eh:"optional"`
	ExtensionPeriod   *int      `json:"extension_period,omitempty" eh:"optional"`
}

// CommandType returns the type of the command.
func (c SetObjectionStatusCommand) CommandType() eh.CommandType {
	return CommandSetObjectionStatus
}

// AggregateID returns the ID of the aggregate that the command should be handled by.
func (c SetObjectionStatusCommand) AggregateID() uuid.UUID {
	return c.ID
}

// AggregateType returns the type of the aggregate that the command can be handled by.
func (c SetObjectionStatusCommand) AggregateType() eh.AggregateType {
	return "Case"
}

// SetObjectionAdmissibilityCommand is a command for setting objection admissibility.
type SetObjectionAdmissibilityCommand struct {
	ID         uuid.UUID `json:"id"`
	Admissible *bool     `json:"admissible,omitempty"`
}

// CommandType returns the type of the command.
func (c SetObjectionAdmissibilityCommand) CommandType() eh.CommandType {
	return CommandSetObjectionAdmissibility
}

// AggregateID returns the ID of the aggregate that the command should be handled by.
func (c SetObjectionAdmissibilityCommand) AggregateID() uuid.UUID {
	return c.ID
}

// AggregateType returns the type of the aggregate that the command can be handled by.
func (c SetObjectionAdmissibilityCommand) AggregateType() eh.AggregateType {
	return "Case"
}

// SetAppealStatusCommand is a command for setting appeal status.
type SetAppealStatusCommand struct {
	ID                 uuid.UUID `json:"id"`
	Possible           *bool     `json:"possible,omitempty" eh:"optional"`
	NotPossibleReason  *string   `json:"not_possible_reason,omitempty" eh:"optional"`
	AppealPeriod       *int      `json:"appeal_period,omitempty" eh:"optional"`
	DirectAppeal       *bool     `json:"direct_appeal,omitempty" eh:"optional"`
	DirectAppealReason *string   `json:"direct_appeal_reason,omitempty" eh:"optional"`
	CompetentCourt     *string   `json:"competent_court,omitempty" eh:"optional"`
	CourtType          *string   `json:"court_type,omitempty" eh:"optional"`
}

// CommandType returns the type of the command.
func (c SetAppealStatusCommand) CommandType() eh.CommandType {
	return CommandSetAppealStatus
}

// AggregateID returns the ID of the aggregate that the command should be handled by.
func (c SetAppealStatusCommand) AggregateID() uuid.UUID {
	return c.ID
}

// AggregateType returns the type of the aggregate that the command can be handled by.
func (c SetAppealStatusCommand) AggregateType() eh.AggregateType {
	return "Case"
}
