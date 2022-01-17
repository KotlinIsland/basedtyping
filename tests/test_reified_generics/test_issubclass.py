from typing import TypeVar

from pytest import mark

from basedtyping import ReifiedGeneric, T

T2 = TypeVar("T2")


class Reified(ReifiedGeneric[tuple[T, T2]]):
    pass


class SubReified(Reified[T, T2]):
    pass


# https://github.com/KotlinIsland/basedmypy/issues/5


def test_issubclass() -> None:
    assert issubclass(Reified[int, str], Reified[int, str])  # type: ignore[misc]
    assert not issubclass(Reified[int, str], Reified[int, int])  # type: ignore[misc]


def test_wrong_class_same_generics() -> None:
    class Reified2(ReifiedGeneric[tuple[T, T2]]):
        pass

    assert not issubclass(Reified2[int, int], Reified[int, int])  # type: ignore[misc]


@mark.xfail(reason="not implemented")
def test_without_generics_first_arg() -> None:
    assert not issubclass(Reified, Reified[int, str])  # type: ignore[misc]


def test_without_generics_second_arg() -> None:
    assert issubclass(Reified[int, str], Reified)


def test_without_generics_both() -> None:
    assert issubclass(SubReified, Reified)
    assert not issubclass(Reified, SubReified)


@mark.xfail(reason="not implemented")
def test_without_generics_same_as_bound() -> None:
    _T = TypeVar("_T", bound=int | str)

    class Foo(ReifiedGeneric[T]):
        pass

    assert issubclass(Foo, Foo[int | str])  # type: ignore[misc]
    assert issubclass(Foo[int | str], Foo)
