#!/usr/bin/env python

"""
Simple test script for the gopy_machine module.
Modify this script to test your specific Go functions.
"""

import sys
import os

# Add the package directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import gopy_machine
    print(f"Successfully imported {MODULE_NAME} module")
    
    # TODO: Add your test code here
    # Example:
    # result = gopy_machine.SomeFunction()
    # print(f"Result: {result}")
    
    # Print available functions and classes
    print("\nAvailable attributes in the module:")
    for attr in dir(gopy_machine):
        if not attr.startswith('_'):
            print(f"  - {attr}")
    
except ImportError as e:
    print(f"Error importing module: {e}")
    sys.exit(1)
