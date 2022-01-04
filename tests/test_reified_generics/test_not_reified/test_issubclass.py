from pytest import raises

from basedtyping import ReifiedGeneric, T, UnboundTypeVarError


class Reified(ReifiedGeneric[T]):
    pass


def test_other() -> None:
    with raises(UnboundTypeVarError):
        issubclass(Reified[T], Reified[int])  # type:ignore[misc]


def test_self() -> None:
    with raises(UnboundTypeVarError):
        issubclass(Reified[int], Reified[T])  # type:ignore[misc]