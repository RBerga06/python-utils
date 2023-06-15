#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mypy: ignore-errors
"""Plugin systems."""
from __future__ import annotations
import ast
from collections import deque
from contextlib import suppress
from importlib import import_module
from pkgutil import resolve_name
from pathlib import Path
import sys
from types import ModuleType
from typing import Generic, Iterator, Self, TypeVar, cast, final, overload
from typing_extensions import override
from pydantic import BaseModel, Field

from ..types import Version
from ..imports import absolutize_obj_name, import_from, pythonize
from .spec import Spec, Features


_F = TypeVar("_F", bound=Features)


@final
class Plugin(BaseModel, Generic[_F]):
    """A plugin."""
    sys: System[_F]
    spec: Spec
    features: _F | None = None  # by default, it's not loaded

    @property
    def is_loaded(self) -> bool:
        return self.features is not None

    def load(self) -> Self:
        """Load `self` (in-place) and return it."""
        return self.sys.load(self)

    @property
    def feat(self) -> _F:
        """Lazy shortcut for `.load().features`."""
        if self.features is None:
            self.load()
        return cast(_F, self.features)


# Pydantic model configuration
#   (looks like setting this specific key is not necessary anymore?)
# Plugin.model_config["undefined_types_warning"] = False



def _platform_aliases(aliases: dict[str, set[str]]) -> set[str]:
    platform = sys.platform.lower()
    return {platform} | aliases.get(platform, aliases["__default__"])


_PLATFORM_ALIASES: set[str] = _platform_aliases(dict(
    #     str      --->      set[str]
    # sys.platform |--> accepted aliases
    darwin={"macos", "unix"},
    __default__={"unix"},
))


@final
class _PlatformASTNodeTransformer(ast.NodeTransformer):
    """AST node transformer for platform requirements."""

    @override
    def visit_Name(self, node: ast.Name) -> ast.AST:
        return ast.copy_location(ast.Constant(
            value=(node.id.lower() in _PLATFORM_ALIASES),
            ctx=node.ctx
        ), node)


@final
class System(BaseModel, Generic[_F]):
    """A plugin system."""
    name: str
    version: Version
    package: str      # The Python (virtual?) package that should contain all plugins.
    Features: type[_F]
    path: list[Path] = Field(default_factory=list)
    plugins: dict[str, Plugin[_F]] = Field(default_factory=dict)
    info_file: str = ".plugin.yml"

    def compat_eval(self, spec: str, /) -> bool:
        """Evaluate compatibility with the given spec."""
        # Check name
        name, *segments = spec.split(" ")
        if name != self.name:
            return False
        # Check version
        if not segments: return True
        version, *segments = segments
        if version != "on" and self.version < Version(version):
            return False
        # Check platform
        if not segments: return True
        return cast(bool, eval(compile(_PlatformASTNodeTransformer().visit(
            ast.parse(" ".join(segments).removeprefix("on").strip(), mode="eval")
        ), "<file>", "eval")))

    @overload
    def compat_ensure(self, obj: Plugin[_F], /) -> Plugin[_F]: ...
    @overload
    def compat_ensure(self, obj: Spec, /) -> Spec: ...
    def compat_ensure(self, obj: Plugin[_F] | Spec, /) -> Plugin[_F] | Spec:
        """Make sure the given plugin is compatible with `self`."""
        plugin = None
        if isinstance(obj, Plugin):
            plugin, obj = obj, obj.spec
        if self.compat_eval(obj.sys):
            return obj
        if plugin is None:
            raise RuntimeError(f"Incompatible plugin spec: {obj}")
        raise RuntimeError(f"Incompatible plugin: {plugin}")

    def register(self, plugin: Plugin[_F]) -> Plugin[_F]:
        """Register the given plugin."""
        self.compat_ensure(plugin)
        self.plugins[plugin.spec.info.name] = plugin
        return plugin

    def extend_path_pkg(self, ns: ModuleType | str) -> Self:
        """Extend `self.path` with the given (namespace?) package."""
        if isinstance(ns, str):
            ns = import_module(ns)
        if not hasattr(ns, "__path__"):
            raise ValueError(f"{ns.__name__!r} is not a package!")
        return self.extend_path(*ns.__path__)

    def extend_path(self, *paths: Path | str) -> Self:
        """Extend `self.path` with the given paths."""
        self.path.extend(map(Path, paths))
        return self

    def discover_all(self) -> Self:
        """Run and exhaust `self.discover()` and return `self`."""
        # Exhaust the iterator by feeding it to a zero-length deque
        #   see https://stackoverflow.com/a/36763172
        deque(self.discover(), maxlen=0)
        return self

    def discover(self) -> Iterator[Plugin[_F]]:
        """Discover compatible plugins at `self.path` (and register them)."""
        for root in self.path:
            for child in root.iterdir():
                yield from self._discover(child)

    def _discover(self, root: Path) -> Iterator[Plugin[_F]]:
        """Discover plugins at `root` (and its subdirs)."""
        if root.is_dir():  # implies `.exists()``
            file = (root/self.info_file).resolve()
            if file.is_file():  # implies `.exists()`
                with suppress(Exception):
                    # If any exception occurs, the plugin will simply be discarded
                    spec = self.compat_ensure(Spec.read(file))
                    if spec.info.name in self.plugins:
                        # if the plugin is already there, use that!
                        yield self.plugins[spec.info.name]
                    else:
                        yield self.register(Plugin(sys=self, spec=spec))
            else:
                for child in root.iterdir():
                    yield from self._discover(child)

    def load(self, plugin: Plugin[_F]) -> Plugin[_F]:
        """Load the given plugin (in-place)."""
        # Make sure the plugin has not already been loaded
        if plugin.features is not None:
            return plugin
        # Make sure the module has been imported
        modulename = f"{self.package}.{pythonize(plugin.spec.info.name, ignore='.')}"
        if modulename not in sys.modules:
            sys.modules[modulename] = import_from(
                plugin.spec.root.joinpath(plugin.spec.lib).resolve(),
                modulename,
            )
        # Resolve the specified feature paths
        features = dict[str, object]()
        for name, value in plugin.spec.feat.items():
            features[name] = resolve_name(absolutize_obj_name(value, modulename))
        plugin.features = self.Features.model_validate(features)
        return plugin


# `System` was defined after `Plugin`
#   (looks like this is not required anymore?)
# Plugin.model_rebuild(force=True)


__all__ = [
    "Plugin",
    "System",
]
