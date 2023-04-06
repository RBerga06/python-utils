#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test `rberga06.utils.types`"""
from __future__ import annotations
from pydantic import BaseModel
from rberga06.utils.types import *


class TestVersion:
    """Test pydantic(v2) compatibility."""

    def test_version(self):
        class Model(BaseModel):
            v: Version
        m = Model(v=Version("v1.0.0"))
        assert m == Model(v="1.0.0")  # type: ignore
        assert m == Model.model_validate(dict(v="v1.0.0"))
