GENERATE_DIRS := $(shell grep '^\s*\./.*' go.work | tr -d '(' | tr -d ')' | tr -d ' ' | sed 's/^\.//')

generate:
	openapi-python-client generate --path machinev2/api/openapi.yaml --output-path web/machine_client --overwrite
	@if [ -z "$(GENERATE_DIRS)" ]; then \
		echo "No directories found in go.work"; \
		exit 1; \
	fi
	@for dir in $(GENERATE_DIRS); do \
		echo "Running go generate in $$dir"; \
		(cd $$dir && go generate ./...); \
	done

fix-log-file:
	\[\d{0,2}\dm
