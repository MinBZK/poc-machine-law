package casemanager

import (
	"fmt"
	"time"

	"github.com/google/uuid"
	eh "github.com/looplab/eventhorizon"
)

// CaseStatus represents the status of a case
type CaseStatus string

const (
	// CaseStatusSubmitted indicates a newly submitted case
	CaseStatusSubmitted CaseStatus = "SUBMITTED"

	// CaseStatusDecided indicates a case with a decision
	CaseStatusDecided CaseStatus = "DECIDED"

	// CaseStatusInReview indicates a case being reviewed
	CaseStatusInReview CaseStatus = "IN_REVIEW"

	// CaseStatusObjected indicates a case with an objection
	CaseStatusObjected CaseStatus = "OBJECTED"
)

var _ = eh.Entity(&Case{})
var _ = eh.Versionable(&Case{})

// Case represents a service case
type Case struct {
	ID                 uuid.UUID `json:"id"`
	Version            int
	ClaimIDs           []uuid.UUID         `json:"claim_ids,omitempty"`
	BSN                string              `json:"bsn"`
	Service            string              `json:"service"`
	Law                string              `json:"law"`
	RulespecID         uuid.UUID           `json:"rulespec_uuid"`
	ApprovedClaimsOnly bool                `json:"approved_claims_only"`
	ClaimedResult      map[string]any      `json:"claimed_result"`
	VerifiedResult     map[string]any      `json:"verified_result"`
	Parameters         map[string]any      `json:"parameters"`
	DisputedParameters map[string]any      `json:"disputed_parameters,omitempty"`
	Evidence           string              `json:"evidence,omitempty"`
	Reason             string              `json:"reason,omitempty"`
	VerifierID         string              `json:"verifier_id,omitempty"`
	ObjectionStatus    CaseObjectionStatus `json:"objection_status,omitempty"`
	AppealStatus       CaseAppealStatus    `json:"appeal_status,omitempty"`
	Approved           *bool               `json:"approved,omitempty"`
	Status             CaseStatus          `json:"status"`
	CreatedAt          time.Time           `json:"created_at"`
	UpdatedAt          time.Time           `json:"updated_at"`
}

type CaseObjectionStatus struct {
	Possible          *bool
	NotPossibleReason *string
	ObjectionPeriod   *int
	DecisionPeriod    *int
	ExtensionPeriod   *int
	Admissable        *bool
}

type CaseAppealStatus struct {
	Possible           *bool
	NotPossibleReason  *string
	AppealPeriod       *int
	DirectAppeal       *bool
	DirectAppealReason *string
	CompetentCourt     *string
	CourtType          *string
}

// NewCase creates a new Case
func NewCase(
	bsn string,
	service string,
	law string,
	parameters map[string]any,
	claimedResult map[string]any,
	verifiedResult map[string]any,
	rulespecUUID uuid.UUID,
	approvedClaimsOnly bool,
) *Case {
	now := time.Now()
	return &Case{
		ID:                 uuid.New(),
		Version:            0,
		BSN:                bsn,
		Service:            service,
		Law:                law,
		RulespecID:         rulespecUUID,
		ApprovedClaimsOnly: approvedClaimsOnly,
		ClaimedResult:      claimedResult,
		VerifiedResult:     verifiedResult,
		Parameters:         parameters,
		Status:             CaseStatusSubmitted,
		CreatedAt:          now,
		UpdatedAt:          now,
	}
}

// EntityID implements the EntityID method of the eventhorizon.Entity interface.
func (c *Case) EntityID() uuid.UUID {
	return c.ID
}

// AggregateVersion implements the AggregateVersion method of the
// eventhorizon.Versionable interface.
func (c *Case) AggregateVersion() int {
	return c.Version
}

// Reset resets a case with new parameters and results
func (c *Case) Reset(
	parameters map[string]any,
	claimedResult map[string]any,
	verifiedResult map[string]any,
	approvedClaimsOnly bool,
) error {
	c.ApprovedClaimsOnly = approvedClaimsOnly
	c.ClaimedResult = claimedResult
	c.VerifiedResult = verifiedResult
	c.Parameters = parameters
	c.DisputedParameters = nil
	c.Evidence = ""
	c.Reason = ""
	c.VerifierID = ""
	c.Status = CaseStatusSubmitted
	c.Approved = nil
	c.UpdatedAt = time.Now()
	return nil
}

// DecideAutomatically approves or rejects a case automatically
func (c *Case) DecideAutomatically(
	verifiedResult map[string]any,
	parameters map[string]any,
	approved bool,
) error {
	if c.Status != CaseStatusSubmitted && c.Status != CaseStatusObjected {
		return fmt.Errorf("can only automatically decide on submitted cases or objections")
	}

	c.VerifiedResult = verifiedResult
	c.Parameters = parameters
	c.Status = CaseStatusDecided
	c.Approved = &approved
	c.UpdatedAt = time.Now()
	return nil
}

