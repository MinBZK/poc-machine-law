#!/bin/bash
set -e

# Skip in CI environments
if [ -n "$CI" ] || [ -n "$GITHUB_ACTIONS" ]; then
    echo "Skipping submodule check in CI (submodules handled by checkout action)"
    exit 0
fi

if ! git -C law diff-index --quiet HEAD 2>/dev/null; then
    echo "ERROR: law submodule has uncommitted changes."
    echo "Commit them in the regelrecht-laws repository first."
    exit 1
fi

exit 0
