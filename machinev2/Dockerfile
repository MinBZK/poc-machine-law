FROM golang:latest as go-installer

# Set working directory
WORKDIR /app

FROM golang:latest

# Install gcc, Python3 and dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3 \
    python3-dev \
    python3-pip \
    python3-pybindgen \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create a symlink so 'python' command works
RUN ln -sf /usr/bin/python3 /usr/bin/python

RUN go install github.com/go-python/gopy@latest
RUN go install golang.org/x/tools/cmd/goimports@latest


# Set working directory
WORKDIR /app

# Copy your Go files
COPY . .
