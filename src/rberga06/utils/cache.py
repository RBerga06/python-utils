#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mypy: ignore-errors
"""Useful caching utilities."""
from __future__ import annotations
import enum
from functools import wraps
import inspect
from typing import Any, Callable, Generic, Hashable, Literal, Protocol, Self, TypeGuard, cast, overload
from typing_extensions import TypeVar, override


class _Sentinels(enum.Enum):
    DEFAULT = enum.auto()
DEFAULT = _Sentinels.DEFAULT


_X = TypeVar("_X")
_T = TypeVar("_T", infer_variance=True)
_U = TypeVar("_U", infer_variance=True, default=_T)



class Cache(Generic[_T, _U]):
    """A cache."""
    __slots__ = ("_",)

    _: _T | _U
    """The value stored in the cache."""

    @classmethod
    def default(cls: type[Cache[_T, _U]]) -> _U:
        """The default value (empty cache)."""
        return cast(_U, None)

    def __init__(self, _: _T | _U | Literal[DEFAULT] = DEFAULT) -> None:
        if _ is DEFAULT:
            self._ = self.default()
        else:
            self._ = _

    @override  # from builtins.object
    def __repr__(self) -> str:
        return f"<Cache: {self._!r}>"

    def __bool__(self) -> bool:
        return not self.is_empty

    @property
    def is_empty(self, /) -> bool:
        return self.default() == self._

    @classmethod
    def has(cls, obj: object, /) -> TypeGuard[WithCache[Self]]:
        """Check if `obj` has a cache of this type."""
        return isinstance(getattr(obj, "__cache__", None), cls)

    @overload
    @classmethod
    def get(cls, obj: object, /, *, strict: Literal[True] = ...) -> Self: ...
    @overload
    @classmethod
    def get(cls, obj: object, /, *, strict: Literal[False]) -> Self | None: ...
    @classmethod
    def get(cls, obj: object, /, *, strict: bool = True) -> Self | None:
        """Return `obj`'s cache (or `raise ValueError(...)` if `strict`, else `return None`)."""
        if isinstance(obj, cls):
            return obj
        if cls.has(obj):
            return obj.__cache__
        if strict:
            raise ValueError(f"{obj!r} has no cache.")
        return None

    @overload
    def read(self, /, *, strict: Literal[True] = ...) -> _T: ...
    @overload
    def read(self, /, *, strict: Literal[False]) -> _T | _U: ...
    def read(self, /, *, strict: bool = False) -> _T | _U:
        """Read `self`'s cache."""
        if strict and self.is_empty:
            raise ValueError(f"Empty cache: {self!r}")
        return self._

    def clear(self, /) -> None:
        """Clar `obj`'s cache (if any)."""
        self._ = self.default()

    def set(self, obj: _X, /) -> _X:
        """Decorator: set `self` as `obj`'s cache."""
        setattr(obj, "__cache__", self)
        return obj


_C = TypeVar("_C", infer_variance=True, bound=Cache[Any, Any])
_F = TypeVar("_F", bound=Callable[..., object])


class WithCache(Protocol[_C]):
    __cache__: _C


def clear(obj: object, /, *, cls: type[Cache[Any, Any]] = Cache[object, None]) -> None:
    c = cls.get(obj, strict=False)
    if c is not None:
        c.clear()


_K = TypeVar(
    "_K", infer_variance=True, bound=Hashable, default=tuple[
        tuple[object, ...],             # *args
        frozenset[tuple[str, object]],  # **kwargs
    ]
)


class FCache(Cache[dict[_K, tuple[object, bool]], dict[_K, tuple[object, bool]]]):
    """Function cache."""

    @override  # from Cache
    @classmethod
    def default(cls) -> dict[_K, tuple[object, bool]]:
        return {}

    def _freeze_params(self, args: tuple[object, ...], kwargs: dict[str, object], /) -> _K:
        """Freeze call parameters."""
        return cast(_K, (args, frozenset(kwargs.items())))

    def func(self, f: _F, /) -> _F:
        """Cache `f`'s calls (and exceptions!)."""
        @wraps(f)
        @self.set
        def inner(*args: object, **kwargs: object) -> object:
            frozen = self._freeze_params(args, kwargs)
            cached = self.read()
            if frozen in cached:
                result, failed = cached[frozen]
                if failed:
                    raise cast(BaseException, result)
                return result
            try:
                result = f(*args, **kwargs)
            except BaseException as result:
                cached[frozen] = (result, True)
                raise
            else:
                cached[frozen] = (result, False)
                return result
        return cast(_F, inner)


class FCacheNoParams(FCache[None]):
    """A function cache that ignores `*args` and `**kwargs`."""

    @override  # from FCache
    def _freeze_params(self, args: tuple[object, ...], kwargs: dict[str, object], /) -> None:
        return None


class FCacheKwOnly(FCache[frozenset[tuple[str, object]]]):
    """A function cache that ignores `*args`."""

    @override  # from FCache
    def _freeze_params(self, args: tuple[object, ...], kwargs: dict[str, object], /) -> frozenset[tuple[str, object]]:
        return frozenset(kwargs.items())


class FCacheArgOnly(FCache[tuple[object, ...]]):
    """A function cache that ignores `**kwargs`."""

    @override  # from FCache
    def _freeze_params(self, args: tuple[object, ...], kwargs: dict[str, object], /) -> tuple[object, ...]:
        return args


class FCacheOneArg(FCache[object]):
    """A function cache that only checks the first positional argument."""

    @override  # from FCache
    def _freeze_params(self, args: tuple[object, ...], kwargs: dict[str, object], /) -> object:
        return args[0]


def _optimal_fcache(f: Callable[..., Any], /) -> type[FCache[Any]]:
    """Get the optimal `FCache` type for the given function, based on its signature."""
    params = [p.kind for p in inspect.signature(f).parameters.values()]
    if not params:
        return FCacheNoParams
    if inspect.Parameter.POSITIONAL_OR_KEYWORD in params:
        # It's not safe to exclude *args or **kwargs
        return FCache[Any]
    has_var_pos = inspect.Parameter.VAR_POSITIONAL in params
    if (inspect.Parameter.KEYWORD_ONLY in params) or (inspect.Parameter.VAR_KEYWORD in params):
        # We need to preserve **kwargs
        if has_var_pos or (inspect.Parameter.POSITIONAL_ONLY in params):
            # We also need to preserve *args
            return FCache[Any]
        # No need to preserve *args
        return FCacheKwOnly
    # No need to preserve **kwargs
    if (len(params) == 1) and not has_var_pos:
        # There is only one arg
        return FCacheOneArg
    return FCacheArgOnly


@overload
def func(f: None = ..., /, *, cls: type[FCache[Any]] | None = ...) -> Callable[[_F], _F]: ...
@overload
def func(f: _F, /) -> _F: ...
def func(f: _F | None = None, /, *, cls: type[FCache[Any]] | None = None) -> _F | Callable[[_F], _F]:
    if f is None:
        if cls is None:
            return func
        return cls().func
    if cls is None:
        cls = _optimal_fcache(f)
    return cls().func(f)



__all__ = [
    "DEFAULT",
    "WithCache",
    "Cache",
    "clear",
    "func",
    "FCache",
    "FCacheKwOnly",
    "FCacheArgOnly",
    "FCacheOneArg",
    "FCacheNoParams",
]
