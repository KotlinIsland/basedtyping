from typing import Generic, TypeVar

from basedtyping.generics import T
from basedtyping.reified_generic import ReifiedGeneric

T2 = TypeVar("T2")


class Reified(ReifiedGeneric[tuple[T, T2]]):
    ...


class ReifiedList(list[T], ReifiedGeneric[tuple[T]]):
    ...


class Normal(Generic[T, T2]):
    ...


def test_args_and_params() -> None:
    assert (
        Normal[int, str].__args__  # type:ignore[attr-defined,misc]
        == Reified[int, str].__args__
    )
    assert (
        Normal[int, str].__origin__.__parameters__  # type:ignore[attr-defined,misc]
        == Reified[int, str].__origin__.__parameters__  # type:ignore[attr-defined,misc]
    )


def test_reified_list() -> None:
    it = ReifiedList[int]([1, 2, 3]).__orig_class__
    assert it.__orig_bases__[0].__origin__ == list  # type:ignore[attr-defined,misc]
    assert it.__args__ == (int,)
    assert it.__parameters__ == ()


# https://github.com/KotlinIsland/basedmypy/issues/5
def test_isinstance() -> None:
    assert isinstance(Reified[int, str](), Reified[int, str])  # type:ignore[misc]
    assert not isinstance(Reified[int, str](), Reified[int, int])  # type:ignore[misc]


def test_issubclass() -> None:
    assert issubclass(Reified[int, str], Reified[int, str])  # type:ignore[misc]
    assert not issubclass(Reified[int, str], Reified[int, int])  # type:ignore[misc]
