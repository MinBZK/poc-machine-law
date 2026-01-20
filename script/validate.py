#!/usr/bin/env python3
"""Wrapper to import validate from submodule."""

import sys
from pathlib import Path

# Add the submodules directory to the path
submodule_path = Path(__file__).parent.parent / "submodules" / "regelrecht-laws" / "script"
sys.path.insert(0, str(submodule_path))

# Import everything from the actual validate module
from validate import *  # noqa: F401, F403

if __name__ == "__main__":
    # Import main and run it
    from validate import main
    main()
