package model

import (
	"fmt"
	"time"

	"github.com/google/uuid"
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

// Case represents a service case
type Case struct {
	ID                 string                 `json:"id"`
	ClaimIDs           []string               `json:"claim_ids,omitempty"`
	BSN                string                 `json:"bsn"`
	Service            string                 `json:"service"`
	Law                string                 `json:"law"`
	RulespecUUID       string                 `json:"rulespec_uuid"`
	ApprovedClaimsOnly bool                   `json:"approved_claims_only"`
	ClaimedResult      map[string]interface{} `json:"claimed_result"`
	VerifiedResult     map[string]interface{} `json:"verified_result"`
	Parameters         map[string]interface{} `json:"parameters"`
	DisputedParameters map[string]interface{} `json:"disputed_parameters,omitempty"`
	Evidence           string                 `json:"evidence,omitempty"`
	Reason             string                 `json:"reason,omitempty"`
	VerifierID         string                 `json:"verifier_id,omitempty"`
	ObjectionStatus    map[string]interface{} `json:"objection_status,omitempty"`
	AppealStatus       map[string]interface{} `json:"appeal_status,omitempty"`
	Approved           *bool                  `json:"approved,omitempty"`
	Status             CaseStatus             `json:"status"`
	CreatedAt          time.Time              `json:"created_at"`
	UpdatedAt          time.Time              `json:"updated_at"`
}

// NewCase creates a new Case
func NewCase(
	bsn string,
	service string,
	law string,
	parameters map[string]interface{},
	claimedResult map[string]interface{},
	verifiedResult map[string]interface{},
	rulespecUUID string,
	approvedClaimsOnly bool,
) *Case {
	now := time.Now()
	return &Case{
		ID:                 uuid.New().String(),
		BSN:                bsn,
		Service:            service,
		Law:                law,
		RulespecUUID:       rulespecUUID,
		ApprovedClaimsOnly: approvedClaimsOnly,
		ClaimedResult:      claimedResult,
		VerifiedResult:     verifiedResult,
		Parameters:         parameters,
		Status:             CaseStatusSubmitted,
		CreatedAt:          now,
		UpdatedAt:          now,
	}
}

// Reset resets a case with new parameters and results
func (c *Case) Reset(
	parameters map[string]interface{},
	claimedResult map[string]interface{},
	verifiedResult map[string]interface{},
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
	verifiedResult map[string]interface{},
	parameters map[string]interface{},
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
	claimedResult map[string]interface{},
	verifiedResult map[string]interface{},
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
	verifiedResult map[string]interface{},
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
	notPossibleReason string,
	objectionPeriod *int,
	decisionPeriod *int,
	extensionPeriod *int,
) error {
	if c.ObjectionStatus == nil {
		c.ObjectionStatus = make(map[string]interface{})
	}

	if possible != nil {
		c.ObjectionStatus["possible"] = *possible
	}

	if notPossibleReason != "" {
		c.ObjectionStatus["not_possible_reason"] = notPossibleReason
	}

	if objectionPeriod != nil {
		c.ObjectionStatus["objection_period"] = *objectionPeriod
	}

	if decisionPeriod != nil {
		c.ObjectionStatus["decision_period"] = *decisionPeriod
	}

	if extensionPeriod != nil {
		c.ObjectionStatus["extension_period"] = *extensionPeriod
	}

	c.UpdatedAt = time.Now()
	return nil
}

// DetermineObjectionAdmissibility determines whether an objection is admissible
func (c *Case) DetermineObjectionAdmissibility(admissible *bool) error {
	if c.ObjectionStatus == nil {
		c.ObjectionStatus = make(map[string]interface{})
	}

	if admissible != nil {
		c.ObjectionStatus["admissible"] = *admissible
	}

	c.UpdatedAt = time.Now()
	return nil
}

// CanObject checks if objection is possible for this case
func (c *Case) CanObject() bool {
	if c.ObjectionStatus == nil {
		return false
	}

	possible, ok := c.ObjectionStatus["possible"].(bool)
	return ok && possible
}

// DetermineAppealStatus sets appeal status and parameters
func (c *Case) DetermineAppealStatus(
	possible *bool,
	notPossibleReason string,
	appealPeriod *int,
	directAppeal *bool,
	directAppealReason string,
	competentCourt string,
	courtType string,
) error {
	if c.AppealStatus == nil {
		c.AppealStatus = make(map[string]interface{})
	}

	if possible != nil {
		c.AppealStatus["possible"] = *possible
	}

	if notPossibleReason != "" {
		c.AppealStatus["not_possible_reason"] = notPossibleReason
	}

	if appealPeriod != nil {
		c.AppealStatus["appeal_period"] = *appealPeriod
	}

	if directAppeal != nil {
		c.AppealStatus["direct_appeal"] = *directAppeal
	}

	if directAppealReason != "" {
		c.AppealStatus["direct_appeal_reason"] = directAppealReason
	}

	if competentCourt != "" {
		c.AppealStatus["competent_court"] = competentCourt
	}

	if courtType != "" {
		c.AppealStatus["court_type"] = courtType
	}

	c.UpdatedAt = time.Now()
	return nil
}

// CanAppeal checks if appeal is possible for this case
func (c *Case) CanAppeal() bool {
	if c.AppealStatus == nil {
		return false
	}

	possible, ok := c.AppealStatus["possible"].(bool)
	return ok && possible
}

// AddClaim records when a new claim is created for this case
func (c *Case) AddClaim(claimID string) error {
	if c.ClaimIDs == nil {
		c.ClaimIDs = make([]string, 0)
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
func (c *Case) ApproveOrRejectClaim(claimID string) error {
	if c.ClaimIDs == nil {
		c.ClaimIDs = make([]string, 0)
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
