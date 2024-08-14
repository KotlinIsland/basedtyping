from enum import Enum
from typing import Tuple

from transformer import eval_type_based
from typing_extensions import Callable, Literal, TypeIs, Union, TypeGuard
from types import FunctionType
from basedtyping import ForwardRef, Intersection

# ruff: noqa: PYI030, PYI030


def validate(value, expected, *, string_literals=False):
    assert (
        eval_type_based(ForwardRef(value), globalns=globals(), string_literals=string_literals)
        == expected
    )


def test_literal():
    validate("1 | 2", Union[Literal[1], Literal[2]])


def test_literal_literal():
    validate("Literal[1]", Literal[1])


def test_literal_str():
    validate("'int'", int)
    validate("Literal['int']", Literal["int"])
    validate("'int'", Literal["int"], string_literals=True)
    validate("Literal['int']", Literal["int"], string_literals=True)


class E(Enum):
    a = 1
    b = 2


def test_literal_enum():
    validate("E.a | E.b", Union[Literal[E.a], Literal[E.b]])


def test_tuple():
    validate("(int, str)", Tuple[int, str])


def test_typeguard():
    validate("x is 1", TypeIs[Literal[1]])


def test_typeguard_asymmetric():
    validate("x is 1 if True else False", TypeGuard[Literal[1]])


def test_callable():
    validate("(str) -> int", Callable[[str], int])


def test_function():
    validate("def (str) -> int", Callable[[str], int])
    validate("FunctionType[[str], int]", Callable[[str], int])


def test_functiontype():
    validate("FunctionType[[str], int]", Callable[[str], int])


def test_intersection():
    validate("int & str", Intersection[int, str])


def test_nested():
    validate("(1, 2)", Tuple[Literal[1], Literal[2]])
