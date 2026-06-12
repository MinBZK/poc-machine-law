# Machine Law Interface

This package provides interfaces to interact with the law evaluation engine (regelrecht Rust engine) in a uniform way.

## Usage

### Basic Configuration

The interfaces are configured through `web/config/config.yaml`:

```yaml
engines:
  - id: regelrecht
    name: Regelrecht engine
    description: regelrecht Rust engine (default)
    type: regelrecht
    default: true
```

The engine runs in-process via PyO3 (no external binary).

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
- `CaseManagerFactory` and `MachineFactory`: Factories to create instances of the interfaces
