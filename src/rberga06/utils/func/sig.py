#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mypy: ignore-errors
"""Useful decorators for modifying function signatures."""
from __future__ import annotations
from contextlib import suppress
from inspect import Parameter, Signature, signature
from typing import Concatenate as Concat, overload
from typing import Any, Callable as Fn, Generic, ParamSpec, Self, TypeVar, cast, final


_F = TypeVar("_F", bound=Fn[..., Any])
_P = ParamSpec("_P")
_R = TypeVar("_R")
_T = TypeVar("_T")
_T1 = TypeVar("_T1")
_T2 = TypeVar("_T2")
_T3 = TypeVar("_T3")


@final
class SigHelper(Generic[_F]):
    """Signature editing helper."""
    __slots__ = ("_sig", "_runtime")
    _sig: Signature
    _runtime: bool

    def __init__(self, sig: Signature, runtime: bool = True):
        self._sig = sig
        self._runtime = runtime

    def __call__(self, func: Fn[..., Any]) -> _F:
        """Apply this signature to `func`."""
        if self._runtime:
            with suppress(AttributeError):
                object.__setattr__(func, "__signature__", sig)
        return cast(_F, func)

    @property
    def typing(self) -> Self:
        """Only use this for typing."""
        return SigHelper(self._sig, False)

    @property
    def runtime(self) -> Self:
        """Also use this on runtime."""
        return SigHelper(self._sig, True)

    def setruntime(self, runtime: bool, /) -> Self:
        """Set if this should be used on runtime."""
        return SigHelper(self._sig, runtime)

    @overload
    def prepend(self: SigHelper[Fn[_P, _R]], param: type[_T1], /) -> SigHelper[Fn[Concat[_T1, _P], _R]]: ...
    @overload
    def prepend(self: SigHelper[Fn[_P, _R]], *params: *tuple[type[_T1], type[_T2]]) -> SigHelper[Fn[Concat[_T1, _T2, _P], _R]]: ...
    @overload
    def prepend(self: SigHelper[Fn[_P, _R]], *params: *tuple[type[_T1], type[_T2], type[_T3]]) -> SigHelper[Fn[Concat[_T1, _T2, _T3, _P], _R]]: ...
    def prepend(self: SigHelper[Fn[_P, _R]], *params: type[Any]) -> SigHelper[Fn[..., _R]]:
        """Prepend *`params` to the function's signature."""
        sig = self._sig
        if self._runtime:
            ns = [int(s) for n in sig.parameters.keys() if n.startswith("__") and (s := n.removeprefix("__")).isdigit()]
            n0 = (max(ns) + 1) if ns else 0
            sig.replace(parameters=[
                *[Parameter(
                    f"__{n0 + i}",
                    Parameter.POSITIONAL_ONLY, annotation=p,
                ) for i, p in enumerate(params)],
                *sig.parameters.values()
            ])
        return SigHelper[Fn[Concat[_T, _P], _R]](sig, self._runtime)

    def rmleading(self: SigHelper[Fn[Concat[Any, _P], _R]], /) -> SigHelper[Fn[_P, _R]]:
        sig = self._sig
        if self._runtime:
            sig.replace(parameters=[*sig.parameters.values()][1:])
        return SigHelper[Fn[_P, _R]](sig, self._runtime)

    def chleading(self: SigHelper[Fn[Concat[Any, _P], _R]], param: type[_T], /) -> SigHelper[Fn[Concat[_T, _P], _R]]:
        return self.rmleading().prepend(param)


@final
class _SigHelperFactory:
    def __getitem__(self, f: _F) -> SigHelper[_F]:
        return SigHelper[_F](signature(f))

sig = _SigHelperFactory()


__all__ = [
    "sig",
]
