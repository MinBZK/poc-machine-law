package model

import (
	"errors"

	"github.com/google/uuid"
)

var ErrCaseNotFound = errors.New("case_not_found")

type Case struct {
	ID       uuid.UUID
	Service  string
	Law      string
	BSN      string
	Approved *bool
	Status   string
}
