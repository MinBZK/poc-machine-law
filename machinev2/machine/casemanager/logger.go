package casemanager

import (
	"context"

	eh "github.com/looplab/eventhorizon"
	"github.com/minbzk/poc-machine-law/machinev2/machine/logger"
)

// LoggingMiddleware is a tiny command handle middleware for logger.
func LoggingMiddleware(logr logger.Logger) func(h eh.CommandHandler) eh.CommandHandler {
	return func(h eh.CommandHandler) eh.CommandHandler {
		return eh.CommandHandlerFunc(func(ctx context.Context, cmd eh.Command) error {
			logr.Debug("command handler", logger.NewField("commandType", cmd.CommandType()), logger.NewField("itemId", cmd.AggregateID()), logger.NewField("itemType", cmd.AggregateType()))
			return h.HandleCommand(ctx, cmd)
		})
	}
}

// Logger is a simple event handler for logging all events.
type Logger struct {
	logger logger.Logger
}

func NewLogger(logger logger.Logger) *Logger {
	return &Logger{
		logger: logger.WithName("casemanager"),
	}
}

// HandlerType implements the HandlerType method of the eventhorizon.EventHandler interface.
func (l *Logger) HandlerType() eh.EventHandlerType {
	return "logger"
}

// HandleEvent implements the HandleEvent method of the EventHandler interface.
func (l *Logger) HandleEvent(ctx context.Context, event eh.Event) error {
	l.logger.Debug("handle event", logger.NewField("eventType", event.EventType()), logger.NewField("itemId", event.AggregateID()), logger.NewField("itemType", event.AggregateType()), logger.NewField("event", event.Data()))
	return nil
}
