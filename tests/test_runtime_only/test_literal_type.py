from __future__ import annotations

from typing import Union


def test_literal_type_positive():
    from typing import Literal

    from basedtyping.runtime_only import LiteralType

    assert isinstance(Literal[1, 2], LiteralType)


def test_literal_type_negative():
    from basedtyping.runtime_only import LiteralType

    assert not isinstance(Union[int, str], LiteralType)
