# LLM Explanations Research

This directory contains tools for research on LLM-generated explanations of machine law decisions.

## extract_explanations.py

Extracts LLM-generated explanations ("waarom") for machine law decisions. This script is designed for research purposes, specifically for analyzing how LLMs explain automated legal decisions.

### Prerequisites

1. **Anthropic API Key**: You need an API key from [Anthropic](https://console.anthropic.com/)
2. **Python dependencies**: Install with `uv sync` from the project root

### Quick Start

```bash
# From project root directory
cd /path/to/machine-law

# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Run extraction for all profiles and laws
uv run python analysis/llm_explanations/extract_explanations.py
```

### Usage Examples

```bash
# List available profiles (no API key needed)
uv run python analysis/llm_explanations/extract_explanations.py --list-profiles

# List available laws (no API key needed for listing)
uv run python analysis/llm_explanations/extract_explanations.py --list-laws

# Extract all combinations (uses Claude Haiku 4.5 by default - fast & cheap)
uv run python analysis/llm_explanations/extract_explanations.py

# Use a different model
uv run python analysis/llm_explanations/extract_explanations.py --model sonnet  # More capable
uv run python analysis/llm_explanations/extract_explanations.py --model opus    # Most capable

# Extract explanations for specific laws only
uv run python analysis/llm_explanations/extract_explanations.py --laws zorgtoeslag huurtoeslag

# Extract for specific profiles (BSN numbers)
uv run python analysis/llm_explanations/extract_explanations.py --profiles 100000001 100000002

# Combine filters
uv run python analysis/llm_explanations/extract_explanations.py --laws zorgtoeslag --profiles 100000001

# Save to a specific output file
uv run python analysis/llm_explanations/extract_explanations.py --output research_data.jsonl

# Quiet mode (less verbose output)
uv run python analysis/llm_explanations/extract_explanations.py --quiet

# Pass API key as argument instead of environment variable
uv run python analysis/llm_explanations/extract_explanations.py --api-key "sk-ant-..."
```

### Model Selection

| Model | ID | Speed | Cost | Best for |
|-------|-----|-------|------|----------|
| **haiku** (default) | claude-haiku-4-5 | Fastest | $1/$5 per MTok | Batch processing, research |
| **sonnet** | claude-sonnet-4-5 | Medium | $3/$15 per MTok | Balanced quality/cost |
| **opus** | claude-opus-4-5 | Slowest | $5/$25 per MTok | Highest quality |

For research/thesis work, **haiku** is recommended - it's fast, cheap, and produces good explanations.

### Output Format (JSONL)

The script generates a **JSONL (JSON Lines)** file where each line is a separate JSON object. This format is ideal for:
- Streaming processing of large datasets
- Appending new records without rewriting the entire file
- Handling partial failures gracefully
- Easy processing with tools like `jq`, pandas, etc.

#### First Line: Metadata Record

Contains all information needed for reproducibility:

```json
{
  "record_type": "metadata",
  "extraction_date": "2025-01-19T10:30:00",
  "reference_date": "2025-01-19",
  "git_info": {
    "machine_law_commit": "abc123...",
    "machine_law_branch": "main",
    "machine_law_dirty": false,
    "regelrecht_laws_commit": "def456...",
    "regelrecht_laws_dirty": false
  },
  "llm_params": {
    "model_id": "claude-3-7-sonnet-20250219",
    "max_tokens": 1500,
    "temperature": 0.3,
    "system_prompt": "Je bent een behulpzame assistent..."
  },
  "filters": {
    "laws_filter": null,
    "profiles_filter": null
  },
  "total_profiles": 40,
  "total_laws": 10,
  "expected_records": 400,
  "global_services": { ... }
}
```

#### Subsequent Lines: Explanation Records

Each record contains full context for reproducibility:

```json
{
  "record_type": "explanation",
  "record_number": 1,
  "timestamp": "2025-01-19T10:30:01",
  "bsn": "100000001",
  "profile": {
    "name": "Merijn van der Meer",
    "description": "ZZP'er in de thuiszorg...",
    "sources": {
      "RvIG": { "personen": [...], "relaties": [...] },
      "BELASTINGDIENST": { "box1": [...], "box2": [...], "box3": [...] },
      ...
    }
  },
  "law": {
    "name": "zorgtoeslag",
    "description": "Zorgtoeslag",
    "service_type": "TOESLAGEN",
    "law_path": "zorgtoeslagwet",
    "rule_spec_name": "Zorgtoeslag",
    "rule_spec_version": "2025-01-01"
  },
  "calculation_result": {
    "requirements_met": true,
    "missing_required": false,
    "missing_fields": [],
    "output": {"hoogte_toeslag": 201436, "is_verzekerde_zorgtoeslag": true},
    "input_data": { ... },
    "system_explanation": "U voldoet aan alle voorwaarden..."
  },
  "llm_explanation": "# Uitleg over uw zorgtoeslag\n\n...",
  "llm_usage": {
    "input_tokens": 523,
    "output_tokens": 487
  },
  "prompt_used": "Ik heb zojuist een berekening uitgevoerd..."
}
```

### Reading JSONL Files

```python
import json

# Read all records
records = []
with open("explanations_output.jsonl") as f:
    for line in f:
        records.append(json.loads(line))

# First record is metadata
metadata = records[0]
explanations = records[1:]

# Or with pandas
import pandas as pd
df = pd.read_json("explanations_output.jsonl", lines=True)
```

```bash
# With jq - get all successful explanations
cat explanations_output.jsonl | jq 'select(.record_type == "explanation" and .llm_explanation != null)'

# Count records by requirements_met
cat explanations_output.jsonl | jq -s '[.[] | select(.record_type == "explanation")] | group_by(.calculation_result.requirements_met) | map({met: .[0].calculation_result.requirements_met, count: length})'
```

### Reproducibility

The output includes everything needed to reproduce the extraction:

| Field | Description |
|-------|-------------|
| `git_info.machine_law_commit` | Exact commit of the machine-law codebase |
| `git_info.regelrecht_laws_commit` | Exact commit of the law definitions |
| `git_info.*_dirty` | Whether there were uncommitted changes |
| `llm_params` | Model ID, temperature, max_tokens, system prompt |
| `profile.sources` | Complete input data used for calculation |
| `law.rule_spec_version` | Which dated law YAML was used |
| `prompt_used` | Exact prompt sent to the LLM |

### Available Laws

| Law Name | Description | Service |
|----------|-------------|---------|
| zorgtoeslag | Zorgtoeslag | TOESLAGEN |
| huurtoeslag | Huurtoeslag | TOESLAGEN |
| kinderopvangtoeslag | Kinderopvangtoeslag | TOESLAGEN |
| wetophetkindgebondenbudget | Kindgebonden Budget | TOESLAGEN |
| bijstand | Bijstand | GEMEENTE_AMSTERDAM |
| aow | AOW-uitkering | SVB |
| werkloosheidswet | Werkloosheidsuitkering | UWV |
| inkomstenbelasting | Inkomstenbelasting | BELASTINGDIENST |
| kieswet | Kiesrecht | KIESRAAD |
| besluitbijstandverleningzelfstandigen | Bbz 2004 | SZW |

### API Key Options

1. **Personal API key**: Create one at https://console.anthropic.com/
2. **Anthropic Academic Program**: For research, you may be eligible for credits
3. **Shared key**: Ask your supervisor for a temporary key for batch extraction

### Cost Estimation

- Each explanation uses approximately 500 input tokens + 500 output tokens
- With ~40 profiles × ~10 laws = ~400 API calls

| Model | Est. Cost (400 calls) |
|-------|----------------------|
| haiku | ~$1.20 USD |
| sonnet | ~$3.60 USD |
| opus | ~$6.00 USD |

### Troubleshooting

**"No Anthropic API key found"**
- Set `ANTHROPIC_API_KEY` environment variable or use `--api-key` argument

**"ModuleNotFoundError"**
- Run from the project root directory
- Ensure dependencies are installed: `uv sync`

**"Service not found"**
- Make sure the law submodule is initialized: `git submodule update --init --recursive`
