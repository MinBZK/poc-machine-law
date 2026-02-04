# Build stage
FROM digilabpublic.azurecr.io/golang:1.25.3-alpine3.22 AS builder

# Set working directory
WORKDIR /build

# Install necessary build tools
RUN apk add --no-cache git ca-certificates tzdata && \
    update-ca-certificates


WORKDIR /machine

### COPY local machine
COPY machinev2/machine/go.mod machinev2/machine/go.sum ./
RUN go mod download
COPY ./machinev2/machine/ .

WORKDIR /build

# Copy go mod and sum files
COPY machinev2/backend/go.mod machinev2/backend/go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY ./machinev2/backend/ .

# Build the application with optimizations
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-w -s" -o server .

# Final stage
FROM alpine:3.22

# Add non-root user for security
RUN adduser -D -g '' appuser

# Copy only the binary from the build stage
COPY --from=builder /build/server /app/server
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

COPY ./laws ./app/laws
COPY ./services /app/services

# Set working directory
WORKDIR /app

# Use non-root user
USER appuser

# Expose API port
EXPOSE 8080

# Run the application
CMD ["/app/server", "serve"]
