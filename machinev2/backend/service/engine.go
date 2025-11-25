package service

import (
	"context"
	"fmt"
)

// ResetEngine implements Servicer.
func (service *Service) ResetEngine(ctx context.Context) error {
	service.logger.DebugContext(ctx, "resetting engine")
	if err := service.service.Reset(ctx); err != nil {
		return fmt.Errorf("reset: %w", err)
	}

	if err := service.setInput(ctx); err != nil {
		return fmt.Errorf("set input: %w", err)
	}

	if err := service.casemanager.Reset(ctx); err != nil {
		return fmt.Errorf("case manager reset: %w", err)
	}

	if err := service.claimManager.Reset(ctx); err != nil {
		return fmt.Errorf("case manager reset: %w", err)
	}

	service.logger.DebugContext(ctx, "engine reset done")

	return nil
}
