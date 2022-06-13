import sys
from typing import Union

from basedtyping.runtime_only import OldUnionType


def test_old_union() -> None:
    assert isinstance(Union[int, str], OldUnionType)


def test_new_union() -> None:
    if sys.version_info >= (3, 10):
        assert not isinstance(int | str, OldUnionType)
