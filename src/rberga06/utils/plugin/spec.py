#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plugin specification."""
from __future__ import annotations
from typing import Self, final
from pydantic import BaseModel, DirectoryPath, FilePath
import yaml
from ..types import Version


@final
class Info(BaseModel):
    """Plugin information."""
    name: str
    author: str
    version: Version
    description: str
    license: str = "<none>"


@final
class Spec(BaseModel):
    """Plugin specification."""
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
        return cls.model_validate(data)


class Features(BaseModel):
    """Plugin runtime features."""
    # To be subclassed by plugin systems.


__all__ = [
    "Info",
    "Spec",
    "Features",
]
