from types import UnionType
from typing import Sequence, cast


def is_subclass(type1: type | UnionType, type2: type | UnionType) -> bool:
    """``issubclass`` but works with a union as the first arg
    (like it does for the second arg)"""
    if isinstance(type1, UnionType):
        for t in cast(Sequence[type], type1.__args__):
            if not issubclass(t, type2):
                return False
        return True
    return issubclass(type1, type2)
