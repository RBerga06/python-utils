#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mypy: ignore-errors
"""Function wrappers."""
# Inspired by the wrapt library

from contextlib import suppress
from typing import Callable as Fn
from typing import Any, Sequence, cast
from typing_extensions import TypeVar
from .sig import sig


_F = TypeVar("_F", infer_variance=True, bound = Fn[..., Any], default = Fn[..., Any])


WRAPPER_ASSIGNMENTS = (
    "__module__", "__name__", "__qualname__", "__doc__", "__annotations__",
    # inspect.signature(...) works well with __wrapped__, so there is no need for also adding __signature__.
)
WRAPPER_UPDATES = (
    "__dict__",
)


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
    return sig[wrapped].typing(wrapper)


def wraps(
    wrapped: _F, /, *,
    assigned: Sequence[str] = WRAPPER_ASSIGNMENTS,
    updated:  Sequence[str] = WRAPPER_UPDATES,
) -> Fn[[Fn[..., Any]], _F]:
    """Like `functools.wraps(...)`"""
    def inner(wrapper: Fn[..., Any], /) -> _F:
        return update_wrapper(wrapper, wrapped, assigned=assigned, updated=updated)
    return inner
