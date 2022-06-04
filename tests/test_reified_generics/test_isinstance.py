from typing import Tuple, TypeVar

from pytest import mark

from basedtyping import ReifiedGeneric, T

T2 = TypeVar("T2")


class Reified(ReifiedGeneric[Tuple[T, T2]]):
    pass


class Reified2(ReifiedGeneric[Tuple[T, T2]]):
    pass


@mark.xfail(reason="not implemented")
def test_isinstance_with_out_of_order_params() -> None:
    class A(ReifiedGeneric[T]):
        pass

    class B(ReifiedGeneric[T]):
        pass

    class C1(A[T], B[T2], ReifiedGeneric[Tuple[T, T2]]):
        pass

    class C2(A[T], B[T2], ReifiedGeneric[Tuple[T2, T]]):
        pass

    assert isinstance(C1[int, str](), B[str])  # type: ignore[misc]
    assert not isinstance(C1[str, int](), B[str])  # type: ignore[misc]
    assert issubclass(C1[int, str], B[str])  # type: ignore[misc]
    assert not issubclass(C1[str, int], B[str])  # type: ignore[misc]

    assert isinstance(C2[int, str](), B[str])  # type: ignore[misc]
    assert not isinstance(C2[str, int](), B[str])  # type: ignore[misc]
    assert issubclass(C2[int, str], B[str])  # type: ignore[misc]
    assert not issubclass(C2[str, int], B[str])  # type: ignore[misc]


def test_isinstance() -> None:
    # https://github.com/KotlinIsland/basedmypy/issues/5
    assert isinstance(Reified[int, str](), Reified[int, str])  # type: ignore[misc]
    assert not isinstance(Reified[int, str](), Reified[int, int])  # type: ignore[misc]


def test_without_generics_true() -> None:
    assert isinstance(Reified[int, str](), Reified)


def test_without_generics_false() -> None:
    assert not isinstance(Reified[int, str](), Reified2)


def test_without_generics_one_specified() -> None:
    class SubReified(Reified[int, T2]):
        pass

    assert isinstance(SubReified[str](), SubReified)
