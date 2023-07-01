#!/usr/bin/env python3
# -*- codinig: utf-8 -*-
# mypy: ignore-errors
"""Useful types."""
from __future__ import annotations
from collections.abc import Callable
from typing import Generic, cast, final
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
    ...     @override
    ...     def __repr__(self) -> str:
    ...         return f"<Foo: {self.value!r}>"
    ...
    ...     @classmethod
    ...     @override
    ...     def validate(cls, /, value: Any) -> Self:
    ...         if isinstance(value, str):
    ...             return cls(value)
    ...         return cls(repr(value))
    ...
    >>> class Model(pydantic.BaseModel):
    ...     answer: Foo  # you can use Foo as a pydantic field type
    ...
    >>> Foo("42")
    <Foo: '42'>
    >>> # useful when outside a pydantic model
    >>> Foo.validate(42)
    <Foo: '42'>
    >>> # Foo.validate() is called when validating the pydantic model
    >>> Model(answer=42)
    Model(answer=<Foo: '42'>)
    >>> Model(answer="42")
    Model(answer=<Foo: '42'>)
    >>> Model.model_validate({"answer": 42})
    Model(answer=<Foo: '42'>)
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

    >>> class Model(pydantic.BaseModel):
    ...     # with packaging.version.Version, this would fail
    ...     v: Version
    ...
    >>> Model(v=Version("v1.0.0"))
    Model(v=<Version('1.0.0')>)
    >>> Model(v=packaging.version.Version("v1.0.0"))
    Model(v=<Version('1.0.0')>)
    >>> Model(v="v1.0.0")
    Model(v=<Version('1.0.0')>)
    >>> Model.model_validate(dict(v="v1.0.0"))
    Model(v=<Version('1.0.0')>)
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



@final
class Mut(Generic[_T], SupportsPydanticV2["Mut[_T] | _T"]):
    """
    Flexible, static, mutable strong reference to a value.

    :Example:

    >>> # Immutable data
    >>> data = 42
    >>> m0 = Mut(data)
    >>> m1 = m0
    >>> m2 = Mut(data)
    >>> m0 is m1
    True
    >>> m0 is m2
    False
    >>> print(m0, m1, m2)
    Mut(42) Mut(42) Mut(42)
    >>> m0._ = 69
    >>> print(m0, m1, m2)
    Mut(69) Mut(69) Mut(42)
    >>>
    >>> # Mutable data
    >>> data = [42]
    >>> m0 = Mut(data)
    >>> m1 = m0
    >>> m2 = Mut(data)
    >>> m3 = Mut(data.copy())
    >>> m0 is m1
    True
    >>> m0 is m2
    False
    >>> m0 is m3
    False
    >>> print(m0, m1, m2, m3)
    Mut([42]) Mut([42]) Mut([42]) Mut([42])
    >>> m0._[0] = 33
    >>> print(m0, m1, m2, m3)
    Mut([33]) Mut([33]) Mut([33]) Mut([42])
    >>> m0._ = [69]
    >>> print(m0, m1, m2, m3)
    Mut([69]) Mut([69]) Mut([33]) Mut([42])

    :py:class:`Mut` is most useful when you need to pass around an immutable piece of data
    (like, in the example, :py:class:`int` instances), without bothering to use a full :py:class:`list`,
    where data access might be less readable and more error-prone -
    compare :py:obj:`(l := [42])[0]` with :py:obj:`(m := Mut(42)).value`...

    :py:class:`Mut` can also be used as a Pydantic model field, because it implements :py:class:`SupportsPydanticV2`.

    .. caution::
        Nesting :py:class:`Mut` instances (for example, :py:obj:`Mut(Mut(42))`) is possible, but **strongly discouraged.**
        There are two reasons for this:

        1.  There is no use case for this. If an object is already a `Mut`, why wrapping it _again_ into a `Mut`?
            To get the exact same behaviour the object already has?

        2.  The Pydantic compatibility API (see :py:class:`SupportsPydanticV2`) is designed to allow the following:

            >>> Mut[int].validate(42)
            Mut(42)
            >>> Mut[int].validate(Mut(42))
            Mut(42)

            It's not yet possible to access bound type parameters at runtime with consistency
            (see https://github.com/python/typing/issues/629); this means it's impossible to
            distinguish between these two calls:

            >>> Mut[int].validate(Mut(42))
            Mut(42)
            >>> Mut[Mut[int]].validate(Mut(42))
            Mut(42)
    """
    __slots__ = ("value", )

    value: _T
    """The inner value. Also accessible via the :py:attr:`~_` property."""

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
