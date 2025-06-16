package dataframe

import (
	"fmt"

	"maps"

	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
)

var _ model.DataFrame = &SimpleDataFrame{}

// SimpleDataFrame is a basic implementation of the DataFrame interface
type SimpleDataFrame struct {
	data    []map[string]any
	columns map[string][]any
}

// Append implements model.DataFrame.
func (df *SimpleDataFrame) Append(other model.DataFrame) (model.DataFrame, error) {
	otherData := other.ToRecords()
	if len(otherData) == 0 {
		return New(df.data), nil
	}

	// Pre-calculate total size and allocate once
	totalRows := len(df.data) + len(otherData)
	newData := make([]map[string]any, totalRows)

	// Get column sets once
	currentColumns := df.GetColumns()
	otherColumns := other.GetColumns()

	// Use slices instead of map for better performance when column count is small
	var allColumns []string
	columnSet := make(map[string]struct{}, len(currentColumns)+len(otherColumns))

	// Add current columns
	for _, col := range currentColumns {
		if _, exists := columnSet[col]; !exists {
			columnSet[col] = struct{}{}
			allColumns = append(allColumns, col)
		}
	}

	// Add other columns
	for _, col := range otherColumns {
		if _, exists := columnSet[col]; !exists {
			columnSet[col] = struct{}{}
			allColumns = append(allColumns, col)
		}
	}

	// Process current dataframe rows
	for i, row := range df.data {
		newRow := make(map[string]any, len(allColumns))

		// Copy existing values
		maps.Copy(newRow, row)

		// Add nil for missing columns
		for _, col := range allColumns {
			if _, exists := newRow[col]; !exists {
				newRow[col] = nil
			}
		}

		newData[i] = newRow
	}

	// Process other dataframe rows
	offset := len(df.data)
	for i, row := range otherData {
		newRow := make(map[string]any, len(allColumns))

		// Copy existing values
		maps.Copy(newRow, row)

		// Add nil for missing columns
		for _, col := range allColumns {
			if _, exists := newRow[col]; !exists {
				newRow[col] = nil
			}
		}

		newData[offset+i] = newRow
	}

	return New(newData), nil
}

// New creates a new simple dataframe from records
func New(records []map[string]any) *SimpleDataFrame {
	df := &SimpleDataFrame{
		data:    records,
		columns: make(map[string][]any),
	}

	// Extract columns
	if len(records) > 0 {
		for col := range records[0] {
			values := make([]any, len(records))
			for i, record := range records {
				values[i] = record[col]
			}
			df.columns[col] = values
		}
	}

	return df
}

// Filter filters the DataFrame based on column, operator, and value
func (df *SimpleDataFrame) Filter(column, operator string, value any) (model.DataFrame, error) {
	var filtered []map[string]any

	for _, row := range df.data {
		colValue, exists := row[column]
		if !exists {
			continue
		}

		if v, ok := value.(fmt.Stringer); ok {
			value = v.String()
		}

		if v, ok := colValue.(fmt.Stringer); ok {
			colValue = v.String()
		}

		var match bool
		switch operator {
		case "=":
			match = colValue == value
		case "!=":
			match = colValue != value
		case ">":
			// For simplicity, handle only numeric comparisons
			fv1, ok1 := toFloat(colValue)
			fv2, ok2 := toFloat(value)
			match = ok1 && ok2 && fv1 > fv2
		case "<":
			fv1, ok1 := toFloat(colValue)
			fv2, ok2 := toFloat(value)
			match = ok1 && ok2 && fv1 < fv2
		case ">=":
			fv1, ok1 := toFloat(colValue)
			fv2, ok2 := toFloat(value)
			match = ok1 && ok2 && fv1 >= fv2
		case "<=":
			fv1, ok1 := toFloat(colValue)
			fv2, ok2 := toFloat(value)
			match = ok1 && ok2 && fv1 <= fv2
		case "in":
			// Check if value is in array
			if arr, ok := value.([]any); ok {
				for _, v := range arr {
					if v == colValue {
						match = true
						break
					}
				}
			}
		default:
			return nil, fmt.Errorf("unsupported operator: %s", operator)
		}

		if match {
			filtered = append(filtered, row)
		}
	}

	return New(filtered), nil
}

// Select returns a new DataFrame with only the specified columns
func (df *SimpleDataFrame) Select(columns []string) model.DataFrame {
	var filtered []map[string]any

	for _, row := range df.data {
		newRow := make(map[string]any)
		for _, col := range columns {
			if val, exists := row[col]; exists {
				newRow[col] = val
			}
		}
		filtered = append(filtered, newRow)
	}

	return New(filtered)
}

// ToRecords converts the DataFrame to a slice of maps
func (df *SimpleDataFrame) ToRecords() []map[string]any {
	return df.data
}

func (df *SimpleDataFrame) GetColumns() []string {
	columns := make([]string, 0, len(df.columns))

	for key := range df.columns {
		columns = append(columns, key)
	}

	return columns
}

// HasColumn checks if the DataFrame has a column
func (df *SimpleDataFrame) HasColumn(column string) bool {
	_, exists := df.columns[column]
	return exists
}

// GetColumnValues returns all values from a column
func (df *SimpleDataFrame) GetColumnValues(column string) []any {
	if values, exists := df.columns[column]; exists {
		return values
	}
	return nil
}

// Helper to convert values to float
func toFloat(v any) (float64, bool) {
	switch val := v.(type) {
	case int:
		return float64(val), true
	case int32:
		return float64(val), true
	case int64:
		return float64(val), true
	case float32:
		return float64(val), true
	case float64:
		return val, true
	default:
		return 0, false
	}
}
