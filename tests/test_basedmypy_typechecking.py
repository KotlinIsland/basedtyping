from __future__ import annotations

from basedtyping import BASEDMYPY_TYPE_CHECKING

if bool():  # noqa: UP018
    # hide this from pytest

    if BASEDMYPY_TYPE_CHECKING:  # noqa: SIM108
        _ = 1 + ""  # type: ignore[operator]
    else:
        _ = 1 + ""
