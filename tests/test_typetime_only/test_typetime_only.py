from __future__ import annotations

from pytest import raises


def test_runtime_import() -> None:
    with raises(ImportError):
        import basedtyping.typetime_only  # noqa: F401
