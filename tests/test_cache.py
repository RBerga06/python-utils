#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mypy: ignore-errors
"""Test `rberga06.utils.cache`."""
from __future__ import annotations
from functools import wraps
from typing import Callable, NamedTuple, NoReturn, TypeVar, cast
import pytest
from rberga06.utils import cache
from rberga06.utils.cache import Cache


_F = TypeVar("_F", bound=Callable[..., object])


CALLS_COUNT = dict[str, int]()


def count_calls(f: _F) -> _F:
    """Count `f`'s calls."""
    @wraps(f)
    def inner(*args: object, **kwargs: object) -> object:
        CALLS_COUNT[f.__name__] += 1
        return f(*args, **kwargs)
    CALLS_COUNT[f.__name__] = 0
    return cast(_F, inner)


@count_calls
def factorial(x: int, /) -> int:
    if x == 0:
        return 1
    return factorial(x - 1)


@cache.func
@count_calls
def factorial_cached(x: int, /) -> int:
    if x == 0:
        return 1
    return factorial_cached(x - 1)


@cache.func
def bad_func() -> NoReturn:
    raise RuntimeError("Bad func called!")


class Foo(NamedTuple):
    name: str

    @property
    @cache.func
    def foo(self) -> str:
        return self.name


class TestCache:
    def test_cache(self) -> None:
        assert factorial_cached(20) == factorial(20)
        assert factorial_cached(10) == factorial(10)
        assert CALLS_COUNT["factorial"] == 32
        print(vars(factorial_cached))
        assert CALLS_COUNT["factorial_cached"] == 21

    def test_exception(self) -> None:
        with pytest.raises(ValueError):
            # first call
            bad_func()
        with pytest.raises(ValueError):
            # cached call
            bad_func()

    def test_has(self) -> None:
        assert Cache.has(factorial_cached)
        assert not Cache.has(factorial)
        assert Cache.has(bad_func)
        assert Cache.has(Foo.foo)

    def test_get(self) -> None:
        with pytest.raises(ValueError):
            Cache.get(factorial)
        assert Cache.get(factorial, strict=False) is None
        assert Cache.get(factorial_cached) is not None
        assert Cache.get(Foo.foo) is not None

    def test_read(self) -> None:
        with pytest.raises(ValueError):
            Cache().read(strict=True)
        with pytest.raises(ValueError):
            Cache.get(factorial).read(strict=True)
        assert Cache().read() is None
        assert Cache.get(factorial_cached).read()
        assert isinstance(Cache.get(bad_func).read(), RuntimeError)

    def test_clear(self) -> None:
        Cache().clear()
        cache.clear(factorial)
        cache.clear(factorial_cached)
        cache.clear(Foo.foo)
        assert not Cache.get(factorial_cached)
        factorial_cached(10)
        assert Cache.get(factorial_cached)
