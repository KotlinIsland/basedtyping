from pytest import raises

from basedtyping import MissingTypeParametersError, ReifiedGeneric, T


class Reified(ReifiedGeneric[T]):
    pass


def test_other() -> None:
    with raises(MissingTypeParametersError):
        issubclass(Reified[T], Reified[int])  # type:ignore[misc]


def test_self() -> None:
    with raises(MissingTypeParametersError):
        issubclass(Reified[int], Reified[T])  # type:ignore[misc]
