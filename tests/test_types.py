#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test `rberga06.utils.types`"""
from __future__ import annotations
from typing import cast
import weakref
from pydantic import BaseModel
import pytest
from rberga06.utils.types import *
from testutils import module_requires_feat


module_requires_feat("OTHER")


class TestVersion:
    """Test pydantic(v2) compatibility."""

    def test_version(self) -> None:
        class Model(BaseModel):
            v: Version
        m = Model(v=Version("v1.0.0"))
        assert m == Model(v="1.0.0")  # type: ignore
        assert m == Model.model_validate(dict(v="v1.0.0"))



class Foo: ...


class TestRef:
    def _test_ref(self, obj: object, weak: bool) -> None:
        r = ref(obj)
        assert r.is_weak == weak
        assert obj is r.inner
        if weak:
            assert r._ is r() is cast(weakref.ref[object], obj)()
        else:
            assert r._ is r() is obj

    def test_ref(self) -> None:
        for obj, weak_allowed in (
            (42, False),
            ([42], False),
            (Foo, True),
            (Foo(), True),
        ):
            self._test_ref(obj, False)
            if weak_allowed:
                self._test_ref(weakref.ref(obj), True)
            else:
                with pytest.raises(TypeError):
                    ref[object](weakref.ref(obj))

    def test_empty(self) -> None:
        foo = Foo()
        r = ref[object](weakref.ref(foo))
        del foo
        with pytest.raises(ValueError):
            r._
        with pytest.raises(ValueError):
            r()
        assert r(strict=False) is None

    def test_pytest(self) -> None:
        class Model(BaseModel):
            r: ref[Foo]

        foo = Foo()
        assert Model(r=ref(foo)).r._ is foo
        assert Model(r=ref(weakref.ref(foo))).r._ is foo
        assert Model(r=foo).r._ is foo  # type: ignore
        assert Model(r=weakref.ref(foo)).r._ is foo  # type: ignore
        assert Model.model_validate(dict(r=foo)).r._ is foo
        assert Model.model_validate(dict(r=weakref.ref(foo))).r._ is foo
