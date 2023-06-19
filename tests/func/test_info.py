#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mypy: ignore-errors
"""Tests for `rberga06.utils.func.info`."""
import pytest
from ..testutils import Feat
from rberga06.utils.func.info import *

Feat.FUNC.required()


def raises(p0: int, p1: str, p2: bool, /) -> bool:
    return not any([p0, p1, p2])


@call_info()
def foo(p0: int, /, p1: str, *, p2: bool = False) -> None:
    if not any([p0, p1, p2]):
        raise RuntimeError


class TestCallInfo:
    def test_core(self):
        foo(42, "Magrathea!", p2=True)
        foo(42, p1="Magrathea!")
        with pytest.raises(RuntimeError):
            foo(0, "")
        info = call_info.get(foo)
        assert info[0].args == (42, "Magrathea!")
        assert info[1].args == (42, )
        assert info[2].args == (0, "")
        assert info[0].kwargs == frozenset({("p2", True)})
        assert info[1].kwargs == frozenset({("p1", "Magrathea!")})
        assert info[2].kwargs == frozenset()
        assert info[0].success
        assert info[1].success
        assert not info[2].success
        assert info[0].result == None
        assert info[1].result == None
        assert isinstance(info[2].result, RuntimeError)
