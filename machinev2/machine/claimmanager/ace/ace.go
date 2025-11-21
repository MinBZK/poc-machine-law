package ace

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/Khan/genqlient/graphql"
	"github.com/google/uuid"
	"github.com/minbzk/poc-machine-law/machinev2/machine/claimmanager"
	"github.com/minbzk/poc-machine-law/machinev2/machine/claimmanager/ace/generated"
	"github.com/minbzk/poc-machine-law/machinev2/machine/logger"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
)

// ClaimManager implements the claimmanager interface using ACE
type ClaimManager struct {
	logger       logger.Logger
	clients      clients
	claimTypes   claimTypes
	ruleResolver *ruleresolver.RuleResolve
	service      string
}

type clients struct {
	dml graphql.Client
	ddl graphql.Client
	grp graphql.Client
}

type claimTypes map[string][]claimType
type claimType struct {
	Name           string
	ReferencedName string
	ReferencedType string
}

// New creates a new ACE-backed claim manager
func New(service string, ruleResolver *ruleresolver.RuleResolve, endpoint string, logger logger.Logger) (claimmanager.ClaimManager, error) {
	clients := clients{
		dml: graphql.NewClient(endpoint+"/gql/dml/v0", http.DefaultClient),
		ddl: graphql.NewClient(endpoint+"/gql/ddl/v0", http.DefaultClient),
		grp: graphql.NewClient(endpoint+"/gql/grp/v0", http.DefaultClient),
	}

	claimTypes, err := getClaimTypes(clients.ddl)
	if err != nil {
		return nil, fmt.Errorf("could not get claim types: %w", err)
	}

	return &ClaimManager{
		logger:       logger,
		clients:      clients,
		claimTypes:   claimTypes,
		ruleResolver: ruleResolver,
		service:      service,
	}, nil
}

func getClaimTypes(client graphql.Client) (claimTypes, error) {
	data, err := generated.GetClaimTypes(context.Background(), client)
	if err != nil {
		return nil, nil
	}

	claimTypes := claimTypes{}

	for _, ctype := range data.ClaimTypes {
		name := *ctype.Name
		claimTypes[name] = make([]claimType, 0, len(ctype.Roles))

		for _, role := range ctype.Roles {
			claimTypes[name] = append(claimTypes[name], claimType{
				Name:           *role.Name,
				ReferencedName: *role.ReferencedName,
				ReferencedType: string(*role.ReferencedType),
			})
		}
	}

	return claimTypes, nil
}

// Submit submits a new claim to ACE
func (cm *ClaimManager) Submit(
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
	effectiveDate time.Time,
) (uuid.UUID, error) {
	// Create internal claim
	claim := model.NewClaim(service, key, newValue, reason, claimant, law, bsn, caseID, oldValue, evidencePath)
	key = cm.convertOutputToSourceField(key, service, law)

	if err := cm.transaction(ctx, func(ctx context.Context, txID string) error {
		// Get or create BSN claim
		bsnID, err := cm.getBSN(ctx, &txID, bsn)
		if err != nil {
			return fmt.Errorf("get BSN: %w", err)
		}

		beweringID, err := cm.addBewering(ctx, txID, bsnID, reason, law, key, effectiveDate)
		if err != nil {
			return fmt.Errorf("add bewering: %w", err)
		}

		// Add BeweringStatus as "PENDING"
		if err := cm.addBeweringStatus(ctx, txID, beweringID, "PENDING", &effectiveDate); err != nil {
			return fmt.Errorf("add bewering status: %w", err)
		}

		// Create proposed value in ACE
		claimTypeName := cm.normalizeClaimType(key) + "Proposed"
		proposedID, err := cm.createACEClaim(ctx, txID, claimTypeName, bsnID, newValue, &effectiveDate)
		if err != nil {
			return fmt.Errorf("create proposed claim: %w", err)
		}

		if err = cm.AddBeweringProposed(ctx, txID, beweringID, proposedID, &effectiveDate); err != nil {
			return fmt.Errorf("add bewering proposed: %w", err)
		}

		// Link proposed value to Bewering
		if oldValue != nil {
			// var originalID string
			// // If there's an old value, we would need to find its ACE ID
			// // For now, we'll leave it as nil
			// _, err = generated.AddBeweringOriginal(ctx, cm.clients.dml, &txID, beweringID, originalID)
			// if err != nil {
			// 	return uuid.Nil, fmt.Errorf("add bewering referentie: %w", err)
			// }
		}

		// Auto-approve if requested
		if autoApprove {
			err = cm.approveInTransaction(ctx, txID, claim.ID, newValue, claimant, bsnID, effectiveDate)
			if err != nil {
				return fmt.Errorf("auto-approve: %w", err)
			}
		}

		return nil
	}); err != nil {
		return uuid.Nil, err
	}

	return claim.ID, nil
}