// SelectForManualReview marks a case for manual review
func (c *Case) SelectForManualReview(
	verifierID string,
	reason string,
	claimedResult map[string]any,
	verifiedResult map[string]any,
) error {
	if c.Status != CaseStatusSubmitted && c.Status != CaseStatusObjected {
		return fmt.Errorf("can only add to review from submitted status or objection")
	}

	c.Status = CaseStatusInReview
	c.VerifiedResult = verifiedResult
	c.ClaimedResult = claimedResult
	c.Reason = reason
	c.VerifierID = verifierID
	c.UpdatedAt = time.Now()
	return nil
}

// Decide makes a manual decision on a case
func (c *Case) Decide(
	verifiedResult map[string]any,
	reason string,
	verifierID string,
	approved bool,
) error {
	if c.Status != CaseStatusInReview && c.Status != CaseStatusObjected {
		return fmt.Errorf("can only manually decide on cases in review or objections")
	}

	c.Status = CaseStatusDecided
	c.Approved = &approved
	c.Reason = reason
	c.VerifiedResult = verifiedResult
	c.VerifierID = verifierID
	c.UpdatedAt = time.Now()

	return nil
}

// Object files an objection against a case
func (c *Case) Object(reason string) error {
	if c.Status != CaseStatusDecided {
		return fmt.Errorf("can only object to decided cases")
	}

	c.Status = CaseStatusObjected
	c.Reason = reason
	c.UpdatedAt = time.Now()

	return nil
}

// DetermineObjectionStatus sets objection status and parameters
func (c *Case) DetermineObjectionStatus(
	possible *bool,
	notPossibleReason *string,
	objectionPeriod *int,
	decisionPeriod *int,
	extensionPeriod *int,
) error {
	if possible != nil {
		c.ObjectionStatus.Possible = possible
	}

	if notPossibleReason != nil {
		c.ObjectionStatus.NotPossibleReason = notPossibleReason
	}

	if objectionPeriod != nil {
		c.ObjectionStatus.ObjectionPeriod = objectionPeriod
	}

	if decisionPeriod != nil {
		c.ObjectionStatus.DecisionPeriod = decisionPeriod
	}

	if extensionPeriod != nil {
		c.ObjectionStatus.ExtensionPeriod = extensionPeriod
	}

	c.UpdatedAt = time.Now()
	return nil
}

// DetermineObjectionAdmissibility determines whether an objection is admissible
func (c *Case) DetermineObjectionAdmissibility(admissible *bool) error {

	if admissible != nil {
		c.ObjectionStatus.Admissable = admissible
	}

	c.UpdatedAt = time.Now()
	return nil
}

// CanObject checks if objection is possible for this case
func (c *Case) CanObject() bool {
	return c.ObjectionStatus.Possible != nil && *c.ObjectionStatus.Possible
}

// DetermineAppealStatus sets appeal status and parameters
func (c *Case) DetermineAppealStatus(
	possible *bool,
	notPossibleReason *string,
	appealPeriod *int,
	directAppeal *bool,
	directAppealReason *string,
	competentCourt *string,
	courtType *string,
) error {
	c.AppealStatus.Possible = possible
	c.AppealStatus.NotPossibleReason = notPossibleReason
	c.AppealStatus.AppealPeriod = appealPeriod
	c.AppealStatus.DirectAppeal = directAppeal
	c.AppealStatus.DirectAppealReason = directAppealReason
	c.AppealStatus.CompetentCourt = competentCourt
	c.AppealStatus.CourtType = courtType
	c.UpdatedAt = time.Now()

	return nil
}

// CanAppeal checks if appeal is possible for this case
func (c *Case) CanAppeal() bool {
	if c.AppealStatus.Possible != nil {
		return *c.AppealStatus.Possible
	}

	return false
}

// AddClaim records when a new claim is created for this case
func (c *Case) AddClaim(claimID uuid.UUID) error {
	if c.ClaimIDs == nil {
		c.ClaimIDs = make([]uuid.UUID, 0)
	}

	// Check if claim already exists
	for _, id := range c.ClaimIDs {
		if id == claimID {
			return nil
		}
	}

	c.ClaimIDs = append(c.ClaimIDs, claimID)
	c.UpdatedAt = time.Now()
	return nil
}

// ApproveOrRejectClaim records when a claim is approved or rejected
func (c *Case) ApproveOrRejectClaim(claimID uuid.UUID) error {
	if c.ClaimIDs == nil {
		c.ClaimIDs = make([]uuid.UUID, 0)
	}

	// Check if claim already exists
	for _, id := range c.ClaimIDs {
		if id == claimID {
			return nil
		}
	}

	c.ClaimIDs = append(c.ClaimIDs, claimID)
	c.UpdatedAt = time.Now()
	return nil
}
