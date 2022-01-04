"""mypy should catch these, but it doesn't due to https://github.com/python/mypy/issues/7084"""
from pytest import raises

from basedtyping import MissingTypeParametersError, ReifiedGeneric, T


class Reified(ReifiedGeneric[T]):
    pass


def test_instanciate() -> None:
    with raises(MissingTypeParametersError):
        Reified[T]()


def test_isinstance() -> None:
    with raises(MissingTypeParametersError):
        isinstance(Reified[str](), Reified[T])  # type:ignore[misc]
