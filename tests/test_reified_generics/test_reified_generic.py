from types import NoneType
from typing import Generic, TypeVar

from pytest import raises

from basedtyping import NotReifiedError, ReifiedGeneric, T

T2 = TypeVar("T2")


class Reified(ReifiedGeneric[tuple[T, T2]]):
    pass


class ReifiedList(ReifiedGeneric[tuple[T]], list[T]):
    pass


class Normal(Generic[T, T2]):
    pass


no_parameters_error_match = "Cannot instantiate ReifiedGeneric "
not_reified_parameter_error_match = "TypeVars cannot be used"


def test_class_args_and_params_class() -> None:
    assert (
        Normal[int, str].__args__  # type: ignore[attr-defined,misc]
        == Reified[int, str].__reified_generics__
    )
    assert (
        Normal[int, str].__parameters__  # type: ignore[attr-defined,misc]
        == Reified[int, str].__type_vars__
    )


def test_class_args_and_params_instance() -> None:
    assert Reified[int, str]().__reified_generics__ == (int, str)
    assert not Reified[int, str]().__type_vars__


def test_reified_list() -> None:
    it = ReifiedList[int]([1, 2, 3])
    assert it.__reified_generics__ == (int,)
    assert not it.__type_vars__


# https://github.com/KotlinIsland/basedmypy/issues/5
def test_isinstance() -> None:
    assert isinstance(Reified[int, str](), Reified[int, str])  # type: ignore[misc]
    assert not isinstance(Reified[int, str](), Reified[int, int])  # type: ignore[misc]


def test_issubclass() -> None:
    assert issubclass(Reified[int, str], Reified[int, str])  # type: ignore[misc]
    assert not issubclass(Reified[int, str], Reified[int, int])  # type: ignore[misc]


def test_reified_generic_without_generic_alias() -> None:
    with raises(NotReifiedError, match=no_parameters_error_match):
        Reified()


def test_subclass() -> None:
    class SubReified1(Reified[T, T2]):
        pass

    class SubReified2(Reified[T, T2], ReifiedGeneric[tuple[T, T2]]):
        pass

    with raises(NotReifiedError, match=no_parameters_error_match):
        SubReified1()
    with raises(NotReifiedError, match=no_parameters_error_match):
        SubReified2()
    s = SubReified2[int, str]()
    assert isinstance(s, Reified[int, str])  # type: ignore[misc]
    assert not isinstance(s, Reified[str, int])  # type: ignore[misc]


def unsupported_concrete_subclass() -> None:
    with raises(NotImplementedError):

        class Sub(Reified[int, str]):  # pylint:disable=unused-variable
            pass


def test_reified_in_init() -> None:
    class Foo(ReifiedGeneric[T]):
        def __init__(self) -> None:
            assert self.__reified_generics__ == (int,)

    Foo[int]()
    assert not hasattr(Foo, "__orig_class__")


def test_concrete_subclass() -> None:
    class A(ReifiedGeneric[T]):
        pass

    class SubASpecified(A[int]):
        pass

    print(SubASpecified.mro())
    assert issubclass(SubASpecified, A[int])  # type: ignore[misc]
    assert not issubclass(SubASpecified, A[str])  # type: ignore[misc]

    s = SubASpecified()
    assert isinstance(s, A[int])  # type: ignore[misc]
    assert not isinstance(s, A[str])  # type: ignore[misc]
