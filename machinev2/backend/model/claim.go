package model

import "github.com/google/uuid"

type Claim struct {
	ID      string    `json:"id"`
	Service string    `json:"service"`
	Key     string    `json:"key"`
	CaseID  uuid.UUID `json:"case_id,omitempty"`
	Law     string    `json:"law"`
	BSN     string    `json:"bsn"`
}
