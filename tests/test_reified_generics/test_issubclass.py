from __future__ import annotations

from typing import Tuple, TypeVar, Union

from pytest import mark

from basedtyping import ReifiedGeneric, T, out_T

T2 = TypeVar("T2")


class Reified(ReifiedGeneric[Tuple[T, T2]]):
    pass


# https://github.com/KotlinIsland/basedmypy/issues/5


def test_issubclass():
    assert issubclass(Reified[int, str], Reified[int, str])  # type: ignore[misc]
    assert not issubclass(Reified[int, str], Reified[int, int])  # type: ignore[misc]


def test_wrong_class_same_generics():
    class Reified2(ReifiedGeneric[Tuple[T, T2]]):
        pass

    assert not issubclass(Reified2[int, int], Reified[int, int])  # type: ignore[misc]


@mark.xfail(reason="not implemented")
def test_without_generics_first_arg_false():
    assert not issubclass(Reified, Reified[int, str])  # type: ignore[misc]


@mark.xfail(reason="not implemented")
def test_without_generics_first_arg_true():
    # https://github.com/KotlinIsland/basedtyping/issues/70
    class Foo(ReifiedGeneric[out_T]):  # type:ignore[type-var]
        pass

    assert not issubclass(Foo, Foo[object])  # type: ignore[misc]


def test_without_generics_second_arg():
    assert issubclass(Reified[int, str], Reified)


def test_without_generics_both():
    class SubReified(Reified[T, T2]):
        pass

    assert issubclass(SubReified, Reified)
    assert not issubclass(Reified, SubReified)


@mark.xfail(reason="not implemented")
def test_without_generics_same_as_bound():
    _T = TypeVar("_T", bound=Union[int, str])  # noqa: PYI018

    class Foo(ReifiedGeneric[T]):
        pass

    assert issubclass(Foo, Foo[Union[int, str]])  # type: ignore[misc]
    assert issubclass(Foo[Union[int, str]], Foo)


def test_without_generics_one_specified():
    class SubReified(Reified[int, T2]):
        pass

    assert issubclass(SubReified[str], SubReified)
