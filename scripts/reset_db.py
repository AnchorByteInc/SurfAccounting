#!/usr/bin/env python3
import sys
import os

# Ensure the project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.utils.db_manager import reset_database

if __name__ == "__main__":
    # If any argument like "-f" or "--force" is passed, run non-interactively
    force = "-f" in sys.argv or "--force" in sys.argv
    reset_database(interactive=not force)
