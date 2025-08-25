package logger_test

import (
	"context"
	"fmt"
	"maps"
	"os"
	"sync"
	"testing"

	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/logger"
	"github.com/sirupsen/logrus"
)

func TestLogger(t *testing.T) {
	var logr logger.Logger = logger.New("test", os.Stdout, logrus.DebugLevel)

	ctx := t.Context()

	logr.Debug("HI")

	ctx = logger.WithLogger(ctx, logr)

	logger2 := logger.FromContext(ctx)
	logger2.Debug("WOW")
	logger2.Warning("asdf")
	logger2.WithIndent().Warning("asdf 2")

	// logger2 -> default
	//
	//
	//
	//
	//
	//

	logger2.IndentBlock(context.Background(), "What", func(ctx context.Context) error {
		logr := logger.FromContext(ctx)

		logr.Info("This")

		logr.IndentBlock(ctx, "What 2", func(ctx context.Context) error {
			logr := logger.FromContext(ctx)

			logr.Info("This 2")

			logr.(*logger.LoggerImpl).Print("test1")

			logr.IndentBlock(ctx, "What 3", func(ctx context.Context) error {
				logr := logger.FromContext(ctx)

				logr.(*logger.LoggerImpl).Print("test2")
				logr.Info("This 3")

				return nil
			})

			return nil
		})

		return nil
	},
		logger.OptionWithDoubleLine,
	)

	test(logr, ctx, "test", 2)
	test(logr, ctx, "test", 2)
}

func TestRace(t *testing.T) {
	var logger logger.Logger = logger.New("test", os.Stdout, logrus.DebugLevel)

	var wg sync.WaitGroup
	for range 100 {
		wg.Add(1)
		go func() {
			defer wg.Done()
			// Access the shared resource
			test(logger, t.Context(), "test", 2)
		}()
	}

	wg.Wait()
}

func test(logr logger.Logger, ctx context.Context, path string, index int) {
	var op []logger.Options
	if index == 1 {
		op = append(op, logger.OptionWithDoubleLine)
	}
	if err := logr.IndentBlock(ctx, fmt.Sprintf("Resolving path: %v", path), func(ctx context.Context) error {
		logr := logger.FromContext(ctx)

		if index != 0 {
			test(logr, ctx, path, index-1)
		}

		logr.Debugf("what is going on")
		logr.WithIndent().Info("this is going on")

		logr.Debugf("Result")
		return nil
	},
		op...,
	); err != nil {
		logr.Error("error")
	}
}

// Field represents a key-value pair for logger
type Field struct {
	Key   string
	Value interface{}
}

// Mocked LoggerImpl for testing
type LoggerImpl struct {
	logger          *logrus.Logger
	fields          logrus.Fields
	name            string
	service         string
	law             string
	cachedBaseEntry *logrus.Entry
}

// Original implementation
func (l *LoggerImpl) createEntryOriginal(fields ...Field) *logrus.Entry {
	allFields := make(logrus.Fields, len(l.fields)+len(fields)+3)
	maps.Copy(allFields, l.fields)
	// Add component name
	allFields["component"] = l.name
	if l.service != "" {
		allFields["service"] = l.service
	}
	if l.law != "" {
		allFields["law"] = l.law
	}
	// Add immediate fields
	for _, f := range fields {
		allFields[f.Key] = f.Value
	}
	return l.logger.WithFields(allFields)
}

// Optimized implementation with single WithFields call
func (l *LoggerImpl) createEntryOptimized(fields ...Field) *logrus.Entry {
	// Calculate the exact size needed for immediate fields
	immediateFieldCount := len(fields)
	if l.name != "" {
		immediateFieldCount++
	}
	if l.service != "" {
		immediateFieldCount++
	}
	if l.law != "" {
		immediateFieldCount++
	}

	// Create a map only for the immediate fields
	immediateFields := make(logrus.Fields, immediateFieldCount)

	// Add component name and optional fields
	immediateFields["component"] = l.name

	if l.service != "" {
		immediateFields["service"] = l.service
	}

	if l.law != "" {
		immediateFields["law"] = l.law
	}

	// Add custom fields
	for _, f := range fields {
		immediateFields[f.Key] = f.Value
	}

	// Start with the logger's base fields, then add immediate fields in one call
	return l.logger.WithFields(l.fields).WithFields(immediateFields)
}

// Cached implementation that reuses cached entry for empty fields
func (l *LoggerImpl) createEntryCached(fields ...Field) *logrus.Entry {
	// If no immediate fields, use/create cached base entry
	if len(fields) == 0 {
		if l.cachedBaseEntry == nil {
			baseFields := make(logrus.Fields, len(l.fields)+3)
			maps.Copy(baseFields, l.fields)
			baseFields["component"] = l.name
			if l.service != "" {
				baseFields["service"] = l.service
			}
			if l.law != "" {
				baseFields["law"] = l.law
			}
			l.cachedBaseEntry = l.logger.WithFields(baseFields)
		}
		return l.cachedBaseEntry
	}

	// For cases with fields, create a comprehensive map
	allFields := make(logrus.Fields, len(l.fields)+len(fields)+3)
	maps.Copy(allFields, l.fields)

	// Add component name and optional fields
	allFields["component"] = l.name
	if l.service != "" {
		allFields["service"] = l.service
	}
	if l.law != "" {
		allFields["law"] = l.law
	}

	// Add immediate fields
	for _, f := range fields {
		allFields[f.Key] = f.Value
	}

	return l.logger.WithFields(allFields)
}

