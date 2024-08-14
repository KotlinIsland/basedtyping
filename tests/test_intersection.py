from __future__ import annotations

import pickle

from basedtyping import Intersection


class A:
    x: int


class B:
    y: int


class C(A, B):
    ...


value = Intersection[A, B]
other = Intersection[A, int]


def test_intersection():
    assert (
        str(value) == f"basedtyping.Intersection[{A.__module__}.{A.__qualname__},"
        f" {B.__module__}.{B.__qualname__}]"
    )


def test_intersection_eq():
    assert value == value  # noqa: PLR0124 we are testing __eq__
    assert value != other


def test_intersection_eq_hash():
    assert hash(value) == hash(value)
    assert hash(value) != other  # type: ignore[comparison-overlap]


def test_intersection_instancecheck():
    assert isinstance(C(), value)  # type: ignore[arg-type, misc]
    assert not isinstance(A(), value)  # type: ignore[arg-type, misc]
    assert not isinstance(B(), value)  # type: ignore[arg-type, misc]


def test_intersection_subclasscheck():
    assert issubclass(C, value)  # type: ignore[arg-type, misc]
    assert not issubclass(A, value)  # type: ignore[arg-type, misc]
    assert not issubclass(B, value)  # type: ignore[arg-type, misc]


def test_intersection_reduce():
    pickled = pickle.dumps(value)
    loaded = pickle.loads(pickled)  # type: ignore[no-any-expr]
    assert loaded is value  # type: ignore[no-any-expr]
    assert loaded is not other  # type: ignore[no-any-expr]
