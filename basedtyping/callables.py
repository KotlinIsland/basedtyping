from typing import Callable

Function = Callable[..., object]  # type:ignore[misc]
"""any ``Callable``. useful when using mypy with ``disallow-any-explicit`` due to https://github.com/python/mypy/issues/9496"""
