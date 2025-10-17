#!/usr/bin/env bash
set -e

if [ ! -f submodules/regelrecht-laws/.git ]; then
    echo "ERROR: regelrecht-laws submodule not initialized."
    echo "Run: git submodule update --init --recursive"
    exit 1
fi

exit 0
