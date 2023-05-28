#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilities for distribution data access."""
from pathlib import Path
from typing import ContextManager, NamedTuple, TypeVar
import importlib.resources
import importlib.metadata
from packaging.requirements import Requirement
from .deps import dependency, DepsEnum


_E = TypeVar("_E", bound=type[DepsEnum])


class about(NamedTuple):
    """Utilities for distribution data access."""

    name: str
    """The distribution's name."""
    pkg: str
    """The distribution's root package."""

    @property
    def dist(self) -> importlib.metadata.Distribution:
        """Get the `importlib.metadata.Distribution` object."""
        return importlib.metadata.distribution(self.name)

    @property
    def version(self) -> str:
        """Get the version."""
        return importlib.metadata.version(self.name)

    def path(self, child: str) -> ContextManager[Path]:
        """Get the `Path` of `child` in this distribution."""
        return importlib.resources.as_file(importlib.resources.files(self.pkg) / child)

    def deps(self) -> dict[str, dependency]:
        """Get infos about all dependencies."""
        return {
            (req := Requirement(info)).name: dependency(req.name, str(req.specifier))
            for info in (importlib.metadata.requires(self.name) or [])
        }

    def dep(self, name: str, /) -> dependency:
        """Get infos about this dependency."""
        return self.deps()[name]

    def deps_enum(self, enum: _E) -> _E:
        enum.register(self)
        return enum


__all__ = [
    "about",
]
