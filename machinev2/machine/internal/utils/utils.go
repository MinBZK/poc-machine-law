package utils

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"

	// "github.com/goccy/go-yaml"
	"gopkg.in/yaml.v3"
)

const (
	// LawBaseDir is the base directory for rule specs
	LawBaseDir     = "law"
	ServiceBaseDir = "services"
)

type ServiceSpec struct {
	ID       string `json:"uuid" yaml:"uuid"`
	Name     string `json:"name" yaml:"name"`
	Endpoint string `json:"endpoint" yaml:"endpoint"`
}

var (
	servicesLoaded bool = false
	serviceSpec    []ServiceSpec
	serviceOnce    sync.Once
)

type ServiceResolver struct {
	Dir      string
	Services []ServiceSpec
	mu       sync.RWMutex
}

func NewServiceResolver() (*ServiceResolver, error) {
	var err error

	serviceOnce.Do(func() {
		serviceSpec, err = serviceLoad(ServiceBaseDir)
		if err != nil {
			return
		}

		servicesLoaded = true
	})

	if err != nil {
		return nil, fmt.Errorf("load services: %w", err)
	}

	if !servicesLoaded {
		return nil, fmt.Errorf("services not loaded yet")
	}

	return &ServiceResolver{
		Dir:      LawBaseDir,
		Services: serviceSpec,
	}, nil
}

func serviceLoad(dir string) ([]ServiceSpec, error) {

	// Find all .yaml and .yml files recursively
	var yamlFiles []string

	err := func() error {
		// First, evaluate the symlink to get the actual path
		realPath, err := filepath.EvalSymlinks(dir)
		if err != nil {
			return fmt.Errorf("failed to evaluate symlink %s: %w", dir, err)
		}

		// Now walk the real path
		return filepath.Walk(realPath, func(path string, info os.FileInfo, err error) error {
			if err != nil {
				return err
			}

			if !info.IsDir() {
				ext := strings.ToLower(filepath.Ext(path))
				if ext == ".yaml" || ext == ".yml" {
					yamlFiles = append(yamlFiles, path)
				}
			}

			return nil
		})
	}()

	if err != nil {
		return nil, err
	}

	services := make([]ServiceSpec, 0, len(yamlFiles))
	// Load each rule file
	for _, path := range yamlFiles {
		data, err := os.ReadFile(path)
		if err != nil {
			fmt.Printf("Error reading file %s: %v\n", path, err)
			continue
		}

		service := ServiceSpec{}
		if err := yaml.Unmarshal(data, &service); err != nil {
			fmt.Printf("Error parsing YAML from %s: %v\n", path, err)
			continue
		}

		services = append(services, service)
	}

	return services, nil
}
