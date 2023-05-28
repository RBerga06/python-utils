#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test utilities."""

from enum import StrEnum, auto
import os
from typing import Any, Iterator
from typing_extensions import override

import pytest


def env(flag: str, /, *, default: str = "") -> str:
    return os.environ.get(flag, default)


### Features ###

_FEAT_PREFIX = "FEAT_"


class _FeatBase(StrEnum):
    @override   # from StrEnum
    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[Any]) -> str:
        return name

    def required(self, /) -> None:
        return module_requires_feat(self)


class Feat(_FeatBase):
    # Known testing features
    CACHE   = auto()
    PLUGIN  = auto()
    FUNC    = auto()
    OTHER   = auto()


def feats() -> Iterator[str]:
    for k, v in os.environ.items():
        if k.startswith(_FEAT_PREFIX) and v:
            yield k.removeprefix(_FEAT_PREFIX)


def feat(feat: str, /) -> bool:
    all = [*feats()]
    if "ALL" in all or not all:
        # by default, all features are on
        return True
    return feat in all


def module_requires_feat(feature: str, /) -> None:
    if not feat(feature):
        pytest.skip(reason=f"Feature {feature} is not enabled.", allow_module_level=True)


print("Features: ", *feats())
