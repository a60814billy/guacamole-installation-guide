#!/usr/bin/env python3
"""
Entry point for the refactored CSV import script.
This script imports and runs the main function from the src package.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the main function from the src package
from src.main import main

if __name__ == "__main__":
    main()
