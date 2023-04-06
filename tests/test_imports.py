#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
from pytest import raises
from rberga06.utils.imports import *


class TestImports:
    def test_pythonize(self):
        for inp, out in [
            ("abc", "abc"),
            ("a-b", "a_b"),
            ("a+b", "a_b"),
            ("a.b", "a_b"),
            ("a!b", "a_b"),
            ("a?b", "a_b"),
            ("a@b", "a_b"),
            ("a:b", "a_b"),
            ("a#b", "a_b"),
        ]:
            assert pythonize(inp) == out

    def test_absolutize_obj_name(self):
        for inp, out in [
            ("a.b",      "a.b"),
            ("a.b:c.d",  "a.b:c.d"),
            (".b:c.d",   "root.b:c.d"),
            (".a.b:c.d", "root.a.b:c.d"),
            (".a.b",     "root.a.b"),
            (".:c.d",    "root:c.d"),
            (".",        "root"),
        ]:
            assert absolutize_obj_name(inp, "root") == out

    def test_import_from(self):
        mod = import_from(
            Path(__file__).parent/"plugins/hello/lib.py",
            "this.is_.a.very.particular.package.in_.a.fake.namespace.with_.an.extremely.long.name",
            inject=dict(
                answer=42
            ),
        )
        from this.is_.a.very.particular.package.in_.a.fake.namespace.with_.an.extremely.long import name  # type: ignore
        assert mod is name
        assert mod.answer == 42
        with raises(ModuleNotFoundError):
            import_from(Path("/this/path/does/not/exist"), "doesnt.matter")
        with raises(ModuleNotFoundError):
            # dir exists, but __init__.py not found
            import_from(Path(__file__).parent/"plugins", "doesnt.matter")

    def test_fake_module(self):
        import_or_fake("this.package.will.be.created", parents_know=True)
