#!/usr/bin/env python3
# -*- codinig: utf-8 -*-
# mypy: ignore-errors
"""Useful types."""
from __future__ import annotations
from collections.abc import Callable
from typing import Generic, cast
from typing_extensions import Any, Literal, Protocol, Self, TypeVar, overload, override
import weakref
import packaging.version
from pydantic_core import core_schema


_T = TypeVar("_T", infer_variance=True)


class SupportsPydanticV2(Protocol[_T]):
    """
    A :py:class:`typing.Protocol` that makes it easy to implement :py:mod:`pydantic` v2 support.

    :Example:

    >>> class Foo(SupportsPydanticV2[Any]):
    ...     def __init__(self, value: str, /) -> None:
    ...         self.value = value
    ...
    ...     def __repr__(self) -> str:
    ...         return f"<Foo: {self.value}>"
    ...
    ...     @override
    ...     def validate(cls, value: Any) -> Self:
    ...         if isinstance(value, str):
    ...             return cls(value)
    ...         return cls(repr(value))
    ...
    >>> class Model(pydantic.BaseModel):
    ...     answer: Foo  # you can use Foo as a pydantic field type
    ...
    >>> Foo("42")
    <Foo: 42>
    >>> # useful when outside a pydantic model
    >>> Foo.validate(42)
    <Foo: 42>
    >>> # Foo.validate() is called when validating the pydantic model
    >>> Model(answer=42)
    answer=<Foo: 42>
    >>> Model(answer="42")
    answer=<Foo: 42>
    >>> Model.model_validate({"answer": 42})
    answer=<Foo: 42>
    """

    @classmethod
    def validate(cls, obj: _T, /) -> Self:
        """
        Instantiate this class from :py:obj:`obj`.
        """
        ...

    @classmethod
    def __get_pydantic_core_schema__(cls, *args: Any, **kwargs: Any) -> core_schema.PlainValidatorFunctionSchema:
        """Provides a :py:mod:`pydantic_core` schema. Implements :py:mod:`pydantic` v2 support."""
        # See https://github.com/pydantic/pydantic/issues/5373
        return core_schema.no_info_plain_validator_function(
            lambda _: cls.validate(_), serialization=core_schema.to_string_ser_schema()
        )



class Version(packaging.version.Version, SupportsPydanticV2["Version | packaging.version.Version | str"]):
    """
    A :py:mod:`pydantic` v2-compatible :class:`packaging.version.Version` subclass.

    :Example:

    >>> class Model(BaseModel):
    ...     # with packaging.version.Version, this would fail
    ...     v: Version
    ...
    >>> Model(v=Version("v1.0.0"))
    v = <Version 1.0.0>
    >>> Model(v=packaging.version.Version("v1.0.0"))
    v = <Version 1.0.0>
    >>> Model(v="v1.0.0")
    v = <Version 1.0.0>
    >>> Model.model_validate(dict(v="v1.0.0"))
    v = <Version 1.0.0>
    >>> # In addition, Version behaves exactly like packaging.version.Version:
    >>> Version("1.0.0") > Version("1.0.0.a2")
    True

    See :py:class:`packaging.version.Version` for more details.
    """

    @classmethod
    @override
    def validate(cls, obj: Version | packaging.version.Version | str, /) -> Self:
        if isinstance(obj, cls):
            return obj
        elif isinstance(obj, packaging.version.Version):
            return cls(str(obj))
        else:
            return Version(obj)



class Mut(Generic[_T], SupportsPydanticV2["Mut[_T] | _T"]):
    """Flexible, static, mutable strong reference to a value."""
    __slots__ = ("value", )

    value: _T
    """The inner value."""

    def __init__(self, value: _T, /) -> None:
        self.value = value

    def get(self) -> _T:
        """Get the inner value."""
        return self.value

    def set(self, value: _T, /) -> None:
        """Set the inner value."""
        self.value = value

    @property
    def _(self) -> _T:
        """The inner value."""
        return self.value
    @_.setter
    def _(self, _: _T) -> None:
        self.set(_)

    @override
    def __repr__(self) -> str:
        return f"Mut({self.value!r})"

    @classmethod
    @override
    def validate(cls, obj: "Mut[_T] | _T") -> Self:
        if isinstance(obj, cls):
            return obj
        return cls(obj)



class ref(Generic[_T], SupportsPydanticV2["ref[_T] | weakref.ref[_T] | _T"]):
    """Flexible, static reference (can be either a weak or a strong reference)."""
    __slots__ = ("inner",)

    inner: weakref.ref[_T] | _T
    """The wrapped value or a weak reference to it."""

    def __init__(self, inner: _T | weakref.ref[_T], /) -> None:
        self.inner = inner

    @property
    def _(self) -> _T:
        """The wrapped value."""
        return self()

    @overload
    def __call__(self, /, *, strict: Literal[True] = ...) -> _T: ...
    @overload
    def __call__(self, /, *, strict: Literal[False]) -> _T | None: ...
    def __call__(self, /, *, strict: bool = True) -> _T | None:
        """The wrapped value (`weakref`-style access)."""
        if self.is_weak:
            val = cast(weakref.ref[_T], self.inner)()
            if strict and val is None:
                raise ValueError("Empty reference.")
        else:
            val = cast(_T, self.inner)
        return val

    @property
    def is_weak(self) -> bool:
        """Check if :py:obj:`self` is a weak reference."""
        return isinstance(self.inner, weakref.ref)

    @classmethod
    @override
    def validate(cls, obj: ref[_T] | weakref.ref[_T] | _T, /) -> Self:
        if isinstance(obj, ref):
            return cast(ref[_T], obj)
        else:
            return ref(obj)


_A = TypeVar("_A")
_B = TypeVar("_B")


class ItemFunc(Generic[_A, _B]):
    """Similar to a (_A, ) -> _B function, but called via [...] instead of (...)."""
    __slots__ = ("__wrapped__", )
    __wrapped__: Callable[[_A], _B]

    def __init__(self, func: Callable[[_A], _B], /) -> None:
        self.__wrapped__ = func

    def __getitem__(self, item: _A, /) -> _B:
        return self.__wrapped__(item)


class AttrFunc(Generic[_T]):
    """Similar to a (str, ) -> _T function but called via attribute access instead of (...)."""
    __slots__ = ("__wrapped__", )
    __wrapped__: Callable[[str], _T]

    def __init__(self, func: Callable[[str], _T], /) -> None:
        self.__wrapped__ = func

    def __getattr__(self, item: str, /) -> _T:
        return self.__wrapped__(item)


__all__ = [
    "SupportsPydanticV2",
    "Version",
    "Mut", "ref",
    "ItemFunc", "AttrFunc",
]
