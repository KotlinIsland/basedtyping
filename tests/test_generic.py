from __future__ import annotations

import sys
from typing import Callable, cast

import pytest

from basedtyping import T, generic


def test_generic_with_args():
    deco = generic[T]

    @deco  # Python version 3.8 does not support arbitrary expressions as a decorator
    def f(t: T) -> T:
        return t

    assert f.__type_params__ == (T,)
    assert f[int].__type_args__ == (int,)
    assert f[object](1) == 1


def test_generic_without_args():
    # not using a decorator because of mypy
    if sys.version_info < (3, 12):
        pytest.skip(reason="Needs generic syntax support")
    local: dict[str, object] = {}
    # Can't use the actual function because then <3.12 wouldn't load
    exec("def f[T](t: T) -> T: return t", None, local)
    _f = cast(Callable[[object], object], local["f"])
    f = generic(_f)

    assert f.__type_params__ == _f.__type_params__  # type: ignore[attr-defined, unused-ignore]
    assert f[int].__type_args__ == (int,)
    assert f[int](1) == 1
