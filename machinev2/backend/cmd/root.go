package cmd

import (
	"fmt"
	"log"
	"log/slog"
	"os"

	"github.com/alecthomas/kong"
	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
	"gopkg.in/yaml.v3"
)

type Context struct {
	Debug  bool
	Logger slog.Logger
}

var cli struct {
	Debug bool `env:"APP_DEBUG" default:"false" optional:"" name:"debug" help:"Enable debug mode."`

	Serve ServeCmd `cmd:"serve" help:"Startup server."`
}

func Run() error {
	// Parse the command line.
	ctx := kong.Parse(&cli)

	logLevel := slog.LevelInfo
	if cli.Debug {
		logLevel = slog.LevelDebug
	}

	options := &slog.HandlerOptions{
		Level: logLevel,
	}

	logger := slog.New(slog.NewJSONHandler(os.Stdout, options))

	// Call the Run() method of the selected parsed command.
	err := ctx.Run(&Context{Logger: *logger, Debug: cli.Debug})

	return err
}

func parseInputFile(path string) (model.Input, error) {
	// Read the YAML file
	yamlFile, err := os.ReadFile(path)
	if err != nil {
		log.Fatalf("Error reading YAML file: %v", err)
	}

	// Parse the YAML file into the Config structure
	var input model.Input
	if err := yaml.Unmarshal(yamlFile, &input); err != nil {
		log.Fatalf("Error parsing YAML: %v", err)
	}

	for k, v := range input.Profiles {
		for k1, source := range v.Sources {
			for k2, sourcedata := range source {
				for k3, data := range sourcedata {
					input.Profiles[k].Sources[k1][k2][k3] = convertMapToStringKeys(data)
				}

			}
		}
	}

	return input, nil
}

func convertMapToStringKeys(m map[string]any) map[string]any {
	result := make(map[string]any)

	for k, v := range m {
		switch vt := v.(type) {
		case map[string]any:
			// Recursively convert nested map[string]any
			result[k] = convertMapToStringKeys(vt)
		case map[any]any:
			result[k] = convertNestedMapAnyToStringKeys(vt)
		case []any:
			b := make([]any, 0, len(vt))

			for _, v1 := range vt {
				switch vnt := v1.(type) {
				case map[any]any:
					b = append(b, convertNestedMapAnyToStringKeys(vnt))
				}
			}

			result[k] = b
		default:
			// Keep non-map values as is
			result[k] = v
		}
	}

	return result
}

// Helper function for map[any]any to map[string]any conversion
func convertNestedMapAnyToStringKeys(m map[any]any) map[string]any {
	result := make(map[string]any)

	for k, v := range m {
		strKey := fmt.Sprintf("%v", k)

		switch vt := v.(type) {
		case map[string]any:
			result[strKey] = convertMapToStringKeys(vt)
		case map[any]any:
			result[strKey] = convertNestedMapAnyToStringKeys(vt)
		default:
			result[strKey] = v
		}
	}

	return result
}
