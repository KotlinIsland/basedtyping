from __future__ import annotations

from basedtyping import Intersection, TypeForm, Untyped


def test_basedgenericalias_intersection():
    assert TypeForm[int] & None == Intersection[TypeForm[int], None]
    assert None & TypeForm[int] == Intersection[None, TypeForm[int]]


def test_basedspecialform_intersection():
    assert Untyped & None == Intersection[Untyped, None]
    assert None & Untyped == Intersection[Untyped, None]
