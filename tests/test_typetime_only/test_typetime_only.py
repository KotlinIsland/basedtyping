from pytest import raises


def test_runtime_import() -> None:
    with raises(ImportError):
        import basedtyping.typetime_only  # pylint:disable=import-outside-toplevel # noqa: F401
