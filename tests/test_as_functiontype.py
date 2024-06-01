from __future__ import annotations

import pytest

from basedtyping import as_functiontype


def test_as_functiontype():
    with pytest.raises(TypeError):
        as_functiontype(all)
    assert as_functiontype(test_as_functiontype) is test_as_functiontype  # type: ignore[comparison-overlap]
