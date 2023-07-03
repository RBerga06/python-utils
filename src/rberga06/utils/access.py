#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mypy: ignore-errors
"""Access specifiers for Python. Mostly intended for documentation."""
from contextlib import AbstractContextManager
from collections.abc import Callable
import inspect
from types import TracebackType
from typing import Any, Generic, Iterable, Self, final, overload
from typing_extensions import TypeVar, TypeVarTuple, override


_X = TypeVar("_X", default=Any)
_T = TypeVar("_T")
_TT = TypeVarTuple("_TT")


class _access(Generic[_X]):
    _depth: int
    _ns: dict[str, Any] | None

    def __init__(self, ns: dict[str, Any] | None = None, /) -> None:
        self._depth = 0
        self._ns = ns

    @property
    def _inc_depth(self, /) -> Self:
        """Return a copy of `self` with `self._depth` incremented by 1."""
        other = type(self)(self._ns)
        other._depth = self._depth + 1
        return other

    @property
    def ns(self, /) -> dict[str, _X]:
        """The attached namespace."""
        ns = self._ns
        if ns is not None:
            return ns
        frame = inspect.stack()[self._depth + 1].frame
        ns = frame.f_locals
        del frame
        return ns

    @property
    def all(self, /) -> list[str]:
        """The attached :py:obj:`__all__`."""
        ns: dict[str, Any]  = self._inc_depth.ns
        _all: Iterable[str] = ns.get("__all__", [])
        all = _all if isinstance(_all, list) else list(_all)
        ns["__all__"] = all
        return all


@final
class access(_access[_X]):
    """
    Access specifiers.

    :param ns: The namespace in which to operate. Defaults to the caller's `locals()`.

    :Example:

    >>> locals().clear()
    >>> from rberga06.utils.access import *
    >>> __all__
    Traceback (most recent call last):
    ...
    NameError: name '__all__' is not defined
    >>> a = access()
    >>> @a.public
    ... def _foo(x: int) -> int:
    ...     return x
    ...
    >>> @a.private
    ... def priv(y: str) -> str:
    ...     return y
    ...
    >>> with a.public:
    ...     _x: str = "public"
    ...
    >>> with a.private:
    ...     y: int = 42
    ...
    >>> __all__
    ['_foo', '_x']
    >>> __all__ is a.all
    True
    """

    @property
    def public(self) -> "public[_X]":
        """Mark something public"""
        return self._specialized(public[_X])

    @property
    def private(self) -> "private[_X]":
        """Mark something private"""
        return self._specialized(private[_X])

    def _specialized(self, cls: "type[_AS]") -> "_AS":
        obj = cls(self._ns)
        obj._depth = self._depth
        return obj


class _access_specialized(_access[_X], AbstractContextManager[dict[str, _X]]):
    @classmethod
    def _ns_special_key(cls, /) -> str:
        return f"<brs.utils.access:{cls.__name__}:namespace-backup-keys>"

    @override
    def __enter__(self, /) -> dict[str, Any]:
        ns: dict[str, Any] = self._inc_depth.ns
        ns[type(self)._ns_special_key()] = frozenset(ns.keys())
        return ns

    @override
    def __exit__(self, typ: type[BaseException] | None, val: BaseException | None, tb: TracebackType | None, /) -> bool | None:
        special_key = type(self)._ns_special_key()
        # Call `self.__call__(...)` on the added or removed keys
        ns: dict[str, Any] = self._inc_depth.ns
        new = set(ns.keys())
        old = set(ns.pop(special_key, ns))
        for key in (new - old) - {special_key}:
            self._inc_depth(key)
        # Do not handle any exception
        return super().__exit__(typ, val, tb)

    @overload
    def _operate(self, cb: Callable[[list[str], str], None], obj: _T, /) -> _T: ...
    @overload
    def _operate(self, cb: Callable[[list[str], str], None], *objs: *_TT) -> tuple[*_TT]: ...
    def _operate(self, cb: Callable[[list[str], str], None], *objs: *tuple[_T | Any, ...]) -> _T | tuple[Any, ...]:
        all = self._inc_depth.all
        for obj in objs:
            name = getattr(obj, "__name__", obj if isinstance(obj, str) else None)
            if name is not None:
                cb(all, name)
        return objs[0] if len(objs) == 1 else objs

    @overload
    def __call__(self, obj: _T, /) -> _T: ...
    @overload
    def __call__(self, *objs: *_TT) -> tuple[*_TT]: ...
    def __call__(self, *objs: *tuple[_T | Any, ...]) -> _T | tuple[Any, ...]:
        raise NotImplementedError(f"{type(self).__module__}:{type(self).__qualname__}.__call__(...)")


_AS = TypeVar("_AS", bound=_access_specialized)


@final
class public(_access_specialized[_X]):
    """
    Mark something public.

    :param ns: The namespace in which to operate. Defaults to the caller's `locals()`.

    :Example:

    >>> locals().clear()
    >>> from rberga06.utils.access import *
    >>> @public()
    ... def _foo(x: int) -> int:
    ...     return x
    ...
    >>> with public():
    ...     x: str = "public"
    ...     _y: str = "also public"
    ...
    >>> set(__all__)
    {'_foo', 'x', '_y'}
    >>> __all__ is public().all
    True
    """
    @overload
    def __call__(self, obj: _T, /) -> _T: ...
    @overload
    def __call__(self, *objs: *_TT) -> tuple[*_TT]: ...
    def __call__(self, *objs: *tuple[_T | Any, ...]) -> _T | tuple[Any, ...]:  # type: ignore
        return self._inc_depth._operate(lambda all, x: (None if x in all else all.append(x)), *objs)


@final
class private(_access_specialized[_X]):
    """
    Mark something private.

    :param ns: The namespace in which to operate. Defaults to the caller's `locals()`.

    :Example:

    >>> locals().clear()
    >>> from rberga06.utils.access import *
    >>> @private()
    ... def foo(x: int) -> int:
    ...     return x
    ...
    >>> with private():
    ...     _x: str = "private"
    ...     y: str = "also private"
    ...
    >>> __all__
    []
    >>> __all__ is private().all
    True
    """
    @overload
    def __call__(self, obj: _T, /) -> _T: ...
    @overload
    def __call__(self, *objs: *_TT) -> tuple[*_TT]: ...
    def __call__(self, *objs: *tuple[_T | Any, ...]) -> _T | tuple[Any, ...]:  # type: ignore
        return self._inc_depth._operate(lambda all, x: (all.remove(x) if x in all else None), *objs)


__all__ = ["access", "public", "private"]
