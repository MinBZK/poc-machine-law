package config

type Config struct {
	Debug                   bool
	BackendListenAddress    string
	Organization            string
	StandaloneMode          bool
	WithRuleServiceInMemory bool
}
