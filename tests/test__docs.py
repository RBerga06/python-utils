#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test docstrings."""
from collections.abc import Iterator
import doctest
import importlib
import pytest
import pkgutil
import textwrap as tw
import traceback
from types import ModuleType
from typing_extensions import TYPE_CHECKING, Any, override
import rberga06.utils



class EnhancedDocTestFailure(doctest.DocTestFailure):
    @override
    def __str__(self) -> str:
        l = "  "
        message = "\n".join([
            "Doc test:",
            tw.indent(self.example.source, l),
            "Got:",
            tw.indent(self.got, l),
            "Expected:",
            tw.indent(self.example.want or "None", l),
        ])
        return f"Doctest failure.\n{tw.indent(message, '  ')}"


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


_ns = namespace()


@pytest.mark.parametrize("module", [*_iterpkg(rberga06.utils)])
def test_doctest(module: ModuleType) -> None:
    try:
        doctest.testmod(
            module,
            extraglobs=_ns.copy(),
            # verbose=True,  # uncomment this when needed
            raise_on_error=True,
        )
    except doctest.DocTestFailure as exc:
        raise EnhancedDocTestFailure(exc.test, exc.example, exc.got)
    except doctest.UnexpectedException as exc:
        cls, err, _ = exc.exc_info
        err_str = "\n".join(traceback.format_exception_only(cls, value=err))
        raise EnhancedDocTestFailure(
            exc.test, exc.example,
            f"Traceback (most recent call last):\n...\n{err_str}"
        )
