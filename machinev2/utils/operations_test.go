package utils_test

import (
	"fmt"
	"testing"

	"github.com/minbzk/poc-machine-law/machinev2/utils"
)

type testCase struct {
	name     string
	a        any
	b        any
	expected bool
	err      error
}

func TestCompare(t *testing.T) {
	tests := []testCase{
		// Basic same-type comparisons
		{
			name:     "Equal integers",
			a:        42,
			b:        42,
			expected: true,
			err:      nil,
		},
		{
			name:     "Unequal integers",
			a:        42,
			b:        43,
			expected: false,
			err:      nil,
		},
		{
			name:     "Equal strings",
			a:        "hello",
			b:        "hello",
			expected: true,
			err:      nil,
		},
		{
			name:     "Unequal strings",
			a:        "hello",
			b:        "world",
			expected: false,
			err:      nil,
		},
		{
			name:     "Equal booleans",
			a:        true,
			b:        true,
			expected: true,
			err:      nil,
		},
		{
			name:     "Unequal booleans",
			a:        true,
			b:        false,
			expected: false,
			err:      nil,
		},

		// Cross-type numeric comparisons
		{
			name:     "Int to float64 equal",
			a:        int(1),
			b:        float64(1.0),
			expected: true,
			err:      nil,
		},
		{
			name:     "Int to float64 unequal",
			a:        int(1),
			b:        float64(1.1),
			expected: false,
			err:      nil,
		},
		{
			name:     "Int8 to int32 equal",
			a:        int8(10),
			b:        int32(10),
			expected: true,
			err:      nil,
		},
		{
			name:     "Uint to int equal values",
			a:        uint(5),
			b:        int(5),
			expected: true,
			err:      nil,
		},
		{
			name:     "Int16 to float32 equal",
			a:        int16(25),
			b:        float32(25.0),
			expected: true,
			err:      nil,
		},
		{
			name:     "Float32 to float64 equal",
			a:        float32(3.14),
			b:        float64(3.14),
			expected: true,
			err:      nil,
		},

		// Nil and pointer cases
		{
			name:     "Both nil",
			a:        nil,
			b:        nil,
			expected: true,
			err:      nil,
		},
		{
			name:     "One nil",
			a:        42,
			b:        nil,
			expected: false,
			err:      nil,
		},
		{
			name:     "Equal pointers to same value",
			a:        &struct{ X int }{X: 5},
			b:        &struct{ X int }{X: 5},
			expected: true,
			err:      nil,
		},
		{
			name:     "Unequal pointers",
			a:        &struct{ X int }{X: 5},
			b:        &struct{ X int }{X: 10},
			expected: false,
			err:      nil,
		},

		// Slice and array comparisons
		{
			name:     "Equal slices",
			a:        []int{1, 2, 3},
			b:        []int{1, 2, 3},
			expected: true,
			err:      nil,
		},
		{
			name:     "Unequal slices",
			a:        []int{1, 2, 3},
			b:        []int{1, 2, 4},
			expected: false,
			err:      nil,
		},
		{
			name:     "Different length slices",
			a:        []int{1, 2, 3},
			b:        []int{1, 2},
			expected: false,
			err:      nil,
		},
		{
			name:     "Empty slices",
			a:        []int{},
			b:        []int{},
			expected: true,
			err:      nil,
		},
		{
			name:     "Array to slice with same values",
			a:        [3]int{1, 2, 3},
			b:        []int{1, 2, 3},
			expected: false, // Different types
			err:      fmt.Errorf("cannot compare values of types [3]int and []int"),
		},

		// Map comparisons
		{
			name:     "Equal maps",
			a:        map[string]int{"a": 1, "b": 2},
			b:        map[string]int{"a": 1, "b": 2},
			expected: true,
			err:      nil,
		},
		{
			name:     "Unequal maps (different values)",
			a:        map[string]int{"a": 1, "b": 2},
			b:        map[string]int{"a": 1, "b": 3},
			expected: false,
			err:      nil,
		},
		{
			name:     "Unequal maps (different keys)",
			a:        map[string]int{"a": 1, "b": 2},
			b:        map[string]int{"a": 1, "c": 2},
			expected: false,
			err:      nil,
		},
		{
			name:     "Empty maps",
			a:        map[string]int{},
			b:        map[string]int{},
			expected: true,
			err:      nil,
		},

		// Struct comparisons
		{
			name: "Equal structs",
			a: struct {
				Name string
				Age  int
			}{"John", 30},
			b: struct {
				Name string
				Age  int
			}{"John", 30},
			expected: true,
			err:      nil,
		},
		{
			name: "Unequal structs",
			a: struct {
				Name string
				Age  int
			}{"John", 30},
			b: struct {
				Name string
				Age  int
			}{"John", 31},
			expected: false,
			err:      nil,
		},
		{
			name: "Different struct types",
			a: struct {
				Name string
				Age  int
			}{"John", 30},
			b: struct {
				First string
				Years int
			}{"John", 30},
			expected: false,
			err:      fmt.Errorf("cannot compare values of types struct { Name string; Age int } and struct { First string; Years int }"),
		},

		// Complex nested types
		{
			name:     "Complex nested equal",
			a:        map[string][]int{"nums": {1, 2, 3}, "more": {4, 5, 6}},
			b:        map[string][]int{"nums": {1, 2, 3}, "more": {4, 5, 6}},
			expected: true,
			err:      nil,
		},
		{
			name:     "Complex nested unequal",
			a:        map[string][]int{"nums": {1, 2, 3}, "more": {4, 5, 6}},
			b:        map[string][]int{"nums": {1, 2, 3}, "more": {4, 5, 7}},
			expected: false,
			err:      nil,
		},

		// Incomparable types
		{
			name:     "String to int",
			a:        "42",
			b:        42,
			expected: false,
			err:      fmt.Errorf("cannot compare values of types string and int"),
		},
		{
			name:     "Func to int",
			a:        func() {},
			b:        42,
			expected: false,
			err:      fmt.Errorf("cannot compare values of types func() and int"),
		},
		{
			name:     "Chan to slice",
			a:        make(chan int),
			b:        []int{1, 2, 3},
			expected: false,
			err:      fmt.Errorf("cannot compare values of types chan int and []int"),
		},
		{
			name:     "types who are both strings",
			a:        StatusActive,
			b:        "active",
			expected: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			actual, err := utils.Equal(tt.a, tt.b)

			if tt.err == nil && err != nil {
				t.Errorf("Expected no error, got: %v", err)
			} else if tt.err != nil && err == nil {
				t.Errorf("Expected error: %v, got nil", tt.err)
			} else if tt.err != nil && err != nil && tt.err.Error() != err.Error() {
				t.Errorf("Expected error: %v, got: %v", tt.err, err)
			}

			if actual != tt.expected {
				t.Errorf("Expected %v, got %v", tt.expected, actual)
			}
		})
	}
}

type Status string

const (
	StatusActive Status = "active"
)