// Approve approves a claim
func (cm *ClaimManager) Approve(ctx context.Context, claimID uuid.UUID, verification model.ClaimVerification) error {
	if err := cm.transaction(ctx, func(ctx context.Context, txID string) error {
		bewering, err := cm.get(ctx, &txID, claimID)
		if err != nil {
			return fmt.Errorf("get bewering: %w", err)
		}

		if err := cm.approveInTransaction(ctx, txID, bewering.ID, verification.Value, verification.By, bewering.BSN, time.Now()); err != nil {
			return err
		}

		return nil
	}); err != nil {
		return err
	}

	return nil
}

// Reject rejects a claim
func (cm *ClaimManager) Reject(ctx context.Context, claimID uuid.UUID, rejection model.ClaimRejection) error {
	return cm.transaction(ctx, func(ctx context.Context, txID string) error {
		if err := cm.addBeweringStatus(ctx, txID, claimID, "REJECTED", nil); err != nil {
			return fmt.Errorf("update bewering status: %w", err)
		}

		return nil
	})
}

// AddEvidence adds evidence to a claim
func (cm *ClaimManager) AddEvidence(ctx context.Context, claimID uuid.UUID, evidence string) error {
	return cm.transaction(ctx, func(ctx context.Context, txID string) error {
		if err := cm.addBeweringEvidencePath(ctx, txID, claimID, evidence); err != nil {
			return fmt.Errorf("add bewering evidence path: %w", err)
		}

		return nil
	})

}

// LinkCase links a claim to a case
func (cm *ClaimManager) LinkCase(ctx context.Context, claimID uuid.UUID, caseID uuid.UUID) error {
	return cm.transaction(ctx, func(ctx context.Context, txID string) error {
		if err := cm.addBeweringCase(ctx, txID, claimID, caseID); err != nil {
			return fmt.Errorf("add bewering case: %w", err)
		}

		return nil
	})
}

func (cm *ClaimManager) Get(ctx context.Context, claimID uuid.UUID) (*model.Claim, error) {
	return cm.get(ctx, nil, claimID)
}

// Get retrieves a claim by ID
func (cm *ClaimManager) get(ctx context.Context, txID *string, claimID uuid.UUID) (*model.Claim, error) {
	claim, err := generated.ClaimAttributesByClaimID(ctx, cm.clients.grp, txID, claimID.String(), time.Now())
	if err != nil {
		return nil, fmt.Errorf("get claims bewering: %w", err)
	}

	if claim.ClaimAttributesByClaimID == nil {
		return nil, ErrBeweringNotFound
	}

	bewering := claim.ClaimAttributesByClaimID

	m := &model.Claim{
		ID:      claimID,
		Service: cm.service,
	}

	for _, value := range bewering.Values {
		switch *value.Key {
		case "key":
			m.Key = *value.Value
		case "law":
			m.Law = *value.Value
		case "Bsn":
			m.BSN = *value.Value
		case "reason":
			m.Reason = *value.Value
		}
	}

	m.Key = cm.convertSourceToOutputField(m.Key, cm.service, m.Law)

	for _, value := range bewering.Subvalues {
		switch value.Name {
		case "Bewering/Status":
			m.Status = model.ClaimStatus(*value.Values[0].Value)
		}
	}

	response, err := generated.GetClaimsBeweringProposed(ctx, cm.clients.dml, txID, claimID.String())
	if err != nil {
		return nil, fmt.Errorf("get claims bewering proposed: %w", err)
	}

	proposedClaims := response.GetClaimsBeweringProposed

	for _, v := range proposedClaims {
		claim, err := generated.ClaimAttributesByClaimID(ctx, cm.clients.grp, txID, *v.Roles.Proposed, time.Now())
		if err != nil {
			return nil, fmt.Errorf("get claims bewering: %w", err)
		}

		for _, value := range claim.ClaimAttributesByClaimID.Values {
			if *value.Key == "amountEurocent" {
				m.NewValue, _ = strconv.Atoi(*value.Value)
			}
		}
	}

	return m, nil
}

// GetClaimsByService retrieves claims by service
func (cm *ClaimManager) GetClaimsByService(ctx context.Context, service string, approved bool, includeRejected bool) ([]model.Claim, error) {
	panic("unimplemented")
}

