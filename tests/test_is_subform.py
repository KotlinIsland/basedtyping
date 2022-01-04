from typing import Union

from basedtyping import issubform


def test_normal() -> None:
    assert issubform(int, int | str)


def test_union_first_arg() -> None:
    assert not issubform(int | str, int)
    assert issubform(int | str, object)


def test_old_union() -> None:
    # TODO: fix the mypy error
    assert not issubform(
        Union[int, str],  # type:ignore[arg-type]
        int,
    )
    assert issubform(
        Union[int, str],  # type:ignore[arg-type]
        object,
    )
