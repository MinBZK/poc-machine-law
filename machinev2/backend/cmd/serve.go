package cmd

import (
	"context"
	"errors"
	"fmt"
	"net/http"

	"github.com/minbzk/poc-machine-law/machinev2/backend/config"
	"github.com/minbzk/poc-machine-law/machinev2/backend/handler"
	"github.com/minbzk/poc-machine-law/machinev2/backend/process"
	"github.com/minbzk/poc-machine-law/machinev2/backend/service"
)

type ServeCmd struct {
	BackendListenAddress string `env:"APP_BACKEND_LISTEN_ADDRESS" default:":8080" name:"backend-listen-address" help:"Address to listen  on."`
	InputFile            string `env:"APP_INPUT_FILE" name:"input-file"`
}

func (opt *ServeCmd) Run(ctx *Context) error {
	proc := process.New()

	config := config.Config{
		Debug:                ctx.Debug,
		BackendListenAddress: opt.BackendListenAddress,
	}

	logger := ctx.Logger.With("application", "http_server")
	logger.Info("starting uwv backend", "config", config)

	// services := service.NewServices(time.Now())

	svc := service.New(logger, &config)

	if opt.InputFile != "" {
		input, err := parseInputFile(opt.InputFile)
		if err != nil {
			logger.Error("parse input file", "err", err)
		}

		logger.Debug("successfully parsed input file", "services", len(input.GlobalServices), "profiles", len(input.Profiles))

		svc.AppendInput(input)
	}

	app, err := handler.New(logger, &config, svc)
	if err != nil {
		logger.Error("handler new", "err", err)
		return fmt.Errorf("handler new: %w", err)
	}

	logger.Info("starting server", "address", opt.BackendListenAddress)

	go func() {
		if err := app.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			logger.Error("listen and serve failed", "err", err)
		}
	}()

	proc.Wait()

	logger.Info("shutting down server")

	// Shutdown application
	shutdownCtx := context.Background()

	if err := app.Shutdown(shutdownCtx); err != nil {
		logger.Error("handler shutdown failed", "err", err)
	}

	logger.Info("shutdown finished")

	return nil
}
