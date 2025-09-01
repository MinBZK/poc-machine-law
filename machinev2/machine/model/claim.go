package model

import (
	"fmt"
	"time"

	"github.com/google/uuid"
)

// ClaimStatus represents the status of a claim
type ClaimStatus string

const (
	// ClaimStatusPending indicates a pending claim
	ClaimStatusPending ClaimStatus = "PENDING"

	// ClaimStatusApproved indicates an approved claim
	ClaimStatusApproved ClaimStatus = "APPROVED"

	// ClaimStatusRejected indicates a rejected claim
	ClaimStatusRejected ClaimStatus = "REJECTED"
)

// Claim represents a claim for data modification
type Claim struct {
	ID              uuid.UUID   `json:"id"`
	Service         string      `json:"service"`
	Key             string      `json:"key"`
	OldValue        any         `json:"old_value,omitempty"`
	NewValue        any         `json:"new_value"`
	Reason          string      `json:"reason"`
	EvidencePath    string      `json:"evidence_path,omitempty"`
	Claimant        string      `json:"claimant"`
	CaseID          uuid.UUID   `json:"case_id,omitempty"`
	Law             string      `json:"law"`
	BSN             string      `json:"bsn"`
	Status          ClaimStatus `json:"status"`
	CreatedAt       time.Time   `json:"created_at"`
	VerifiedBy      string      `json:"verified_by,omitempty"`
	VerifiedValue   any         `json:"verified_value,omitempty"`
	VerifiedAt      *time.Time  `json:"verified_at,omitempty"`
	RejectedBy      string      `json:"rejected_by,omitempty"`
	RejectionReason string      `json:"rejection_reason,omitempty"`
	RejectedAt      *time.Time  `json:"rejected_at,omitempty"`
}

type ClaimRejection struct {
	By     string
	Reason string
}

type ClaimVerification struct {
	By    string
	Value any
}

type ClaimCreate struct {
	Service      string
	Law          string
	Key          string
	OldValue     any
	NewValue     any
	Reason       string
	Claimant     string
	BSN          string
	CaseID       *uuid.UUID
	EvidencePath string
	AutoApprove  bool
}

// NewClaim creates a new Claim
func NewClaim(
	service string,
	key string,
	newValue any,
	reason string,
	claimant string,
	law string,
	bsn string,
	caseID uuid.UUID,
	oldValue any,
	evidencePath string,
) *Claim {
	return &Claim{
		ID:           uuid.New(),
		Service:      service,
		Key:          key,
		OldValue:     oldValue,
		NewValue:     newValue,
		Reason:       reason,
		EvidencePath: evidencePath,
		Claimant:     claimant,
		CaseID:       caseID,
		Law:          law,
		BSN:          bsn,
		Status:       ClaimStatusPending,
		CreatedAt:    time.Now(),
	}
}

// Reset resets a claim with new values
func (c *Claim) Reset(
	service string,
	key string,
	newValue any,
	reason string,
	claimant string,
	law string,
	bsn string,
	caseID uuid.UUID,
	oldValue any,
	evidencePath string,
) {
	c.Service = service
	c.Key = key
	c.OldValue = oldValue
	c.NewValue = newValue
	c.Reason = reason
	c.EvidencePath = evidencePath
	c.Claimant = claimant
	c.CaseID = caseID
	c.Law = law
	c.BSN = bsn
	c.Status = ClaimStatusPending
	c.CreatedAt = time.Now()

	// Reset approval/rejection fields
	c.VerifiedBy = ""
	c.VerifiedValue = nil
	c.VerifiedAt = nil
	c.RejectedBy = ""
	c.RejectionReason = ""
	c.RejectedAt = nil
}

// AutoApprove automatically approves a claim
func (c *Claim) AutoApprove(verifiedBy string, verifiedValue any) error {
	c.Status = ClaimStatusApproved
	c.VerifiedBy = verifiedBy
	c.VerifiedValue = verifiedValue
	now := time.Now()
	c.VerifiedAt = &now
	return nil
}

// Approve approves a claim
func (c *Claim) Approve(verifiedBy string, verifiedValue any) error {
	c.Status = ClaimStatusApproved
	c.VerifiedBy = verifiedBy
	c.VerifiedValue = verifiedValue
	now := time.Now()
	c.VerifiedAt = &now
	return nil
}

// Reject rejects a claim
func (c *Claim) Reject(rejectedBy string, rejectionReason string) error {
	c.Status = ClaimStatusRejected
	c.RejectedBy = rejectedBy
	c.RejectionReason = rejectionReason
	now := time.Now()
	c.RejectedAt = &now
	return nil
}

// LinkCase links a claim to a case
func (c *Claim) LinkCase(caseID uuid.UUID) error {
	if c.CaseID != uuid.Nil {
		return fmt.Errorf("claim is already linked to a case")
	}

	c.CaseID = caseID

	return nil
}

// AddEvidence adds evidence to a claim
func (c *Claim) AddEvidence(evidencePath string) error {
	if c.Status != ClaimStatusPending {
		return fmt.Errorf("can only add evidence to pending claims")
	}
	c.EvidencePath = evidencePath
	return nil
}
