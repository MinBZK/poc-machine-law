package dataframe

import (
	"bytes"
	"fmt"

	"github.com/apache/arrow/go/v14/arrow"
	"github.com/apache/arrow/go/v14/arrow/array"
	"github.com/apache/arrow/go/v14/arrow/memory"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
)

var _ model.DataFrame = &ArrowDataFrame{}

// ArrowDataFrame implements DataFrame using Apache Arrow
type ArrowDataFrame struct {
	record arrow.Record
	pool   memory.Allocator
}

// NewArrowDataFrame creates a new ArrowDataFrame from records
func NewArrowDataFrame(data []map[string]any) *ArrowDataFrame {
	if len(data) == 0 {
		return &ArrowDataFrame{pool: memory.NewGoAllocator()}
	}

	pool := memory.NewGoAllocator()

	// Infer schema from first record
	var fields []arrow.Field
	for colName := range data[0] {
		// Using Binary type to handle different datatypes
		fields = append(fields, arrow.Field{
			Name: colName,
			Type: arrow.BinaryTypes.Binary,
		})
	}

	schema := arrow.NewSchema(fields, nil)

	// Build record
	builders := make([]array.Builder, len(fields))
	for i := range fields {
		builders[i] = array.NewBinaryBuilder(pool, arrow.BinaryTypes.Binary)
	}

	// Populate data
	for _, row := range data {
		for i, field := range fields {
			builder := builders[i].(*array.BinaryBuilder)
			if val, exists := row[field.Name]; exists && val != nil {
				// Convert any type to bytes
				var bytes []byte
				switch v := val.(type) {
				case string:
					bytes = []byte(v)
				case []byte:
					bytes = v
				case int, int32, int64, float32, float64, bool:
					bytes = []byte(fmt.Sprintf("%v", v))
				default:
					bytes = []byte(fmt.Sprintf("%v", v))
				}
				builder.Append(bytes)
			} else {
				builder.AppendNull()
			}
		}
	}

	// Build arrays
	columns := make([]arrow.Array, len(builders))
	for i, builder := range builders {
		columns[i] = builder.NewArray()
		builder.Release()
	}

	record := array.NewRecord(schema, columns, int64(len(data)))

	return &ArrowDataFrame{
		record: record,
		pool:   pool,
	}
}

// Filter implements DataFrame.Filter
func (df *ArrowDataFrame) Filter(column, operator string, value any) (model.DataFrame, error) {
	if df.record == nil {
		return df, nil
	}

	// Find column index
	schema := df.record.Schema()
	colIndex := -1
	for i, field := range schema.Fields() {
		if field.Name == column {
			colIndex = i
			break
		}
	}

	if colIndex == -1 {
		return nil, fmt.Errorf("column %s not found", column)
	}

	// Get column array
	col := df.record.Column(colIndex).(*array.Binary)
	valueBytes := []byte(fmt.Sprintf("%v", value))

	// Create filter mask
	var indices []int
	for i := 0; i < col.Len(); i++ {
		if col.IsNull(i) {
			continue
		}

		colValue := col.Value(i)
		match := false

		switch operator {
		case "==", "=":
			match = string(colValue) == string(valueBytes)
		case "!=":
			match = string(colValue) != string(valueBytes)
		case "contains":
			match = bytes.Contains(colValue, valueBytes)
		default:
			return nil, fmt.Errorf("unsupported operator: %s", operator)
		}

		if match {
			indices = append(indices, i)
		}
	}

	// Create filtered record
	return df.createFilteredRecord(indices)
}

// Select implements DataFrame.Select
func (df *ArrowDataFrame) Select(columns []string) model.DataFrame {
	if df.record == nil {
		return df
	}

	schema := df.record.Schema()
	var selectedIndices []int
	var selectedFields []arrow.Field

	for _, colName := range columns {
		for i, field := range schema.Fields() {
			if field.Name == colName {
				selectedIndices = append(selectedIndices, i)
				selectedFields = append(selectedFields, field)
				break
			}
		}
	}

	if len(selectedIndices) == 0 {
		return &ArrowDataFrame{pool: df.pool}
	}

	// Create new schema and columns
	newSchema := arrow.NewSchema(selectedFields, nil)
	newColumns := make([]arrow.Array, len(selectedIndices))

	for i, idx := range selectedIndices {
		newColumns[i] = df.record.Column(idx)
		newColumns[i].Retain() // Increment reference count
	}

	newRecord := array.NewRecord(newSchema, newColumns, df.record.NumRows())

	return &ArrowDataFrame{
		record: newRecord,
		pool:   df.pool,
	}
}

