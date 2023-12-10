"""This module only works at runtime. the types defined here do not work as type annotations
and are only intended for runtime checks, for example ``isinstance``.

This is the similar to the ``types`` module.
"""

from __future__ import annotations

from typing import Final, Final as Final_ext, Literal, Union

LiteralType: Final = type(Literal[1])
"""A type that can be used to check if type hints are a ``typing.Literal`` instance"""

# TODO: this is type[object], we need it to be 'SpecialForm[Union]' (or something)
OldUnionType: Final_ext[type[object]] = type(Union[str, int])
"""A type that can be used to check if type hints are a ``typing.Union`` instance."""
