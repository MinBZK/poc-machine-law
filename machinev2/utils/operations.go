package utils

import (
	"fmt"
	"reflect"
	"strings"

	"github.com/shopspring/decimal"
)

func NotEqual(a, b any) (bool, error) {
	c, err := Compare(a, b)
	if err != nil {
		return false, err
	}

	return c != 0, err
}

func Equal(a, b any) (bool, error) {
	c, err := Compare(a, b)
	if err != nil {
		return false, err
	}

	return c == 0, err
}

// Compare compares two values of any type and returns:
//
//	-1 if a < b
//	 0 if a == b
//	 1 if a > b
//
// It handles cross-type numeric comparisons (e.g., int(1) == float64(1.0) is true).
func Compare(a, b interface{}) (int, error) {
	// Handle nil cases
	if a == nil && b == nil {
		return 0, nil
	}
	if a == nil {
		return -1, nil // nil is considered smaller than non-nil
	}
	if b == nil {
		return 1, nil // non-nil is considered larger than nil
	}

	// Get reflect values
	va := reflect.ValueOf(a)
	vb := reflect.ValueOf(b)

	// If types are directly comparable
	if va.Type() == vb.Type() {
		switch va.Kind() {
		case reflect.Bool:
			if va.Bool() == vb.Bool() {
				return 0, nil
			}
			if !va.Bool() && vb.Bool() {
				return -1, nil // false < true
			}
			return 1, nil // true > false

		case reflect.String:
			if va.String() == vb.String() {
				return 0, nil
			}
			if va.String() < vb.String() {
				return -1, nil
			}
			return 1, nil

		case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
			if va.Int() == vb.Int() {
				return 0, nil
			}
			if va.Int() < vb.Int() {
				return -1, nil
			}
			return 1, nil

		case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64, reflect.Uintptr:
			if va.Uint() == vb.Uint() {
				return 0, nil
			}
			if va.Uint() < vb.Uint() {
				return -1, nil
			}
			return 1, nil

		case reflect.Float32, reflect.Float64:
			if va.Float() == vb.Float() {
				return 0, nil
			}
			if va.Float() < vb.Float() {
				return -1, nil
			}
			return 1, nil

		case reflect.Complex64, reflect.Complex128:
			// Complex numbers don't have a natural ordering
			if va.Complex() == vb.Complex() {
				return 0, nil
			}
			return 0, fmt.Errorf("complex numbers can only be tested for equality, not ordered")

		case reflect.Ptr, reflect.UnsafePointer:
			if va.IsNil() && vb.IsNil() {
				return 0, nil
			}
			if va.IsNil() {
				return -1, nil
			}
			if vb.IsNil() {
				return 1, nil
			}
			return Compare(va.Elem().Interface(), vb.Elem().Interface())

		case reflect.Struct:
			return compareStructs(va, vb)

		case reflect.Map:
			return compareMaps(va, vb)

		case reflect.Slice, reflect.Array:
			return compareSlicesOrArrays(va, vb)
		}
	}

	// Handle cross-type numeric comparisons
	if isNumeric(va.Kind()) && isNumeric(vb.Kind()) {
		if isInteger(va.Kind()) && isInteger(vb.Kind()) {
			if va.Int() == vb.Int() {
				return 0, nil
			}
			if va.Int() < vb.Int() {
				return -1, nil
			}
			return 1, nil
		} else if isUnsignedInteger(va.Kind()) && isUnsignedInteger(vb.Kind()) {
			if va.Uint() == vb.Uint() {
				return 0, nil
			}
			if va.Uint() < vb.Uint() {
				return -1, nil
			}
			return 1, nil
		} else {
			// Convert both to float64 for comparison
			var aDec, bDec decimal.Decimal

			switch va.Kind() {
			case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
				aDec = decimal.NewFromInt(va.Int())
			case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64, reflect.Uintptr:
				aDec = decimal.NewFromUint64(va.Uint())
			case reflect.Float32:
				aDec = decimal.NewFromFloat32(va.Interface().(float32))
			case reflect.Float64:
				aDec = decimal.NewFromFloat(va.Float())
			}

			switch vb.Kind() {
			case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
				bDec = decimal.NewFromInt(vb.Int())

			case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64, reflect.Uintptr:
				bDec = decimal.NewFromUint64(vb.Uint())
			case reflect.Float32:
				bDec = decimal.NewFromFloat32(vb.Interface().(float32))
			case reflect.Float64:
				bDec = decimal.NewFromFloat(vb.Float())
			}

			return aDec.Compare(bDec), nil
		}
	}

	if isString(va) && isString(vb) {
		return strings.Compare(va.String(), vb.String()), nil
	}

	// Types are not comparable
	return 0, fmt.Errorf("cannot compare values of types %s and %s", va.Type(), vb.Type())
}

