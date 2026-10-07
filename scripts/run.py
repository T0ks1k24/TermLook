#!/usr/bin/env python3
"""Desktop launcher that works independently of the working directory."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from termlook.app import main

main()
