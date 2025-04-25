package service

import (
	"context"
	"fmt"
	"sync"

	"github.com/looplab/eventhorizon/uuid"
	"github.com/minbzk/poc-machine-law/machinev2/machine/casemanager"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
)

// ClaimManager manages claims against services
type ClaimManager struct {
	Services           *Services
	CaseManager        *CaseManager
	serviceIndex       map[string][]uuid.UUID            // service -> [claim_ids]
	caseIndex          map[uuid.UUID][]uuid.UUID         // case_id -> [claim_ids]
	claimantIndex      map[string][]uuid.UUID            // claimant -> [claim_ids]
	bsnIndex           map[string][]uuid.UUID            // bsn -> [claim_ids]
	statusIndex        map[model.ClaimStatus][]uuid.UUID // status -> [claim_ids]
	bsnServiceLawIndex map[string]map[string]uuid.UUID   // "bsn:service:law" -> (key -> claim_id)
	claims             map[uuid.UUID]*model.Claim
	mu                 sync.RWMutex
}

// NewClaimManager creates a new claim manager
func NewClaimManager(services *Services) *ClaimManager {
	return &ClaimManager{
		Services:           services,
		serviceIndex:       make(map[string][]uuid.UUID),
		caseIndex:          make(map[uuid.UUID][]uuid.UUID),
		claimantIndex:      make(map[string][]uuid.UUID),
		bsnIndex:           make(map[string][]uuid.UUID),
		statusIndex:        make(map[model.ClaimStatus][]uuid.UUID),
		bsnServiceLawIndex: make(map[string]map[string]uuid.UUID),
		claims:             make(map[uuid.UUID]*model.Claim),
	}
}

// indexClaim adds a claim to all indexes
func (cm *ClaimManager) indexClaim(claim *model.Claim) {
	claimID := claim.ID

	// Service index
	cm.serviceIndex[claim.Service] = append(cm.serviceIndex[claim.Service], claimID)

	// Case index (if applicable)
	if claim.CaseID == uuid.Nil {
		cm.caseIndex[claim.CaseID] = append(cm.caseIndex[claim.CaseID], claimID)
	}

	// Claimant index
	cm.claimantIndex[claim.Claimant] = append(cm.claimantIndex[claim.Claimant], claimID)

	// BSN index
	cm.bsnIndex[claim.BSN] = append(cm.bsnIndex[claim.BSN], claimID)

	// Status index
	cm.statusIndex[claim.Status] = append(cm.statusIndex[claim.Status], claimID)

	// BSN-Service-Law index
	bslKey := fmt.Sprintf("%s:%s:%s", claim.BSN, claim.Service, claim.Law)
	if _, exists := cm.bsnServiceLawIndex[bslKey]; !exists {
		cm.bsnServiceLawIndex[bslKey] = make(map[string]uuid.UUID)
	}
	cm.bsnServiceLawIndex[bslKey][claim.Key] = claimID
}

// SubmitClaim submits a new claim
func (cm *ClaimManager) SubmitClaim(
	ctx context.Context,
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
	autoApprove bool,
) (uuid.UUID, error) {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	// Check for existing claim
	var claim *model.Claim
	bslKey := fmt.Sprintf("%s:%s:%s", bsn, service, law)

	if keyMap, exists := cm.bsnServiceLawIndex[bslKey]; exists {
		if claimID, exists := keyMap[key]; exists {
			claim = cm.claims[claimID]

			// Reset existing claim
			claim.Reset(
				service,
				key,
				newValue,
				reason,
				claimant,
				law,
				bsn,
				caseID,
				oldValue,
				evidencePath,
			)
		}
	}

	// Create new claim if none exists
	if claim == nil {
		claim = model.NewClaim(
			service,
			key,
			newValue,
			reason,
			claimant,
			law,
			bsn,
			caseID,
			oldValue,
			evidencePath,
		)

		// Add to maps and indexes
		cm.claims[claim.ID] = claim
		cm.indexClaim(claim)
	}

	// Link to case if provided
	var case_ *casemanager.Case
	if caseID != uuid.Nil {
		var err error
		case_, err = cm.CaseManager.GetCaseByID(ctx, caseID)
		if err == nil && case_ != nil {
			err = case_.AddClaim(claim.ID)
			if err != nil {
				return uuid.Nil, err
			}
		}
	}

	// Auto-approve if requested
	if autoApprove {
		err := claim.AutoApprove(claimant, newValue)
		if err != nil {
			return uuid.Nil, err
		}

		if case_ != nil {
			err = case_.ApproveOrRejectClaim(claim.ID)
			if err != nil {
				return uuid.Nil, err
			}
		}
	}

	return claim.ID, nil
}

// ApproveClaim approves a claim with verified value
func (cm *ClaimManager) ApproveClaim(ctx context.Context, claimID uuid.UUID, verifiedBy string, verifiedValue any) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	claim, err := cm.GetClaim(claimID)
	if err != nil {
		return err
	}

	err = claim.Approve(verifiedBy, verifiedValue)
	if err != nil {
		return err
	}

	if claim.CaseID != uuid.Nil {
		case_, err := cm.CaseManager.GetCaseByID(ctx, claim.CaseID)
		if err == nil && case_ != nil {
			err = case_.ApproveOrRejectClaim(claim.ID)
			if err != nil {
				return err
			}
		}
	}

	return nil
}

