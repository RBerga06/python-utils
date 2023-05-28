#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for `rberga06.utils.func.sig`."""
from rberga06.utils.func.sig import sig
from ..testutils import TestFeat

TestFeat.FUNC.required()


def foo(x: int, /, y: bool = True, *, z: list[str] | None = None) -> str:
    return str(len(z) if z and y else x)


class TestSig:
    def test_sig(self) -> None:
        assert sig[foo]
