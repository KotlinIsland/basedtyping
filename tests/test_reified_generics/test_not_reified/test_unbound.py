"""mypy should catch these, but it doesn't due to https://github.com/python/mypy/issues/7084"""
from pytest import raises

from basedtyping import ReifiedGeneric, T, UnboundTypeVarError


class Reified(ReifiedGeneric[T]):
    pass


def test_instanciate() -> None:
    with raises(UnboundTypeVarError):
        Reified[T]()


def test_isinstance() -> None:
    with raises(UnboundTypeVarError):
        isinstance(Reified[str](), Reified[T])  # type:ignore[misc]
