#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mypy: ignore-errors
"""Test `rberga06.utils.cache`."""
from __future__ import annotations
from functools import wraps
from typing import Any, Callable, NoReturn, TypeVar, cast
import pytest
from rberga06.utils.cache import *
from .testutils import Feat

Feat.CACHE.required()


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


class TestCache:
    def test_base(self) -> None:
        """Test basic cache methods."""
        empty = Cache[int, None]()
        cache = Cache[int, None](42)
        assert      cache  and (not cache.is_empty)
        assert (not empty) and      empty.is_empty
        assert cache._ == cache.read() == 42
        assert empty._ == empty.read(strict=False) == Cache.default()
        assert Cache.get(cache) is cache
        assert Cache.get(empty) is empty
        with pytest.raises(ValueError):
            empty.read(strict=True)

    def test_func(self) -> None:
        """Test basic function caches's behaviour."""
        @count_calls
        def factorial(x: int, /) -> int:
            """x!"""
            if x == 0:
                return 1
            return x * factorial(x - 1)

        @func()
        @count_calls
        def cfactorial(x: int, /) -> int:
            """x!, but cached."""
            if x == 0:
                return 1
            return x * cfactorial(x - 1)

        assert isinstance(FCache.get(cfactorial), FCacheOneArg)

        assert cfactorial(2) == factorial(2)    # cfactorial() >> cache
        assert cfactorial(1) == factorial(1)    #              << cache
        # Calls to `factorial()`:
        # 1| => factorial(2)
        # 2|  -> factorial(1)
        # 3|   -> factorial(0)
        # 4| => factorial(1)
        # 5|   -> factorial(0)
        assert CALLS_COUNT["factorial"] == 5
        # Calls to `cfactorial()`:
        # 1| => cfactorial(2)    >> cache
        # 2|  -> cfactorial(1)   >> cache
        # 3|   -> cfactorial(0)  >> cache
        #  | => cfactorial(1)    << cache
        assert CALLS_COUNT["cfactorial"] == 3
        # assert cfactorial(100) == int(
        #     "9332621544394415268169923885626670049071596826438162146859296389521759999322991"
        #     "5608941463976156518286253697920827223758251185210916864000000000000000000000000"
        # )
        # Test `get(...)` (ad `read(...)`)
        assert (cfactorial_cache := Cache[dict[int, int], None].get(cfactorial))
        assert cfactorial_cache.read() == {
            0: (1, False),
            1: (1, False),
            2: (2, False),
        }
        with pytest.raises(ValueError):
            Cache.get(factorial)
        assert Cache.get(factorial, strict=False) is None
        # Test `clear(...)`
        clear(cfactorial)
        clear(factorial)
        assert not cfactorial_cache
        # Test `has(...)`
        assert Cache.has(cfactorial)
        assert not Cache.has(factorial)

    def test_func_exc(self) -> None:
        @func
        def bad_func() -> NoReturn:
            raise RuntimeError("Bad func called!")

        @func
        def divide(x: int, y: int) -> float:
            return x / y

        assert isinstance(FCache.get(bad_func), FCacheNoParams)
        assert not isinstance(FCache.get(divide), FCacheArgOnly)

        with pytest.raises(RuntimeError) as e1:
            # first call
            bad_func()
        with pytest.raises(RuntimeError) as e2:
            # cached call
            bad_func()
        assert e1.value is e2.value

        assert divide(0, 42) == 0

        with pytest.raises(ZeroDivisionError) as e1:
            # first call
            divide(42, 0)
        with pytest.raises(ZeroDivisionError) as e2:
            # cached call
            divide(42, 0)
        assert e1.value is e2.value

    def test_func_params(self) -> None:
        @func
        def foo(x: bool, /, *args: int) -> bool:
            return x and all(args)

        assert isinstance(FCache.get(foo), FCacheArgOnly)
        assert foo(True, 3, 14)
        assert not foo(True, 0)

        @func
        def bar(*, x: int = 42, **kwargs: str) -> int:
            return x

        assert isinstance(FCache.get(bar), FCacheKwOnly)
        assert bar(foo="foo") == 42

        @func(cls=FCacheNoParams)
        def once(val: float = 3.14) -> float:
            return val

        assert once(42.) == 42.
        assert once(3.14) == 42.

        @func
        def baz(*args: int, **kwargs: str) -> None:
            return None

        baz_cache = FCache.get(baz)
        assert not isinstance(baz_cache, FCacheArgOnly)
        assert not isinstance(baz_cache, FCacheKwOnly)
        assert not isinstance(baz_cache, FCacheOneArg)
        assert     isinstance(baz_cache, FCache)


@pytest.mark.skip(reason="Mypy doesn't support (yet) PEP 695 & PEP 696")
@pytest.mark.mypy_testing
def test_mypy() -> None:
    x: Any = 42
    if Cache[int].has(x):  # type: ignore
        x.__cache__


# from time import sleep
#
# @func
# def f(x: float, /) -> float:
#     sleep(x)
#     return x
#
#
# N =   5  # Number of benchmarks for each function
# M = .01  # Maximum run time for f
#
#
# class TestBenchmarks:
#     """Run benchmarks."""
#
#     @pytest.mark.parametrize("time", [x*M/N for x in range(1, N + 1)])
#     def test_run1(self, time: float, benchmark: Any) -> None:
#         """Benchmark first run of a cached function."""
#         assert time not in FCacheOneArg.get(f).read()
#         benchmark(f, time)
#
#     @pytest.mark.parametrize("time", [x*M/N for x in range(1, N + 1)])
#     def test_run2(self, time: float, benchmark: Any) -> None:
#         """Benchmark the second run of a cached function."""
#         assert time in FCacheOneArg.get(f).read()
#         benchmark(f, time)
