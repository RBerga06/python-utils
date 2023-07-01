#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test docstrings."""
from collections.abc import Iterator
import pkgutil
from types import ModuleType
import doctest
import importlib
from typing import TYPE_CHECKING, Any


def _iterpkg(mod: ModuleType) -> Iterator[ModuleType]:
    if mod.__file__ is not None:
        # mod is a module, or an ordinary package
        yield mod
    if (path := getattr(mod, "__path__", None)) is not None:
        # mod is a package, possibly a namespace package
        for _, name, _ in pkgutil.iter_modules(path, f"{mod.__name__}."):
            yield from _iterpkg(importlib.import_module(name))


def _import_all(modulename: str) -> dict[str, Any]:
    module = importlib.import_module(modulename)
    return {
        name: getattr(module, name)
        for name in getattr(
            module, "__all__",
            [name for name in vars(module) if not name.startswith("_")],
        )
    }


def namespace() -> dict[str, Any]:
    assert not TYPE_CHECKING
    import packaging.version
    import pydantic
    return {
        **locals(),
        **_import_all("typing_extensions"),
    }


def test_doctest() -> None:
    import rberga06.utils

    for module in _iterpkg(rberga06.utils):
        doctest.testmod(
            module,
            extraglobs=namespace(),
            # verbose=True,  # uncomment this when needed
            raise_on_error=True,
        )
