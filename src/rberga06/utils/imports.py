#!/usr/bin/env python3
"""Imports utilities."""
from __future__ import annotations

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType


def import_from(path: Path, name: str, /, *, inject: dict[str, object] | None = None) -> ModuleType:
    """Import a module (or package) at the given path."""
    path = path.resolve()
    if not path.exists():
        raise ModuleNotFoundError(name=name, path=str(path))
    if path.is_dir():
        return import_from(path/"__init__.py", name, inject=inject)
    spec = spec_from_file_location(name, path)
    if spec is None:
        raise ImportError(name=name, path=str(path))
    module = module_from_spec(spec)
    if spec.loader is None:
        raise ImportError(name=name, path=str(path))
    sys.modules[spec.name] = module 
    if inject:
        for name, value in inject.items():
            setattr(module, name, value)
    spec.loader.exec_module(module)
    return module


__all__ = [
    "import_from",
]
