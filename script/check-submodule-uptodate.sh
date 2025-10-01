#!/bin/bash
set -e

cd law

# Fetch latest from remote
git fetch origin main --quiet

# Get local and remote commit hashes
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "ERROR: law submodule is not up-to-date with remote."
    echo "Local commit:  $LOCAL"
    echo "Remote commit: $REMOTE"
    echo ""
    echo "To update:"
    echo "  cd law"
    echo "  git pull origin main"
    echo "  cd .."
    echo "  git add law"
    exit 1
fi

exit 0
