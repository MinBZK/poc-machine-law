package main

import (
	"bufio"
	"bytes"
	"embed"
	"errors"
	"flag"
	"fmt"
	"log/slog"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"text/template"

	"github.com/Masterminds/sprig/v3"
	"github.com/bmatcuk/doublestar/v4"
	"golang.org/x/text/cases"
	"golang.org/x/text/language"
	"gopkg.in/yaml.v3"
)

//go:embed templates/*.tmpl
var tmpl embed.FS

func getBaseTemplate(ruleset RuleSet) (*template.Template, error) {
	t := template.New("output.tmpl").Funcs(template.FuncMap{
		"map": func(pairs ...any) (map[string]any, error) {
			if len(pairs)%2 != 0 {
				return nil, errors.New("misaligned map")
			}

			m := make(map[string]any, len(pairs)/2)

			for i := 0; i < len(pairs); i += 2 {
				key, ok := pairs[i].(string)

				if !ok {
					return nil, fmt.Errorf("cannot use type %T as map key", pairs[i])
				}
				m[key] = pairs[i+1]
			}
			return m, nil
		},
		"solveReference": func(ref string) Requirements {
			if len(ruleset.Requirements) <= 0 {
				return Requirements{}
			}

			return ruleset.Requirements[0]
		},
		"isIndexer": func(i any) bool {
			v := reflect.ValueOf(i)
			if v.Kind() == reflect.Ptr {
				v = v.Elem()
			}

			switch v.Kind() {
			case reflect.Map, reflect.Array, reflect.Slice:
				return true
			default:
				return false
			}
		},
		"isStruct": func(i any) bool {
			v := reflect.ValueOf(i)
			if v.Kind() == reflect.Ptr {
				v = v.Elem()
			}

			switch v.Kind() {
			case reflect.Struct:
				return true
			default:
				return false
			}
		},
		"toActionConditionRequirement": toActionConditionRequirement,
		"avail": func(data any, name string) bool {
			v := reflect.ValueOf(data)
			if v.Kind() == reflect.Ptr {
				v = v.Elem()
			}

			switch v.Kind() {
			case reflect.Map:
				if v.MapIndex(reflect.ValueOf(name)).IsValid() {
					return !v.MapIndex(reflect.ValueOf(name)).IsNil()
				}

				return false
			case reflect.Struct:
				if v.FieldByName(name).IsValid() {
					return !v.FieldByName(name).IsZero()
				}

				return false
			default:
				return false
			}
		},
		"FormatID":            formatIdentifier,
		"FormatRequirement":   formatRequirement,
		"FormatActionCondReq": formatActionConReq,
		"FormatActionOutput":  formatActionOutput,
		"FormatOperation": func(op any) any {
			switch v := op.(type) {
			case string:
				switch v {
				// Operators
				case "ADD":
					return "plus"
				case "SUBTRACT":
					return "min"
				case "MULTIPLY":
					return "keer"
				case "DIVIDE":
					return "delen door"

				// Comparators
				case "EQUALS":
					return "gelijk aan"
				case "GREATER_THAN":
					return "groter dan"
				case "GREATER_OR_EQUAL":
					return "groter dan of gelijk aan"
				case "LESS_THAN":
					return "minder dan"
				case "LESS_OR_EQUAL":
					return "minder dan of gelijk aan"

				// BINARY
				case "AND":
					return "en"
				case "OR":
					return "of"

				// Other
				case "FOREACH":
					return "voor elke"
				case "MIN":
					return "minimaal"
				case "MAX":
					return "maximaal"
				case "CONCAT":
					return "samenvoegend"
				case "IN":
					return "in"
				}
			}

			fmt.Printf("UNKNOWN OP: %v\n", op)

			return op
		},
		"FormatColor": func(v any) string {
			value, ok := v.(string)
			if !ok {
				return "green"
			}

			for key := range ruleset.Properties.Definitions {
				if strings.TrimPrefix(value, "$") == key {
					return "blue"
				}
			}

			return "green"
		},
	})

	var funcMap template.FuncMap = map[string]any{
		"include": func(name string, data any) (string, error) {
			buf := bytes.NewBuffer(nil)
			if err := t.ExecuteTemplate(buf, name, data); err != nil {
				return "", err
			}
			return buf.String(), nil
		},
	}

	t, err := t.Funcs(sprig.GenericFuncMap()).
		Funcs(funcMap).
		ParseFS(tmpl, "templates/*.tmpl")
	if err != nil {
		return nil, fmt.Errorf("template parse fs: %w", err)
	}

	return t, nil
}

func toActionConditionRequirement(v any) *ActionConditionRequirement {
	if v == nil {
		return &ActionConditionRequirement{}
	}

	switch i := v.(type) {
	case map[string]any:
		var operation string
		if value, ok := i["operation"].(string); ok {
			operation = value
		}

		var subject string
		if value, ok := i["subject"].(string); ok {
			subject = value
		}

		var conditions []ActionCondition
		if v, ok := i["conditions"]; ok {
			if value, ok := v.([]ActionCondition); ok {
				conditions = value
			} else if value, ok := v.([]any); ok {
				for _, v := range value {
					if value, ok := v.(map[string]any); ok {
						conditions = append(conditions, ActionCondition{
							Test: *toActionConditionRequirement(value["test"]),
							Then: value["then"],
							Else: value["else"],
						})
					}
				}
			}
		}

		return &ActionConditionRequirement{
			Operation:  operation,
			Subject:    subject,
			Conditions: conditions,
			Value:      i["value"],
			Values:     i["values"],
		}
	case Action:
		return &ActionConditionRequirement{
			Operation:  i.Operation,
			Conditions: i.Conditions,
			Value:      i.Value,
			Values:     i.Values,
		}
	case ActionConditionRequirement:
		return &i
	default:
		panic(fmt.Sprintf("unsupported type: %s", i))
		return nil
	}
}

