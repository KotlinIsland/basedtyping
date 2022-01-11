from typing import TypeVar

from pytest import mark

from basedtyping import ReifiedGeneric, T

T2 = TypeVar("T2")


class A(ReifiedGeneric[T]):
    pass


class B(ReifiedGeneric[T]):
    pass


class C1(A[T], B[T2], ReifiedGeneric[tuple[T, T2]]):
    pass


class C2(A[T], B[T2], ReifiedGeneric[tuple[T2, T]]):
    pass


@mark.xfail(reason="not implemented")
def test_isinstance_with_out_of_order_params() -> None:
    assert isinstance(C1[int, str](), B[str])  # type: ignore[misc]
    assert not isinstance(C1[str, int](), B[str])  # type: ignore[misc]
    assert issubclass(C1[int, str], B[str])  # type: ignore[misc]
    assert not issubclass(C1[str, int], B[str])  # type: ignore[misc]

    assert isinstance(C2[int, str](), B[str])  # type: ignore[misc]
    assert not isinstance(C2[str, int](), B[str])  # type: ignore[misc]
    assert issubclass(C2[int, str], B[str])  # type: ignore[misc]
    assert not issubclass(C2[str, int], B[str])  # type: ignore[misc]
