#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test `rberga06.utils.cache`."""
from functools import wraps
from typing import Callable, TypeVar, cast
from rberga06.utils.cache import cache


_F = TypeVar("_F", bound=Callable[..., object])


def get_count(f: Callable[..., object]) -> int:
    if hasattr(f, "count"):
        return f.count
    if hasattr(f, "__wrapped__"):
        return get_count(f.__wrapped__)
    raise


def set_count(f: _F) -> _F:
    """Count `f`'s calls."""
    @wraps(f)
    def inner(*args, **kwargs):
        inner.count += 1  # type: ignore
        return f(*args, **kwargs)
    inner.count = 0  # type: ignore
    return cast(_F, inner)


@set_count
def factorial(x: int, /) -> int:
    if x == 0:
        return 1
    return factorial(x - 1)


@cache.call
@set_count
def factorial_cached(x: int, /) -> int:
    if x == 0:
        return 1
    return factorial_cached(x - 1)


def test_cache():
    assert factorial_cached(20) == factorial(20)
    assert factorial_cached(10) == factorial(10)
    assert get_count(factorial) == 32
    print(vars(factorial_cached))
    assert get_count(factorial_cached) == 22
