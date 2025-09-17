# Law MCP Server

Clean, modular MCP (Model Context Protocol) server for executing Dutch laws and regulations.

## Architecture

```
law_mcp/
├── server.py          # MCP protocol implementation
├── engine_adapter.py  # Adapter to core law engine
├── models.py          # Type definitions
├── utils.py           # General utilities
├── mock_data.py       # Test data (separated from business logic)
├── demo.py            # Live demonstration
└── test_integration.py # Integration tests
```

## Key Design Principles

- **Law-Agnostic**: No hardcoded law logic, only generic protocol handling
- **Thin Layer**: Minimal code that delegates to the core law engine
- **Clean Separation**: Mock data isolated from business logic
- **Extensible**: New laws work automatically without code changes

## Usage

### Start the Server
```bash
uv run python -m law_mcp.server
```

### Run Demo
```bash
uv run python law_mcp/demo.py
```

### Run Tests
```bash
uv run python law_mcp/test_integration.py
```

## Configuration for Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "machine-law-executor": {
      "command": "uv",
      "args": ["run", "python", "-m", "law_mcp.server"],
      "cwd": "/path/to/poc-machine-law"
    }
  }
}
```

## Available Capabilities

### Tools (3)
- `execute_law` - Execute laws with parameters and overrides
- `check_eligibility` - Quick eligibility checking
- `calculate_benefit_amount` - Calculate specific outputs

### Resources (3)
- `laws://list` - Browse available laws
- `law://{service}/{law}/spec` - Get law specifications
- `profile://{bsn}` - Access citizen profile data

### Prompts (3)
- `check_all_benefits` - Comprehensive benefit analysis
- `explain_calculation` - Step-by-step law explanations
- `compare_scenarios` - Multi-scenario comparisons

## Mock Data

Mock profile data is isolated in `mock_data.py` and includes basic citizen information for testing. In production, this would be replaced with real data sources like RvIG/BRP.
