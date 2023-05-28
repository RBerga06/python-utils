#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mypy: ignore-errors
"""Function wrappers."""
# Inspired by the wrapt library
from contextlib import suppress
from inspect import signature
from typing import Callable as Fn, Literal, ParamSpec, Protocol, overload
from typing import Any, cast
from typing_extensions import TypeVar
from ..types import Mut
from .sig import sig

# TypeVars
_F = TypeVar("_F", infer_variance=True, bound=Fn[..., Any], default=Fn[..., Any])
_G = TypeVar("_G", infer_variance=True, bound=Fn[..., Any], default=Fn[..., Any])
_P = ParamSpec("_P")
_R = TypeVar("_R")
_X = TypeVar("_X", infer_variance=True, default=dict[str, Any])
# Type aliases
Decorator = Fn[[_F], _F]
DecoratorFactory = Fn[_P, Decorator[_F]]

WRAPPER_ATTRS = {
    "__module__", "__name__", "__qualname__", "__doc__",
}


def withattrs(**attrs: Any) -> Decorator[_F]:
    def withattrs(f: _F) -> _F:
        for attr, value in attrs:
            with suppress(AttributeError):
                object.__setattr__(f, attr, value)
        return f
    return withattrs


@overload
def update_wrapper(
    wrapper: _F,
    wrapped: Fn[..., Any],
    /, *,
    silent: bool = False,
    signature: Literal[False],
    assigned: set[str] = WRAPPER_ATTRS,
) -> _F: ...
@overload
def update_wrapper(
    wrapper: Fn[..., Any],
    wrapped: _G,
    /, *,
    silent: bool = False,
    signature: Literal[True] = ...,
    assigned: set[str] = WRAPPER_ATTRS,
) -> _G: ...
@overload
def update_wrapper(
    wrapper: _F,
    wrapped: _G,
    /, *,
    silent: bool = False,
    signature: bool = ...,
    assigned: set[str] = WRAPPER_ATTRS,
) -> _F | _G: ...
def update_wrapper(
    wrapper: _F,
    wrapped: _G,
    /, *,
    silent: bool = False,
    signature: bool = True,
    assigned: set[str] = WRAPPER_ATTRS,
) -> _F | _G:
    """Like `functools.update_wrapper(...)`"""
    if signature:
        assigned |= {"__annotations__"}  # __signature__ is not necessary
    for attr in assigned:
        with suppress(AttributeError):
            object.__setattr__(wrapper, attr, object.__getattribute__(wrapped, attr))
    with suppress(AttributeError):
        wrapper_dict: dict[str, Any] = object.__getattribute__(wrapper, "__dict__")
        wrapped_dict: dict[str, Any] = object.__getattribute__(wrapped, "__dict__")
        wrapper_dict.update(wrapped_dict)
    if not silent:
        with suppress(AttributeError):
            object.__setattr__(wrapper, "__wrapped__", wrapped)
    if signature:
        # if it's not silent, then __wrapped__ is set and inspect.signature(...) is able to retrieve the original signature.
        return sig[wrapped].setruntime(silent)(wrapper)
    return wrapper


@overload
def wraps(
    wrapped: Fn[..., Any], /, *,
    silent: bool = False,
    signature: Literal[False],
    assigned: set[str] = WRAPPER_ATTRS,
) -> Fn[[_G], _G]: ...
@overload
def wraps(
    wrapped: _F, /, *,
    silent: bool = False,
    signature: Literal[True] = ...,
    assigned: set[str] = WRAPPER_ATTRS,
) -> Fn[[Fn[..., Any]], _F]: ...
def wraps(
    wrapped: _F, /, *,
    silent: bool = False,
    signature: bool = True,
    assigned: set[str] = WRAPPER_ATTRS,
) -> Fn[[_G], _F | _G]:
    """Like `functools.wraps(...)`, but typechecks."""
    def inner(wrapper: _G, /) -> _F | _G:
        return update_wrapper(
            wrapper, wrapped,
            silent=silent,
            signature=signature,
            assigned=assigned,
        )
    return inner



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
        self: "DecoratorSpec[Fn[_P, _R]]",
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


DataFactory = Fn[[_F], _X] | Fn[[], _X]  # Data factory


def _mkdata(factory: DataFactory[_F, _X], func: _F, /) -> _X:
    if signature(factory).parameters:
        return cast(Fn[[_F], _X], factory)(func)
    return cast(Fn[[], _X], factory)()


@overload
def decorator(*, data: DataFactory[_F, _X]) -> DecoratorFactory[[DecoratorSpecWithData[_F, _X]], _F]: ...
@overload
def decorator(*, data: None = ...) -> DecoratorFactory[[DecoratorSpec[_F]], _F]: ...
def decorator(*, data: DataFactory[_F, _X] | None = None) -> DecoratorFactory[[DecoratorSpecWithData[_F, _X]], _F] | DecoratorFactory[[DecoratorSpec[_F]], _F]:
    """Create a decorator."""
    def factory(decorator: DecoratorSpecWithData[_F, _X] | DecoratorSpec[_F], /) -> Decorator[_F]:
        @wraps(decorator, silent=True, signature=False)
        def inner(f: _F) -> _F:
            if data is not None:
                _data = _mkdata(data, f)
            @wraps(f)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                if data is None:
                    return cast(DecoratorSpec[_F], decorator)(f, *args, **kwargs)
                return cast(DecoratorSpecWithData[_F, _X], decorator)(_data, f, *args, **kwargs)
            return wrapper
        return inner
    return factory


@decorator()
def pass_through(__decorated__: _F, *args: Any, **kwargs: Any) -> Any:
    """A decorator that doesn't do anything at all."""
    return __decorated__(*args, **kwargs)


def count_calls(counter: Mut[int]) -> Decorator[_F]:
    """A decorator that counts the calls of a function."""
    @decorator()
    def count_calls(__decorated__: _F, *args: Any, **kwargs: Any) -> Any:
        counter._ += 1
        return __decorated__(*args, **kwargs)
    return count_calls
