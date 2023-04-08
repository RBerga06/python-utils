#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilities for distribution data access."""
from pathlib import Path
from typing import ContextManager, NamedTuple
import importlib.resources
import importlib.metadata


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


__all__ = [
    "about",
]
