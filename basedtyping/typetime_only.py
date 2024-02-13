"""This module only works at type-time, and cannot be used at runtime.

This is the similar to the ``_typeshed`` module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic

from basedtyping import T

if not TYPE_CHECKING:
    raise ImportError(
        "The ``basedtyping.typetime_only`` module cannot be imported at runtime. "
        "You should only import it within an ``if TYPE_CHECKING:`` block."
    )


class assert_type(Generic[T]):  # noqa: N801
    """Used to assert that a value is type ``T``.

    note: This is more like a function than a class,
    but it's defined as a class so that you can explicitly specify the generic.
    """

    # TODO: deprecate this  # noqa: TD003
    # TODO: make this use ReifiedGeneric so that it can check at runtime
    #  https://github.com/KotlinIsland/basedtyping/issues/15
    # None return type on __new__ is supported in pyright but not mypy
    def __new__(cls, _value: T):  # type: ignore[empty-body]
        pass
