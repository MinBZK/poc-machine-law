dir := $(shell pwd)

generate:
	pnpx @hey-api/openapi-ts -i $(dir)/../api/openapi.yaml -o $(dir)/src/lib/api-client -c @hey-api/client-fetch
