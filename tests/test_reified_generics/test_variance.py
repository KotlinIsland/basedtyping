from basedtyping import ReifiedGeneric, T, T_co, T_cont

# type ignores are due to https://github.com/KotlinIsland/basedmypy/issues/5


def test_covariant() -> None:
    class Foo(ReifiedGeneric[T_co]):
        pass

    assert isinstance(Foo[int](), Foo[int | str])  # type:ignore[misc]
    assert not isinstance(Foo[int | str](), Foo[int])  # type:ignore[misc]


def test_contravariant() -> None:
    class Foo(ReifiedGeneric[T_cont]):
        pass

    assert isinstance(Foo[int | str](), Foo[int])  # type:ignore[misc]
    assert not isinstance(Foo[int](), Foo[int | str])  # type:ignore[misc]


def test_invariant() -> None:
    class Foo(ReifiedGeneric[T]):
        pass

    assert not isinstance(Foo[int](), Foo[int | str])  # type:ignore[misc]
    assert not isinstance(Foo[int | str](), Foo[int])  # type:ignore[misc]
