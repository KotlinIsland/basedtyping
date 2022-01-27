from pytest import mark, raises

from basedtyping import Never, issubform

# type ignores due to # https://github.com/KotlinIsland/basedmypy/issues/136


@mark.xfail  # https://github.com/KotlinIsland/basedtyping/issues/22
def test_isinstance() -> None:
    assert not isinstance(  # type: ignore[misc]
        1,
        Never,  # type: ignore[arg-type]
    )


def test_issubform_true() -> None:
    assert issubform(Never, int)  # type: ignore[arg-type]


def test_issubform_false() -> None:
    assert not issubform(str, Never)  # type: ignore[arg-type]


def test_issubform_never_is_never() -> None:
    assert issubform(Never, Never)  # type: ignore[arg-type]


def test_issubclass() -> None:
    with raises(TypeError):
        assert issubclass(  # type: ignore[misc]
            int, Never  # type: ignore[arg-type]
        )


def test_cant_instantiate() -> None:
    with raises(TypeError):
        Never()  # type: ignore[operator]


def test_cant_subtype() -> None:
    with raises(TypeError):

        class _SubNever(Never):  # type: ignore[misc]
            pass
