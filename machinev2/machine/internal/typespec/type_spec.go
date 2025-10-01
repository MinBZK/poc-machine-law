package typespec

import (
	"fmt"
	"math"
	"strconv"

	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
)

// roundHalfToEven implements banker's rounding (round half to even)
// to match Python's round() behavior.
// Examples: 12.5 -> 12, 13.5 -> 14, 14.5 -> 14, 15.5 -> 16
func roundHalfToEven(x float64) float64 {
	t := math.Trunc(x)
	if math.Abs(x-t) != 0.5 {
		return math.Round(x)
	}
	if math.Mod(t, 2) == 0 {
		return t
	}
	return t + math.Copysign(1, x)
}

// Enforce applies type specifications to a value
func Enforce(ts model.TypeSpec, value any) any {
	if value == nil {
		return value
	}

	if ts.Type == "string" {
		return fmt.Sprintf("%v", value)
	}

	// Convert to numeric if needed
	var floatVal float64
	switch v := value.(type) {
	case string:
		var err error
		floatVal, err = strconv.ParseFloat(v, 64)
		if err != nil {
			return value
		}
	case int:
		floatVal = float64(v)
	case int32:
		floatVal = float64(v)
	case int64:
		floatVal = float64(v)
	case float32:
		floatVal = float64(v)
	case float64:
		floatVal = v
	default:
		return value
	}

	// Apply min/max constraints
	if ts.Min != nil {
		floatVal = math.Max(floatVal, *ts.Min)
	}
	if ts.Max != nil {
		floatVal = math.Min(floatVal, *ts.Max)
	}

	// Apply precision
	if ts.Precision != nil {
		if *ts.Precision == 0 {
			// Use banker's rounding (round half to even) to match Python's behavior
			// Python's round(12.5, 0) = 12.0, round(13.5, 0) = 14.0
			return int(roundHalfToEven(floatVal))
		}

		factor := math.Pow(10, float64(*ts.Precision))
		floatVal = roundHalfToEven(floatVal*factor) / factor
	}

	// Convert to int for cent units
	if ts.Unit != nil {
		switch *ts.Unit {
		case "eurocent":
			return int(roundHalfToEven(floatVal))
		}
	}

	return floatVal
}
