#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test utilities."""

import os
from typing import Iterator


def env(flag: str, /, *, default: str = "") -> str:
    return os.environ.get(flag, default)


### Features ###

_FEAT_PREFIX = "FEAT_"


def feats() -> Iterator[str]:
    for k, v in os.environ.items():
        if k.startswith(_FEAT_PREFIX) and v:
            yield k.removeprefix(_FEAT_PREFIX)


def feat(feat: str) -> bool:
    all = [*feats()]
    if "ALL" in all or not all:
        # by default, all features are on
        return True
    return feat in all
