#!/bin/bash
set -e

if [ ! -f law/.git ]; then
    echo "ERROR: law submodule not initialized."
    echo "Run: git submodule update --init"
    exit 1
fi

exit 0
