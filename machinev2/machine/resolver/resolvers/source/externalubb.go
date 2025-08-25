package source

import (
	"context"
	"fmt"
	"net/http"
	"regexp"
	"strings"

	"github.com/Khan/genqlient/graphql"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/logger"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/typespec"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	machine "github.com/minbzk/poc-machine-law/machinev2/machine/resolver/resolvers/source/generated"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
	"golang.org/x/text/cases"
	"golang.org/x/text/language"
)

type ubbResolver struct {
	propertySpec map[string]ruleresolver.Field
	endpoint     string
	client       graphql.Client
}

func newUBBResolver(endpoint string, propertySpec map[string]ruleresolver.Field) *ubbResolver {

	endpoint = "http://belastingdienst-ace-svc/gql/grp/v0"

	return &ubbResolver{
		client:       graphql.NewClient(endpoint, http.DefaultClient),
		propertySpec: propertySpec,
	}

}

// Resolve implements Resolver.
func (c ubbResolver) do(ctx context.Context, key string, table string, field string, filters Filters) (any, error) {
	logr := logger.FromContext(ctx)
	logr = logr.WithField("resolver", "external_claim").
		WithField("table", table).
		WithField("field", field).
		WithField("filters", filters)

	logr.Debug("ubb resolve")

	f := c.propertySpec[key]

	resp, err := machine.ClaimAttributesByObjectID(ctx, c.client, filters[0].Value.(string), pascalCase(table))
	if err != nil {
		return nil, fmt.Errorf("claim attributes object id: %w", err)
	}

	for _, value := range resp.ClaimAttributesByObjectID.Subvalues {
		if strings.EqualFold(strings.ToLower(value.Name), strings.ToLower(table+strings.ReplaceAll(field, "_", ""))) {
			v := value.Values[0]

			return typespec.Enforce(model.TypeSpec(*f.Source.TypeSpec), v.Value), nil
		}
	}

	return nil, nil
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