// GetClaimsByCase retrieves claims by case
func (cm *ClaimManager) GetClaimsByCase(ctx context.Context, caseID uuid.UUID, approved bool, includeRejected bool) ([]model.Claim, error) {
	panic("unimplemented")
}

// GetClaimsByClaimant retrieves claims by claimant
func (cm *ClaimManager) GetClaimsByClaimant(ctx context.Context, claimant string, approved bool, includeRejected bool) ([]model.Claim, error) {
	panic("unimplemented")
}

// GetClaimsByBSN retrieves claims by BSN
func (cm *ClaimManager) GetClaimsByBSN(ctx context.Context, bsn string, approved bool, includeRejected bool) ([]model.Claim, error) {
	log := cm.logger.WithFields(logger.NewField("bsn", bsn), logger.NewField("approved", approved), logger.NewField("include rejected", includeRejected))
	log.Info("GetClaimsByBSN")

	bsnID, err := cm.getBSN(ctx, nil, bsn)
	if err != nil {
		return nil, fmt.Errorf("get bsn: %w", err)
	}

	beweringIDs, err := generated.GetBeweringOnBsn(ctx, cm.clients.dml, bsnID)
	if err != nil {
		return nil, fmt.Errorf("get bewering on bsn: %w", err)
	}

	beweringen := make([]model.Claim, 0)

	for _, v := range beweringIDs.GetClaimsBewering {
		bewering, err := cm.get(ctx, nil, uuid.MustParse(*v.Id))
		if err != nil {
			return nil, fmt.Errorf("get bewering: %w", err)
		}

		if cm.matchesStatusFilter(bewering, approved, includeRejected) {
			beweringen = append(beweringen, *bewering)
		}
	}

	return beweringen, nil
}

// GetClaimByBSNServiceLaw retrieves claims by BSN, service, and law
func (cm *ClaimManager) GetClaimByBSNServiceLaw(ctx context.Context, bsn string, service string, law string, approved bool, includeRejected bool) (map[string]model.Claim, error) {
	bsnID, err := cm.getBSN(ctx, nil, bsn)
	if err != nil {
		return nil, fmt.Errorf("get bsn: %w", err)
	}

	beweringIDs, err := generated.GetBeweringOnBsn(ctx, cm.clients.dml, bsnID)
	if err != nil {
		return nil, fmt.Errorf("get bewering on bsn: %w", err)
	}

	result := make(map[string]model.Claim)

	for _, v := range beweringIDs.GetClaimsBewering {
		bewering, err := cm.get(ctx, nil, uuid.MustParse(*v.Id))
		if err != nil {
			return nil, fmt.Errorf("get bewering: %w", err)
		}

		if bewering.BSN == bsn && bewering.Law == law {
			if cm.matchesStatusFilter(bewering, approved, includeRejected) {
				result[bewering.Key] = *bewering
			}
		}
	}

	return result, nil
}

// Helper functions

func (cm *ClaimManager) getBSN(ctx context.Context, txID *string, bsn string) (string, error) {
	data, err := generated.GetClaimsBsn(ctx, cm.clients.dml, txID, bsn)
	if err != nil {
		return "", fmt.Errorf("get claims bsn: %w", err)
	}

	if len(data.GetClaimsBsn) == 0 {
		return "", errors.New("bsn not found")
	}

	if len(data.GetClaimsBsn) > 1 {
		return "", errors.New("multiple bsn claims found: invalid state")
	}

	return data.GetClaimsBsn[0].Id, nil
}

func (cm *ClaimManager) createACEClaim(ctx context.Context, txID string, claimType string, bsnID string, value any, t *time.Time) (string, error) {
	cm.logger.Info("create ace claim", logger.NewField("claimType", claimType), logger.NewField("bsn", bsnID), logger.NewField("value", value))

	input := []generated.TagInput{
		{Name: "Bsn", Value: bsnID},
	}

	cType, ok := cm.claimTypes[claimType]
	if !ok {
		return "", fmt.Errorf("could not retrieve claim type: %s", claimType)
	}

	for _, role := range cType {
		if role.ReferencedType == "LabelType" {
			// Handle float values, since '%v' formats large numbers using scientific notation
			var val string
			switch x := value.(type) {
			case int:
				val = strconv.Itoa(x)
			case float32:
				val = strconv.FormatFloat(float64(x), 'f', -1, 32)
			case float64:
				val = strconv.FormatFloat(x, 'f', -1, 64)
			default:
				val = fmt.Sprintf("%v", x)
			}

			input = append(input, generated.TagInput{Name: role.Name, Value: val})
		}
	}

	response, err := generated.AddClaim(ctx, cm.clients.ddl, &txID, claimType, input)
	if err != nil {
		return "", err
	}

	t1 := time.Now()
	if t != nil {
		t1 = *t
	}

	// Add ValidFrom annotation to proposed claim (valid from now)
	_, err = generated.AddAnnotationValidFrom(ctx, cm.clients.dml, &txID, response.AddClaim, t1)
	if err != nil {
		return "", fmt.Errorf("add annotation valid from: %w", err)
	}

	return response.AddClaim, nil
}