// RejectClaim rejects a claim with reason
func (cm *ClaimManager) RejectClaim(ctx context.Context, claimID uuid.UUID, rejectedBy, rejectionReason string) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	claim, err := cm.GetClaim(claimID)
	if err != nil {
		return err
	}

	err = claim.Reject(rejectedBy, rejectionReason)
	if err != nil {
		return err
	}

	if claim.CaseID != uuid.Nil {
		case_, err := cm.CaseManager.GetCaseByID(ctx, claim.CaseID)
		if err == nil && case_ != nil {
			err = case_.ApproveOrRejectClaim(claim.ID)
			if err != nil {
				return err
			}
		}
	}

	return nil
}

// LinkCase links an existing claim to a case
func (cm *ClaimManager) LinkCase(claimID uuid.UUID, caseID uuid.UUID) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	claim, err := cm.GetClaim(claimID)
	if err != nil {
		return err
	}

	err = claim.LinkCase(caseID)
	if err != nil {
		return err
	}

	// Update case index
	cm.caseIndex[caseID] = append(cm.caseIndex[caseID], claimID)

	return nil
}

// AddEvidence adds evidence to an existing claim
func (cm *ClaimManager) AddEvidence(claimID uuid.UUID, evidencePath string) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	claim, err := cm.GetClaim(claimID)
	if err != nil {
		return err
	}

	return claim.AddEvidence(evidencePath)
}

// GetClaim gets a claim by ID
func (cm *ClaimManager) GetClaim(claimID uuid.UUID) (*model.Claim, error) {
	if claimID == uuid.Nil {
		return nil, fmt.Errorf("claim ID cannot be empty")
	}

	claim, exists := cm.claims[claimID]
	if !exists {
		return nil, fmt.Errorf("claim not found: %s", claimID)
	}

	return claim, nil
}

// filterClaimsByStatus filters claims based on status parameters
func (cm *ClaimManager) filterClaimsByStatus(
	claims []model.Claim,
	approved bool,
	includeRejected bool,
) []model.Claim {
	var result []model.Claim

	for _, claim := range claims {
		if approved {
			// Only return approved claims
			if claim.Status == model.ClaimStatusApproved {
				result = append(result, claim)
			}
		} else {
			// Return approved and pending claims
			if claim.Status == model.ClaimStatusApproved ||
				claim.Status == model.ClaimStatusPending ||
				(includeRejected && claim.Status == model.ClaimStatusRejected) {
				result = append(result, claim)
			}
		}
	}

	return result
}

// GetClaimsByService gets all claims for a service
func (cm *ClaimManager) GetClaimsByService(
	service string,
	approved bool,
	includeRejected bool,
) ([]model.Claim, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	var claims []model.Claim

	for _, claimID := range cm.serviceIndex[service] {
		if claim, exists := cm.claims[claimID]; exists {
			claims = append(claims, *claim)
		}
	}

	return cm.filterClaimsByStatus(claims, approved, includeRejected), nil
}

// GetClaimsByCase gets all claims for a case
func (cm *ClaimManager) GetClaimsByCase(
	caseID uuid.UUID,
	approved bool,
	includeRejected bool,
) ([]model.Claim, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	var claims []model.Claim

	for _, claimID := range cm.caseIndex[caseID] {
		if claim, exists := cm.claims[claimID]; exists {
			claims = append(claims, *claim)
		}
	}

	return cm.filterClaimsByStatus(claims, approved, includeRejected), nil
}

// GetClaimsByClaimant gets all claims by a claimant
func (cm *ClaimManager) GetClaimsByClaimant(
	claimant string,
	approved bool,
	includeRejected bool,
) ([]model.Claim, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	var claims []model.Claim

	for _, claimID := range cm.claimantIndex[claimant] {
		if claim, exists := cm.claims[claimID]; exists {
			claims = append(claims, *claim)
		}
	}

	return cm.filterClaimsByStatus(claims, approved, includeRejected), nil
}

// GetClaimsByBSN gets all claims for a BSN
func (cm *ClaimManager) GetClaimsByBSN(
	bsn string,
	approved bool,
	includeRejected bool,
) ([]model.Claim, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	var claims []model.Claim

	for _, claimID := range cm.bsnIndex[bsn] {
		if claim, exists := cm.claims[claimID]; exists {
			claims = append(claims, *claim)
		}
	}

	return cm.filterClaimsByStatus(claims, approved, includeRejected), nil
}

// GetClaimByBSNServiceLaw gets claims for a BSN, service, and law combination
func (cm *ClaimManager) GetClaimByBSNServiceLaw(
	bsn string,
	service string,
	law string,
	approved bool,
	includeRejected bool,
) (map[string]model.Claim, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	bslKey := fmt.Sprintf("%s:%s:%s", bsn, service, law)
	keyMap, exists := cm.bsnServiceLawIndex[bslKey]
	if !exists {
		return nil, nil
	}

	result := make(map[string]model.Claim)

	for key, claimID := range keyMap {
		if claim, exists := cm.claims[claimID]; exists {
			// Filter by status
			if approved && claim.Status != model.ClaimStatusApproved {
				continue
			}

			if !approved && claim.Status == model.ClaimStatusRejected && !includeRejected {
				continue
			}

			result[key] = *claim
		}
	}

	if len(result) == 0 {
		return nil, nil
	}

	return result, nil
}
