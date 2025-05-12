package casemanager

import (
	"reflect"
	"strings"
)

func structToMap(obj any) map[string]any {
	result := make(map[string]any)

	v := reflect.ValueOf(obj)
	if v.Kind() == reflect.Ptr {
		v = v.Elem()
	}

	if v.Kind() != reflect.Struct {
		return result // Return empty map if not a struct
	}

	t := v.Type()
	for i := range v.NumField() {
		field := t.Field(i)
		fieldValue := v.Field(i)

		// Get the field's JSON tag or use field name if tag not present
		tag := field.Tag.Get("json")
		if tag == "" || tag == "-" {
			continue // Skip if no JSON tag or explicitly ignored
		}

		tag, opts := parseTag(tag)

		// Skip nil pointers if omitempty is set
		if opts.Contains("omitempty") {
			// Check if field is a nil pointer
			if fieldValue.Kind() == reflect.Ptr && fieldValue.IsNil() {
				continue
			}

			// Check for zero values if omitempty is specified
			if isZeroValue(fieldValue) {
				continue
			}
		}
		// Add to result map
		result[tag] = fieldValue.Interface()
	}

	return result
}

// isZeroValue determines if a value should be considered "empty" for omitempty purposes
func isZeroValue(v reflect.Value) bool {
	switch v.Kind() {
	case reflect.Array, reflect.Map, reflect.Slice, reflect.String:
		return v.Len() == 0
	case reflect.Bool:
		return !v.Bool()
	case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
		return v.Int() == 0
	case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64, reflect.Uintptr:
		return v.Uint() == 0
	case reflect.Float32, reflect.Float64:
		return v.Float() == 0
	case reflect.Interface, reflect.Ptr:
		return v.IsNil()
	}
	return false
}

// parseTag splits a struct field's json tag into its name and
// comma-separated options.
func parseTag(tag string) (string, tagOptions) {
	tag, opt, _ := strings.Cut(tag, ",")
	return tag, tagOptions(opt)
}

// tagOptions is the string following a comma in a struct field's "json"
// tag, or the empty string. It does not include the leading comma.
type tagOptions string

// Contains reports whether a comma-separated list of options
// contains a particular substr flag. substr must be surrounded by a
// string boundary or commas.
func (o tagOptions) Contains(optionName string) bool {
	if len(o) == 0 {
		return false
	}
	s := string(o)
	for s != "" {
		var name string
		name, s, _ = strings.Cut(s, ",")
		if name == optionName {
			return true
		}
	}
	return false
}
