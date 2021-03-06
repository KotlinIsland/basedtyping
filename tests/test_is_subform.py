import sys
from typing import Union

from basedtyping import issubform


def test_normal() -> None:
    if sys.version_info >= (3, 10):
        assert issubform(int, int | str)


def test_union_first_arg() -> None:
    if sys.version_info >= (3, 10):
        assert not issubform(int | str, int)
        assert issubform(int | str, object)
        assert issubform(int | str, int | str)
        assert issubform(int | str, Union[int, str])  # type: ignore[unused-ignore, arg-type]


def test_old_union() -> None:
    # TODO: fix the mypy error
    assert not issubform(
        Union[int, str],  # type: ignore[arg-type]
        int,
    )
    assert issubform(
        Union[int, str],  # type: ignore[arg-type]
        object,
    )
    assert issubform(
        Union[int, str],  # type: ignore[arg-type]
        Union[str, int],  # type: ignore[arg-type]
    )
    if sys.version_info >= (3, 10):
        assert issubform(
            Union[int, str],  # type: ignore[unused-ignore, arg-type]
            int | str,
        )
