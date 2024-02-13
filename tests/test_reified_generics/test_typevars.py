"""mypy should catch these, but it doesn't due to https://github.com/python/mypy/issues/7084"""

from __future__ import annotations

from typing import Generic

from pytest import raises

from basedtyping import NotReifiedError, ReifiedGeneric, T


class Reified(ReifiedGeneric[T]):
    pass


class TestTypeVars(Generic[T]):
    def test_instantiate(self):
        with raises(NotReifiedError):
            Reified[T]()

    def test_isinstance(self):
        with raises(NotReifiedError):
            isinstance(Reified[str](), Reified[T])  # type: ignore[misc]

    def test_unbound_instantiate(self):
        with raises(NotReifiedError):
            Reified[T]()

    def test_unbound_isinstance(self):
        with raises(NotReifiedError):
            isinstance(Reified[str](), Reified[T])  # type: ignore[misc]

    def test_issubclass_left(self):
        with raises(NotReifiedError):
            issubclass(Reified[T], Reified[int])  # type: ignore[misc]

    def test_issubclass_right(self):
        with raises(NotReifiedError):
            issubclass(Reified[int], Reified[T])  # type: ignore[misc]
