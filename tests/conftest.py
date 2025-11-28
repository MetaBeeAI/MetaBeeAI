"""Pytest configuration to ensure local src package is imported.

Adds the workspace `src/` directory to the front of `sys.path` so that
`import metabeeai` resolves to the local code instead of an installed package.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
sys.path.insert(0, str(SRC_DIR))
