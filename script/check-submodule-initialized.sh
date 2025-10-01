#!/bin/bash
set -e

# Skip in CI environments
if [ -n "$CI" ] || [ -n "$GITHUB_ACTIONS" ]; then
    echo "Skipping submodule check in CI (submodules handled by checkout action)"
    exit 0
fi

if [ ! -f law/.git ]; then
    echo "ERROR: law submodule not initialized."
    echo "Run: git submodule update --init"
    exit 1
fi

exit 0
