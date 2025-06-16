module github.com/minbzk/poc-machine-law/features

go 1.24.1

replace github.com/minbzk/poc-machine-law/machinev2/machine => ../machinev2/machine

require (
	github.com/cucumber/godog v0.15.0
	github.com/google/uuid v1.6.0
	github.com/minbzk/poc-machine-law/machinev2/machine v0.0.0-20250311082128-0b97b4006c7b
	github.com/sirupsen/logrus v1.9.3
	github.com/stretchr/testify v1.10.0
)

require (
	github.com/apapsch/go-jsonmerge/v2 v2.0.0 // indirect
	github.com/cucumber/gherkin/go/v26 v26.2.0 // indirect
	github.com/cucumber/messages/go/v21 v21.0.1 // indirect
	github.com/davecgh/go-spew v1.1.1 // indirect
	github.com/gofrs/uuid v4.3.1+incompatible // indirect
	github.com/hashicorp/go-immutable-radix v1.3.1 // indirect
	github.com/hashicorp/go-memdb v1.3.4 // indirect
	github.com/hashicorp/golang-lru v0.5.4 // indirect
	github.com/jinzhu/copier v0.4.0 // indirect
	github.com/jpillora/backoff v1.0.0 // indirect
	github.com/looplab/eventhorizon v0.16.0 // indirect
	github.com/oapi-codegen/runtime v1.1.1 // indirect
	github.com/pmezard/go-difflib v1.0.0 // indirect
	github.com/shopspring/decimal v1.4.0 // indirect
	github.com/spf13/pflag v1.0.5 // indirect
	golang.org/x/sys v0.33.0 // indirect
	gopkg.in/yaml.v3 v3.0.1 // indirect
)
