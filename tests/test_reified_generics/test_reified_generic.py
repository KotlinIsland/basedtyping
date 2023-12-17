from __future__ import annotations

from typing import TYPE_CHECKING, Generic, List, Tuple, TypeVar

from pytest import raises

from basedtyping import NotReifiedError, ReifiedGeneric, T

T2 = TypeVar("T2")

NoneType = type(None)


class Reified(ReifiedGeneric[Tuple[T, T2]]):
    pass


# TODO: investigate this "metaclass conflict" mypy error
class ReifiedList(ReifiedGeneric[Tuple[T]], List[T]):  # type:ignore[misc]
    pass


class Normal(Generic[T, T2]):
    pass


not_reified_parameter_error_match = "TypeVars cannot be used"


def test_class_args_and_params_class():
    assert (
        Normal[int, str].__args__  # type: ignore[attr-defined]
        == Reified[int, str].__reified_generics__
    )
    assert (
        Normal[int, str].__parameters__  # type: ignore[attr-defined]
        == Reified[int, str].__type_vars__
    )


def test_class_args_and_params_instance():
    assert Reified[int, str]().__reified_generics__ == (int, str)
    assert not Reified[int, str]().__type_vars__


def test_reified_list():
    it = ReifiedList[int]([1, 2, 3])
    assert it.__reified_generics__ == (int,)
    assert not it.__type_vars__


def test_reified_generic_without_generic_alias():
    with raises(NotReifiedError, match="Cannot instantiate ReifiedGeneric "):
        Reified()


def test_reified_in_init():
    class Foo(ReifiedGeneric[T]):
        def __init__(self):
            assert self.__reified_generics__ == (int,)

    Foo[int]()


def test_concrete_subclass():
    class A(ReifiedGeneric[T]):
        pass

    class SubASpecified(A[int]):
        pass

    assert issubclass(SubASpecified, A[int])  # type: ignore[misc]
    assert not issubclass(SubASpecified, A[str])  # type: ignore[misc]

    s = SubASpecified()
    assert isinstance(s, A[int])  # type: ignore[misc]
    assert not isinstance(s, A[str])  # type: ignore[misc]


def test_none_type():
    # TODO: is this mypy error correct?
    assert Reified[None, None].__reified_generics__ == (
        NoneType,
        NoneType,
    )  # type:ignore[comparison-overlap]


if TYPE_CHECKING:
    # this is just a type-time test, not a real life pytest test. it's only run by mypy
    from typing_extensions import assert_type

    def test_reified_generic_subtype_self():
        """make sure that the generic in the metaclass doesn't break instance types, and that
        the `Self` type works properly on the metaclass"""

        class Subtype(Reified[int, int]):
            pass

        assert_type(Subtype(), Subtype)
