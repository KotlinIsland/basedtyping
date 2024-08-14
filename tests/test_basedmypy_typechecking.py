from __future__ import annotations

from basedtyping import BASEDMYPY_TYPE_CHECKING


def _():
    """type test"""
    if BASEDMYPY_TYPE_CHECKING:  # noqa: SIM108
        _ = 1 + ""  # type: ignore[operator]
    else:
        _ = 1 + ""
