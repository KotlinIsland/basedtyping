from __future__ import annotations

import re

from typing_extensions import Literal, Union, override

from basedtyping import get_type_hints


def test_get_type_hints_class():
    result: object = None

    class Base:
        @override
        def __init_subclass__(cls):
            nonlocal result
            result = get_type_hints(cls)

    class A(Base):
        a: A

    assert result == {"a": A}


def test_get_type_hints_based():
    class A:
        a: Union[re.RegexFlag.ASCII, re.RegexFlag.DOTALL]

    assert get_type_hints(A) == {
        "a": Union[Literal[re.RegexFlag.ASCII], Literal[re.RegexFlag.DOTALL]]  # noqa: PYI030
    }
