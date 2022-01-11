from typing import TypeVar

from basedtyping import ReifiedGeneric, T

U = TypeVar("U")


class Reified(ReifiedGeneric[tuple[T, U]]):
    pass


def test_true() -> None:
    assert Reified[int, str] is Reified[int, str]


def test_false() -> None:
    assert (
        Reified[int, bool] is not Reified[int, str]  # type:ignore[comparison-overlap]
    )
