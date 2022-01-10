from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # these are just type-time tests, not real life pytest tests. they are only run by mypy
    # they are currently failing since it's not currently possible to maintain the types of each type

    from typing import TypeVar

    from basedtyping import ReifiedGeneric, T

    U = TypeVar("U")

    class Reified(ReifiedGeneric[tuple[T, U]]):
        pass

    from basedtyping.typetime_only import assert_type

    def test_instance() -> None:
        """may be possible once https://github.com/KotlinIsland/basedmypy/issues/24 is resolved"""
        assert_type[tuple[type[int], type[str]]](
            Reified[int, str]().__orig_class__.__args__  # type: ignore[arg-type]
        )

    def from_class() -> None:
        """may be possible once https://github.com/python/mypy/issues/11672 is resolved"""
        assert_type[tuple[type[int], type[str]]](
            Reified[int, str].__args__  # type: ignore[arg-type]
        )
