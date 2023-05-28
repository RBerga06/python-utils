#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
import pytest
from rberga06.utils.imports import *
from testutils import TestFeat

TestFeat.OTHER.required()


class TestPythonize:
    def _test_define(self, name: str, /, *, fails: bool = False) -> None:
        # Test if `exec(f"{name} = 42")` works (or fails) as expected.
        ctx = dict[str, object]()
        try:
            exec(f"{name} = 42", {}, ctx)
        except (SyntaxError, NameError, TypeError):
            if not fails:  raise
        assert (ctx != {name: 42}) == fails

    @pytest.mark.parametrize("c", "=-+*/%&|^<>:;,.@{}[]()!?'\\\"\n\r\t #$")
    def test_invalid_char(self, c: str) -> None:
        # Test `pythonize(...)` itself
        assert (name := pythonize(orig := f"a{c}b")) == f"a_b"
        assert pythonize(orig, ignore=c) == orig
        # Make sure `pythonize(...)` is useful in this case
        self._test_define(orig, fails=True)  # orig doesn't work as Python id
        self._test_define(name)              # new name works as a Python id

    @pytest.mark.parametrize("c", "_0aπßñå")
    def test_valid_char(self, c: str) -> None:
        # Test `pythonize(...)` itself
        assert pythonize(name := f"a{c}b") == name
        # Make sure it's a valid Python id
        self._test_define(name)


class TestImports:
    @pytest.mark.parametrize("inp,out", [
        ("a.b",      "a.b"),
        ("a.b:c.d",  "a.b:c.d"),
        (".b:c.d",   "root.b:c.d"),
        (".a.b:c.d", "root.a.b:c.d"),
        (".a.b",     "root.a.b"),
        (".:c.d",    "root:c.d"),
        (".",        "root"),
    ])
    def test_absolutize_obj_name(self, inp: str, out: str) -> None:
        assert absolutize_obj_name(inp, "root") == out

    def test_import_from(self) -> None:
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
        with pytest.raises(ModuleNotFoundError):
            import_from(Path("/this/path/does/not/exist"), "doesnt.matter")
        with pytest.raises(ModuleNotFoundError):
            # dir exists, but __init__.py not found
            import_from(Path(__file__).parent/"plugins", "doesnt.matter")

    def test_fake_module(self) -> None:
        pkg = import_or_fake("this.package.will.be.created", parents_know=True)
        import this
        assert this.package.will.be.created is pkg  # type: ignore
