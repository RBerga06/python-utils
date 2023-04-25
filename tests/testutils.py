#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test utilities."""

import os

def flag(flag: str) -> bool:
    return f"RBERGA06_{flag}" in os.environ
