from __future__ import annotations

import sys

import pytest

from basedtyping import Intersection, TypeForm, Untyped


def test_basedgenericalias_intersection():
    assert TypeForm[int] & None == Intersection[TypeForm[int], None]
    assert None & TypeForm[int] == Intersection[None, TypeForm[int]]


@pytest.mark.xfail(
    sys.version_info >= (3, 9),
    reason="""
`typing._type_check` says:

    if arg in (Any, LiteralString, NoReturn, Never, Self, TypeAlias):
        return arg
""",
)
def test_basedspecialform_intersection():
    assert Untyped & None == Intersection[Untyped, None]  # type: ignore[no-any-expr]
    assert None & Untyped == Intersection[Untyped, None]  # type: ignore[no-any-expr]
