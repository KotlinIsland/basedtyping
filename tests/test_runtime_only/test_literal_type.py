import sys

if sys.version_info >= (3, 8):
    from typing import Literal, Union

    from basedtyping.runtime_only import LiteralType

    def test_literal_type_positive() -> None:
        assert isinstance(Literal[1, 2], LiteralType)

    def test_literal_type_negative() -> None:
        assert not isinstance(Union[int, str], LiteralType)
