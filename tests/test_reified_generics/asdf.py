from __future__ import annotations

from typing import Tuple, TypeVar

from basedtyping import ReifiedGeneric, T

U = TypeVar("U")
V = TypeVar("V")


class Foo(ReifiedGeneric[Tuple[T, U, V]]):
    def __init__(self) -> None:
        print(self.__reified_generics__)


class Bar(Foo[int, U, None]):
    pass


Bar[str]()
