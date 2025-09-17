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
- **Parameter-Agnostic**: Supports any parameter type (BSN, kvk-nummer, or custom parameters)
- **Thin Layer**: Minimal code that delegates to the core law engine
- **Clean Separation**: Mock data isolated from business logic
- **Extensible**: New laws work automatically without code changes
- **Backward Compatible**: Existing BSN-based integrations continue to work

## Major Updates (v2.0)

🎉 **Generic Parameter Support**: The MCP server now supports any parameter type:
- ✅ **Citizen Laws**: Use `BSN` parameter for individual citizens
- ✅ **Business Laws**: Use `kvk-nummer` parameter for business entities
- ✅ **Custom Laws**: Use any parameter combination your law requires
- ✅ **Custom Parameters**: Support any parameter type (case_id, reference_date, etc.)
- ✅ **Backward Compatible**: All existing BSN-based calls continue to work

🏢 **Business Law Support**: New discoverable business laws like WPM are now fully supported and appear in law discovery.

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

## HTTP Deployment (Production)

The MCP server is also available as HTTP endpoints at `/mcp` when integrated with the main web application:

### Start Web Server
```bash
uv run python web/main.py
```

### HTTP Endpoints
- `GET /mcp/health` - Health check and capabilities
- `POST /mcp/rpc` - JSON-RPC endpoint for tool calls
- `GET /mcp/sse` - Server-Sent Events for streaming (future)

### Production URL
```
https://ui.lac.apps.digilab.network/mcp/
```

## Available Capabilities

### Tools (3)
- `execute_law` - Execute laws with generic parameters (BSN for citizens, kvk-nummer for businesses, etc.)
- `check_eligibility` - Quick eligibility checking for any law type
- `calculate_benefit_amount` - Calculate specific outputs for any parameter type

### Resources (3)
- `laws://list` - Browse available laws
- `law://{service}/{law}/spec` - Get law specifications
- `profile://{bsn}` - Access citizen profile data

### Prompts (3)
- `check_all_benefits` - Comprehensive benefit analysis
- `explain_calculation` - Step-by-step law explanations
- `compare_scenarios` - Multi-scenario comparisons

## Working Examples

### Example 1: Health Check
```bash
curl -s http://localhost:8000/mcp/health | jq
```

**Response:**
```json
{
  "status": "healthy",
  "transport": "http+sse",
  "active_sessions": 0,
  "capabilities": {
    "tools": ["execute_law", "check_eligibility", "calculate_benefit_amount"],
    "resources": ["laws://list", "law://{service}/{law}/spec", "profile://{bsn}"],
    "prompts": ["check_all_benefits", "explain_calculation", "compare_scenarios"]
  }
}
```

### Example 2: List Available Tools
```bash
curl -s -X POST http://localhost:8000/mcp/rpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' | jq
```

**Response:** Returns detailed tool schemas with required parameters and descriptions.

### Example 3: Check Zorgtoeslag Eligibility (Citizen Law)
```bash
curl -s -X POST http://localhost:8000/mcp/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "check_eligibility",
      "arguments": {
        "service": "TOESLAGEN",
        "law": "zorgtoeslagwet",
        "parameters": {"BSN": "100000001"}
      }
    },
    "id": 2
  }' | jq
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [{"type": "text", "text": "Eligible: True"}]
  },
  "id": 2
}
```

### Example 4: Full Law Execution with Calculation
```bash
curl -s -X POST http://localhost:8000/mcp/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "execute_law",
      "arguments": {
        "service": "TOESLAGEN",
        "law": "zorgtoeslagwet",
        "parameters": {"BSN": "100000001"}
      }
    },
    "id": 3
  }' | jq
```

**Response:** Returns complete law execution with:
- `is_verzekerde_zorgtoeslag: true`
- `hoogte_toeslag: 183424` (€1,834.24 monthly)
- Full calculation path and intermediate results
- All input parameters used in calculation

