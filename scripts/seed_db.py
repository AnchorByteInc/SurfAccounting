#!/usr/bin/env python3
import sys
import os

# Ensure the project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.utils.db_manager import seed_database

if __name__ == "__main__":
    seed_database()
