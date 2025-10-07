#!/bin/bash
set -e

cd submodules/regelrecht-laws

# Fetch latest from remote
git fetch origin main --quiet

# Get local and remote commit hashes
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "ERROR: regelrecht-laws submodule is not up-to-date with remote."
    echo "Local commit:  $LOCAL"
    echo "Remote commit: $REMOTE"
    echo ""
    echo "To update:"
    echo "  cd submodules/regelrecht-laws"
    echo "  git pull origin main"
    echo "  cd ../.."
    echo "  git add submodules/regelrecht-laws"
    exit 1
fi

exit 0
