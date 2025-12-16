# Machine Law Codebase Guidelines

## Commands
- Run all tests: `uv run behave features --no-capture -v --define log_level=DEBUG`
- Run specific feature: `uv run behave features/zorgtoeslag.feature`
- Lint code: `ruff check` and `ruff format`
- Run pre-commit hooks: `pre-commit run --all-files`
- Validate schemas: `./script/validate.py`
- Run web interface: `uv run web/main.py` (available at http://0.0.0.0:8000)
- Run simulations: `uv run simulate.py`
- Package management: `uv add [package]` to install dependencies

## Code Style
- Python 3.12+
- Indentation: 4 spaces (Python), 2 spaces (YAML)
- Line length: 120 characters
- Naming: snake_case (variables/functions), PascalCase (classes), UPPER_CASE (constants)
- Imports: stdlib → third-party → local, sorted alphabetically within groups
- Type annotations: required for all function parameters and return values
- Error handling: specific exceptions, contextual logging, fallback values
- YAML: structured hierarchies with explicit types for law definitions
- Architecture: modular, service-oriented with event-driven components

## Git Workflow
- NEVER amend commits that failed to go through - make new commits instead
- ALWAYS run `pre-commit run --all-files` BEFORE every commit (hooks don't auto-run in Claude's Bash environment)
- Always check git status before committing to make sure you're working with the latest changes
