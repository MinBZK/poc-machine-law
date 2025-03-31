#!/usr/bin/env bash

# Build script for Go-Python bindings using gopy
# Usage: ./build.sh [options]

set -e

# Default values
PYTHON_VERSION="3"
OUTPUT_DIR="build"
MODULE_NAME="gopy_machine"
PACKAGE_PATH="."
VERBOSE=0

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --python=*)
      PYTHON_VERSION="${1#*=}"
      shift
      ;;
    --output=*)
      OUTPUT_DIR="${1#*=}"
      shift
      ;;
    --name=*)
      MODULE_NAME="${1#*=}"
      shift
      ;;
    --package=*)
      PACKAGE_PATH="${1#*=}"
      shift
      ;;
    --verbose)
      VERBOSE=1
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --python=VERSION    Python version to build against (e.g., '3', '3.9')"
      echo "  --output=DIR        Output directory for the built extension"
      echo "  --name=NAME         Name of the Python module"
      echo "  --package=PATH      Go package path to bind"
      echo "  --verbose           Enable verbose output"
      echo "  --help              Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# ANSI colors for prettier output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Logging functions
log() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
  echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

error() {
  echo -e "${RED}[ERROR]${NC} $1" >&2
  exit 1
}

debug() {
  if [[ $VERBOSE -eq 1 ]]; then
    echo -e "[DEBUG] $1"
  fi
}

# Determine python executable
PYTHON_EXE="python${PYTHON_VERSION}"
if ! command -v "$PYTHON_EXE" &> /dev/null; then
  warn "Python executable '$PYTHON_EXE' not found, trying 'python'"
  PYTHON_EXE="python"
  if ! command -v "$PYTHON_EXE" &> /dev/null; then
    error "Python not found. Please install Python."
  fi
fi

# Check for gopy
if ! command -v gopy &> /dev/null; then
  log "gopy not found, installing..."
  go install golang.org/x/tools/cmd/goimports@latest
  go install github.com/go-python/gopy@latest

  if ! command -v gopy &> /dev/null; then
    error "Failed to install gopy. Please install manually: go install github.com/go-python/gopy@latest"
  fi
fi

# Create output directory
mkdir -p "$OUTPUT_DIR" || error "Failed to create output directory: $OUTPUT_DIR"

# Get Python version information
PYTHON_VERSION_FULL=$($PYTHON_EXE -c "import sys; print('{}.{}'.format(sys.version_info.major, sys.version_info.minor))")
debug "Full Python version: $PYTHON_VERSION_FULL"

# Get pip executable
PIP_EXE="pip${PYTHON_VERSION}"
if ! command -v "$PIP_EXE" &> /dev/null; then
  PIP_EXE="pip"
  if ! command -v "$PIP_EXE" &> /dev/null; then
    warn "pip not found. Will skip dependency installation."
    PIP_EXE=""
  fi
fi

# Install required Python packages
if [ -n "$PIP_EXE" ]; then
  log "Installing required Python packages..."
  $PIP_EXE install cffi
fi

# Get Go package name (last part of the path)
PACKAGE_NAME=$(basename "$PACKAGE_PATH")
debug "Package name: $PACKAGE_NAME"

# Prepare build directory
log "Preparing build environment..."
BUILD_TMP="$OUTPUT_DIR/tmp"
mkdir -p "$BUILD_TMP" || error "Failed to create temporary build directory"

# Check if we're in a Go module and initialize one if needed
if [ ! -f "go.mod" ]; then
  log "No go.mod file found. Initializing a temporary Go module..."

  # Create a temporary module for building
  MODULE_TEMP_NAME="tempmodule$(date +%s)"

  if [ $VERBOSE -eq 1 ]; then
    go mod init "$MODULE_TEMP_NAME" || error "Failed to initialize Go module"
    # Try to tidy the module to resolve dependencies
    go mod tidy || warn "go mod tidy had issues, but continuing..."
  else
    go mod init "$MODULE_TEMP_NAME" >/dev/null 2>&1 || error "Failed to initialize Go module"
    # Try to tidy the module to resolve dependencies
    go mod tidy >/dev/null 2>&1 || warn "go mod tidy had issues, but continuing..."
  fi

  # Remember that we created a temporary module so we can clean it up later
  CREATED_TEMP_MODULE=1
else
  log "Found existing go.mod file"
  CREATED_TEMP_MODULE=0
fi

