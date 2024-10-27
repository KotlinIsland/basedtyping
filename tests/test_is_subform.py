from __future__ import annotations

import sys
from typing import Union

from basedtyping import issubform


def test_normal():
    if sys.version_info >= (3, 10):
        assert issubform(int, int | str)


def test_union_first_arg():
    if sys.version_info >= (3, 10):
        assert not issubform(int | str, int)
        assert issubform(int | str, object)
        assert issubform(int | str, int | str)
        assert issubform(int | str, Union[int, str])  # type: ignore[unused-ignore, arg-type]


def test_old_union():
    assert not issubform(Union[int, str], int)
    assert issubform(Union[int, str], object)
    assert issubform(Union[int, str], Union[str, int])
    if sys.version_info >= (3, 10):
        assert issubform(
            Union[int, str],
            int | str,  # type: ignore[unused-ignore, arg-type]
        )
