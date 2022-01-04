"""mypy should catch these, but it doesn't due to https://github.com/python/mypy/issues/7084"""
from typing import TypeVar

from pytest import raises

from basedtyping import MissingTypeParametersError, ReifiedGeneric, T


class Reified(ReifiedGeneric[T]):
    pass


def test_instanciate() -> None:
    def function(_value: T) -> None:
        with raises(MissingTypeParametersError):
            Reified[T]()

    function(1)


def test_isinstance() -> None:
    def function(_value: T) -> None:
        with raises(MissingTypeParametersError):
            isinstance(Reified[str](), Reified[T])  # type:ignore[misc]

    function("")


def test_not_enough_type_params() -> None:
    """mypy does catch this one"""
    U = TypeVar("U")

    class Reified2(ReifiedGeneric[tuple[T, U]]):
        pass

    def function(_value: T) -> None:
        with raises(TypeError):
            Reified2[int]()  # type:ignore[misc]

    function("")
