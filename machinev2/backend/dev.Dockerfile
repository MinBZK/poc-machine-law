FROM digilabpublic.azurecr.io/golang:1.24.4-alpine3.22 AS builder

# Cache dependencies
RUN go install github.com/githubnemo/CompileDaemon@latest


WORKDIR /build/machine

### COPY machine mod
COPY machinev2/machine/go.mod machinev2/machine/go.sum ./

### Download modules
RUN go mod download

### Copy rest of the machine code
COPY ./machinev2/machine/ .

WORKDIR /build/backend

### COPY backend mod
COPY machinev2/backend/go.mod machinev2/backend/go.sum ./

### Download modules
RUN go mod download

### Copy rest of the backend code
COPY ./machinev2/backend/ .

### Go a directory down to make sure the watcher can watch both dirs
WORKDIR /build

### Copy necessary files into correct folder
COPY ./law ./law
COPY ./services ./services
COPY ./machinev2/backend/cmd/serve_input.yaml ./cmd/

RUN go work init
RUN go work use ./machine
RUN go work use ./backend

## Run the server for dev
ENTRYPOINT CompileDaemon -log-prefix=false -build='go build -o server ./backend' -command='./server serve'
