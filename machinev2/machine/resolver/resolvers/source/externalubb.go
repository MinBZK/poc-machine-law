package source

import (
	"context"
	"fmt"
	"net/http"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/Khan/genqlient/graphql"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/typespec"
	"github.com/minbzk/poc-machine-law/machinev2/machine/logger"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	machine "github.com/minbzk/poc-machine-law/machinev2/machine/resolver/resolvers/source/generated"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
	"golang.org/x/text/cases"
	"golang.org/x/text/language"
)

type ubbResolver struct {
	propertySpec  map[string]ruleresolver.Field
	client        graphql.Client
	effectiveDate time.Time
}

func newUBBResolver(endpoint string, propertySpec map[string]ruleresolver.Field, effectiveDate time.Time) *ubbResolver {
	return &ubbResolver{
		client:        graphql.NewClient(endpoint+"/gql/grp/v0", http.DefaultClient),
		propertySpec:  propertySpec,
		effectiveDate: effectiveDate,
	}

}

// Resolve implements Resolver.
func (c ubbResolver) do(ctx context.Context, key string, table string, field string, filters Filters) (any, error) {
	logr := logger.FromContext(ctx)
	logr = logr.WithField("resolver", "external_claim").
		WithField("resolver_type", "ubb").
		WithField("table", table).
		WithField("field", field).
		WithField("filters", filters)

	f := c.propertySpec[key]

	resp, err := machine.ClaimAttributesByObjectID(ctx, c.client, filters[0].Value.(string), c.effectiveDate)
	if err != nil {
		return nil, fmt.Errorf("claim attributes object id: %w", err)
	}

	return solver(logr, table, field, resp.GetClaimAttributesByObjectID().Subvalues, f)
}

func pascalCase(s string) string {
	// Remove all characters that are not alphanumeric or spaces or underscores
	s = regexp.MustCompile("[^a-zA-Z0-9_ ]+").ReplaceAllString(s, "")

	// Replace all underscores with spaces
	s = strings.ReplaceAll(s, "_", " ")

	// Title case s
	s = cases.Title(language.AmericanEnglish, cases.NoLower).String(s)

	// Remove all spaces
	s = strings.ReplaceAll(s, " ", "")

	// Lowercase the first letter
	if len(s) > 0 {
		s = strings.ToUpper(s[:1]) + s[1:]
	}

	return s
}

func solver(
	logr logger.Logger,
	table, field string,
	values []machine.ClaimAttributesByObjectIDClaimAttributesByObjectIDSampleResultSubvaluesSampleResult,
	f ruleresolver.Field,
) (any, error) {
	for _, value := range values {
		if strings.EqualFold(strings.ToLower(value.Name), strings.ToLower(field)) ||
			strings.EqualFold(strings.ToLower(value.Name), pascalCase(field)) {
			return solveField(logr, value, f)
		}

		if strings.EqualFold(strings.ToLower(value.Name), strings.ToLower(table)) ||
			strings.EqualFold(strings.ToLower(value.Name), pascalCase(table)) {
			return solver(logr, table, field, conv(value.Values), f)
		}
	}

	return nil, nil
}

func conv(
	values []machine.ClaimAttributesByObjectIDClaimAttributesByObjectIDSampleResultSubvaluesSampleResultValues,
) []machine.ClaimAttributesByObjectIDClaimAttributesByObjectIDSampleResultSubvaluesSampleResult {
	v := make([]machine.ClaimAttributesByObjectIDClaimAttributesByObjectIDSampleResultSubvaluesSampleResult, 0, len(values))

	for idx := range values {
		v = append(v, machine.ClaimAttributesByObjectIDClaimAttributesByObjectIDSampleResultSubvaluesSampleResult{
			Name: values[idx].Key,
			Values: []machine.ClaimAttributesByObjectIDClaimAttributesByObjectIDSampleResultSubvaluesSampleResultValues{
				{
					Key:   values[idx].Key,
					Value: values[idx].Value,
				},
			},
		})
	}

	return v
}

func solveField(
	logr logger.Logger,
	value machine.ClaimAttributesByObjectIDClaimAttributesByObjectIDSampleResultSubvaluesSampleResult,
	f ruleresolver.Field,
) (any, error) {
	v := value.Values[0]

	var x any = v.Value

	switch v.Key {
	case "date":
		t, err := strconv.Atoi(v.Value)
		if err != nil {
			return nil, fmt.Errorf("could not parse date: %w", err)
		}

		x = time.Unix(int64(t), 0)
	case "eurocent", "amountEurocent":
		t, err := strconv.Atoi(v.Value)
		if err != nil {
			return nil, fmt.Errorf("could not parse eurocent: %w", err)
		}

		x = t
	default:
		logr.Warning("unknown key", logger.NewField("key", v.Key))
	}

	if f.Source != nil && f.Source.TypeSpec != nil {
		return typespec.Enforce(model.TypeSpec(*f.Source.TypeSpec), x), nil
	}

	return x, nil
}