# Use gopy to generate bindings
log "Generating Python bindings with gopy..."
if [ $VERBOSE -eq 1 ]; then
  gopy build -vm="$PYTHON_EXE" -output="$BUILD_TMP" -name="$MODULE_NAME" "$PACKAGE_PATH" || error "gopy build failed"
else
  gopy build -vm="$PYTHON_EXE" -output="$BUILD_TMP" -name="$MODULE_NAME" "$PACKAGE_PATH" >/dev/null 2>&1 || error "gopy build failed"
fi

# Copy the built module to the output directory
log "Finalizing build..."
cp -r "$BUILD_TMP"/* "$OUTPUT_DIR/" || error "Failed to copy built files to output directory"

# Clean up temporary directory
rm -rf "$BUILD_TMP"

# Clean up temporary module if we created one
if [ "$CREATED_TEMP_MODULE" -eq 1 ]; then
  log "Cleaning up temporary Go module..."
  rm -f go.mod go.sum
fi

# Create a more user-friendly README
README_FILE="$OUTPUT_DIR/README.md"
cat > "$README_FILE" << EOF
# ${MODULE_NAME} - Go-Python Bindings

This package provides Python bindings for Go code, generated with gopy.

## Installation

You can install this package directly from the directory:

\`\`\`
pip install -e ${OUTPUT_DIR}
\`\`\`

## Usage

\`\`\`python
import ${MODULE_NAME}

# Example (adjust based on your actual exported functions/types):
# result = ${MODULE_NAME}.SomeFunction()
\`\`\`

## Development

This package was generated using gopy. To regenerate the bindings:

\`\`\`
./build.sh --name=${MODULE_NAME} --package=${PACKAGE_PATH} --output=${OUTPUT_DIR}
\`\`\`
EOF

log "Successfully built $MODULE_NAME module in $OUTPUT_DIR"
log "To install, run: pip install -e $OUTPUT_DIR"

# Print additional helpful information in verbose mode
if [[ $VERBOSE -eq 1 ]]; then
  echo ""
  echo "Additional Information:"
  echo "----------------------"
  echo "1. Make sure your Go code follows gopy's requirements:"
  echo "   - Exported types must be defined in the main package"
  echo "   - Avoid using interfaces as arguments or return values"
  echo "   - Use basic types that can be easily converted between Go and Python"
  echo ""
  echo "2. Example Go code compatible with gopy:"
  echo ""
  echo "   package main"
  echo ""
  echo "   // Add adds two integers and returns the result."
  echo "   func Add(a, b int) int {"
  echo "       return a + b"
  echo "   }"
  echo ""
  echo "   // Point represents a 2D point with X and Y coordinates."
  echo "   type Point struct {"
  echo "       X float64"
  echo "       Y float64"
  echo "   }"
  echo ""
  echo "   // Distance calculates the distance between two points."
  echo "   func (p *Point) Distance(other *Point) float64 {"
  echo "       dx := p.X - other.X"
  echo "       dy := p.Y - other.Y"
  echo "       return math.Sqrt(dx*dx + dy*dy)"
  echo "   }"
  echo ""
  echo "3. In Python, you can use the module like this:"
  echo ""
  echo "   import $MODULE_NAME"
  echo ""
  echo "   # Using functions"
  echo "   result = $MODULE_NAME.Add(5, 3)  # 8"
  echo ""
  echo "   # Using types"
  echo "   p1 = $MODULE_NAME.Point(1.0, 2.0)"
  echo "   p2 = $MODULE_NAME.Point(4.0, 6.0)"
  echo "   dist = p1.Distance(p2)  # 5.0"
  echo ""
fi

# Provide a sample test script
TEST_SCRIPT="$OUTPUT_DIR/test_${MODULE_NAME}.py"
cat > "$TEST_SCRIPT" << EOF
#!/usr/bin/env python

"""
Simple test script for the ${MODULE_NAME} module.
Modify this script to test your specific Go functions.
"""

import sys
import os

# Add the package directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import ${MODULE_NAME}
    print(f"Successfully imported {MODULE_NAME} module")

    # TODO: Add your test code here
    # Example:
    # result = ${MODULE_NAME}.SomeFunction()
    # print(f"Result: {result}")

    # Print available functions and classes
    print("\nAvailable attributes in the module:")
    for attr in dir(${MODULE_NAME}):
        if not attr.startswith('_'):
            print(f"  - {attr}")

except ImportError as e:
    print(f"Error importing module: {e}")
    sys.exit(1)
EOF

chmod +x "$TEST_SCRIPT"
log "Created test script: $TEST_SCRIPT"
