"""mypy should catch these, but it doesn't due to https://github.com/python/mypy/issues/7084"""

from __future__ import annotations

from pytest import fixture, raises

from basedtyping import NotReifiedError, ReifiedGeneric, T


class Reified(ReifiedGeneric[T]):
    pass


@fixture  # type: ignore[no-any-expr]
def _value() -> int:
    return 1


def test_instantiate(_value: T) -> None:
    with raises(NotReifiedError):
        Reified[T]()


def test_isinstance(_value: T) -> None:
    with raises(NotReifiedError):
        isinstance(Reified[str](), Reified[T])  # type: ignore[misc]


def test_unbound_instantiate(_value: T) -> None:
    with raises(NotReifiedError):
        Reified[T]()


def test_unbound_isinstance(_value: T) -> None:
    with raises(NotReifiedError):
        isinstance(Reified[str](), Reified[T])  # type: ignore[misc]


def test_issubclass_left(_value: T) -> None:
    with raises(NotReifiedError):
        issubclass(Reified[T], Reified[int])  # type: ignore[misc]


def test_issubclass_right(_value: T) -> None:
    with raises(NotReifiedError):
        issubclass(Reified[int], Reified[T])  # type: ignore[misc]
