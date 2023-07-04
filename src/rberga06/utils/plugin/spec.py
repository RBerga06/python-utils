#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plugin specification."""
from __future__ import annotations
from typing_extensions import Self, final
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
        """Read the info file at ``root/.plugin.yml``."""
        data = yaml.load(file.read_text("utf-8"), yaml.SafeLoader)
        data["root"] = file.parent
        return cls.model_validate(data)


class Features(BaseModel):
    """Plugin runtime features.

    To be subclassed by plugin systems.

    :Example:

    >>> from rberga06.utils import plugin
    >>>
    >>> class MyFeats(plugin.Features):
    ...     foo: int
    ...
    >>> sys = plugin.System(
    ...     name="my.plugin", version="1.0.0",
    ...     package="mypackage.plugins",
    ...     Features=MyFeats,
    ... ).extend_path_pkg("mypackage.plugins").discover_all()
    >>> myplugin = sys.plugins[0]
    >>> myfeats = myplugin.feat
    >>> type(myfeats)
    <class __main__.MyFeats>
    >>> myfeats.foo
    42
    """


__all__ = ["Info", "Spec", "Features"]
