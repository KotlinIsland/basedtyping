"""This module only works at type-time, and cannot be used at runtime.

This is the similar to the ``_typeshed`` module.
"""

from typing import TYPE_CHECKING, Generic

from basedtyping import T

if not TYPE_CHECKING:
    raise ImportError(
        "The ``basedtyping.typetime_only`` module cannot be imported at runtime. "
        "You should only import it within an ``if TYPE_CHECKING:`` block."
    )


class assert_type(Generic[T]):
    """Used to assert that a value is type ``T``.

    note: This is more like a function than a class,
    but it's defined as a class so that you can explicitly specify the generic.
    """

    # TODO: make this use ReifiedGeneric so that it can check at runtime
    # None return type on __new__ is supported in pyright but not mypy
    def __new__(cls, _value: T) -> None:  # type: ignore[misc]
        ...
