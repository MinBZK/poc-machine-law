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

	service.logger.DebugContext(ctx, "engine reset done")

	return nil
}
