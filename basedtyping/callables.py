from typing import Callable

Function = Callable[..., object]  # type:ignore[misc]
"""any ``Callable``. useful when using mypy with ``disallow-any-explicit`` due to https://github.com/python/mypy/issues/9496

cannot actually be called unless it's narrowed, so it should only really be used as a bound in a ``TypeVar``"""
