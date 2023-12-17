from ast import parse, unparse
from enum import Enum, auto

from pytest import fixture, mark

from basedtyping.runtime_only import get_type_hints
import basedtyping
from runtime_only import BasedTypeParser
import typing


class E(Enum):
    a = auto()


@fixture(scope="session")
def hints():
    class A:
        a: "int & str"
        b: "1"
        e: "E.a"

    yield get_type_hints(A)


def test_get_intersection(hints):
    a = hints["a"]
    assert isinstance(a, basedtyping._IntersectionGenericAlias)
    assert a.__args__ == (int, str)


def test_get_literal(hints):
    b = hints["b"]
    assert isinstance(b, typing._LiteralGenericAlias)
    assert b.__args__ == (1,)


@mark.xfail(condition=True, reason="this isn't implemented")
def test_get_literal_enum(hints):
    e = hints["e"]
    assert isinstance(e, typing._LiteralGenericAlias)
    assert e.__args__ == (E.a,)


def process(value):
    return unparse(parser.visit(parse(value)))


parser = BasedTypeParser()
bprefix = "__basedsecret__"
prefix = "__secret__"


def test_intersection():
    assert process("int & str") == f"{bprefix}.Intersection[int, str]"


def test_literal():
    assert process("1 | 2") == f"{prefix}.Literal[1] | {prefix}.Literal[2]"


def test_tuple():
    assert process("(int, str)") == f"{prefix}.Tuple[int, str]"


def test_tuple():
    assert process("(int, str)") == f"{prefix}.Tuple[int, str]"


def test_subscript():
    """To ensure tuple expressions within a subscript don't get interpreted as tuple literals"""
    assert process("a[b, c]") == "a[b, c]"


@mark.xfail(condition=True, reason="Not implemented")
def test_implicit():
    class A:
        a: "Literal[1]"

    result = get_type_hints(A, implicit=True)["a"]
    assert isinstance(result, typing._LiteralGenericAlias)
    assert result.__args__ == (1,)
