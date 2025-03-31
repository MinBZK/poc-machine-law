# gopy_machine - Go-Python Bindings

This package provides Python bindings for Go code, generated with gopy.

## Installation

You can install this package directly from the directory:

```
pip install -e gopy_machine
```

## Usage

```python
import gopy_machine

# Example (adjust based on your actual exported functions/types):
# result = gopy_machine.SomeFunction()
```

## Development

This package was generated using gopy. To regenerate the bindings:

```
./build.sh --name=gopy_machine --package=github.com/minbzk/poc-machine-law/machinev2/service --output=gopy_machine
```
