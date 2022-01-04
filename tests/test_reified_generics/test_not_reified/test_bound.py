"""mypy should catch these, but it doesn't due to https://github.com/python/mypy/issues/7084"""
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
