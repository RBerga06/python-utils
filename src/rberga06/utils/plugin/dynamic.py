#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runtime / Dynamic plugin data."""
from __future__ import annotations
from typing import TYPE_CHECKING, ClassVar, Generic, Self, TypeVar, cast
from pydantic import BaseModel, ConfigDict
from .static import Static

if TYPE_CHECKING:
    # Avoid circular imports
    from .system import System


class Features(BaseModel):
    """Plugin dynamic features."""
    # To be subclassed by plugin systems.


_F = TypeVar("_F", bound=Features)


class Plugin(BaseModel, Generic[_F]):
    """A plugin."""
    sys: System[_F]
    static: Static
    features: _F | None = None  # by default, it's not loaded

    @property
    def is_loaded(self) -> bool:
        return self.features is not None

    def load(self) -> Self:
        """Load `self` (in-place) and return it."""
        return self.sys.load(self)

    @property
    def feat(self) -> _F:
        """Lazy shortcut for `.load().features`."""
        if self.features is None:
            self.load()
        return cast(_F, self.features)

    # Pydantic model configuration
    model_config: ClassVar[ConfigDict] = {
        "undefined_types_warning": False,
    }


__all__ = [
    "Features",
    "Plugin",
]
