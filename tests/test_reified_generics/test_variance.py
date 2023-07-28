from typing import Union

from basedtyping import ReifiedGeneric, T, T_co, T_contra

# type ignores are due to https://github.com/KotlinIsland/basedmypy/issues/5


def test_covariant() -> None:
    # https://github.com/KotlinIsland/basedtyping/issues/70
    class Foo(ReifiedGeneric[T_co]):  # type:ignore[type-var]
        pass

    assert isinstance(Foo[int](), Foo[Union[int, str]])  # type: ignore[misc]
    assert not isinstance(Foo[Union[int, str]](), Foo[int])  # type: ignore[misc]


def test_contravariant() -> None:
    # https://github.com/KotlinIsland/basedtyping/issues/70
    class Foo(ReifiedGeneric[T_contra]):  # type:ignore[type-var]
        pass

    assert isinstance(Foo[Union[int, str]](), Foo[int])  # type: ignore[misc]
    assert not isinstance(Foo[int](), Foo[Union[int, str]])  # type: ignore[misc]


def test_invariant() -> None:
    class Foo(ReifiedGeneric[T]):
        pass

    assert not isinstance(Foo[int](), Foo[Union[int, str]])  # type: ignore[misc]
    assert not isinstance(Foo[Union[int, str]](), Foo[int])  # type: ignore[misc]
