"""mypy should catch these, but it doesn't due to https://github.com/python/mypy/issues/7084"""
from pytest import fixture, raises

from basedtyping import NotReifiedParameterError, ReifiedGeneric, T


class Reified(ReifiedGeneric[T]):
    pass


@fixture  # type: ignore[misc]
def _value() -> int:
    return 1


def test_instantiate(_value: T) -> None:
    with raises(NotReifiedParameterError):
        Reified[T]()


def test_isinstance(_value: T) -> None:
    with raises(NotReifiedParameterError):
        isinstance(Reified[str](), Reified[T])  # type: ignore[misc]


def test_unbound_instantiate() -> None:
    with raises(NotReifiedParameterError):
        Reified[T]()


def test_unbound_isinstance() -> None:
    with raises(NotReifiedParameterError):
        isinstance(Reified[str](), Reified[T])  # type: ignore[misc]


def test_issubclass_left(_value: T) -> None:
    with raises(NotReifiedParameterError):
        issubclass(Reified[T], Reified[int])  # type: ignore[misc]


def test_issubclass_right(_value: T) -> None:
    with raises(NotReifiedParameterError):
        issubclass(Reified[int], Reified[T])  # type: ignore[misc]
