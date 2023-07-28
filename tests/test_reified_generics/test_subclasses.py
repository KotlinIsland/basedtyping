from typing import List, Tuple, TypeVar

from pytest import raises

from basedtyping import NotReifiedError, ReifiedGeneric, T

T2 = TypeVar("T2")

no_parameters_error_match = "Cannot instantiate ReifiedGeneric "


class Reified(ReifiedGeneric[Tuple[T, T2]]):
    pass


# TODO: investigate this "metaclass conflict" mypy error
class ReifiedList(ReifiedGeneric[Tuple[T]], List[T]):  # type:ignore[misc]
    pass


def test_subclass() -> None:
    class SubReified1(Reified[T, T2]):
        pass

    class SubReified2(Reified[T, T2], ReifiedGeneric[Tuple[T, T2]]):
        pass

    with raises(NotReifiedError, match=no_parameters_error_match):
        SubReified1()
    with raises(NotReifiedError, match=no_parameters_error_match):
        SubReified2()
    s = SubReified2[int, str]()
    assert isinstance(s, Reified[int, str])  # type: ignore[misc]
    assert not isinstance(s, Reified[str, int])  # type: ignore[misc]


def test_subclass_one_generic_specified() -> None:
    class SubReified(Reified[int, T2]):
        pass

    assert SubReified[str]().__reified_generics__ == (int, str)
