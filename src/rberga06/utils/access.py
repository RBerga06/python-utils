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


class access(Generic[_X]):
    """Access specifiers."""

    _depth: int
    _ns: dict[str, Any] | None
    _pub: list[str]
    _priv: list[str]

    def __init__(self, ns: dict[str, Any] | None = None, /) -> None:
        self._depth = 0
        self._ns = ns
        self._pub = []
        self._priv = []

    @property
    def _inc_depth(self, /) -> Self:
        """Return a copy of `self` with `self._depth` incremented by 1."""
        other = type(self)(self._ns)
        other._depth = self._depth + 1
        return other

    @property
    def ns(self, /) -> dict[str, _X]:
        ns = self._ns
        if ns is not None:
            return ns
        frame = inspect.stack()[self._depth + 1].frame
        ns = frame.f_locals
        del frame
        return ns

    @property
    def all(self, /) -> list[str]:
        ns: dict[str, Any]  = self._inc_depth.ns
        _all: Iterable[str] = ns.get("__all__", [])
        all = _all if isinstance(_all, list) else list(_all)
        ns["__all__"] = all
        return all

    @overload
    def public(self, obj: _T, /) -> _T: ...
    @overload
    def public(self, *objs: *_TT) -> tuple[*_TT]: ...
    def public(self, *objs: *tuple[_T | Any, ...]) -> _T | tuple[Any, ...]:
        return self._inc_depth._operate(lambda all, x: (None if x in all else all.append(x)), *objs)

    @overload
    def private(self, obj: _T, /) -> _T: ...
    @overload
    def private(self, *objs: *_TT) -> tuple[*_TT]: ...
    def private(self, *objs: *tuple[_T | Any, ...]) -> _T | tuple[Any, ...]:
        return self._inc_depth._operate(lambda all, x: (all.remove(x) if x in all else None), *objs)

    @overload
    def _operate(self, cb: Callable[[list[str], str], None], obj: _T, /) -> _T: ...
    @overload
    def _operate(self, cb: Callable[[list[str], str], None], *objs: *_TT) -> tuple[*_TT]: ...
    def _operate(self, cb: Callable[[list[str], str], None], *objs: *tuple[_T | Any, ...]) -> _T | tuple[Any, ...]:
        ns  = self._inc_depth.ns
        all = self._inc_depth.all
        for obj in objs:
            name = getattr(obj, "__name__", obj if isinstance(obj, str) else None)
            if name is not None and name in ns:
                cb(all, name)
        return objs[0] if len(objs) == 1 else objs


class _access_specialized(access[_X], AbstractContextManager[dict[str, _X]]):
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
        # Call `self.__call__(...)` on the added or removed keys
        ns: dict[str, Any] = self._inc_depth.ns
        new = set(ns.keys())
        old = set(ns.pop(type(self)._ns_special_key(), ns))
        for key in new - old:
            self._inc_depth(key)
        # Do not handle any exception
        return super().__exit__(typ, val, tb)

    @overload
    def __call__(self, obj: _T, /) -> _T: ...
    @overload
    def __call__(self, *objs: *_TT) -> tuple[*_TT]: ...
    def __call__(self, *objs: *tuple[_T | Any, ...]) -> _T | tuple[Any, ...]:
        raise NotImplementedError(f"{type(self).__module__}:{type(self).__qualname__}.__call__(...)")


@final
class public(_access_specialized[_X]):
    @overload
    def __call__(self, obj: _T, /) -> _T: ...
    @overload
    def __call__(self, *objs: *_TT) -> tuple[*_TT]: ...
    def __call__(self, *objs: *tuple[_T | Any, ...]) -> _T | tuple[Any, ...]:  # type: ignore
        return self._inc_depth.public(*objs)


@final
class private(_access_specialized[_X]):
    @overload
    def __call__(self, obj: _T, /) -> _T: ...
    @overload
    def __call__(self, *objs: *_TT) -> tuple[*_TT]: ...
    def __call__(self, *objs: *tuple[_T | Any, ...]) -> _T | tuple[Any, ...]:  # type: ignore
        return self._inc_depth.private(*objs)


public(globals())(
    access, public, private
)
