#!/usr/bin/env python
"""
Wrapper script to run Behave features from PyCharm.
Usage: python run_behave.py <feature_file_path>
"""
import sys
import subprocess
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_behave.py <feature_file_path>")
        sys.exit(1)

    feature_file = sys.argv[1]

    # Get the project root (where this script is located)
    project_root = Path(__file__).parent

    # Build the behave command
    cmd = [
        sys.executable,
        "-m",
        "behave",
        feature_file,
        "--no-capture",
        "-v",
        "--define",
        "log_level=DEBUG"
    ]

    print(f"Running: {' '.join(cmd)}")
    print(f"Working directory: {project_root}")

    # Run the command
    result = subprocess.run(cmd, cwd=project_root)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
