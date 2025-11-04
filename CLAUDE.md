# Machine Law Codebase Guidelines

## Commands
- Run all tests: `uv run behave features --no-capture -v --define log_level=DEBUG`
- Run specific feature: `uv run behave features/zorgtoeslag.feature`
- Run DMN tests (pytest): `uv run python -m pytest tests/integration/dmn/ -v`
- Run DMN feature tests (behave): `uv run behave features/dmn/ --no-capture -v --dry-run`
- Validate DMN files: `python validate_dmn.py`
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

## DMN Testing
- DMN files are located in `dmn/` directory
- DMN tests use pytest and are located in `tests/integration/dmn/`
- DMN Behave features are in `features/dmn/` with corresponding steps in `features/steps/dmn_steps.py`
- Test fixtures are defined in `tests/integration/dmn/conftest.py`
- DMN files follow OMG DMN 1.3 standard
- Decision services with single output return the value directly (no dict wrapping)
- Decision services with multiple outputs return a dict with all outputs
- BKM functions are registered using the BKM ID without "bkm_" prefix
- FEEL expressions should be single-line to avoid parsing issues in the current engine

## Git Workflow
- NEVER amend commits that failed to go through - make new commits instead
- Run pre-commit hooks before committing to catch formatting issues
- Always check git status before committing to make sure you're working with the latest changes