func isString(value reflect.Value) bool {
	if value.Kind() == reflect.String {
		return true
	}

	if value.CanInterface() {
		_, ok := value.Interface().(fmt.Stringer)
		return ok
	}

	return false
}

// Helper functions
func isNumeric(kind reflect.Kind) bool {
	switch kind {
	case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64,
		reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64, reflect.Uintptr,
		reflect.Float32, reflect.Float64:
		return true
	}
	return false
}

func isInteger(kind reflect.Kind) bool {
	switch kind {
	case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
		return true
	}
	return false
}

func isUnsignedInteger(kind reflect.Kind) bool {
	switch kind {
	case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64, reflect.Uintptr:
		return true
	}
	return false
}

func compareStructs(a, b reflect.Value) (int, error) {
	if a.Type() != b.Type() {
		return 0, fmt.Errorf("cannot compare different struct types %s and %s", a.Type(), b.Type())
	}

	if a.NumField() != b.NumField() {
		return 1, nil
	}

	for i := range a.NumField() {
		fieldA := a.Field(i)
		fieldB := b.Field(i)

		if a.Type().Field(i).Name != b.Type().Field(i).Name {
			return 1, nil
		}

		if !fieldA.CanInterface() || !fieldB.CanInterface() {
			return 1, nil
		}

		result, err := Compare(fieldA.Interface(), fieldB.Interface())
		if err != nil {
			return 0, err
		}

		if result != 0 {
			return result, nil
		}
	}

	return 0, nil // All fields are equal
}

func compareMaps(a, b reflect.Value) (int, error) {
	if a.Type() != b.Type() {
		return 0, fmt.Errorf("cannot compare different map types %s and %s", a.Type(), b.Type())
	}

	// Compare lengths first
	if a.Len() < b.Len() {
		return -1, nil
	}
	if a.Len() > b.Len() {
		return 1, nil
	}

	if a.Len() == 0 {
		return 0, nil
	}

	// Sort keys for deterministic comparison
	keys := a.MapKeys()

	// Check if all keys in a exist in b and have the same values
	for _, key := range keys {
		valA := a.MapIndex(key)
		valB := b.MapIndex(key)

		if !valB.IsValid() {
			// Key exists in a but not in b
			return 1, nil
		}

		result, err := Compare(valA.Interface(), valB.Interface())
		if err != nil {
			return 0, err
		}
		if result != 0 {
			return result, nil
		}
	}

	return 0, nil // Maps are equal
}

func compareSlicesOrArrays(a, b reflect.Value) (int, error) {
	// Compare lengths first
	if a.Len() < b.Len() {
		return -1, nil
	}
	if a.Len() > b.Len() {
		return 1, nil
	}

	// Compare element by element
	for i := 0; i < a.Len(); i++ {
		result, err := Compare(a.Index(i).Interface(), b.Index(i).Interface())
		if err != nil {
			return 0, err
		}
		if result != 0 {
			return result, nil
		}
	}

	return 0, nil // Arrays/slices are equal
}
