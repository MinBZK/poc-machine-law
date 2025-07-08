FROM digilabpublic.azurecr.io/golang:1.24.4-alpine3.22 AS builder

# Cache dependencies
RUN go install github.com/githubnemo/CompileDaemon@latest


WORKDIR /build

### COPY machine mod
COPY go.mod go.sum .

### Download modules
RUN go mod download

### Copy rest of the machine code
COPY . .

## Run the server for dev
ENTRYPOINT CompileDaemon -log-prefix=false -build='go build -o backend .' -command='./backend'
