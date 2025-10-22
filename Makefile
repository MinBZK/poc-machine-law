PROJECT_NAME := lac
CLUSTER_EXISTS := $$(k3d cluster list $(PROJECT_NAME) --no-headers | wc -l | xargs)
ARCH := $(shell if [ "$(shell uname -m)" = "arm64" ]; then echo "linux/arm64"; else echo "linux/amd64"; fi)
GENERATE_DIRS := $(shell grep '^\s*\./.*' go.work | tr -d '(' | tr -d ')' | tr -d ' ' | sed 's/^\.//')


.PHONY: set_k8s_context
set_k8s_context:
	kubectl config use-context "k3d-$(PROJECT_NAME)"

.PHONY: k3d
k3d:
	@if [ $(CLUSTER_EXISTS) -eq 0 ]; then \
		k3d cluster create --config=deploy/k3d/config.yaml --image=rancher/k3s:v1.33.1-k3s1; \
	else \
		k3d cluster start "$(PROJECT_NAME)"; \
	fi
	$(set_k8s_context)

.PHONY: dev
dev: set_k8s_context
	skaffold dev --platform=$(ARCH) --cleanup=false

.PHONY: stop
stop:
	k3d cluster stop "$(PROJECT_NAME)"

.PHONY: clean
clean:
	k3d cluster delete "$(PROJECT_NAME)"
	rm -f .fsc-db-status

.PHONY: lint
lint:
	find . -maxdepth 3 -type d -exec sh -c "cd \"{}\"/ && if [ -f go.mod ]; then golangci-lint run; fi;" \;

generate:
	openapi-python-client generate --path machinev2/api/openapi.yaml --output-path web/engines/http_engine/machine_client --overwrite
	@if [ -z "$(GENERATE_DIRS)" ]; then \
		echo "No directories found in go.work"; \
		exit 1; \
	fi
	@for dir in $(GENERATE_DIRS); do \
		echo "Running go generate in $$dir"; \
		(cd $$dir && go generate ./...); \
	done
