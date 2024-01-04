from __future__ import annotations

from basedtyping import SpecialForm


class A:
    x: int


class B:
    y: int


def test_typeform():
    assert str(SpecialForm[Union[A, B]]) == f"basedtyping.TypeForm[Union[{A.__module__}.{A.__qualname__}, {B.__module__}.{B.__qualname__}]]"
