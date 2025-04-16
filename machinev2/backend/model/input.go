package model

// Root structure for the entire YAML document
type Input struct {
	GlobalServices map[string]Source      `yaml:"globalServices"`
	Profiles       map[string]ProfileData `yaml:"profiles"`
}

// ProfileData contains information about a profile
type ProfileData struct {
	Name              string            `yaml:"name"`
	Description       string            `yaml:"description"`
	UseGlobalServices bool              `yaml:"useGlobalServices"`
	Sources           map[string]Source `yaml:"sources"`
}

type Source map[string]SourceData
type SourceData []map[string]any