// Setup function for creating a test logger
func setupLogger() *LoggerImpl {
	logger := logrus.New()
	logger.SetLevel(logrus.InfoLevel)
	// Discard output for benchmarking
	logger.SetOutput(nil)

	return &LoggerImpl{
		logger:  logger,
		fields:  logrus.Fields{"app": "test", "version": "1.0"},
		name:    "benchmark-component",
		service: "test-service",
		law:     "test-law",
	}
}

// Test helper to create varying numbers of fields
func createFields(count int) []Field {
	fields := make([]Field, count)
	for i := range count {
		fields[i] = Field{
			Key:   "field" + string(rune('A'+i)),
			Value: i,
		}
	}
	return fields
}

// Benchmark the original implementation with 0 fields
func BenchmarkCreateEntryOriginal_0Fields(b *testing.B) {
	l := setupLogger()
	b.ResetTimer()
	for b.Loop() {
		l.createEntryOriginal()
	}
}

// Benchmark the original implementation with 5 fields
func BenchmarkCreateEntryOriginal_5Fields(b *testing.B) {
	l := setupLogger()
	fields := createFields(5)
	b.ResetTimer()
	for b.Loop() {
		l.createEntryOriginal(fields...)
	}
}

// Benchmark the original implementation with 10 fields
func BenchmarkCreateEntryOriginal_10Fields(b *testing.B) {
	l := setupLogger()
	fields := createFields(10)
	b.ResetTimer()
	for b.Loop() {
		l.createEntryOriginal(fields...)
	}
}

// Benchmark the optimized implementation with 0 fields
func BenchmarkCreateEntryOptimized_0Fields(b *testing.B) {
	l := setupLogger()
	b.ResetTimer()
	for b.Loop() {
		l.createEntryOptimized()
	}
}

// Benchmark the optimized implementation with 5 fields
func BenchmarkCreateEntryOptimized_5Fields(b *testing.B) {
	l := setupLogger()
	fields := createFields(5)
	b.ResetTimer()
	for b.Loop() {
		l.createEntryOptimized(fields...)
	}
}

// Benchmark the optimized implementation with 10 fields
func BenchmarkCreateEntryOptimized_10Fields(b *testing.B) {
	l := setupLogger()
	fields := createFields(10)
	b.ResetTimer()
	for b.Loop() {
		l.createEntryOptimized(fields...)
	}
}

// Benchmark the cached implementation with 0 fields
func BenchmarkCreateEntryCached_0Fields(b *testing.B) {
	l := setupLogger()
	b.ResetTimer()
	for b.Loop() {
		l.createEntryCached()
	}
}

// Benchmark the cached implementation with 5 fields
func BenchmarkCreateEntryCached_5Fields(b *testing.B) {
	l := setupLogger()
	fields := createFields(5)
	b.ResetTimer()
	for b.Loop() {
		l.createEntryCached(fields...)
	}
}

// Benchmark the cached implementation with 10 fields
func BenchmarkCreateEntryCached_10Fields(b *testing.B) {
	l := setupLogger()
	fields := createFields(10)
	b.ResetTimer()
	for b.Loop() {
		l.createEntryCached(fields...)
	}
}

// Benchmark for allocation profiling with original implementation
func BenchmarkCreateEntryOriginalAlloc(b *testing.B) {
	b.ReportAllocs()
	l := setupLogger()
	fields := createFields(5)
	b.ResetTimer()
	for b.Loop() {
		l.createEntryOriginal(fields...)
	}
}

// Benchmark for allocation profiling with optimized implementation
func BenchmarkCreateEntryOptimizedAlloc(b *testing.B) {
	b.ReportAllocs()
	l := setupLogger()
	fields := createFields(5)
	b.ResetTimer()
	for b.Loop() {
		l.createEntryOptimized(fields...)
	}
}

// Benchmark for allocation profiling with cached implementation
func BenchmarkCreateEntryCachedAlloc(b *testing.B) {
	b.ReportAllocs()
	l := setupLogger()
	fields := createFields(5)
	b.ResetTimer()
	for b.Loop() {
		l.createEntryCached(fields...)
	}
}

// Benchmark for a real-world scenario with mixed calls (mostly empty fields)
func BenchmarkMixedloggerScenario(b *testing.B) {
	l := setupLogger()
	fields1 := createFields(1)
	fields5 := createFields(5)
	b.ResetTimer()

	for i := range b.N {
		// Simulate typical logger pattern: 80% with no fields, 15% with 1 field, 5% with multiple fields
		switch i % 20 {
		case 0, 1, 2:
			l.createEntryOriginal(fields1...)
		case 4:
			l.createEntryOriginal(fields5...)
		default:
			l.createEntryOriginal()
		}
	}
}

// Same mixed scenario with optimized implementation
func BenchmarkMixedloggerScenarioOptimized(b *testing.B) {
	l := setupLogger()
	fields1 := createFields(1)
	fields5 := createFields(5)
	b.ResetTimer()

	for i := range b.N {
		switch i % 20 {
		case 0, 1, 2:
			l.createEntryOptimized(fields1...)
		case 4:
			l.createEntryOptimized(fields5...)
		default:
			l.createEntryOptimized()
		}
	}
}

// Same mixed scenario with cached implementation
func BenchmarkMixedloggerScenarioCached(b *testing.B) {
	l := setupLogger()
	fields1 := createFields(1)
	fields5 := createFields(5)
	b.ResetTimer()

	for i := range b.N {
		switch i % 20 {
		case 0, 1, 2:
			l.createEntryCached(fields1...)
		case 4:
			l.createEntryCached(fields5...)
		default:
			l.createEntryCached()
		}
	}
}
