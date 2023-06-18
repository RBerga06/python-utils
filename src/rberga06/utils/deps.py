#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mypy: ignore-errors
"""Utilities for runtime dependencies management."""
from enum import Enum
import sys
from types import EllipsisType
from typing import TYPE_CHECKING, Any, Callable, Self, TypeVar
import importlib.metadata
from typing_extensions import override
from packaging.specifiers import SpecifierSet
from textwrap import dedent

from .types import Mut
from .func.dec import AnyDecorator, decorator

if TYPE_CHECKING:
    from .about import about as _about


class RequirementError(RuntimeError):
    """A requirement is not met."""

    @classmethod
    def mk(cls, err: "RequirementError | Any", *args: Any) -> Self:
        return err if isinstance(err, cls) else cls(err, *args)


class DependencyError(RequirementError):
    """A dependency is missing."""
    args: tuple[str, str, str | None]

    def __init__(self, name: str, version: str, installed: str | None = None, /) -> None:
        super().__init__(name, version, installed)

    @override
    def __str__(self) -> str:
        name, version, installed = self.args
        if version and installed:
            error = f"Incompatible version for distribution {name!r}: expected {version!r}, found {installed!r}."
        else:
            error = f"Could not find distribution {name!r}."
        install = f"{name}{f' {version}' if version else ''}"
        return dedent(f"""\
            {error}
            You should consider installing it.
            In case you use `pip`, the command would be:
              $ {sys.executable} -m pip install {install!r}\
        """)


class dependency:
    _depname: str   # Dependency name
    _version: str   # Version specification

    def __init__(self, name: EllipsisType | str, version: str | None = None, /) -> None:
        if name is ...:  name = "???"
        if version is None and " " in name:
            name, version = name.split(" ", 1)
        self._depname = name
        self._version = version or ""

    def __set_name__(self, name: str) -> None:
        self._depname = name

    def read_about(self, about: "_about") -> Self:
        try:
            self._version = about.dep(self._depname)._version
        except KeyError:
            pass
        return self

    @property
    def depname(self) -> str:
        return self._depname

    @property
    def version(self):
        return self._version

    def ensure(self) -> Self:
        name, version = self._depname, self._version
        if " " in name and not version:
            name, version = name.split(" ", maxsplit=1)
        try:
            installed = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            raise DependencyError(name, version)
        if not SpecifierSet(version or "").contains(installed):
            raise DependencyError(name, version, installed)
        return self

    def available(self) -> bool:
        try:
            self.ensure()
        except RequirementError:
            return False
        else:
            return True


class DepsEnum(dependency, Enum):
    """dependency enum for `__about__`s"""

    @classmethod
    def register(cls, about: "_about") -> None:
        for dep in cls:
            dep.__set_name__(dep._name_)
            dep.read_about(about)


_F = TypeVar("_F", bound=Callable[..., Any])


def ensure(check: bool | Callable[[], bool | Any] | dependency | Any, /, err: str | RequirementError = RequirementError()) -> None:
    """Like `assert`, but better."""
    if callable(check):
        return ensure(check(), err=err)
    if isinstance(check, bool) and not check:
        raise RequirementError.mk(err)
    if isinstance(check, dependency):
        check.ensure()


def requires(check: bool | Callable[[], bool | Any] | dependency, /, *, err: str | RequirementError = RequirementError()) -> AnyDecorator[_F]:
    @decorator(data=lambda: Mut(True))
    def requires(__data__: Mut[bool], __decorated__: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        if __data__.get():
            ensure(check, err=err)
            __data__.set(False)
        return __decorated__(*args, **kwargs)
    requires.__name__ = f"requires({check!r})"
    return requires
