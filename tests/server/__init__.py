"""Server test package bootstrap."""

import importlib.util
import sys
from pathlib import Path


project_root = Path(__file__).resolve().parents[2]
server_package = project_root / "server"
spec = importlib.util.spec_from_file_location(
    "server",
    server_package / "__init__.py",
    submodule_search_locations=[str(server_package)],
)
server_module = importlib.util.module_from_spec(spec)
sys.modules["server"] = server_module
assert spec.loader is not None
spec.loader.exec_module(server_module)
