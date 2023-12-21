from __future__ import annotations

from basedtyping import T, generic


def test_generic():
    @generic
    def f(t: T) -> T:
        return t

    assert f[object](1) == 1


def test_generic_with_args():
    deco = generic[T]

    @deco  # Python version 3.8 does not support arbitrary expressions as a decorator
    def f(t: T) -> T:
        return t

    assert f[object](1) == 1
