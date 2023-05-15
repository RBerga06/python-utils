#!/usr/bin/env python3
# -*- codinig: utf-8 -*-
"""Useful types."""
from __future__ import annotations
from typing import Any, Callable, Generic, Literal, TypeVar, cast, overload
import weakref
from packaging.version import Version as _Version
from pydantic_core import core_schema


class Version(_Version):
    # pydantic(v2)-compatible packaging.version.Version

    @staticmethod
    def validate(obj: str | Version, /) -> Version:
        if isinstance(obj, Version):
            return obj
        else:
            return Version(obj)

    @classmethod
    def __get_pydantic_core_schema__(cls, *args: Any, **kwargs: Any) -> core_schema.PlainValidatorFunctionSchema:
        # See https://github.com/pydantic/pydantic/issues/5373
        return core_schema.no_info_plain_validator_function(
            cls.validate, serialization=core_schema.to_string_ser_schema()
        )


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
        if self.is_weak:
            val = cast(weakref.ref[_T], self.inner)()
            if strict and val is None:
                raise ValueError("Empty reference.")
        else:
            val = cast(_T, self.inner)
        return val

    @property
    def is_weak(self) -> bool:
        """Check if `self` is a weak reference."""
        return isinstance(self.inner, weakref.ref)

    @staticmethod
    def validate(obj: ref[_T] | weakref.ref[_T] | _T, /) -> ref[_T]:
        if isinstance(obj, ref):
            return cast(ref[_T], obj)
        else:
            return ref(obj)

    @classmethod
    def __get_pydantic_core_schema__(cls, *args: Any, **kwargs: Any) -> core_schema.PlainValidatorFunctionSchema:
        # See https://github.com/pydantic/pydantic/issues/5373
        return core_schema.no_info_plain_validator_function(
            cls.validate, serialization=core_schema.to_string_ser_schema()
        )


_A = TypeVar("_A")
_B = TypeVar("_B")


class ItemFunc(Generic[_A, _B]):
    """Similar to a (_A, ) -> _B function, but called via [...] instead of (...)."""
    __slots__ = ("__wrapped__", )
    __wrapped__: Callable[[_A], _B]

    def __init__(self, func: Callable[[_A], _B], /) -> None:
        self.__wrapped__ = func

    def __getitem__(self, item: _A, /) -> _B:
        return self.__wrapped__(item)


class AttrFunc(Generic[_T]):
    """Similar to a (str, ) -> _T function but called via attribute access instead of (...)."""
    __slots__ = ("__wrapped__", )
    __wrapped__: Callable[[str], _T]

    def __init__(self, func: Callable[[str], _T], /) -> None:
        self.__wrapped__ = func

    def __getattr__(self, item: str, /) -> _T:
        return self.__wrapped__(item)


__all__ = [
    "Version", "ref",
]
