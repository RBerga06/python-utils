#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mypy: ignore-errors
"""Decorators."""
# Inspired by the `wrapt` library (but better)
from contextlib import suppress
from inspect import signature
from typing import Any, Callable as Fn, ClassVar, Generic, cast, final, overload
from typing_extensions import ParamSpec, Protocol, TypeVar, override

from ..types import Mut
from .wrap import wraps

# Type aliases
AnyFn = Fn[..., Any]
# TypeVars
_P = ParamSpec("_P")
_R = TypeVar("_R", infer_variance=True)
_T = TypeVar("_T", infer_variance=True)
_X = TypeVar("_X", infer_variance=True, default=dict[str, Any])
_F = TypeVar("_F", infer_variance=True, bound=AnyFn, default=AnyFn)
# Type aliases
AnyDecorator = Fn[[_T], _T]
AnyDecoratorFactory = Fn[_P, AnyDecorator[_F]]
AnyDataFactory = Fn[[AnyFn], _X] | Fn[[], _X]


WRAPPER_ATTRS = {
    "__module__", "__name__", "__qualname__", "__doc__",
}


### CLASS API ###

class DecoratorBase(Protocol):
    """Define a decorator."""

    def decorate(self, f: _F, /) -> _F:
        """Decorate function `f`."""
        ...

    def __call__(self, f: _F, /) -> _F:
        """Decorate function `f`."""
        return self.decorate(f)


class Decorator(DecoratorBase, Protocol):
    """Define a decorator."""

    @overload
    def spec(__self__, __decorated__: Fn[_P, _R], *args: _P.args, **kwargs: _P.kwargs) -> _R: ...
    @overload
    def spec(__self__, __decorated__: AnyFn, *args: Any, **kwargs: Any) -> Any: ...
    def spec(__self__, __decorated__: AnyFn, *args: Any, **kwargs: Any) -> Any:
        """Decorator behaviour specification."""
        ...

    @override
    def decorate(self, f: _F, /) -> _F:
        """Decorate function `f`."""
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return self.spec(f, *args, **kwargs)
        return wrapper


class DecoratorWithAttr(Decorator, Protocol[_X]):
    """Define a decorator that manages an attribute on a function."""
    ATTR: ClassVar[str]
    data: _X

    def __init__(self, data: _X, /) -> None:
        self.data = data

    @override
    def decorate(self, f: _F, /) -> _F:
        f = super().decorate(f)
        setattr(f, type(self).ATTR, self.data)
        return f

    @classmethod
    def get(cls, f: Fn[..., Any], /) -> _X:
        return getattr(f, cls.ATTR)


### FUNCTIONAL API ###


class DecoratorSpec(Protocol):
    """A ordinary decorator."""
    @overload
    def __call__(self, __decorated__: Fn[_P, _R], *args: _P.args, **kwargs: _P.kwargs) -> _R: ...
    @overload
    def __call__(self, __decorated__: Fn[..., Any], *args: Any, **kwargs: Any) -> Any: ...


class DecoratorSpecWithData(Protocol[_X]):
    """A decorator with data associated to each decorated function."""
    @overload
    def __call__(self, __data__: _X, __decorated__: Fn[_P, _R], *args: _P.args, **kwargs: _P.kwargs) -> _R: ...  # type: ignore
    @overload
    def __call__(self, __data__: _X, __decorated__: Fn[..., Any], *args: Any, **kwargs: Any) -> Any: ...


def _mkdata(factory: AnyDataFactory[_X], func: Fn[..., Any], /) -> _X:
    if signature(factory).parameters:
        return cast(Fn[[Fn[..., Any]], _X], factory)(func)
    return cast(Fn[[], _X], factory)()


@final
class _decorator(DecoratorBase):
    """A `Decorator` subclass for the functional API."""
    __slots__ = ("_spec",)
    _spec: DecoratorSpec

    def __init__(self, spec: DecoratorSpec, /) -> None:
        self._spec = spec

    @override
    def decorate(self, f: _F, /) -> _F:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return self._spec(f, *args, **kwargs)
        return wrapper


@final
class _decorator_with_data(DecoratorBase, Generic[_X]):
    """A `Decorator` subclass for the functional API."""
    __slots__ = ("_spec", "_data")
    _spec: DecoratorSpecWithData[_X]
    _data: AnyDataFactory[_X]

    def __init__(self, spec: DecoratorSpecWithData[_X], data: AnyDataFactory[_X], /) -> None:
        self._spec = spec
        self._data = data

    @override
    def decorate(self, f: _F, /) -> _F:
        data = _mkdata(self._data, f)
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return self._spec(data, f, *args, **kwargs)
        return wrapper


@overload
def decorator(*, data: None = ...) -> Fn[[DecoratorSpec], _decorator]: ...
@overload
def decorator(*, data: AnyDataFactory[_X]) -> Fn[[DecoratorSpecWithData[_X]], _decorator_with_data[_X]]: ...
def decorator(*, data: AnyDataFactory[_X] | None = None) -> Fn[[DecoratorSpec], _decorator] | Fn[[DecoratorSpecWithData[_X]], _decorator_with_data[_X]]:
    """Create a decorator."""
    if data is None:
        return _decorator
    def factory(spec: DecoratorSpecWithData[_X], /) -> _decorator_with_data[_X]:
        return _decorator_with_data(spec, data)
    return factory


### Useful decorators ###

def withattrs(**attrs: Any) -> AnyDecorator[_T]:
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


class count_calls(DecoratorWithAttr[Mut[int]]):
    """A decorator that counts the calls of a function."""
    ATTR: ClassVar[str] = "calls_count"

    def __init__(self, counter: Mut[int] | None = None, /) -> None:
        super().__init__(Mut(0) if counter is None else counter)

    @override
    def spec(__self__, __decorated__: AnyFn, *args: Any, **kwargs: Any) -> Any:
        __self__.data._ += 1
        return __decorated__(*args, **kwargs)
