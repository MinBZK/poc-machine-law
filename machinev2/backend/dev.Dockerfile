FROM digilabpublic.azurecr.io/golang:1.22.5-alpine3.19 AS builder

# Cache dependencies
RUN ["go", "install", "github.com/githubnemo/CompileDaemon@latest"]

WORKDIR /build
COPY go.mod go.sum ./

RUN go mod download

## Build the Go Files
COPY . .

## Run the server for dev
ENTRYPOINT CompileDaemon -log-prefix=false -build='go build -o server .' -command='./server serve'
