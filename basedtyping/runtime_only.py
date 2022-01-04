"""this module only works at runtime. the types defined here do not work as a type hint and are only intended for runtime checks, for example ``isinstance``

this is the equivalent of the `types` module"""

from typing import Literal, Union

LiteralType = type(Literal[1])
"""A type that can be  used to check if type hints are a typing.Literal instance"""

OldUnionType = type(Union[str, int])
"""A type that can be used to check if type hints are a typing.Union instance."""