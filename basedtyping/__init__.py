from typing import Literal, Union

LiteralType = type(Literal[1])
"""A type that can be  used to check if type hints are a typing.Literal instance

Doesn't work as a type hint.
"""

OldUnionType = type(Union[str, int])
"""A type that can be used to check if type hints are a typing.Union instance.

Doesn't work as a type hint.
"""