### Example 5: Calculate Specific Benefit Amount
```bash
curl -s -X POST http://localhost:8000/mcp/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "calculate_benefit_amount",
      "arguments": {
        "service": "TOESLAGEN",
        "law": "zorgtoeslagwet",
        "parameters": {"BSN": "100000001"},
        "output_field": "hoogte_toeslag"
      }
    },
    "id": 4
  }' | jq
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [{"type": "text", "text": "Amount: 183424"}]
  },
  "id": 4
}
```

### Example 6: Access Citizen Profile
```bash
curl -s -X POST http://localhost:8000/mcp/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "resources/read",
    "params": {"uri": "profile://100000001"},
    "id": 5
  }' | jq
```

**Response:** Returns complete citizen profile with data from:
- RvIG (personal data, address, relationships)
- BELASTINGDIENST (income, assets, tax data)
- KVK (business registrations)
- UWV (employment status)
- RVZ (health insurance)
- And more...

### Example 7: List Available Laws
```bash
curl -s -X POST http://localhost:8000/mcp/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "resources/list",
    "params": {},
    "id": 6
  }' | jq
```

**Response:** Returns all available laws across government services.

### Example 8: Check AOW Eligibility
```bash
curl -s -X POST http://localhost:8000/mcp/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "check_eligibility",
      "arguments": {
        "service": "SVB",
        "law": "algemene_ouderdomswet",
        "parameters": {"BSN": "100000001"}
      }
    },
    "id": 7
  }' | jq
```

### Example 9: Check Bijstand Eligibility (Amsterdam)
```bash
curl -s -X POST http://localhost:8000/mcp/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "check_eligibility",
      "arguments": {
        "service": "GEMEENTE_AMSTERDAM",
        "law": "participatiewet/bijstand",
        "parameters": {"BSN": "100000001"}
      }
    },
    "id": 8
  }' | jq
```

### Example 10: Check Voting Rights
```bash
curl -s -X POST http://localhost:8000/mcp/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "execute_law",
      "arguments": {
        "service": "KIESRAAD",
        "law": "kieswet",
        "parameters": {"BSN": "100000001"}
      }
    },
    "id": 9
  }' | jq
```

### Example 11: Check WPM Business Law (NEW!)
```bash
curl -s -X POST http://localhost:8000/mcp/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "check_eligibility",
      "arguments": {
        "service": "RVO",
        "law": "wpm",
        "parameters": {"kvk-nummer": "12345678"}
      }
    },
    "id": 10
  }' | jq
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [{"type": "text", "text": "Eligible: false"}]
  },
  "id": 10
}
```

### Example 12: Execute WPM Law with Full Details (NEW!)
```bash
curl -s -X POST http://localhost:8000/mcp/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "execute_law",
      "arguments": {
        "service": "RVO",
        "law": "wpm",
        "parameters": {"kvk-nummer": "12345678"}
      }
    },
    "id": 11
  }' | jq
```

## Available Test Data

### Test BSNs (Citizen Laws)
The following BSNs have complete test data:
- `100000001` - ZZP'er in thuiszorg, alleenstaande ouder (€1,550/month income)
- `123456782` - Basic profile for testing (may have limited data)

### Test KvK Numbers (Business Laws)
The following KvK numbers can be used for business law testing:
- `12345678` - Basic test business registration
- `87654321` - Alternative test business registration

## Parameter System

The MCP server now supports **generic parameters** for maximum flexibility:

### Citizen Laws (use BSN)
```json
{
  "service": "TOESLAGEN",
  "law": "zorgtoeslagwet",
  "parameters": {"BSN": "100000001"}
}
```

### Business Laws (use kvk-nummer)
```json
{
  "service": "RVO",
  "law": "wpm",
  "parameters": {"kvk-nummer": "12345678"}
}
```

### Custom Parameters (for laws with specific requirements)
```json
{
  "service": "EXAMPLE",
  "law": "custom_law",
  "parameters": {
    "case_id": "CASE-12345",
    "reference_date": "2024-01-01",
    "custom_field": "value"
  }
}
```

## Mock Data

Mock profile data is isolated in `mock_data.py` and includes basic citizen information for testing. In production, this would be replaced with real data sources like RvIG/BRP.
