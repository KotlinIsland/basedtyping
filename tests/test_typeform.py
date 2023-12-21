from __future__ import annotations

from basedtyping import TypeForm


class A:
    x: int


class B:
    y: int


def test_typeform():
    assert str(TypeForm[A]) == f"basedtyping.TypeForm[{A.__module__}.{A.__qualname__}]"
