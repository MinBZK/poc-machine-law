FROM golang:latest

# Install dependencies needed for building Python
RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    libreadline-dev \
    libncursesw5-dev \
    libssl-dev \
    libsqlite3-dev \
    tk-dev \
    libgdbm-dev \
    libc6-dev \
    libbz2-dev \
    libffi-dev \
    zlib1g-dev

# Download and install Python 3.13
WORKDIR /tmp
RUN wget https://www.python.org/ftp/python/3.13.0/Python-3.13.0.tgz \
    && tar -xf Python-3.13.0.tgz \
    && cd Python-3.13.0 \
    && ./configure --enable-optimizations \
    && make -j$(nproc) \
    && make install

# Install pip if not already installed with Python
RUN python3 -m ensurepip --upgrade

# Install python3.13-dev (development headers)
# Since we're building from source, the development headers are already included
# But we'll make sure we have the pkg-config file and other necessary components
RUN cd /tmp/Python-3.13.0 \
    && make install includedir=/usr/include

# Install pybindgen using pip
RUN pip3 install pybindgen


# Verify installations
RUN go version && python3.13 --version && pip3 --version && \
    python3 -c "import pybindgen; print(f'pybindgen version: {pybindgen.__version__}')"

# Create a symlink so 'python' command works
RUN ln -sf /usr/bin/python3 /usr/bin/python

RUN go install github.com/go-python/gopy@latest
RUN go install golang.org/x/tools/cmd/goimports@latest


# Set working directory
WORKDIR /app

# Copy your Go files
COPY . .
