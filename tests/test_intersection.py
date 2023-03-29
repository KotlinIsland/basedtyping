from basedtyping import Intersection


class A:
    x: int


class B:
    y: int


def test_intersection() -> None:
    assert (
        str(Intersection[A, B])
        == f"basedtyping.Intersection[{A.__module__}.{A.__qualname__},"
        f" {B.__module__}.{B.__qualname__}]"
    )
