"""Auto-import prompts."""
import os
from pathlib import Path

tools_dir = Path(__file__).parent
for file in tools_dir.glob("*.py"):
    if file.name != "__init__.py" and not file.name.startswith("_"):
        import importlib
        importlib.import_module(f".{file.stem}", package=__name__)
