from __future__ import annotations

from typing import Generic

from basedtyping.generics import T


class assert_type(Generic[T]):
    """used to assert at type-time that a value is type ``T``

    this is only intended for type-time tests, and therefore should only ever be used from within an ``if TYPE_CHECKING:`` block.

    note: this is more like a function than a class, but it's defined as a class so that you can explicitly specify the generic"""

    # None return type on __new__ is supported in pyright but not mypy
    def __new__(cls, value: T) -> None:  # type:ignore[misc]
        # TODO: make this use ReifiedGeneric so that it can check at runtime
        raise TypeError(
            "assert_type should not be called at runtime, as it doesn't check anything at runtime"
        )
