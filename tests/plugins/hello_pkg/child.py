#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

def hello(name: str = "World", /) -> str:
    return f"Hello, {name}!"
