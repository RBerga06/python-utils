#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mypy: ignore-errors
"""Retrieve detailed information about function calls."""
from typing import Any, ClassVar, Generic, NamedTuple, TypeVar, cast
from typing_extensions import override
from .dec import AnyFn, DecoratorWithAttr
from .info import CallInfo

# Type variables
_F = TypeVar("_F", bound=AnyFn)
# Type aliases
FrozenArgs = tuple[Any, ...]
FrozenKwargs = frozenset[tuple[str, Any]]


def freeze_params(*args: Any, **kwargs: Any) -> tuple[FrozenArgs, FrozenKwargs]:
    return args, frozenset(kwargs.items())


class CallInfo(NamedTuple, Generic[_F]):
    func: _F
    args: FrozenArgs
    kwargs: FrozenKwargs
    result: Any
    success: bool


class call_info(DecoratorWithAttr[list[CallInfo[AnyFn]]]):
    ATTR: ClassVar[str] = "call_info"

    def __init__(self, /) -> None:
        super().__init__([])

    @override
    def spec(__self__, __decorated__: AnyFn, *args: Any, **kwargs: Any) -> Any:
        """Decorator behaviour specification."""
        try:
            result = __decorated__(*args, **kwargs)
        except BaseException as err:
            result = err
            success = False
            raise
        except:
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

    @classmethod
    @override
    def get(cls, f: _F, /) -> list[CallInfo[_F]]:  # type: ignore
        return cast(list[CallInfo[_F]], super().get(f))
