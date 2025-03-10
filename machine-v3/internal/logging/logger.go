package logging

import (
	"context"
	"fmt"
	"sync"

	"github.com/sirupsen/logrus"
)

func init() {
	loggers = make(map[string]*Logger)
}

// Increase increments the indentation level
func (g *GlobalIndent) Increase(doubleLine bool) {
	g.mu.Lock()
	defer g.mu.Unlock()

	g.Level++
	g.ActiveBranches[g.Level-1] = true
	if doubleLine {
		g.DoubleLines[g.Level-1] = true
	}
}

// Decrease decrements the indentation level
func (g *GlobalIndent) Decrease() {
	g.mu.Lock()
	defer g.mu.Unlock()

	if g.Level > 0 {
		delete(g.ActiveBranches, g.Level-1)
		delete(g.DoubleLines, g.Level-1)
		g.Level--
	}
}

// GetIndent returns the current indentation string
func (g *GlobalIndent) GetIndent() string {
	g.mu.Lock()
	defer g.mu.Unlock()

	if g.Level == 0 {
		return ""
	}

	var result string

	// For all levels except current, show pipe only if level is still active
	for i := 0; i < g.Level-1; i++ {
		if _, active := g.ActiveBranches[i]; active {
			chars := SingleTreeChars
			if _, isDouble := g.DoubleLines[i]; isDouble {
				chars = DoubleTreeChars
			}
			result += chars.Pipe + chars.Space
		} else {
			result += "    "
		}
	}

	// For current level, use leaf if not active (end of block)
	chars := SingleTreeChars
	if _, isDouble := g.DoubleLines[g.Level-1]; isDouble {
		chars = DoubleTreeChars
	}

	_, isEnd := g.ActiveBranches[g.Level-1]
	if !isEnd {
		result += chars.Leaf
	} else {
		result += chars.Branch
	}

	return result
}

// IndentLogger provides indented logging functionality
type Logger struct {
	logger *logrus.Logger
	name   string
}

// IndentEntry is a wrapper around a log entry with indentation
type IndentEntry struct {
	entry *logrus.Entry
}

// NewLogger creates a new IndentLogger
func NewLogger(name string) *Logger {
	logger := logrus.New()
	logger.SetFormatter(&logrus.TextFormatter{
		DisableTimestamp: false,
		FullTimestamp:    true,
		ForceColors:      true,
	})

	return &Logger{
		logger: logger,
		name:   name,
	}
}

// WithIndent returns an IndentEntry with indentation
func (l *Logger) WithIndent() *IndentEntry {
	entry := l.logger.WithField("component", l.name)
	return &IndentEntry{entry: entry}
}

// SetLevel sets the logging level
func (l *Logger) SetLevel(level logrus.Level) {
	l.logger.SetLevel(level)
}

// Debugf logs a debug message with indentation
func (e *IndentEntry) Debugf(format string, args ...interface{}) {
	e.entry.Debugf("%s %s", global.GetIndent(), fmt.Sprintf(format, args...))
}

// Infof logs an info message with indentation
func (e *IndentEntry) Infof(format string, args ...interface{}) {
	e.entry.Infof("%s %s", global.GetIndent(), fmt.Sprintf(format, args...))
}

// Warningf logs a warning message with indentation
func (e *IndentEntry) Warningf(format string, args ...interface{}) {
	e.entry.Warnf("%s %s", global.GetIndent(), fmt.Sprintf(format, args...))
}

// Errorf logs an error message with indentation
func (e *IndentEntry) Errorf(format string, args ...interface{}) {
	e.entry.Errorf("%s %s", global.GetIndent(), fmt.Sprintf(format, args...))
}

// GetLogger returns a logger for the given name
func GetLogger(name string) *Logger {
	loggersMutex.Lock()
	defer loggersMutex.Unlock()

	if logger, exists := loggers[name]; exists {
		return logger
	}

	logger := NewLogger(name)
	loggers[name] = logger
	return logger
}

// IndentBlock executes a function within an indented block
func IndentBlock(ctx context.Context, initialMessage string, doubleLine bool, fn func(context.Context) error) error {
	logger := GetLogger("system")

	if initialMessage != "" {
		logger.WithIndent().Debugf(initialMessage)
	}

	global.Increase(doubleLine)
	defer global.Decrease()

	return fn(ctx)
}

// ConfigureLogging sets up logging with the specified level
func ConfigureLogging(level string) {
	// Parse level string
	logLevel := logrus.InfoLevel
	switch level {
	case "debug":
		logLevel = logrus.DebugLevel
	case "info":
		logLevel = logrus.InfoLevel
	case "warn", "warning":
		logLevel = logrus.WarnLevel
	case "error":
		logLevel = logrus.ErrorLevel
	}

	// Configure loggers
	logComponents := []string{
		"rules_engine",
		"service",
		"rule_context",
		"logger",
		"system",
	}

	for _, component := range logComponents {
		logger := GetLogger(component)
		logger.SetLevel(logLevel)
	}
}

// GlobalIndent manages indentation globally across threads
type GlobalIndent struct {
	Level          int
	ActiveBranches map[int]bool
	DoubleLines    map[int]bool
	mu             sync.Mutex
}

// TreeChars defines characters used for tree-like output
type TreeChars struct {
	Pipe   string
	Branch string
	Leaf   string
	Space  string
}

var (
	global = &GlobalIndent{
		Level:          0,
		ActiveBranches: make(map[int]bool),
		DoubleLines:    make(map[int]bool),
		mu:             sync.Mutex{},
	}

	SingleTreeChars = TreeChars{
		Pipe:   "│",
		Branch: "├──",
		Leaf:   "└──",
		Space:  "   ",
	}

	DoubleTreeChars = TreeChars{
		Pipe:   "║",
		Branch: "║──",
		Leaf:   "╚══",
		Space:  "   ",
	}

	loggers      map[string]*Logger
	loggersMutex sync.Mutex
)
