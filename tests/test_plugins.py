#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the plugin system."""
from __future__ import annotations
from pathlib import Path
import sys
from typing import Protocol
from pydantic import ValidationError
import pytest
from rberga06.utils.types import ref
from rberga06.utils.plugin import *
from testutils import module_requires_feat


module_requires_feat("PLUGINS")


class _Hello(Protocol):
    def __call__(self, name: str = ..., /) -> str:
        ...


class _TestPluginSystemFeatures(Features):
    hello: ref[_Hello]


s: System[_TestPluginSystemFeatures]


class TestPluginSystem:
    @pytest.mark.order(1)
    def test_sys_init(self) -> None:
        global s
        s = System(
            name="rberga06.utils.<tests>",
            version="v1.0.0",   # type: ignore
            package="rberga06.utils.tests.plugins",
            Features=_TestPluginSystemFeatures
        ).extend_path(Path(__file__).parent/"plugins")

        with pytest.raises(ModuleNotFoundError):
            s.extend_path_pkg("package.does.not.exist")

        with pytest.raises(ValueError):
            s.extend_path_pkg("os")

    @pytest.mark.order(2)
    def test_compat(self) -> None:
        assert not s.compat_eval( "unsupported.plugin.system")
        assert     s.compat_eval( "rberga06.utils.<tests>")
        assert     s.compat_eval( "rberga06.utils.<tests> v1.0.0")
        assert     s.compat_eval( "rberga06.utils.<tests> v0.1.0")
        assert not s.compat_eval( "rberga06.utils.<tests> v3.1.4")
        assert     s.compat_eval(f"rberga06.utils.<tests> v1.0.0 on {sys.platform}")
        assert not s.compat_eval(f"rberga06.utils.<tests> v1.0.0 on unknown-platform")
        assert     s.compat_eval(f"rberga06.utils.<tests> on {sys.platform}")
        assert not s.compat_eval(f"rberga06.utils.<tests> on unknown-platform")
        assert     s.compat_eval( "rberga06.utils.<tests> v1.0.0 on macOS") == (sys.platform.lower() == "darwin")

    @pytest.mark.order(3)
    def test_read_static(self) -> None:
        plugins = Path(__file__).parent/"plugins"
        hello = Spec.read(plugins/"hello/.plugin.yml")
        error = Spec.read(plugins/"err_compat/.plugin.yml")
        assert hello
        assert error
        assert s.compat_ensure(hello)
        with pytest.raises(RuntimeError):
            s.compat_ensure(error)

    @pytest.mark.order(4)
    def test_discover(self) -> None:
        assert {*s.discover_all().plugins.keys()} == {
            "hello", "hello-pkg", "err-feature",
        }
        # re-run the discovery: already-discovered plugins will be used
        assert s.plugins == s.discover_all().plugins

    @pytest.mark.order(5)
    def test_hello(self) -> None:
        hello = s.plugins["hello"]
        assert hello.feat.hello._() == "Hello, World!"
        assert hello.feat.hello._("pytest") == "Hello, pytest!"
        assert hello.is_loaded
        # `load()`ing again the plugin does nothing
        assert hello is hello.load()
        # Make sure the module can be loaded
        from rberga06.utils.tests.plugins.hello import hello as orig  # type: ignore
        assert hello.feat.hello._ is orig

    @pytest.mark.order(6)
    def test_hello_pkg(self) -> None:
        pkg = s.plugins["hello-pkg"]
        assert pkg.feat.hello._() == "Hello, World!"
        assert pkg.feat.hello._("pytest") == "Hello, pytest!"
        assert pkg.is_loaded
        # `load()`ing again the plugin does nothing
        assert pkg is pkg.load()
        # Make sure the module can be loaded
        from rberga06.utils.tests.plugins.hello_pkg import hello as orig  # type: ignore
        assert pkg.feat.hello._ is orig

    @pytest.mark.order(7)
    def test_errors(self) -> None:
        assert "err-malformed" not in s.plugins
        assert "err-compat" not in s.plugins
        err = s.plugins["err-feature"]
        with pytest.raises(ValidationError):
            err.load()
        with pytest.raises(RuntimeError):
            System(
                name="wrong",
                version="v1.0.0",  # type: ignore
                package="this.is.wrong",
                Features=Features,
            ).compat_ensure(err)  # type: ignore
        # The module can still be loaded
        import rberga06.utils.tests.plugins.err_feature  # type: ignore
