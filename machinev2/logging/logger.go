package logging

import (
	"context"
	"fmt"
	"io"
	"os"

	"maps"

	"github.com/sirupsen/logrus"
)

var _ Logger = &LoggerImpl{}

// Logger interface defines the logging methods
type Logger interface {
	Debug(ctx context.Context, msg string, fields ...Field)
	Info(ctx context.Context, msg string, fields ...Field)
	Warning(ctx context.Context, msg string, fields ...Field)
	Error(ctx context.Context, msg string, fields ...Field)
	Debugf(ctx context.Context, format string, args ...any)
	Infof(ctx context.Context, format string, args ...any)
	Warningf(ctx context.Context, format string, args ...any)
	Errorf(ctx context.Context, format string, args ...any)
	WithName(name string) Logger
	WithService(svc string) Logger
	WithLaw(law string) Logger
	WithField(key string, value any) Logger
	WithFields(fields ...Field) Logger
	WithIndent() Logger
	IndentBlock(ctx context.Context, msg string, fn func(context.Context) error, op ...Options) error
}

type Options func(l *LoggerImpl) error

func OptionWithDoubleLine(l *LoggerImpl) error {
	l.doubleLine = true
	return nil
}

// Field represents a key-value pair for structured logging
type Field struct {
	Key   string
	Value interface{}
}

// LoggerImpl is the concrete implementation of Logger
type LoggerImpl struct {
	logger     *logrus.Logger
	name       string
	service    string
	law        string
	fields     logrus.Fields
	indentLvl  int
	doubleLine bool
}

// New creates a new logger instance
func New(name string, output io.Writer, level logrus.Level) *LoggerImpl {
	l := logrus.New()
	l.SetOutput(output)
	l.SetLevel(level)
	l.SetFormatter(&logrus.TextFormatter{
		ForceColors:      true,
		DisableColors:    false,
		DisableTimestamp: false,
		FullTimestamp:    false,
		ForceQuote:       true,
	})

	return &LoggerImpl{
		logger: l,
		name:   name,
		fields: make(logrus.Fields),
	}
}

// getIndent generates the indentation string with proper tree structure
func (l *LoggerImpl) getIndent(ctx context.Context) string {
	other := FromContext(ctx).(*LoggerImpl)

	total := l.indentLvl + other.indentLvl

	if total == 0 {
		return ""
	}

	var indent string

	for i := range total {
		if l.doubleLine {

			if i == total-1 {
				indent += string(BranchDouble)
			} else {
				indent += string(PipeDouble)
			}
		}

		if i == total-1 {
			indent += string(BranchSingle)
		} else {
			indent += string(PipeSingle)
		}

		indent += " "
	}

	return indent
}

// Debug logs a debug message with indentation
func (l *LoggerImpl) Debug(ctx context.Context, msg string, fields ...Field) {
	entry := l.createEntry(fields...)
	entry.Debug(l.getIndent(ctx) + msg)
}

// Debugf logs a debug message with indentation
func (l *LoggerImpl) Debugf(ctx context.Context, format string, args ...any) {

	entry := l.createEntry()
	entry.Debug(l.getIndent(ctx) + fmt.Sprintf(format, args...))
}

// Info logs an info message with indentation
func (l *LoggerImpl) Info(ctx context.Context, msg string, fields ...Field) {
	entry := l.createEntry(fields...)
	entry.Info(l.getIndent(ctx) + msg)
}

// Infof logs a debug message with indentation
func (l *LoggerImpl) Infof(ctx context.Context, format string, args ...any) {
	entry := l.createEntry()
	entry.Info(l.getIndent(ctx) + fmt.Sprintf(format, args...))
}

// Warning logs a warning message with indentation
func (l *LoggerImpl) Warning(ctx context.Context, msg string, fields ...Field) {
	entry := l.createEntry(fields...)
	entry.Warn(l.getIndent(ctx) + msg)
}