func fileNameWithoutExtension(fileName string) string {
	return fmt.Sprintf("%s/%s", filepath.Dir(fileName), strings.TrimSuffix(filepath.Base(fileName), filepath.Ext(fileName)))
}

type arrayFlags []string

// String is an implementation of the flag.Value interface
func (i *arrayFlags) String() string {
	return fmt.Sprintf("%v", *i)
}

// Set is an implementation of the flag.Value interface
func (i *arrayFlags) Set(value string) error {
	*i = append(*i, value)
	return nil
}

var inputPatterns arrayFlags

func main() {
	flag.Var(&inputPatterns, "input", "input names of the files that need to be parsed.")
	flag.Parse()

	fsys := os.DirFS(".")

	logger := slog.Default()

	for _, pattern := range inputPatterns {
		logger = logger.With("pattern", pattern)

		files, err := doublestar.Glob(fsys, pattern)
		if err != nil {
			logger.Error("glob matching", "err", err)
			continue
		}

		for _, file := range files {
			log := logger.With("file", file)
			yamlFile, err := os.ReadFile(file)
			if err != nil {
				log.Error("Error reading YAML file", "err", err)
				continue
			}

			var ruleset RuleSet

			if err := yaml.Unmarshal(yamlFile, &ruleset); err != nil {
				log.Error("Error parsing YAML", "err", err)
				continue
			}

			ruleset.Subject = "Natuurlijk persoon"

			t, err := getBaseTemplate(ruleset)
			if err != nil {
				log.Error("error get base template", "err", err)
				continue
			}

			file, err := os.Create(fmt.Sprintf("%s.md", fileNameWithoutExtension(file)))
			if err != nil {
				log.Error("error creating file", "err", err)
				continue
			}
			defer file.Close()

			writer := bufio.NewWriter(file)
			defer writer.Flush()

			if err := t.Execute(writer, ruleset); err != nil {
				log.Error("error executing template", "err", err)
				continue
			}
		}
	}
}

func formatIdentifier(s string) string {
	// Convert from SNAKE_CASE to Camel Case with spaces
	parts := strings.Split(strings.ToLower(s), "_")
	for i, part := range parts {
		if i == 0 {
			parts[i] = cases.Title(language.Dutch).String(part)
		}
	}
	return strings.Join(parts, " ")
}

func formatRequirement(s Requirement) string {
	operation := formatRequirementOperation(s.Operation)
	switch v := s.Value.(type) {
	case bool:
		switch v {
		case true:
			return fmt.Sprintf(`Indien <span style="color:green">%s</span> waar is`, s.Subject)
		case false:
			return fmt.Sprintf(`Indien <span style="color:green">%s</span> onwaar is`, s.Subject)
		}
	}

	return fmt.Sprintf(`Zijn <span style="color:green">%s</span> %s <span style="color:blue">%v</span>`, s.Subject, operation, s.Value)
}

func formatRequirementOperation(s string) string {
	switch s {
	case "EQUALS":
		return "is gelijk aan"
	case "GREATER_OR_EQUAL":
		return "is groter of gelijk aan"
	default:
		return s
	}
}

func formatActionConReq(s ActionConditionRequirement) string {
	if s.Value != nil {
		return formatActionConReqValue(s)
	}

	if s.Values != nil {
		return formatActionConReqValues(s)
	}

	return ""
}

func formatActionConReqValues(s ActionConditionRequirement) string {
	if s.Values == nil {
		panic("values = nil should not happen")
	}

	operation := formatRequirementOperation(s.Operation)
	switch v := s.Value.(type) {
	case bool:
		switch v {
		case true:
			return fmt.Sprintf(`Indien <span style="color:green">%s</span> waar is`, s.Subject)
		case false:
			return fmt.Sprintf(`Indien <span style="color:green">%s</span> onwaar is`, s.Subject)
		}
	}

	return fmt.Sprintf(`Zijn <span style="color:green">%s</span> %s <span style="color:blue">%v</span>`, s.Subject, operation, s.Value)
}

func formatActionConReqValue(s ActionConditionRequirement) string {
	if s.Value == nil {
		panic("value = nil should not happen")
	}
	operation := formatRequirementOperation(s.Operation)
	switch v := s.Value.(type) {
	case bool:
		switch v {
		case true:
			return fmt.Sprintf(`Indien <span style="color:green">%s</span> waar is`, s.Subject)
		case false:
			return fmt.Sprintf(`Indien <span style="color:green">%s</span> onwaar is`, s.Subject)
		}
	}

	return fmt.Sprintf(`Zijn <span style="color:green">%s</span> %s <span style="color:blue">%v</span>`, s.Subject, operation, s.Value)

}

func formatActionOutput(s string) string {
	return strings.ReplaceAll(s, "_", " ")
}
