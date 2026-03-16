"""Root conftest.py for test configuration."""

import sys
from pathlib import Path


project_root = str(Path(__file__).resolve().parent.parent)
while project_root in sys.path:
    sys.path.remove(project_root)
sys.path.insert(0, project_root)
