#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mypy: ignore-errors
"""Retrieve detailed information about function calls."""
from collections.abc import Iterable
from typing import Any, ClassVar, Generic, NamedTuple, TypeVar, cast
from typing_extensions import override
from .dec import AnyFn, DecoratorWithAttr
import logging

# Type variables
_F = TypeVar("_F", bound=AnyFn)
# Type aliases
FrozenArgs   = tuple[Any, ...]
FrozenKwargs = frozenset[tuple[str, Any]]


def freeze_params(*args: Any, **kwargs: Any) -> tuple[FrozenArgs, FrozenKwargs]:
    return args, frozenset(kwargs.items())


def _f_full_name(f: AnyFn) -> str:
    module, qualname = f.__module__, f.__qualname__
    if module == "__main__":  # pragma: no cover
        return qualname
    return f"{module}:{qualname}"


def _desc_f_call(f: AnyFn, args: Iterable[Any], kwargs: Iterable[tuple[str, Any]]) -> str:
    params = [*map(repr, args), *[f"{k}={v!r}" for k, v in kwargs]]
    return f"{_f_full_name(f)}({', '.join(params)})"


class CallInfo(NamedTuple, Generic[_F]):
    func: _F
    args: FrozenArgs
    kwargs: FrozenKwargs
    result: Any
    success: bool

    def describe(self) -> str:
        result = f"{self.result!r}" if self.success else f"(!) {type(self.result).__qualname__} (!)"
        return f"{_desc_f_call(self.func, self.args, self.kwargs)} -> {result}"

    @override
    def __repr__(self) -> str:
        return f"<CallInfo: {self.describe()}>"


class call_info(DecoratorWithAttr[list[CallInfo[AnyFn]]]):
    """Collect detailed information about a function call."""
    ATTR: ClassVar[str] = "call_info"
    apply: bool
    log: bool
    logger: logging.Logger | None

    def __init__(self, /, *, log: bool = True, logger: logging.Logger | None = None, apply: bool = __debug__) -> None:
        super().__init__([])
        self.apply = apply
        self.log = log
        self.logger = logger

    @override
    def spec(__self__, __decorated__: AnyFn, *args: Any, **kwargs: Any) -> Any:
        """Decorator behaviour specification."""
        if __self__.log:
            (__self__.logger or logging.getLogger()).debug(
                f"-> {_desc_f_call(__decorated__, args, kwargs.items())}"
            )
        try:
            result = __decorated__(*args, **kwargs)
        except BaseException as err:
            result = err
            success = False
            raise
        except:  # pragma: no cover
            # unreachable
            assert False
        else:
            success = True
            return result
        finally:
            __self__.data.append(CallInfo(
                __decorated__,
                *freeze_params(*args, **kwargs),
                result, success
            ))

    @override
    def decorate(self, f: _F) -> _F:
        if not self.apply:
            return f
        self.logger = logging.getLogger(_f_full_name(f))
        return super().decorate(f)

    @classmethod
    @override
    def get(cls, f: _F, /) -> list[CallInfo[_F]]:  # type: ignore
        return cast(list[CallInfo[_F]], super().get(f))
