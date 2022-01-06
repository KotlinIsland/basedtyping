from typing import TYPE_CHECKING, NoReturn, cast

if TYPE_CHECKING:
    # these are just type-time tests, not real life pytest tests. they are only run by mypy

    from basedtyping import Never
    from basedtyping.typetime_only import assert_type

    def test_never_equals_noreturn() -> None:
        # TODO: better way to check if types are equal
        assert_type[NoReturn](cast(Never, 1))
        assert_type[Never](cast(NoReturn, 1))

    def test_valid_type_hint() -> None:
        _never: Never

    def test_cant_assign_to_never() -> None:
        _never: Never = 1  # type:ignore[assignment]

    def test_cant_subtype() -> None:
        class _A(Never):  # type:ignore[misc]
            ...
