import importlib.util
import sys
from pathlib import Path
from typing import Any, Type


def load_agent_class(agent_filename: str, class_name: str) -> Type[Any]:
    module_path = Path(__file__).resolve().parents[2] / "src" / "agents" / agent_filename
    if not module_path.exists():
        raise FileNotFoundError(f"Agent module not found: {module_path}")

    spec = importlib.util.spec_from_file_location(class_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import {class_name} from {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return getattr(module, class_name)
