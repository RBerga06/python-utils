#!/usr/bin/env python3
# -*- codinig: utf-8 -*-
"""Useful types."""
from __future__ import annotations
from typing import Generic, Literal, TypeVar, cast, overload
import weakref
from packaging.version import Version as _Version
from pydantic import ValidationInfo
from pydantic_core.core_schema import PlainValidatorFunctionSchema


class Version(_Version):
    # pydantic(v2)-compatible packaging.version.Version

    @staticmethod
    def validate(obj: str | Version, info: ValidationInfo, /) -> Version:
        if isinstance(obj, Version):
            return obj
        else:
            return Version(obj)

    # See https://docs.pydantic.dev/blog/pydantic-v2/#changes-to-custom-field-types
    __pydantic_core_schema__: PlainValidatorFunctionSchema = {
        "type": "function-plain",
        "function": {
            "type": "general",
            "function": validate,
        },
    }


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

    @staticmethod
    def validate(obj: ref[_T] | weakref.ref[_T] | _T, info: ValidationInfo, /) -> ref[_T]:
        if isinstance(obj, ref):
            return cast(ref[_T], obj)
        else:
            return ref(obj)

    # See https://docs.pydantic.dev/blog/pydantic-v2/#changes-to-custom-field-types
    __pydantic_core_schema__: PlainValidatorFunctionSchema = {
        "type": "function-plain",
        "function": {
            "type": "general",
            "function": validate,
        },
    }


__all__ = [
    "Version", "ref",
]
