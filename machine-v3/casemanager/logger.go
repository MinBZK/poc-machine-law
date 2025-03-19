package casemanager

import (
	"context"
	"log"

	eh "github.com/looplab/eventhorizon"
)

// LoggingMiddleware is a tiny command handle middleware for logging.
func LoggingMiddleware(h eh.CommandHandler) eh.CommandHandler {
	return eh.CommandHandlerFunc(func(ctx context.Context, cmd eh.Command) error {
		log.Printf("command: %#v", cmd)
		return h.HandleCommand(ctx, cmd)
	})
}

// Logger is a simple event handler for logging all events.
type Logger struct{}

// HandlerType implements the HandlerType method of the eventhorizon.EventHandler interface.
func (l *Logger) HandlerType() eh.EventHandlerType {
	return "logger"
}

// HandleEvent implements the HandleEvent method of the EventHandler interface.
func (l *Logger) HandleEvent(ctx context.Context, event eh.Event) error {
	log.Println("event:", event)
	return nil
}
