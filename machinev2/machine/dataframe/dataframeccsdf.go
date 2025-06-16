package dataframe

import (
	"fmt"
	"strings"

	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
)

var _ model.DataFrame = &ColumnDataFrame{}

// ColumnDataFrame implements DataFrame using columnar storage
type ColumnDataFrame struct {
	columns map[string][]any
	length  int
}

// NewColumnDataFrame creates a new ColumnDataFrame from records
func NewColumnDataFrame(data []map[string]any) *ColumnDataFrame {
	if len(data) == 0 {
		return &ColumnDataFrame{
			columns: make(map[string][]any),
			length:  0,
		}
	}

	// Collect all unique column names first
	columnSet := make(map[string]struct{})
	for _, record := range data {
		for col := range record {
			columnSet[col] = struct{}{}
		}
	}

	// Pre-allocate columns with exact capacity
	columns := make(map[string][]any, len(columnSet))
	for col := range columnSet {
		columns[col] = make([]any, 0, len(data))
	}

	// Fill columns row by row
	for _, record := range data {
		for col := range columnSet {
			if val, exists := record[col]; exists {
				columns[col] = append(columns[col], val)
			} else {
				columns[col] = append(columns[col], nil)
			}
		}
	}

	return &ColumnDataFrame{
		columns: columns,
		length:  len(data),
	}
}

// Filter implements DataFrame.Filter
func (df *ColumnDataFrame) Filter(column, operator string, value any) (model.DataFrame, error) {
	columnData, exists := df.columns[column]
	if !exists {
		return nil, fmt.Errorf("column %s not found", column)
	}

	// Find matching row indices
	var matchedIndices []int
	for i, colValue := range columnData {
		match := false

		switch operator {
		case "==", "=":
			match = compareValues(colValue, value, "==")
		case "!=":
			match = compareValues(colValue, value, "!=")
		case "contains":
			match = containsValue(colValue, value)
		case ">":
			match = compareValues(colValue, value, ">")
		case "<":
			match = compareValues(colValue, value, "<")
		case ">=":
			match = compareValues(colValue, value, ">=")
		case "<=":
			match = compareValues(colValue, value, "<=")
		default:
			return nil, fmt.Errorf("unsupported operator: %s", operator)
		}

		if match {
			matchedIndices = append(matchedIndices, i)
		}
	}

	// Create new filtered columns
	newColumns := make(map[string][]any, len(df.columns))
	for col, colData := range df.columns {
		newColumn := make([]any, 0, len(matchedIndices))
		for _, idx := range matchedIndices {
			newColumn = append(newColumn, colData[idx])
		}
		newColumns[col] = newColumn
	}

	return &ColumnDataFrame{
		columns: newColumns,
		length:  len(matchedIndices),
	}, nil
}

// Select implements DataFrame.Select
func (df *ColumnDataFrame) Select(columnNames []string) model.DataFrame {
	newColumns := make(map[string][]any, len(columnNames))

	for _, colName := range columnNames {
		if colData, exists := df.columns[colName]; exists {
			// Share the slice (zero-copy!)
			newColumns[colName] = colData
		}
	}

	return &ColumnDataFrame{
		columns: newColumns,
		length:  df.length,
	}
}

// ToRecords implements DataFrame.ToRecords
func (df *ColumnDataFrame) ToRecords() []map[string]any {
	if df.length == 0 {
		return []map[string]any{}
	}

	records := make([]map[string]any, df.length)

	// Pre-allocate maps
	for i := 0; i < df.length; i++ {
		records[i] = make(map[string]any, len(df.columns))
	}

	// Fill records column by column (cache-friendly)
	for colName, colData := range df.columns {
		for i, val := range colData {
			records[i][colName] = val
		}
	}

	return records
}

// GetColumns implements DataFrame.GetColumns
func (df *ColumnDataFrame) GetColumns() []string {
	columns := make([]string, 0, len(df.columns))
	for col := range df.columns {
		columns = append(columns, col)
	}
	return columns
}

// HasColumn implements DataFrame.HasColumn
func (df *ColumnDataFrame) HasColumn(column string) bool {
	_, exists := df.columns[column]
	return exists
}

