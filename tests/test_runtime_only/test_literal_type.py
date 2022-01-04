from typing import Literal, Union

from basedtyping.runtime_only import LiteralType


def test_true() -> None:
    assert isinstance(Literal[1, 2], LiteralType)


def test_false() -> None:
    assert not isinstance(Union[int, str], LiteralType)
