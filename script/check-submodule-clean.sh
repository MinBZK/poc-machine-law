#!/usr/bin/env bash
set -e

if ! git -C submodules/regelrecht-laws diff-index --quiet HEAD 2>/dev/null; then
    echo "ERROR: regelrecht-laws submodule has uncommitted changes."
    echo "Commit them in the regelrecht-laws repository first."
    exit 1
fi

exit 0
