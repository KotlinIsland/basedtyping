from __future__ import annotations

from typing import TYPE_CHECKING, Tuple, Type

if TYPE_CHECKING:
    # these are just type-time tests, not real life pytest tests. they are only run by mypy
    # they are currently failing since it's not currently possible to maintain the types of each type

    from typing import TypeVar

    from basedtyping import ReifiedGeneric, T

    U = TypeVar("U")

    class Reified(ReifiedGeneric[Tuple[T, U]]):
        pass

    from basedtyping.typetime_only import assert_type

    def test_instance():
        """may be possible once https://github.com/KotlinIsland/basedmypy/issues/24 is resolved"""
        assert_type[Tuple[Type[int], Type[str]]](
            Reified[int, str]().__reified_generics__  # type: ignore[arg-type]
        )

    def from_class():
        """may be possible once https://github.com/python/mypy/issues/11672 is resolved"""
        assert_type[Tuple[Type[int], Type[str]]](
            Reified[int, str].__reified_generics__  # type: ignore[arg-type]
        )
