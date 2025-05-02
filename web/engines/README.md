# Machine Law Interface

This package provides interfaces to interact with the law evaluation engine in a uniform way, regardless of whether you're using the embedded Python implementation or the Go HTTP service.

## Usage

### Basic Configuration

The interfaces are configured through environment variables:

```bash
# Use the Python embedded implementation (default)
export MACHINE_TYPE=python

# Use the Go HTTP service
export MACHINE_TYPE=go
export GO_API_URL=http://localhost:8081/v0
```

### Using the Interfaces

In FastAPI routes, you can use the dependencies to get the interfaces:

```python
from fastapi import Depends

from web.dependencies import get_case_manager, get_machine_service
from engine import CaseManagerInterface, EngineInterface

@router.get("/cases/{bsn}")
def get_case(
    bsn: str,
    service: str,
    law: str,
    case_manager: CaseManagerInterface = Depends(get_case_manager)
):
    case = case_manager.get_case(bsn, service, law)
    return case

@router.post("/evaluate")
def evaluate_law(
    service: str,
    law: str,
    parameters: dict,
    machine_service: EngineInterface = Depends(get_machine_service)
):
    result = machine_service.evaluate(service, law, parameters)
    return result
```

### Checking Available Laws

```python
@router.get("/discoverable-laws")
async def get_discoverable_laws(
    machine_service: EngineInterface = Depends(get_machine_service)
):
    laws = machine_service.get_discoverable_service_laws()
    return laws
```

## Implementation Details

- `CaseManagerInterface`: Interface for case management functionality
- `EngineInterface`: Interface for law evaluation functionality
- `MachineType`: Enum to specify which machine implementation to use
- `CaseManagerFactory` and `MachineFactory`: Factories to create instances of the interfaces

## Switching Implementations at Runtime

You can switch implementations at runtime by reconfiguring the factories:

```python
from engine.factory import CaseManagerFactory, MachineFactory, MachineType

# Switch to Go implementation
case_manager = CaseManagerFactory.create_case_manager(
    machine_type=MachineType.GO,
    go_api_url="http://localhost:8081/v0"
)

# Switch to Python implementation
machine_service = MachineFactory.create_machine_service(
    machine_type=MachineType.PYTHON,
    services=services
)
```
