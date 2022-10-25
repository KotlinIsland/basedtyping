import sys
from typing import Union

import pytest


@pytest.mark.skipif(sys.version_info < (3, 9))
def test_literal_type_positive() -> None:
    from typing import Literal

    from basedtyping.runtime_only import LiteralType

    assert isinstance(Literal[1, 2], LiteralType)


@pytest.mark.skipif(sys.version_info < (3, 9))
def test_literal_type_negative() -> None:
    from basedtyping.runtime_only import LiteralType

    assert not isinstance(Union[int, str], LiteralType)
