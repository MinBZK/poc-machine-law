package service

import (
	"context"
	"errors"

	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
)

var ErrProfileNotFound = errors.New("profile_not_found")

// ProfileList implements Servicer.
func (service *Service) ProfileList(ctx context.Context) ([]model.Profile, error) {
	profiles := make([]model.Profile, 0, len(service.profiles))

	for _, profile := range service.profiles {
		profiles = append(profiles, profile)
	}

	return profiles, nil
}

func (service *Service) Profile(ctx context.Context, bsn string) (model.Profile, error) {
	profile, ok := service.profiles[bsn]
	if !ok {
		return model.Profile{}, ErrProfileNotFound
	}

	return profile, nil
}
