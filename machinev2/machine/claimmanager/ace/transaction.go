package ace

import (
	"context"
	"errors"
	"fmt"

	"github.com/minbzk/poc-machine-law/machinev2/machine/claimmanager/ace/generated"
	"github.com/minbzk/poc-machine-law/machinev2/machine/logger"
)

func (cm *ClaimManager) beginTransaction(ctx context.Context) (string, error) {
	response, err := generated.BeginTransaction(ctx, cm.clients.ddl)
	if err != nil {
		return "", fmt.Errorf("begin transaction: %w", err)
	}

	return response.BeginTransaction, nil
}

func (cm *ClaimManager) rollbackTransaction(ctx context.Context, transactionID string) (bool, error) {
	response, err := generated.RollbackTransaction(ctx, cm.clients.ddl, transactionID)
	if err != nil {
		return false, fmt.Errorf("rollback transaction: %w", err)
	}

	return response.RollbackTransaction, nil
}

func (cm *ClaimManager) commitTransaction(ctx context.Context, transactionID string) (bool, error) {
	response, err := generated.CommitTransaction(ctx, cm.clients.ddl, transactionID)
	if err != nil {
		return false, fmt.Errorf("commit transaction: %w", err)
	}

	return response.CommitTransaction, nil
}

func (cm *ClaimManager) transaction(ctx context.Context, fn func(ctx context.Context, txID string) error) error {
	// Begin ACE transaction
	txID, err := cm.beginTransaction(ctx)
	if err != nil {
		return fmt.Errorf("begin transaction: %w", err)
	}

	if err := fn(ctx, txID); err != nil {
		if rollbacked, err := cm.rollbackTransaction(ctx, txID); err != nil {
			return fmt.Errorf("roll back transaction: %w", err)
		} else if !rollbacked {
			cm.logger.Error("could not rollback transaction", logger.NewField("tx", txID))
		}

		return err
	}

	if commited, err := cm.commitTransaction(ctx, txID); err != nil {
		return err
	} else if !commited {
		return errors.New("transaction could not be commited")
	}

	return nil
}
