package model

import (
	"errors"

	"github.com/google/uuid"
)

var ErrCaseNotFound = errors.New("case_not_found")

type Case struct {
	ID                 uuid.UUID
	Service            string
	Law                string
	BSN                string
	Status             string
	Approved           *bool
	ApprovedClaimsOnly bool
	ClaimedResult      map[string]any
	VerifiedResult     map[string]any
	Parameters         map[string]any
	RuleSpecID         uuid.UUID
	AppealStatus       *map[string]any
	ObjectionStatus    CaseObjectionStatus
}

type CaseObjectionStatus struct {
	Possible          *bool
	NotPossibleReason *string
	ObjectionPeriod   *int
	DecisionPeriod    *int
	ExtensionPeriod   *int
	Admissable        *bool
}

type CaseSubmit struct {
	BSN                string
	Service            string
	Law                string
	ApprovedClaimsOnly bool
	ClaimedResult      map[string]any
	Parameters         map[string]any
}

type CaseReview struct {
	CaseID     uuid.UUID
	VerifierID string
	Approved   bool
	Reason     string
}

type CaseObject struct {
	CaseID uuid.UUID
	Reason string
}
