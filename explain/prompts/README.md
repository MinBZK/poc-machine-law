# Prompt Templates

This directory contains the Jinja2 templates used for prompting LLMs in the Machine Law application.

## Structure

- Main templates:
  - `mcp_system_prompt.j2`: Core system prompt for MCP services
  - `chat_system_prompt.j2`: System prompt for the chat interface
  - `tool_response.j2`: Template for tool execution results
  - `claim_processing.j2`: Template for processing user-provided claim values
  - `chained_service.j2`: Template for processing chained services

- Helper templates:
  - `service_tool_template.j2`: Template for individual service tool definitions
  - `claim_tool_template.j2`: Template for the claim_value tool definition

- Includes (in `includes/` directory):
  - `belangrijk.j2`: Common "BELANGRIJK" section used across templates
  - `explanation_instructions.j2`: Common explanation guidelines
  - `missing_fields_instructions.j2`: Instructions for missing fields
  - `summary_instructions.j2`: Common summary instructions
  - `tool_usage.j2`: Instructions for using the tools
  - `claims_instructions.j2`: Instructions for handling missing data
  - `chained_laws.j2`: Instructions for chaining laws together

## Usage

These templates are used by the `MCPLawConnector` class in `explain/mcp_connector.py` and by
the chat router in `web/routers/chat.py` to generate prompts for LLMs.

The templates use Jinja2 variable interpolation and control structures to generate appropriate
prompts based on the context.

## Best Practices

1. Extract common sections to the `includes/` directory
2. Keep templates focused on their specific use case
3. Use consistent naming conventions
4. Document template parameters