func (cm *ClaimManager) approveInTransaction(ctx context.Context, txID string, claimID uuid.UUID, verifiedValue any, verifiedBy string, bsnID string, effectiveDate time.Time) error {
	log := cm.logger.WithFields(
		logger.NewField("tx", txID),
		logger.NewField("claimID", claimID),
		logger.NewField("value", verifiedValue),
		logger.NewField("by", verifiedBy),
		logger.NewField("bsn", bsnID),
	)

	bewering, err := cm.get(ctx, &txID, claimID)
	if err != nil {
		return fmt.Errorf("get bewering: %w", err)
	}

	log = log.WithFields(logger.NewField("key", bewering.Key), logger.NewField("id", bewering.ID))
	log.Info("create claim")

	// Create real value in ACE
	claimTypeName := cm.normalizeClaimType(bewering.Key)
	if _, err := cm.createACEClaim(ctx, txID, claimTypeName, bsnID, bewering.NewValue, &effectiveDate); err != nil {
		return fmt.Errorf("create real claim: %w", err)
	}

	log.Info("add bewering status")

	if err := cm.addBeweringStatus(ctx, txID, bewering.ID, "APPROVED", &effectiveDate); err != nil {
		return fmt.Errorf("add bewering status: %w", err)
	}

	log.Info("add verified")
	if err := cm.addVerified(ctx, txID, bewering.ID, verifiedBy, bewering.NewValue, &effectiveDate); err != nil {
		return fmt.Errorf("add verified: %w", err)
	}

	return nil
}

func (cm *ClaimManager) normalizeClaimType(key string) string {
	// Convert service name to ACE claim type name (PascalCase)
	parts := strings.Split(key, "_")
	for i, part := range parts {
		if len(part) > 0 {
			parts[i] = strings.ToUpper(part[:1]) + strings.ToLower(part[1:])
		}
	}
	return strings.Join(parts, "")
}

func (cm *ClaimManager) matchesStatusFilter(claim *model.Claim, approved bool, includeRejected bool) bool {
	if approved {
		return claim.Status == model.ClaimStatusApproved
	}

	if claim.Status == model.ClaimStatusRejected {
		return includeRejected
	}

	return claim.Status == model.ClaimStatusApproved || claim.Status == model.ClaimStatusPending
}

func (cm *ClaimManager) addBewering(ctx context.Context, txID string, bsnID string, reason, law, key string, effectiveDate time.Time) (uuid.UUID, error) {
	// Create Bewering (claim tracking) in ACE
	beweringResp, err := generated.AddBewering(ctx, cm.clients.dml, &txID, bsnID, &reason, &law, &key)
	if err != nil {
		return uuid.Nil, fmt.Errorf("add bewering: %w", err)
	}

	beweringID, err := uuid.Parse(beweringResp.AddBewering)
	if err != nil {
		return uuid.Nil, fmt.Errorf("bewerings uuid parse: %w", err)
	}

	if _, err := generated.AddAnnotationValidFrom(ctx, cm.clients.dml, &txID, beweringResp.AddBewering, effectiveDate); err != nil {
		return uuid.Nil, fmt.Errorf("add annotation valid from: %w", err)
	}

	return beweringID, nil
}

func (cm *ClaimManager) addVerified(ctx context.Context, txID string, beweringID uuid.UUID, verifiedBy string, verifiedValue any, verifiedAt *time.Time) error {
	verifiedTime := time.Now()
	if verifiedAt != nil {
		verifiedTime = *verifiedAt
	}

	response, err := generated.AddVerified(ctx, cm.clients.dml, &txID, beweringID.String(), verifiedBy, fmt.Sprintf("%v", verifiedValue), verifiedTime.Format(time.RFC3339))
	if err != nil {
		return fmt.Errorf("add verfied: %w", err)
	}

	if _, err := generated.AddAnnotationValidFrom(ctx, cm.clients.dml, &txID, *response.AddVerified, verifiedTime); err != nil {
		return fmt.Errorf("add annotation valid from to real claim: %w", err)
	}

	return nil
}

