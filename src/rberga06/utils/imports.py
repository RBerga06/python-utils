#!/usr/bin/env python3
"""Imports utilities."""
from __future__ import annotations
import importlib

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Iterable


_FAKE_MODULE_DOC = "This is a fake module!"


def import_or_fake(name: str, is_pkg: bool = False, parents_know: bool = False) -> ModuleType:
    """Import the given module or package if possible, else fake it."""
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError:
        return fake_module(name, pkg=is_pkg, parents_know=parents_know)


def fake_module(name: str, /, *, pkg: bool | Iterable[str] = False, parents_know: bool = False, inject: dict[str, object] | None = None) -> ModuleType:
    """Create and register a “fake” module. If `pkg` is True, make it a package; if `pkg` is an iterable, use that as __path__ for the package."""
    mod = ModuleType(name, doc=_FAKE_MODULE_DOC)
    if inject is None:
        inject = {}
    if pkg is not False:
        if pkg is True:
            pkg = []
        inject.setdefault("__path__", pkg)
    for k, v in inject.items():
        object.__setattr__(mod, k, v)
    sys.modules[name] = mod
    if "." in name:
        pkg, me = name.rsplit(".", maxsplit=1)
        parent = import_or_fake(pkg, is_pkg=True, parents_know=parents_know)
        if parents_know:
            object.__setattr__(parent, me, mod)
    return mod


def import_from(path: Path, name: str, /, *, inject: dict[str, object] | None = None) -> ModuleType:
    """Import a module (or package) at the given path."""
    path = path.resolve()
    if not path.exists():
        raise ModuleNotFoundError(name=name, path=str(path))
    if path.is_dir():
        return import_from(path/"__init__.py", name, inject=inject)
    spec = spec_from_file_location(name, path)
    if spec is None:  # pragma: no cover
        raise ImportError(name=name, path=str(path))
    module = module_from_spec(spec)
    if spec.loader is None:  # pragma: no cover
        raise ImportError(name=name, path=str(path))
    sys.modules[spec.name] = module
    if "." in spec.name:
        # import or fake the parent module, to make sure this is importable
        import_or_fake(spec.name.rsplit(".", maxsplit=1)[0])
    if inject:
        for name, value in inject.items():
            setattr(module, name, value)
    spec.loader.exec_module(module)
    return module


def absolutize_obj_name(name: str, root: str) -> str:
    """Absolutize `name` relatively to `root`."""
    # Example: ('.a:b',  'root') -> 'root.a:b'
    #          ('.:b',   'root') -> 'root:b'
    #          ('.a',    'root') -> 'root.a'
    #          ('c.d:e', 'root') -> 'c.d:e'
    if not name.startswith("."):
        return name
    if not ":" in name:
        name = f"{name}:"
    mod, obj = name.split(":")
    return ":".join([
        f"{root}{mod}".removesuffix("."),
        obj,
    ]).removesuffix(":")


_PYTHON_INVALID_CHARS = "=-+*/%&|^<>:;,.@{}[]()!?'\\\"\n\r\t #$"


def pythonize(id: str, /, *, ignore: Iterable[str] = "") -> str:
    """Return a valid Python identifier inspired by `name`."""
    for char in {*_PYTHON_INVALID_CHARS} - {*ignore}:
        id = id.replace(char, "_")
    return id


__all__ = [
    "import_or_fake",
    "fake_module",
    "import_from",
    "absolutize_obj_name",
    "pythonize",
]
