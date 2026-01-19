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
