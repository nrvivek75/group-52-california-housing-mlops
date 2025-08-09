#!/usr/bin/env python3
"""
Script to train all models for California Housing prediction
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.models.train import main

if __name__ == "__main__":
    main()