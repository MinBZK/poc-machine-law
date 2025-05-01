package model

// DataFrame is an interface that abstracts DataFrame operations
type DataFrame interface {
	// Filter filters the DataFrame based on column, operator, and value
	Filter(column, operator string, value any) (DataFrame, error)

	// Select returns a new DataFrame with only the specified columns
	Select(columns []string) DataFrame

	// ToRecords converts the DataFrame to a slice of maps
	ToRecords() []map[string]any

	GetColumns() []string

	// HasColumn checks if the DataFrame has a column
	HasColumn(column string) bool

	// GetColumnValues returns all values from a column
	GetColumnValues(column string) []any

	Append(df DataFrame) (DataFrame, error)
}

type SourceDataFrame interface {
	Get(table string) (DataFrame, bool)
	Set(table string, df DataFrame)
	Reset()
}
