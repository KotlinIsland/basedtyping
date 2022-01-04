"""this module only works at type-time, and cannot be used at runtime

this is the equivalent of the `_typeshed` module"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Generic

    from basedtyping import T

    class assert_type(Generic[T]):
        """used to assert that a value is type ``T``

        note: this is more like a function than a class, but it's defined as a class so that you can explicitly specify the generic"""

        # TODO: make this use ReifiedGeneric so that it can check at runtime
        # None return type on __new__ is supported in pyright but not mypy
        def __new__(cls, _value: T) -> None:  # type:ignore[misc]
            ...

else:
    raise ImportError(
        "the basedtyping.typetime_only module cannot be imported at runtime. you should only import it within an `if TYPE_CHECKING:` block"
    )
