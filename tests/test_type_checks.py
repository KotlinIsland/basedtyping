from typing import TYPE_CHECKING

from basedtyping.type_checks import assert_type

if TYPE_CHECKING:

    def test_assert_type_pass() -> None:
        assert_type[int](1)

    def test_assert_type_fail() -> None:
        assert_type[int]("")  # type:ignore[arg-type]
