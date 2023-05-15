#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mypy: ignore-errors
"""Function wrappers."""
# Inspired by the wrapt library

from contextlib import suppress
from inspect import signature
from typing import Callable as Fn
from typing import Any, Sequence, cast
from typing_extensions import TypeVar, ParamSpec


_F = TypeVar("_F", infer_variance=True, bound = Fn[..., Any], default = Fn[..., Any])
_P = ParamSpec("_P", default=...)
_R = TypeVar("_R", default=Any)


WRAPPER_ASSIGNMENTS = (
    "__module__", "__name__", "__qualname__", "__doc__", "__annotations__",
    # inspect.signature(...) works well with __wrapped__, so there is no need for also adding __signature__.
)
WRAPPER_UPDATES = (
    "__dict__",
)


def copysignature(src: _F, /, *, runtime: bool = True) -> Fn[[Fn[..., Any]], _F]:
    def inner(dst: Fn[..., Any], /) -> _F:
        if runtime:
            with suppress(AttributeError):
                object.__setattr__(dst, "__signature__", signature(src))
        return cast(_F, dst)
    return inner


def update_wrapper(
    wrapper: Fn[..., Any],
    wrapped: _F,
    /, *,
    assigned: Sequence[str] = WRAPPER_ASSIGNMENTS,
    updated:  Sequence[str] = WRAPPER_UPDATES,
) -> _F:
    """Like `functools.update_wrapper(...)`"""
    for attr in assigned:
        with suppress(AttributeError):
            object.__setattr__(wrapper, attr, object.__getattribute__(wrapped, attr))
    for attr in updated:
        with suppress(AttributeError):
            cast(dict[str, Any], object.__getattribute__(wrapper, attr)).update(
                cast(dict[str, Any], object.__getattribute__(wrapped, attr))
            )
    return copysignature(wrapped, runtime=False)(wrapper)


def wraps(
    wrapped: _F, /, *,
    assigned: Sequence[str] = WRAPPER_ASSIGNMENTS,
    updated:  Sequence[str] = WRAPPER_UPDATES,
) -> Fn[[Fn[..., Any]], _F]:
    """Like `functools.wraps(...)`"""
    def inner(wrapper: Fn[..., Any], /) -> _F:
        return update_wrapper(wrapper, wrapped, assigned=assigned, updated=updated)
    return inner



@wraps(int)
def int2(*args: Any, **kwargs: Any) -> int:
    return int(*args, **kwargs)

print(int, int.__doc__)
print(int2, int2.__doc__)
