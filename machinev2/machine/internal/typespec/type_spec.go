package typespec

import (
	"fmt"
	"math"
	"strconv"

	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
)

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
			return int(math.Round(floatVal))
		}

		factor := math.Pow(10, float64(*ts.Precision))
		floatVal = math.Round(floatVal*factor) / factor
	}

	// Convert to int for cent units
	if ts.Unit != nil {
		switch *ts.Unit {
		case "eurocent":
			return int(math.Round(floatVal))
		}
	}

	return floatVal
}