func (cm *ClaimManager) addBeweringStatus(ctx context.Context, txID string, beweringID uuid.UUID, status string, approvedAt *time.Time) error {
	// Update BeweringStatus to status
	response, err := generated.AddBeweringStatus(ctx, cm.clients.dml, &txID, beweringID.String(), status)
	if err != nil {
		return fmt.Errorf("update bewering status: %w", err)
	}

	approvedTime := time.Now()
	if approvedAt != nil {
		approvedTime = *approvedAt
	}

	if _, err := generated.AddAnnotationValidFrom(ctx, cm.clients.dml, &txID, *response.AddBeweringStatus, approvedTime); err != nil {
		return fmt.Errorf("add annotation valid from to real claim: %w", err)
	}

	return nil
}

func (cm *ClaimManager) AddBeweringProposed(ctx context.Context, txID string, beweringID uuid.UUID, realID string, approvedAt *time.Time) error {
	resp, err := generated.AddBeweringProposed(ctx, cm.clients.dml, &txID, beweringID.String(), realID)
	if err != nil {
		return fmt.Errorf("update bewering referentie: %w", err)
	}

	approvedTime := time.Now()
	if approvedAt != nil {
		approvedTime = *approvedAt
	}

	if _, err := generated.AddAnnotationValidFrom(ctx, cm.clients.dml, &txID, *resp.AddBeweringProposed, approvedTime); err != nil {
		return fmt.Errorf("add annotation valid from to real claim: %w", err)
	}

	return nil
}

func (cm *ClaimManager) addBeweringEvidencePath(ctx context.Context, txID string, claimID uuid.UUID, evidence string) error {
	resp, err := generated.AddBeweringEvidencePath(ctx, cm.clients.dml, &txID, claimID.String(), evidence)
	if err != nil {
		return fmt.Errorf("add bewering evidence path: %w", err)
	}

	if _, err := generated.AddAnnotationValidFrom(ctx, cm.clients.dml, &txID, *resp.AddBeweringEvidencePath, time.Now()); err != nil {
		return fmt.Errorf("add annotation valid from to real claim: %w", err)
	}

	return nil
}

func (cm *ClaimManager) addBeweringCase(ctx context.Context, txID string, claimID uuid.UUID, caseID uuid.UUID) error {
	resp, err := generated.AddBeweringCase(ctx, cm.clients.dml, &txID, claimID.String(), caseID.String())
	if err != nil {
		return fmt.Errorf("add bewering case: %w", err)
	}

	if _, err := generated.AddAnnotationValidFrom(ctx, cm.clients.dml, &txID, *resp.AddBeweringCase, time.Now()); err != nil {
		return fmt.Errorf("add annotation valid from to real claim: %w", err)
	}

	return nil
}

// convertOutputToSourceField converts an output field name to its source field name.
func (cm *ClaimManager) convertOutputToSourceField(key, svc, law string) string {
	// Get the rule spec
	spec, err := cm.ruleResolver.GetRuleSpec(law, time.Now(), svc)
	if err != nil {
		// If we can't get the spec, just return the original key
		return key
	}

	// Build the mapping
	outputToSource := buildOutputToSourceMap(spec)

	// Return the mapped field name, or the original key if no mapping exists
	if sourceField, ok := outputToSource[key]; ok {
		return sourceField[0]
	}

	return key
}

// convertSourceToOutputField converts a source field name to its output field name(s).
func (cm *ClaimManager) convertSourceToOutputField(key, svc, law string) string {
	// Get the rule spec
	spec, err := cm.ruleResolver.GetRuleSpec(law, time.Now(), svc)
	if err != nil {
		// If we can't get the spec, just return the original key
		return key
	}

	// Build the mapping
	outputToSource := buildOutputToSourceMap(spec)

	// Reverse the mapping to find output names
	// Return the mapped field name, or the original key if no mapping exists

	for k, v := range outputToSource {
		for _, v1 := range v {
			if v1 == key {
				return k
			}
		}
	}

	return key
}

// buildOutputToSourceMap builds a mapping from output field names to source_reference field names.
func buildOutputToSourceMap(spec ruleresolver.RuleSpec) map[string][]string {
	// Build a map of source names to their fields
	sourceFields := make(map[string][]string)
	for _, source := range spec.Properties.Sources {
		if source.SourceReference != nil {
			if source.SourceReference.Fields != nil {
				sourceFields[source.Name] = *source.SourceReference.Fields
			}
			if source.SourceReference.Field != nil {
				sourceFields[source.Name] = []string{*source.SourceReference.Field}
			}
		}
	}

	return sourceFields
}

var ErrBeweringNotFound = errors.New("bewering_not_found")
var ErrBeweringMultipleFound = errors.New("bewering_multiple_found")
