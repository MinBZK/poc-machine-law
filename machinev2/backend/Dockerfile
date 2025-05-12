# Build stage
FROM golang:1.24.1-alpine AS builder

# Set working directory
WORKDIR /build

# Install necessary build tools
RUN apk add --no-cache git ca-certificates tzdata && \
    update-ca-certificates

# Copy go mod and sum files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the application with optimizations
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-w -s" -o server .

# Final stage
FROM alpine:3.21

# Add non-root user for security
RUN adduser -D -g '' appuser

# Copy only the binary from the build stage
COPY --from=builder /build/server /app/server
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Set working directory
WORKDIR /app

# Use non-root user
USER appuser

# Expose API port
EXPOSE 8080

# Run the application
CMD ["/app/server", "serve"]
