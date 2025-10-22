package casemanager

import (
	"context"

	eh "github.com/looplab/eventhorizon"
	"github.com/minbzk/poc-machine-law/machinev2/machine/logger"
)

var _ eh.EventHandler = &Executor{}

// Executor is a simple event handler for logging all events.
type Transaction struct {
	logger   logger.Logger
	handlers []eh.EventHandler
}

func NewTransaction(logger logger.Logger, handlers ...eh.EventHandler) *Transaction {
	return &Transaction{
		logger:   logger,
		handlers: handlers,
	}
}

// HandlerType implements the HandlerType method of the eventhorizon.EventHandler interface.
func (l *Transaction) HandlerType() eh.EventHandlerType {
	return "transaction"
}

// HandleEvent implements the HandleEvent method of the EventHandler interface.
func (l *Transaction) HandleEvent(ctx context.Context, event eh.Event) error {
	for _, handler := range l.handlers {
		if err := handler.HandleEvent(ctx, event); err != nil {
			return err
		}
	}

	return nil
}
