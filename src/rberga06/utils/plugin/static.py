#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static plugin data."""
from __future__ import annotations
from typing import Self
from pydantic import BaseModel, DirectoryPath, FilePath
import yaml
from ..types import Version


class Info(BaseModel):
    """Plugin information."""
    name: str
    author: str
    version: Version
    description: str
    license: str = "<none>"


class Static(BaseModel):
    """Static plugin data."""
    root: DirectoryPath
    sys: str
    info: Info
    lib: str
    feat: dict[str, str]

    @classmethod
    def read(cls, file: FilePath) -> Self:
        """Read the info file at `root/.plugin.yml`."""
        data = yaml.load(file.read_text("utf-8"), yaml.SafeLoader)
        data["root"] = file.parent
        return cls.validate(data)



__all__ = [
    "Info",
    "Static",
]
