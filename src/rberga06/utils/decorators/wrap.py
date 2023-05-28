#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mypy: ignore-errors
"""Function wrappers."""
from contextlib import suppress
from typing import Any, Callable as Fn, Literal, overload
from typing_extensions import TypeVar
from .sig import sig

# Type aliases
_AnyFn = Fn[..., Any]
# TypeVars
_F = TypeVar("_F", infer_variance=True, bound=_AnyFn, default=_AnyFn)
_G = TypeVar("_G", infer_variance=True, bound=_AnyFn, default=_AnyFn)


WRAPPER_ATTRS = {
    "__module__", "__name__", "__qualname__", "__doc__",
}


@overload
def update_wrapper(
    wrapper: _F,
    wrapped: _AnyFn,
    /, *,
    silent: bool = False,
    signature: Literal[False],
    assigned: set[str] = WRAPPER_ATTRS,
) -> _F: ...
@overload
def update_wrapper(
    wrapper: _AnyFn,
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
    """Like `functools.update_wrapper(...)`, but type checked."""
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
    wrapped: _AnyFn, /, *,
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
) -> Fn[[_AnyFn], _F]: ...
def wraps(
    wrapped: _F, /, *,
    silent: bool = False,
    signature: bool = True,
    assigned: set[str] = WRAPPER_ATTRS,
) -> Fn[[_G], _F | _G]:
    """Like `functools.wraps(...)`, but type checked."""
    def inner(wrapper: _G, /) -> _F | _G:
        return update_wrapper(
            wrapper, wrapped,
            silent=silent,
            signature=signature,
            assigned=assigned,
        )
    return inner
