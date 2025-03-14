package model

import "time"

// Event represents an event in the system
type Event struct {
	CaseID    string                 `json:"case_id"`
	Timestamp time.Time              `json:"timestamp"`
	EventType string                 `json:"event_type"`
	Data      map[string]interface{} `json:"data"`
}
