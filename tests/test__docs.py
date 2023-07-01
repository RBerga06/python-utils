#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test docstrings."""
from collections.abc import Iterator
import pkgutil
from types import ModuleType
import doctest
import importlib

import rberga06.utils


def _iterpkg(mod: ModuleType) -> Iterator[ModuleType]:
    if mod.__file__ is not None:
        # mod is a module, or an ordinary package
        yield mod
    if (path := getattr(mod, "__path__", None)) is not None:
        # mod is a package, possibly a namespace package
        for _, name, _ in pkgutil.iter_modules(path, f"{mod.__name__}."):
            yield from _iterpkg(importlib.import_module(name))


def test_doctest() -> None:
    for module in _iterpkg(rberga06.utils):
        doctest.testmod(module, raise_on_error=True)