// GetColumnValues implements DataFrame.GetColumnValues
func (df *ColumnDataFrame) GetColumnValues(column string) []any {
	if colData, exists := df.columns[column]; exists {
		// Return a copy to prevent external modification
		result := make([]any, len(colData))
		copy(result, colData)
		return result
	}
	return []any{}
}

// Append implements DataFrame.Append - THIS IS THE SUPER FAST PART!
func (df *ColumnDataFrame) Append(other model.DataFrame) (model.DataFrame, error) {
	otherCol, ok := other.(*ColumnDataFrame)
	if !ok {
		// Fallback: convert other DataFrame to column format
		return df.appendFromRecords(other.ToRecords())
	}

	if df.length == 0 {
		// If current dataframe is empty, just return the other one
		return otherCol, nil
	}

	if otherCol.length == 0 {
		// If other dataframe is empty, return current one
		return df, nil
	}

	// Collect all unique columns from both DataFrames
	allColumns := make(map[string]struct{})
	for col := range df.columns {
		allColumns[col] = struct{}{}
	}
	for col := range otherCol.columns {
		allColumns[col] = struct{}{}
	}

	// Pre-allocate new columns with exact capacity
	newLength := df.length + otherCol.length
	newColumns := make(map[string][]any, len(allColumns))

	for col := range allColumns {
		newColumn := make([]any, 0, newLength)

		// Append from first DataFrame
		if colData, exists := df.columns[col]; exists {
			newColumn = append(newColumn, colData...)
		} else {
			// Fill with nils for missing column
			for i := 0; i < df.length; i++ {
				newColumn = append(newColumn, nil)
			}
		}

		// Append from second DataFrame
		if colData, exists := otherCol.columns[col]; exists {
			newColumn = append(newColumn, colData...)
		} else {
			// Fill with nils for missing column
			for i := 0; i < otherCol.length; i++ {
				newColumn = append(newColumn, nil)
			}
		}

		newColumns[col] = newColumn
	}

	return &ColumnDataFrame{
		columns: newColumns,
		length:  newLength,
	}, nil
}

// Helper method for fallback append
func (df *ColumnDataFrame) appendFromRecords(records []map[string]any) (model.DataFrame, error) {
	if len(records) == 0 {
		return df, nil
	}

	otherDF := NewColumnDataFrame(records)
	return df.Append(otherDF)
}

// Helper functions for comparison
func compareValues(a, b any, operator string) bool {
	if a == nil || b == nil {
		return operator == "!=" && (a != b)
	}

	// Try numeric comparison first
	if aNum, aOk := toFloat64(a); aOk {
		if bNum, bOk := toFloat64(b); bOk {
			switch operator {
			case "==":
				return aNum == bNum
			case "!=":
				return aNum != bNum
			case ">":
				return aNum > bNum
			case "<":
				return aNum < bNum
			case ">=":
				return aNum >= bNum
			case "<=":
				return aNum <= bNum
			}
		}
	}

	// Fallback to string comparison
	aStr := fmt.Sprintf("%v", a)
	bStr := fmt.Sprintf("%v", b)

	switch operator {
	case "==":
		return aStr == bStr
	case "!=":
		return aStr != bStr
	case ">":
		return aStr > bStr
	case "<":
		return aStr < bStr
	case ">=":
		return aStr >= bStr
	case "<=":
		return aStr <= bStr
	}

	return false
}

func containsValue(haystack, needle any) bool {
	if haystack == nil {
		return false
	}

	haystackStr := fmt.Sprintf("%v", haystack)
	needleStr := fmt.Sprintf("%v", needle)

	return strings.Contains(haystackStr, needleStr)
}

func toFloat64(val any) (float64, bool) {
	switch v := val.(type) {
	case int:
		return float64(v), true
	case int32:
		return float64(v), true
	case int64:
		return float64(v), true
	case float32:
		return float64(v), true
	case float64:
		return v, true
	default:
		return 0, false
	}
}

// Additional utility methods
func (df *ColumnDataFrame) Len() int {
	return df.length
}

func (df *ColumnDataFrame) IsEmpty() bool {
	return df.length == 0
}

// GetColumn returns a specific column's data (zero-copy)
func (df *ColumnDataFrame) GetColumn(name string) ([]any, bool) {
	col, exists := df.columns[name]
	return col, exists
}
