package logger

import (
	"context"
	"fmt"
	"io"
	"os"
	"slices"
	"strings"

	"maps"

	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

var _ Logger = &LoggerImpl{}

// Logger interface defines the logging methods
type Logger interface {
	Debug(msg string, fields ...Field)
	Info(msg string, fields ...Field)
	Warning(msg string, fields ...Field)
	Error(msg string, fields ...Field)
	Debugf(format string, args ...any)
	Infof(format string, args ...any)
	Warningf(format string, args ...any)
	Errorf(format string, args ...any)
	WithName(name string) Logger
	WithService(service string) Logger
	WithLaw(law string) Logger
	WithField(key string, value any) Logger
	WithFields(fields ...Field) Logger
	WithIndent() Logger
	WithContext(context.Context) Logger
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
	Value any
}

func NewField(key string, value any) Field {
	return Field{
		Key:   key,
		Value: value,
	}
}

// LoggerImpl is the concrete implementation of Logger
type LoggerImpl struct {
	id              uuid.UUID
	logger          *logrus.Logger
	name            string
	service         string
	law             string
	fields          logrus.Fields
	IndentLvl       []LoggerIdent
	doubleLine      bool
	cachedBaseEntry *logrus.Entry
	Parent          *LoggerImpl
}

type LoggerIdent struct {
	Double bool
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

	id := uuid.New()
	// fmt.Printf("create logger: %s", id)

	return &LoggerImpl{
		id:     id,
		logger: l,
		name:   name,
		fields: make(logrus.Fields),
	}
}

// getIndent generates the indentation string with proper tree structure
func (l *LoggerImpl) getIndent() string {
	var sb strings.Builder

	collection := [][]LoggerIdent{l.IndentLvl}
	parent := l.Parent

	for parent != nil {
		collection = append(collection, parent.IndentLvl)
		parent = parent.Parent
	}

	slices.Reverse(collection)

	indents := []LoggerIdent{}
	for _, ids := range collection {
		indents = append(indents, ids...)
	}

	for i, indent := range indents {
		branch := BranchSingle
		pipe := PipeSingle

		if indent.Double {
			branch = BranchDouble
			pipe = PipeDouble
		}

		write := pipe
		if i == len(indents)-1 {
			write = branch
		}

		sb.WriteString(string(write))
		sb.WriteString(" ")
	}

	return sb.String()
}

// Debug logs a debug message with indentation
func (l *LoggerImpl) Debug(msg string, fields ...Field) {
	entry := l.createEntry(fields...)
	entry.Debug(l.getIndent() + msg)
}

// Debugf logs a debug message with indentation
func (l *LoggerImpl) Debugf(format string, args ...any) {

	entry := l.createEntry()
	entry.Debug(l.getIndent() + fmt.Sprintf(format, args...))
}

// Info logs an info message with indentation
func (l *LoggerImpl) Info(msg string, fields ...Field) {
	entry := l.createEntry(fields...)
	entry.Info(l.getIndent() + msg)
}

// Infof logs a debug message with indentation
func (l *LoggerImpl) Infof(format string, args ...any) {
	entry := l.createEntry()
	entry.Info(l.getIndent() + fmt.Sprintf(format, args...))
}

// Warning logs a warning message with indentation
func (l *LoggerImpl) Warning(msg string, fields ...Field) {
	entry := l.createEntry(fields...)
	entry.Warn(l.getIndent() + msg)
}

// Warningf logs a debug message with indentation
func (l *LoggerImpl) Warningf(format string, args ...any) {
	entry := l.createEntry()
	entry.Warn(l.getIndent() + fmt.Sprintf(format, args...))
}

// Error logs an error message with indentation
func (l *LoggerImpl) Error(msg string, fields ...Field) {
	entry := l.createEntry(fields...)
	entry.Error(l.getIndent() + msg)
}

// Errorf logs a debug message with indentation
func (l *LoggerImpl) Errorf(format string, args ...any) {
	entry := l.createEntry()
	entry.Error(l.getIndent() + fmt.Errorf(format, args...).Error())
}

func (l *LoggerImpl) WithName(name string) Logger {
	other := copyLogger(l)
	other.name = name

	return other
}

func (l *LoggerImpl) WithService(service string) Logger {
	other := copyLogger(l)
	other.service = service

	return other
}

func (l *LoggerImpl) WithLaw(law string) Logger {
	other := copyLogger(l)
	other.law = law

	return other
}

// WithField returns a new logger with an additional field
func (l *LoggerImpl) WithField(key string, value any) Logger {
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

func (l *LoggerImpl) WithContext(ctx context.Context) Logger {
	other := FromContext(ctx).(*LoggerImpl)

	// fmt.Printf("pointers base: %p ctx: %p\n", l, other)

	logger := copyLogger(other)

	parent := other.Parent
	if l == other {
		parent = l.Parent
	}

	logger.Parent = parent

	return logger
}

// WithIndent returns a new logger with increased indentation level
func (l *LoggerImpl) WithIndent() Logger {
	return l.withIndentValue(1)
}

// WithIndent returns a new logger with increased indentation level
func (l *LoggerImpl) withIndentValue(v int) Logger {
	other := copyLogger(l)
	// other.IndentLvl = make([]LoggerIdent, 0, v)

	for range v {
		other.IndentLvl = append(other.IndentLvl, LoggerIdent{Double: l.doubleLine})
	}

	l.doubleLine = false
	other.Parent = l.Parent

	return other
}

// IndentBlock executes a function within an indented logging block
func (l *LoggerImpl) IndentBlock(ctx context.Context, msg string, fn func(context.Context) error, options ...Options) error {
	if msg != "" {
		l.Info(msg)
	}

	logger := l.WithContext(ctx).(*LoggerImpl)
	for _, option := range options {
		if err := option(logger); err != nil {
			return fmt.Errorf("could not apply option: %v", option)
		}
	}

	return fn(WithLogger(ctx, logger.WithIndent()))
}

// createEntry creates a logrus entry with all fields and context values
func (l *LoggerImpl) createEntry(fields ...Field) *logrus.Entry {
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

func copyLogger(l *LoggerImpl) *LoggerImpl {
	id := uuid.New()
	// fmt.Printf("copy logger\tid: %s\tnew: %s\n", l.id, id)

	return &LoggerImpl{
		id:        id,
		logger:    l.logger,
		name:      l.name,
		service:   l.service,
		law:       l.law,
		IndentLvl: l.IndentLvl,
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
	return New("default", os.Stdout, logrus.DebugLevel)
}

type TreeChar string

const (
	PipeSingle   TreeChar = "│  "
	BranchSingle TreeChar = "├──"
	LeafSingle   TreeChar = "└──"

	PipeDouble   TreeChar = "║  "
	BranchDouble TreeChar = "╠══"
	LeadDouble   TreeChar = "╚══"

	Space TreeChar = "   "
)

func (l *LoggerImpl) Print(name string) {
	fmt.Printf("LOGGER\t%s %s\tidentlevels: %d\tid: %s\n", l.name, name, len(l.IndentLvl), l.id)
	if l.Parent != nil {
		l.Parent.Print(fmt.Sprintf("Parent %p %s", l.Parent, name))
	}
}
