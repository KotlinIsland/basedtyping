from typing import Generic, TypeVar

from pytest import raises

from basedtyping import NoParametersError, ReifiedGeneric, T

T2 = TypeVar("T2")


class Reified(ReifiedGeneric[tuple[T, T2]]):
    pass


class ReifiedList(ReifiedGeneric[tuple[T]], list[T]):
    pass


class Normal(Generic[T, T2]):
    pass


def test_class_args_and_params_class() -> None:
    assert (
        Normal[int, str].__args__  # type: ignore[attr-defined,misc]
        == Reified[int, str].__args__
    )
    assert (
        Normal[int, str].__origin__.__parameters__  # type: ignore[attr-defined,misc]
        == Reified[int, str].__origin__.__parameters__  # type: ignore[attr-defined,misc]
    )


def test_class_args_and_params_instance() -> None:
    assert (
        Normal[int, str]().__orig_class__.__args__  # type: ignore[attr-defined,misc]
        == Reified[int, str]().__orig_class__.__args__
    )
    assert (
        Normal[int, str]().__orig_class__.__origin__.__parameters__  # type: ignore[attr-defined,misc]
        == Reified[int, str]().__orig_class__.__origin__.__parameters__  # type: ignore[attr-defined,misc]
    )


def test_reified_list() -> None:
    it = ReifiedList[int]([1, 2, 3]).__orig_class__
    assert it.__origin__ == ReifiedList  # type: ignore[attr-defined,misc]
    assert it.__args__ == (int,)
    assert it.__parameters__ == ()


# https://github.com/KotlinIsland/basedmypy/issues/5
def test_isinstance() -> None:
    assert isinstance(Reified[int, str](), Reified[int, str])  # type: ignore[misc]
    assert not isinstance(Reified[int, str](), Reified[int, int])  # type: ignore[misc]


def test_issubclass() -> None:
    assert issubclass(Reified[int, str], Reified[int, str])  # type: ignore[misc]
    assert not issubclass(Reified[int, str], Reified[int, int])  # type: ignore[misc]


def test_reified_generic_without_generic_alias() -> None:
    with raises(NoParametersError):
        Reified()  # pylint:disable=no-value-for-parameter


def test_subclass() -> None:
    class SubReified1(Reified[T, T2]):
        pass

    class SubReified2(Reified[T, T2], ReifiedGeneric[tuple[T, T2]]):
        pass

    with raises(NoParametersError):
        SubReified1()
    with raises(NoParametersError):
        SubReified2()
    s = SubReified2[int, str]()
    assert isinstance(s, Reified[int, str])  # type: ignore[misc]
    assert not isinstance(s, Reified[str, int])  # type: ignore[misc]


def unsupported_concrete_subclass() -> None:
    with raises(NotImplementedError):

        class Sub(Reified[int, str]):
            pass


def test_reified_in_init() -> None:
    class Foo(ReifiedGeneric[T]):
        # https://github.com/PyCQA/pylint/issues/5637
        def __init__(self) -> None:  # pylint:disable=super-init-not-called
            assert self.__orig_class__.__args__ == (int,)

    Foo[int]()
    assert not hasattr(Foo, "__orig_class__")
