#!/bin/bash
# Install all pre-commit hooks

set -e

echo "Installing pre-commit hooks..."
pre-commit install
pre-commit install --hook-type commit-msg

echo ""
echo "✅ Hooks installed successfully!"
echo ""
echo "Installed hooks:"
echo "  - pre-commit: code formatting, linting, schema validation"
echo "  - commit-msg: conventional commit message enforcement"
echo ""
echo "Commit message format:"
echo "  type(scope): description"
echo ""
echo "Allowed types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert"
echo ""
echo "Examples:"
echo "  feat: add user authentication"
echo "  fix: resolve null pointer in tax calculation"
echo "  docs: update API documentation"
