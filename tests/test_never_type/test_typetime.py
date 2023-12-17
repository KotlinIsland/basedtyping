from __future__ import annotations

from typing import TYPE_CHECKING, NoReturn, cast

if TYPE_CHECKING:
    # these are just type-time tests, not real life pytest tests. they are only run by mypy

    from typing_extensions import Never

    from basedtyping.typetime_only import assert_type

    def test_never_equals_noreturn():
        # TODO: better way to check if types are equal
        assert_type[NoReturn](cast(Never, 1))
        assert_type[Never](cast(NoReturn, 1))

    def test_valid_type_hint():
        _never: Never

    def test_cant_assign_to_never():
        _never: Never = 1  # type: ignore[assignment]

    def test_cant_subtype():
        class _A(Never):  # type: ignore[misc]
            ...

    def test_type_never():
        """``type[Never]`` is invalid as ``Never`` is not a ``type``.

        Should actually be:
         ``_t: type[Never]  # type: ignore[type-var]``
        due to https://github.com/python/mypy/issues/11291

        So current implementation resembles an xfail.
        """
        _t: type[Never]