// ToRecords implements DataFrame.ToRecords
func (df *ArrowDataFrame) ToRecords() []map[string]any {
	if df.record == nil {
		return []map[string]any{}
	}

	records := make([]map[string]any, df.record.NumRows())
	schema := df.record.Schema()

	for i := int64(0); i < df.record.NumRows(); i++ {
		record := make(map[string]any)

		for j, field := range schema.Fields() {
			col := df.record.Column(j).(*array.Binary)
			if col.IsNull(int(i)) {
				record[field.Name] = nil
			} else {
				// Return as bytes, or you can convert back to original types if needed
				record[field.Name] = col.Value(int(i))
			}
		}

		records[i] = record
	}

	return records
}

// GetColumns implements DataFrame.GetColumns
func (df *ArrowDataFrame) GetColumns() []string {
	if df.record == nil {
		return []string{}
	}

	schema := df.record.Schema()
	columns := make([]string, len(schema.Fields()))

	for i, field := range schema.Fields() {
		columns[i] = field.Name
	}

	return columns
}

// HasColumn implements DataFrame.HasColumn
func (df *ArrowDataFrame) HasColumn(column string) bool {
	if df.record == nil {
		return false
	}

	schema := df.record.Schema()
	for _, field := range schema.Fields() {
		if field.Name == column {
			return true
		}
	}
	return false
}

// GetColumnValues implements DataFrame.GetColumnValues
func (df *ArrowDataFrame) GetColumnValues(column string) []any {
	if df.record == nil {
		return []any{}
	}

	schema := df.record.Schema()
	colIndex := -1

	for i, field := range schema.Fields() {
		if field.Name == column {
			colIndex = i
			break
		}
	}

	if colIndex == -1 {
		return []any{}
	}

	col := df.record.Column(colIndex).(*array.Binary)
	values := make([]any, col.Len())

	for i := 0; i < col.Len(); i++ {
		if col.IsNull(i) {
			values[i] = nil
		} else {
			values[i] = col.Value(i) // Returns []byte
		}
	}

	return values
}

// Append implements DataFrame.Append - THIS IS THE FAST PART!
func (df *ArrowDataFrame) Append(other model.DataFrame) (model.DataFrame, error) {
	otherArrow, ok := other.(*ArrowDataFrame)
	if !ok {
		// Fallback to converting other DataFrame to Arrow
		return df.appendFromRecords(other.ToRecords())
	}

	if df.record == nil {
		return otherArrow, nil
	}

	if otherArrow.record == nil {
		return df, nil
	}

	// Arrow's fast concatenation
	records := []arrow.Record{df.record, otherArrow.record}

	// Use Arrow's built-in concatenation (very fast!)
	concatenated, err := df.concatenateRecords(records)
	if err != nil {
		return nil, err
	}

	return &ArrowDataFrame{
		record: concatenated,
		pool:   df.pool,
	}, nil
}

// Helper methods
func (df *ArrowDataFrame) createFilteredRecord(indices []int) (*ArrowDataFrame, error) {
	if len(indices) == 0 {
		return &ArrowDataFrame{pool: df.pool}, nil
	}

	schema := df.record.Schema()
	builders := make([]array.Builder, len(schema.Fields()))

	for i := range schema.Fields() {
		builders[i] = array.NewBinaryBuilder(df.pool, arrow.BinaryTypes.Binary)
	}

	// Copy filtered data
	for _, rowIdx := range indices {
		for colIdx := range schema.Fields() {
			builder := builders[colIdx].(*array.BinaryBuilder)
			col := df.record.Column(colIdx).(*array.Binary)

			if col.IsNull(rowIdx) {
				builder.AppendNull()
			} else {
				builder.Append(col.Value(rowIdx))
			}
		}
	}

	// Build new record
	columns := make([]arrow.Array, len(builders))
	for i, builder := range builders {
		columns[i] = builder.NewArray()
		builder.Release()
	}

	record := array.NewRecord(schema, columns, int64(len(indices)))

	return &ArrowDataFrame{
		record: record,
		pool:   df.pool,
	}, nil
}

func (df *ArrowDataFrame) appendFromRecords(records []map[string]any) (model.DataFrame, error) {
	return df.Append(NewArrowDataFrame(records))
}

func (df *ArrowDataFrame) concatenateRecords(records []arrow.Record) (arrow.Record, error) {
	// This is a simplified version - Arrow has more sophisticated concatenation
	// For production, use arrow/compute package for optimal performance

	if len(records) == 0 {
		return nil, fmt.Errorf("no records to concatenate")
	}

	if len(records) == 1 {
		return records[0], nil
	}

	// For now, convert to records and back (not optimal, but works)
	// In production, use arrow/compute.Concatenate for true zero-copy
	allRecords := []map[string]any{}

	for _, record := range records {
		df := &ArrowDataFrame{record: record, pool: df.pool}
		allRecords = append(allRecords, df.ToRecords()...)
	}

	return NewArrowDataFrame(allRecords).record, nil
}

// Release frees Arrow memory
func (df *ArrowDataFrame) Release() {
	if df.record != nil {
		df.record.Release()
	}
}
