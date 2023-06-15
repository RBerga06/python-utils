#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mypy: ignore-errors
"""Decorators."""
# Inspired by the `wrapt` library (but better)
from contextlib import suppress
from inspect import signature
from typing import Any, Callable as Fn, cast, overload
from typing_extensions import ParamSpec, Protocol, TypeVar
from ..types import Mut
from .wrap import wraps

# TypeVars
_P = ParamSpec("_P")
_R = TypeVar("_R", infer_variance=True)
_T = TypeVar("_T", infer_variance=True)
_X = TypeVar("_X", infer_variance=True, default=dict[str, Any])
_F = TypeVar("_F", infer_variance=True, bound=Fn[..., Any], default=Fn[..., Any])
_G = TypeVar("_G", infer_variance=True, bound=Fn[..., Any], default=_F)  # In theory, `bound=_F`
# Type aliases
Decorator = Fn[[_T], _T]
DecoratorFactory = Fn[_P, Decorator[_F]]
DataFactory = Fn[[_F], _X] | Fn[[], _X]


WRAPPER_ATTRS = {
    "__module__", "__name__", "__qualname__", "__doc__",
}


class DecoratorSpec(Protocol[_F]):
    """A ordinary decorator."""
    @overload
    def __call__(
        self: "DecoratorSpec[Fn[_P, _R]]",
        __decorated__: Fn[_P, _R],
        *args: _P.args, **kwargs: _P.kwargs,
    ) -> _R: ...
    @overload
    def __call__(
        self,
        __decorated__: _F,
        *args: Any, **kwargs: Any,
    ) -> Any: ...


class DecoratorSpecWithData(Protocol[_F, _X]):
    """A decorator with data associated to each decorated function."""
    @overload
    def __call__(
        self: "DecoratorSpecWithData[Fn[_P, _R], _X]",
        __data__: _X,
        __decorated__: Fn[_P, _R],
        *args: _P.args, **kwargs: _P.kwargs,
    ) -> _R: ...
    @overload
    def __call__(
        self,
        __data__: _X,
        __decorated__: _F,
        *args: Any, **kwargs: Any,
    ) -> Any: ...


def _mkdata(factory: DataFactory[_F, _X], func: _F, /) -> _X:
    if signature(factory).parameters:
        return cast(Fn[[_F], _X], factory)(func)
    return cast(Fn[[], _X], factory)()


@overload
def decorator(*, data: None = ...) -> DecoratorFactory[[DecoratorSpec[_F]], _G]: ...
@overload
def decorator(*, data: DataFactory[_F, _X]) -> DecoratorFactory[[DecoratorSpecWithData[_F, _X]], _G]: ...
def decorator(*, data: DataFactory[_F, _X] | None = None) -> DecoratorFactory[[DecoratorSpecWithData[_F, _X]], _G] | DecoratorFactory[[DecoratorSpec[_F]], _G]:
    """Create a decorator."""
    def factory(decorator: DecoratorSpecWithData[_F, _X] | DecoratorSpec[_F], /) -> Decorator[_G]:
        @wraps(decorator, silent=True, signature=False)
        def inner(f: _G) -> _G:  # type: ignore
            if data is not None:
                _data = _mkdata(data, cast(_F, f))
            @wraps(f)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                if data is None:
                    return cast(DecoratorSpec[_F], decorator)(cast(_F, f), *args, **kwargs)
                return cast(DecoratorSpecWithData[_F, _X], decorator)(_data, cast(_F, f), *args, **kwargs)
            return wrapper
        return inner
    return factory


### Useful decorators ###

def withattrs(**attrs: Any) -> Decorator[_T]:
    """Set the given attributes on the decorated object."""
    def withattrs(obj: _T) -> _T:
        for attr, value in attrs:
            with suppress(AttributeError):
                object.__setattr__(obj, attr, value)
        return obj
    return withattrs

@decorator()
def pass_through(__decorated__: _F, *args: Any, **kwargs: Any) -> Any:
    """A decorator that doesn't do anything at all."""
    return __decorated__(*args, **kwargs)


def count_calls(counter: Mut[int]) -> Decorator[_F]:
    """A decorator that counts the calls of a function. No attribute is set on the decorated function."""
    @decorator()
    def count_calls(__decorated__: _F, *args: Any, **kwargs: Any) -> Any:
        counter._ += 1
        return __decorated__(*args, **kwargs)
    return count_calls
