package logging_test

import (
	"context"
	"fmt"
	"os"
	"sync"
	"testing"

	"github.com/minbzk/poc-machine-law/machinev2/internal/logging"
	"github.com/sirupsen/logrus"
)

func TestLogger(t *testing.T) {
	var logger logging.Logger = logging.New("test", os.Stdout, logrus.DebugLevel)

	ctx := context.Background()

	logger.Debug(ctx, "HI")

	ctx = logging.WithLogger(ctx, logger)

	logger2 := logging.FromContext(ctx)
	logger2.Debug(ctx, "WOW")
	logger2.Warning(ctx, "asdf")
	logger2.WithIndent().Warning(ctx, "asdf 2")

	test(logger, ctx, "test", 2)
	test(logger, ctx, "test", 2)
}

func TestRace(t *testing.T) {
	var logger logging.Logger = logging.New("test", os.Stdout, logrus.DebugLevel)

	var wg sync.WaitGroup
	for range 100 {
		wg.Add(1)
		go func() {
			defer wg.Done()
			// Access the shared resource
			test(logger, context.Background(), "test", 2)
		}()
	}

	wg.Wait()
}

func test(logger logging.Logger, ctx context.Context, path string, index int) {
	if err := logger.IndentBlock(ctx, fmt.Sprintf("Resolving path: %v", path), func(ctx context.Context) error {
		if index != 0 {
			test(logger, ctx, path, index-1)
		}

		logger.Debugf(ctx, "what is going on")
		logger.WithIndent().Info(ctx, "this is going on")

		logger.Debugf(ctx, "Result")
		return nil
	}); err != nil {
		logger.Error(ctx, "error")
	}
}
