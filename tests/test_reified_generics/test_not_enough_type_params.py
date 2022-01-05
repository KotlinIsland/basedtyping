from typing import TypeVar

from pytest import raises

from basedtyping import ReifiedGeneric, T

U = TypeVar("U")


class Reified2(ReifiedGeneric[tuple[T, U]]):
    pass


def test_not_enough_type_params() -> None:
    with raises(TypeError):
        Reified2[int]()  # type: ignore[misc]
