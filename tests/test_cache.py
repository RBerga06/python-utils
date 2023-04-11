#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test `rberga06.utils.cache`."""
from __future__ import annotations
from functools import wraps
from typing import Callable, NamedTuple, NoReturn, TypeVar, cast
import pytest
from rberga06.utils.cache import cache


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


@cache.call
@count_calls
def factorial_cached(x: int, /) -> int:
    if x == 0:
        return 1
    return factorial_cached(x - 1)


@cache.call
def bad_func() -> NoReturn:
    raise ValueError("Bad func called!")


class Foo(NamedTuple):
    name: str

    @property
    @cache.call
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
        assert cache.has(factorial_cached)
        assert not cache.has(factorial)
        assert cache.has(bad_func)
        assert cache.has(Foo.foo)

    def test_get(self) -> None:
        with pytest.raises(ValueError):
            cache.get(factorial)
        assert cache.get(factorial, strict=False) is None
        assert cache.get(factorial_cached) is not None
        assert cache.get(Foo.foo) is not None

    def test_read(self) -> None:
        with pytest.raises(ValueError):
            cache().read(strict=True)
        with pytest.raises(ValueError):
            cache.read(factorial, strict=True)  # type: ignore
        assert cache().read() is None
        assert cache.read(factorial) is None  # type: ignore
        assert cache.read(factorial_cached)  # type: ignore

    def test_clear(self) -> None:
        cache().clear()
        cache.clear(factorial)  # type: ignore
        cache.clear(factorial_cached)  # type: ignore
        cache.clear(Foo.foo)  # type: ignore
        assert cache.read(factorial_cached) is None  # type: ignore
        factorial_cached(10)
        assert cache.read(factorial_cached) is not None  # type: ignore
