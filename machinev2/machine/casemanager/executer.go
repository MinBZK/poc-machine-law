package casemanager

import (
	"context"

	eh "github.com/looplab/eventhorizon"
	"github.com/minbzk/poc-machine-law/machinev2/machine/logger"
)

var _ eh.EventHandler = &Executor{}

// Executor is a simple event handler for logging all events.
type Executor struct {
	logger logger.Logger
	cb     Callback
}

func NewExecutor(logger logger.Logger, cb Callback) *Executor {
	return &Executor{
		logger: logger,
		cb:     cb,
	}
}

// HandlerType implements the HandlerType method of the eventhorizon.EventHandler interface.
func (l *Executor) HandlerType() eh.EventHandlerType {
	return "executor"
}

// HandleEvent implements the HandleEvent method of the EventHandler interface.
func (l *Executor) HandleEvent(ctx context.Context, event eh.Event) error {
	switch data := event.Data().(type) {
	case *CaseSubmitted, *CaseDecided, *CaseObjected, *ObjectionStatusDetermined, *ObjectionAdmissibilityDetermined, *AppealStatusDetermined:
		l.cb(event.AggregateID(), event.EventType().String(), structToMap(data))
	}

	return nil
}
