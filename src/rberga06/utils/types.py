#!/usr/bin/env python3
# -*- codinig: utf-8 -*-
"""Useful types."""
from __future__ import annotations
from typing import Generic, Literal, TypeVar, cast, overload
import weakref
from packaging.version import Version as _Version


class Version(_Version):
    # pydnatic-compatible packaging.version.Version

    @classmethod
    def validate(cls, obj: str | Version) -> Version:
        if isinstance(obj, Version):
            return obj
        else:
            return cls(obj)

    @classmethod
    def __get_validators__(cls):
        """Pydantic compatibility."""
        yield cls.validate



_T = TypeVar("_T")


class ref(Generic[_T]):
    """Flexible, static reference (can be either a weak or a strong reference)."""
    __slots__ = ("inner",)

    inner: weakref.ref[_T] | _T
    """The wrapped value or a weak reference to it."""

    def __init__(self, inner: _T | weakref.ref[_T], /):
        self.inner = inner

    @property
    def _(self) -> _T:
        """The wrapped value."""
        return self()

    @classmethod
    def __get_validators__(cls):
        yield cls

    @overload
    def __call__(self, /, *, strict: Literal[True] = ...) -> _T: ...
    @overload
    def __call__(self, /, *, strict: Literal[False]) -> _T | None: ...
    def __call__(self, /, *, strict: bool = True) -> _T | None:
        """The wrapped value (`weakref`-style access)."""
        val = self.inner
        if self.is_weak:
            val = cast(weakref.ref[_T], val)()
            if strict and val is None:
                raise ValueError("Empty reference.")
        return cast(_T, val)

    @property
    def is_weak(self) -> bool:
        """Check if `self` is a weak reference."""
        return isinstance(self.inner, weakref.ref)


__all__ = [
    "Version", "ref",
]
