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
	BackendListenAddress    string `env:"APP_BACKEND_LISTEN_ADDRESS" default:":8080" name:"backend-listen-address" help:"Address to listen  on."`
	InputFile               string `env:"APP_INPUT_FILE" name:"input-file"`
	Organization            string `env:"APP_ORGANIZATION" name:"organization"`
	StandaloneMode          bool   `env:"APP_STANDALONE_MODE" name:"stand-alone" help:"Will set the engine into stand alone mode"`
	WithRuleServiceInMemory bool   `env:"APP_RULE_SERVICE_IN_MEMORY" name:"rule-service-in-memory" help:"Will only use inmemory rule services"`
}

func (opt *ServeCmd) Run(ctx *Context) error {
	proc := process.New()

	config := config.Config{
		Debug:                   ctx.Debug,
		BackendListenAddress:    opt.BackendListenAddress,
		Organization:            opt.Organization,
		StandaloneMode:          opt.StandaloneMode,
		WithRuleServiceInMemory: opt.WithRuleServiceInMemory,
	}

	logger := ctx.Logger.With("application", "http_server")
	logger.Info("starting uwv backend", "config", config)

	svc, err := service.New(logger, &config)
	if err != nil {
		logger.Error("service new", "err", err)
		return fmt.Errorf("service new: %w", err)
	}

	if opt.InputFile != "" {
		input, err := parseInputFile(opt.InputFile)
		if err != nil {
			logger.Error("parse input file", "err", err)
		}

		logger.Debug("successfully parsed input file", "services", len(input.GlobalServices), "profiles", len(input.Profiles))

		if err := svc.AppendInput(context.Background(), input); err != nil {
			logger.Error("append input", "err", err)
		}
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
