package service

import (
	"context"

	"github.com/looplab/eventhorizon/uuid"
	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
	machinemodel "github.com/minbzk/poc-machine-law/machinev2/machine/model"
)

// EventList implements Servicer.
func (service *Service) EventList(ctx context.Context) ([]model.Event, error) {
	events := service.casemanager.GetEvents(nil)

	return ToEvents(events), nil
}

// CaseEventList implements Servicer.
func (service *Service) CaseEventList(ctx context.Context, caseID uuid.UUID) ([]model.Event, error) {
	events := service.casemanager.GetEventsByUUID(caseID)

	return ToEvents(events), nil
}

func ToEvent(event machinemodel.Event) model.Event {
	return model.Event{
		EventType: event.EventType,
		Timestamp: event.Timestamp,
		Data:      event.Data,
	}
}

func ToEvents(events []machinemodel.Event) []model.Event {
	items := make([]model.Event, 0, len(events))

	for idx := range events {
		items = append(items, ToEvent(events[idx]))
	}

	return items
}
