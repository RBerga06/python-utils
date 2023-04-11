#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Useful caching utilities."""
from __future__ import annotations
from functools import wraps
from typing import Callable, Generic, Literal, Protocol, TypeGuard, TypeVar, cast, final, overload


_T = TypeVar("_T")
_X = TypeVar("_X")
_F = TypeVar("_F", bound=Callable[..., object])


class WithCache(Protocol[_T]):
    __cache__: cache[_T]


@final
class cache(Generic[_T]):
    """A cache."""
    __slots__ = ("_",)

    _: _T | None
    """The value stored in the cache."""

    def __init__(self, _: _T | None = None) -> None:
        self._ = _

    def __repr__(self) -> str:
        return f"<cache: {self._!r}>"

    @staticmethod
    def is_(obj: object, /) -> TypeGuard[cache[_T]]:
        """Check if `obj` is a cache."""
        return isinstance(obj, cache)

    @overload
    @staticmethod
    def has(obj: object, /, *, strict: Literal[True]) -> TypeGuard[WithCache[_T]]: ...
    @overload
    @staticmethod
    def has(obj: object, /, *, strict: Literal[False] = ...) -> bool: ...
    @staticmethod
    def has(obj: object, /, *, strict: bool = False) -> TypeGuard[WithCache[_T]] | bool:
        """Check if `obj` has a cache."""
        if cache.is_(getattr(obj, "__cache__", None)):
            return True
        if strict:
            return False
        if isinstance(obj, property):
            return cache.has(obj.fget, strict=False)
        if hasattr(obj, "__wrapped__"):
            return cache.has(getattr(obj, "__wrapped__"))
        return False

    @overload
    @staticmethod
    def get(obj: WithCache[_T], /, *, strict: bool = ...) -> cache[_T]: ...
    @overload
    @staticmethod
    def get(obj: object, /, *, strict: Literal[True] = ...) -> cache[_T]: ...
    @overload
    @staticmethod
    def get(obj: object, /, *, strict: Literal[False]) -> cache[_T] | None: ...
    @staticmethod
    def get(obj: WithCache[_T] | object, /, *, strict: bool = True) -> cache[_T] | None:
        """Return `obj`'s cache (or `raise ValueError(...)` if `strict`, else `return None`)."""
        if cache[_T].has(obj, strict=True):
            return obj.__cache__
        if isinstance(obj, property):
            return cache.get(obj.fget, strict=strict)  # type: ignore
        if hasattr(obj, "__wrapped__"):
            return cache.get(getattr(obj, "__wrapped__"), strict=strict)
        if strict:
            raise ValueError(f"{obj!r} has no cache.")
        return None

    @overload
    def read(self: cache[_T] | WithCache[_T] | object, /, *, strict: Literal[True]) -> _T: ...
    @overload
    def read(self: cache[_T] | WithCache[_T] | object, /, *, strict: Literal[False] = ...) -> _T | None: ...
    def read(self: cache[_T] | WithCache[_T] | object, /, *, strict: bool = False) -> _T | None:
        """Read `self`'s cache."""
        if cache.is_(self):
            if strict and self._ is None:
                raise ValueError(f"Empty cache: {self!r}")
            return self._
        if cache.has(self):
            return cache.get(self).read()
        if strict:
            raise ValueError(f"{self!r} has no cache.")
        return None

    def clear(self: cache[_T] | WithCache[_T] | object, /) -> None:
        """Clar `obj`'s cache (if any)."""
        if cache.is_(self):
            self._ = None
        elif cache.has(self):
            cache.get(self).clear()

    def set(self, obj: _X, /) -> _X:
        """Decorator: set `self` as `obj`'s cache."""
        setattr(obj, "__cache__", self)
        return obj

    @overload   # type: ignore[misc]
    @staticmethod
    def call(f: _F, /) -> _F: ...
    @overload
    def call(self: cache[CallCacheData], f: _F, /) -> _F: ...
    def call(self: cache[CallCacheData] | _F, f: _F | None = None, /) -> _F:
        """Cache `f`'s calls (and exceptions!)."""
        if f is None:
            this = cache[CallCacheData]({})
            func = cast(_F, self)
        else:
            this = cast(cache[CallCacheData], self)
            func = f
        @wraps(func)
        @this.set
        def inner(*args: object, **kwargs: object) -> object:
            frozen = (args, frozenset(kwargs.items()))
            cached = this.read()
            if cached is None:
                this._ = cached = {}
            if frozen in cached:
                result, failed = cached[frozen]
                if failed:
                    raise cast(BaseException, result)
                return result
            try:
                result = func(*args, **kwargs)
            except BaseException as result:
                cached[frozen] = (result, True)
                raise
            else:
                cached[frozen] = (result, False)
                return result
        return cast(_F, inner)


CallCacheData = dict[
    tuple[
        tuple[object, ...],            # *args
        frozenset[tuple[str, object]], # **kwargs
    ],
    tuple[
        object,                        # return / exception
        bool,                          # did it raise?
    ]
]


__all__ = ["WithCache", "cache", "CallCacheData"]
