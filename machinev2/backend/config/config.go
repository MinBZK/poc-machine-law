package config

type Config struct {
	Debug                         bool
	BackendListenAddress          string
	Organization                  string
	StandaloneMode                bool
	WithRuleServiceInMemory       bool
	LDV                           LDV
	ExternalClaimResolverEndpoint string
}

type LDV struct {
	Enabled  bool
	Endpoint string
}
