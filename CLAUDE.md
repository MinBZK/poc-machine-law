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

## Commit Message Convention (Semantic Versioning)

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automatic version bumping. The version in the footer and `pyproject.toml` is automatically updated when PRs merge to main.

### Commit Format
```
<type>: <description>

[optional body]

[optional footer with BREAKING CHANGE: if needed]
```

### Types and Version Impact
| Type | Version Bump | When to Use |
|------|--------------|-------------|
| `feat:` | Minor (0.1.0 → 0.2.0) | New feature or capability |
| `fix:` | Patch (0.1.0 → 0.1.1) | Bug fix |
| `perf:` | Patch | Performance improvement |
| `docs:` | None | Documentation only |
| `style:` | None | Code style (formatting, semicolons) |
| `refactor:` | None | Code change that neither fixes nor adds |
| `test:` | None | Adding or updating tests |
| `chore:` | None | Maintenance, dependencies, CI |
| `ci:` | None | CI/CD changes |
| `build:` | None | Build system changes |

### Breaking Changes (Major Bump)
For breaking changes (0.1.0 → 1.0.0), use either:
```
feat!: remove deprecated API endpoint
```
or:
```
feat: redesign authentication system

BREAKING CHANGE: JWT tokens now require 'aud' claim
```

### Multiple Commits in a PR
When a PR has multiple commits, the **highest priority** wins:
1. Any `BREAKING CHANGE` or `!` suffix → major bump
2. Any `feat:` → minor bump
3. Only `fix:`/`perf:` → patch bump
4. Only `docs:`/`chore:`/etc. → no bump

### Best Practices
- **One logical change per commit** - don't mix `feat:` and `fix:` in one commit
- **Be specific** - `fix: resolve null pointer in tax calculation` not `fix: bug`
- **Use imperative mood** - "add feature" not "added feature"
- **Reference issues** - `fix: handle empty input (#123)`

### Examples
```bash
# New feature (minor bump)
git commit -m "feat: add delegation support for business users"

# Bug fix (patch bump)
git commit -m "fix: correct tax calculation for edge case with zero income"

# Documentation (no bump)
git commit -m "docs: update API documentation for claims endpoint"

# Breaking change (major bump)
git commit -m "feat!: change profile API response structure"

# Chore/maintenance (no bump)
git commit -m "chore: update dependencies to latest versions"
```
