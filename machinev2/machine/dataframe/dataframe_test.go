package dataframe_test

import (
	"fmt"
	"testing"

	"github.com/minbzk/poc-machine-law/machinev2/machine/dataframe"
)

// Helper function to create test data
func createTestData(rows, cols int, prefix string) []map[string]any {
	data := make([]map[string]any, rows)
	for i := 0; i < rows; i++ {
		row := make(map[string]any)
		for j := 0; j < cols; j++ {
			row[fmt.Sprintf("%s_col_%d", prefix, j)] = fmt.Sprintf("%s_value_%d_%d", prefix, i, j)
		}
		data[i] = row
	}
	return data
}

func BenchmarkAppendSmall_Optimized(b *testing.B) {
	df1 := dataframe.New(createTestData(100, 5, "df1"))
	df2 := dataframe.New(createTestData(100, 5, "df2"))

	for b.Loop() {
		_, _ = df1.Append(df2)
	}
}

func BenchmarkAppendSmall_Arrow(b *testing.B) {
	df1 := dataframe.NewArrowDataFrame(createTestData(100, 5, "df1"))
	df2 := dataframe.NewArrowDataFrame(createTestData(100, 5, "df2"))

	for b.Loop() {
		_, _ = df1.Append(df2)
	}
}

func BenchmarkAppendSmall_CCSDF(b *testing.B) {
	df1 := dataframe.NewColumnDataFrame(createTestData(100, 5, "df1"))
	df2 := dataframe.NewColumnDataFrame(createTestData(100, 5, "df2"))

	for b.Loop() {
		_, _ = df1.Append(df2)
	}
}

func BenchmarkAppendMedium_Optimized(b *testing.B) {
	df1 := dataframe.New(createTestData(1000, 10, "df1"))
	df2 := dataframe.New(createTestData(1000, 10, "df2"))

	for b.Loop() {
		_, _ = df1.Append(df2)
	}
}

// Benchmark medium DataFrames (1000 rows, 10 columns each)
func BenchmarkAppendMedium_Arrow(b *testing.B) {
	df1 := dataframe.NewArrowDataFrame(createTestData(1000, 10, "df1"))
	df2 := dataframe.NewArrowDataFrame(createTestData(1000, 10, "df2"))

	for b.Loop() {
		_, _ = df1.Append(df2)
	}
}

// Benchmark medium DataFrames (1000 rows, 10 columns each)
func BenchmarkAppendMedium_CCSDF(b *testing.B) {
	df1 := dataframe.NewColumnDataFrame(createTestData(1000, 10, "df1"))
	df2 := dataframe.NewColumnDataFrame(createTestData(1000, 10, "df2"))

	for b.Loop() {
		_, _ = df1.Append(df2)
	}
}

func BenchmarkAppendLarge_Optimized(b *testing.B) {
	df1 := dataframe.New(createTestData(5000, 20, "df1"))
	df2 := dataframe.New(createTestData(5000, 20, "df2"))

	for b.Loop() {
		_, _ = df1.Append(df2)
	}
}

func BenchmarkAppendLarge_Arrow(b *testing.B) {
	df1 := dataframe.NewArrowDataFrame(createTestData(5000, 20, "df1"))
	df2 := dataframe.NewArrowDataFrame(createTestData(5000, 20, "df2"))

	for b.Loop() {
		_, _ = df1.Append(df2)
	}
}

func BenchmarkAppendLarge_CCSDF(b *testing.B) {
	df1 := dataframe.NewColumnDataFrame(createTestData(5000, 20, "df1"))
	df2 := dataframe.NewColumnDataFrame(createTestData(5000, 20, "df2"))

	for b.Loop() {
		_, _ = df1.Append(df2)
	}
}

func BenchmarkAppendMismatched_Optimized(b *testing.B) {
	df1 := dataframe.New(createTestData(1000, 8, "df1"))
	df2 := dataframe.New(createTestData(1000, 12, "df2")) // Different column count

	for b.Loop() {
		_, _ = df1.Append(df2)
	}
}

func BenchmarkAppendMismatched_Arrow(b *testing.B) {
	df1 := dataframe.NewArrowDataFrame(createTestData(1000, 8, "df1"))
	df2 := dataframe.NewArrowDataFrame(createTestData(1000, 12, "df2")) // Different column count

	for b.Loop() {
		_, _ = df1.Append(df2)
	}
}

func BenchmarkAppendMismatched_CCSDF(b *testing.B) {
	df1 := dataframe.NewColumnDataFrame(createTestData(1000, 8, "df1"))
	df2 := dataframe.NewColumnDataFrame(createTestData(1000, 12, "df2")) // Different column count

	for b.Loop() {
		_, _ = df1.Append(df2)
	}
}

func BenchmarkAppendMedium_Optimized_Allocs(b *testing.B) {
	df1 := dataframe.New(createTestData(1000, 10, "df1"))
	df2 := dataframe.New(createTestData(1000, 10, "df2"))

	b.ReportAllocs()
	for b.Loop() {
		_, _ = df1.Append(df2)
	}
}

func BenchmarkAppendMedium_Arrow_Allocs(b *testing.B) {
	df1 := dataframe.NewArrowDataFrame(createTestData(1000, 10, "df1"))
	df2 := dataframe.NewArrowDataFrame(createTestData(1000, 10, "df2"))

	b.ReportAllocs()
	for b.Loop() {
		_, _ = df1.Append(df2)
	}
}
func BenchmarkAppendMedium_CCSDF_Allocs(b *testing.B) {
	df1 := dataframe.NewColumnDataFrame(createTestData(1000, 10, "df1"))
	df2 := dataframe.NewColumnDataFrame(createTestData(1000, 10, "df2"))

	b.ReportAllocs()
	for b.Loop() {
		_, _ = df1.Append(df2)
	}
}
