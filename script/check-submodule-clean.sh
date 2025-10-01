#!/bin/bash
set -e

if ! git -C law diff-index --quiet HEAD 2>/dev/null; then
    echo "ERROR: law submodule has uncommitted changes."
    echo "Commit them in the regelrecht-laws repository first."
    exit 1
fi

exit 0
