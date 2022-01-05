from typing import Generic, TypeVar

from _pytest.fixtures import FixtureRequest
from pytest import fixture, mark

from basedtyping import ReifiedGeneric, T

T2 = TypeVar("T2")


class A(ReifiedGeneric[T]):
    pass


class B(ReifiedGeneric[T]):
    pass


class C1(A[T], B[T2], ReifiedGeneric[tuple[T, T2]]):
    pass


class C2(A[T], B[T2], ReifiedGeneric[tuple[T, T2]]):
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


@fixture  # type: ignore[misc]
def a() -> object:
    """Defined like this so that it will fail during execution, not during collection"""

    class SubASpecified1(A[int], ReifiedGeneric[int]):
        pass

    return SubASpecified1


@fixture  # type: ignore[misc]
def b() -> object:
    """Defined like this so that it will fail during execution, not during collection"""

    class SubASpecified2(A[int]):
        pass

    return SubASpecified2


@fixture(params=["a", "b"])
def concrete_subclass(request: FixtureRequest) -> object:
    """Defined like this so that it will fail during execution, not during collection"""

    return request.getfuncargvalue(request.param)  # type: ignore[misc, attr-defined]


@mark.xfail(reason="not implemented")
def test_concrete_subclass(
    concrete_subclass: type[A[int]],  # pylint: disable=redefined-outer-name
) -> None:
    S = concrete_subclass
    assert S.mro() == [
        S,
        A[int],
        ReifiedGeneric,
        Generic,
        object,
    ]
    assert issubclass(S, A[int])  # type: ignore[misc]
    assert not isinstance(S, A[str])  # type: ignore[misc]

    s = S()
    assert isinstance(s, A[int])  # type: ignore[misc]
    assert not isinstance(s, A[str])  # type: ignore[misc, unreachable]


@mark.xfail(reason="not implemented")
def test_reified_during_init() -> None:
    class Reified(ReifiedGeneric[T]):
        def __init__(self) -> None:  # pylint: disable=super-init-not-called
            assert self.__orig_class__.__args__ == (int,)

    Reified[int]()
