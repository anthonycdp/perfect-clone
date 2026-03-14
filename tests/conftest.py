"""Root conftest.py for test configuration."""

import sys
from pathlib import Path

# Add project root to Python path at the VERY FRONT
# This is critical because pytest adds test directories to path,
# which can shadow the actual source packages
project_root = str(Path(__file__).resolve().parent.parent)

# Remove any existing instances and insert at front
while project_root in sys.path:
    sys.path.remove(project_root)
sys.path.insert(0, project_root)
