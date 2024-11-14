from __future__ import annotations

import sys
from enum import Enum
from types import FunctionType  # noqa: F401
from typing import Dict, List, Tuple, cast
from unittest import skipIf

from pytest import raises
from typing_extensions import Annotated, Callable, Literal, TypeGuard, TypeIs, Union

from basedtyping import ForwardRef, Intersection
from basedtyping.transformer import eval_type_based

# ruff: noqa: PYI030 the unions of literals are an artifact of the implementation, they have no bearing on anything practical


def validate(value: str, expected: object, *, string_literals=False):
    assert (
        eval_type_based(
            ForwardRef(value),
            globalns=cast(Dict[str, object], globals()),
            string_literals=string_literals,
        )
        == expected
    )


@skipIf(sys.version_info <= (3, 10), "unsupported")  # type: ignore[no-any-expr]
def test_literal():
    validate("1 | 2", Union[Literal[1], Literal[2]])


def test_negative():
    validate("-1", Literal[-1])
    validate("+1", Literal[1])


def test_literal_union():
    validate("Union[1, 2]", Union[Literal[1], Literal[2]])


def test_literal_literal():
    validate("Literal[1]", Literal[1])


def test_literal_nested():
    validate("(1, 2)", Tuple[Literal[1], Literal[2]])
    validate("List[(1, 2),]", List[Tuple[Literal[1], Literal[2]]])


def test_literal_str_forwardref():
    validate("'1'", Literal[1])
    validate("Literal['1']", Literal["1"])


def test_literal_str_literal():
    validate("'1'", Literal["1"], string_literals=True)
    validate("Literal['1']", Literal["1"], string_literals=True)


class E(Enum):
    a = 1
    b = 2


@skipIf(sys.version_info <= (3, 10), "unsupported")  # type: ignore[no-any-expr]
def test_literal_enum():
    validate("E.a | E.b", Union[Literal[E.a], Literal[E.b]])


def test_literal_enum_union():
    validate("Union[E.a, E.b]", Union[Literal[E.a], Literal[E.b]])


def test_tuple():
    validate("(int, str)", Tuple[int, str])


def test_tuple_nested():
    validate("List[(int, str),]", List[Tuple[int, str]])


def test_typeguard():
    validate("x is 1", TypeIs[Literal[1]])


def test_typeguard_asymmetric():
    validate("x is 1 if True else False", TypeGuard[Literal[1]])


def test_callable():
    validate("(str) -> int", Callable[[str], int])


def test_function():
    validate("def (str) -> int", Callable[[str], int])
    validate("FunctionType[[str], int]", Callable[[str], int])


def_ = int


def test_adversarial_function():
    validate("Union[def_, '() -> int']", Union[def_, Callable[[], int]])


def test_functiontype():
    validate("FunctionType[[str], int]", Callable[[str], int])


def test_intersection():
    validate("int & str", Intersection[int, str])


def test_annotated():
    validate("Annotated[1, 1]", Annotated[Literal[1], 1])


def test_syntax_error():
    with raises(SyntaxError):
        validate("among us", None)


def test_unsupported():
    with raises(TypeError):
        validate("int + str", None)