// Warningf logs a debug message with indentation
func (l *LoggerImpl) Warningf(ctx context.Context, format string, args ...any) {
	entry := l.createEntry()
	entry.Warn(l.getIndent(ctx) + fmt.Sprintf(format, args...))
}

// Error logs an error message with indentation
func (l *LoggerImpl) Error(ctx context.Context, msg string, fields ...Field) {
	entry := l.createEntry(fields...)
	entry.Error(l.getIndent(ctx) + msg)
}

// Errorf logs a debug message with indentation
func (l *LoggerImpl) Errorf(ctx context.Context, format string, args ...any) {
	entry := l.createEntry()
	entry.Error(l.getIndent(ctx) + fmt.Sprintf(format, args...))
}

func (l *LoggerImpl) WithName(name string) Logger {
	other := copyLogger(l)
	other.name = name

	return other
}

func (l *LoggerImpl) WithService(svc string) Logger {
	other := copyLogger(l)
	other.service = svc

	return other
}

func (l *LoggerImpl) WithLaw(law string) Logger {
	other := copyLogger(l)
	other.law = law

	return other
}

// WithField returns a new logger with an additional field
func (l *LoggerImpl) WithField(key string, value interface{}) Logger {
	newFields := make(logrus.Fields, len(l.fields)+1)
	maps.Copy(newFields, l.fields)

	newFields[key] = value

	other := copyLogger(l)
	other.fields = newFields

	return other
}

// WithFields returns a new logger with additional fields
func (l *LoggerImpl) WithFields(fields ...Field) Logger {
	newFields := make(logrus.Fields, len(l.fields)+len(fields))
	maps.Copy(newFields, l.fields)

	for _, f := range fields {
		newFields[f.Key] = f.Value
	}

	other := copyLogger(l)
	other.fields = newFields

	return other
}

// WithIndent returns a new logger with increased indentation level
func (l *LoggerImpl) WithIndent() Logger {
	return l.WithIndentValue(1)
}

// WithIndent returns a new logger with increased indentation level
func (l *LoggerImpl) WithIndentValue(v int) Logger {
	other := copyLogger(l)
	other.indentLvl += v

	return other
}

// IndentBlock executes a function within an indented logging block
func (l *LoggerImpl) IndentBlock(ctx context.Context, msg string, fn func(context.Context) error, options ...Options) error {
	for _, option := range options {
		option(l)
	}

	if msg != "" {
		l.Info(ctx, msg)
	}

	other := FromContext(ctx).(*LoggerImpl)

	return fn(WithLogger(ctx, l.WithIndentValue(1+other.indentLvl)))
}

// createEntry creates a logrus entry with all fields and context values
func (l *LoggerImpl) createEntry(fields ...Field) *logrus.Entry {
	allFields := make(logrus.Fields, len(l.fields)+len(fields)+1)
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

func copyLogger(l *LoggerImpl) *LoggerImpl {
	return &LoggerImpl{
		logger:    l.logger,
		name:      l.name,
		service:   l.service,
		law:       l.law,
		indentLvl: l.indentLvl,
	}
}

// contextKey is a private type for context keys
type contextKey struct{}

var loggerKey = &contextKey{}

// WithLogger adds a logger to the context
func WithLogger(ctx context.Context, logger Logger) context.Context {
	return context.WithValue(ctx, loggerKey, logger)
}

// FromContext retrieves the logger from context
func FromContext(ctx context.Context) Logger {
	if logger, ok := ctx.Value(loggerKey).(Logger); ok {
		return logger
	}

	// Return a default logger if none is found in context
	return New("default", os.Stdout, logrus.InfoLevel)
}

type TreeChar string

const (
	PipeSingle   TreeChar = "│  "
	BranchSingle TreeChar = "├──"
	LeafSingle   TreeChar = "└──"

	PipeDouble   TreeChar = "║  "
	BranchDouble TreeChar = "║──"
	LeadDouble   TreeChar = "╚══"

	Space TreeChar = "   "
)
