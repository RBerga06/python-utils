#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mypy: ignore-errors
"""Test `rberga06.utils.cache`."""
from __future__ import annotations
from functools import wraps
from typing import Callable, NoReturn, TypeVar, cast
import pytest
from rberga06.utils.cache import *


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

        @func(cls=FCacheOneArg)  # We only care about one argument
        @count_calls
        def cfactorial(x: int, /) -> int:
            """x!, but cached."""
            if x == 0:
                return 1
            return x * cfactorial(x - 1)

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
        @func(cls=FCacheNoParams)
        def bad_func() -> NoReturn:
            raise RuntimeError("Bad func called!")

        with pytest.raises(RuntimeError) as e1:
            # first call
            bad_func()
        with pytest.raises(RuntimeError) as e2:
            # cached call
            bad_func()
        assert e1.value is e2.value
