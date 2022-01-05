from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # these are just type-time tests, not real life pytest tests. they are only run by mypy
    from basedtyping.typetime_only import assert_type

    def test_assert_type_pass() -> None:
        assert_type[int](1)

    def test_assert_type_fail() -> None:
        assert_type[int]("")  # type: ignore[arg-type]
