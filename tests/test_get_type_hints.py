from __future__ import annotations

from basedtyping import get_type_hints


def test_get_type_hints():
    result: object = None

    class Base:
        def __init_subclass__(cls):
            nonlocal result
            result = get_type_hints(cls)

    class A(Base):
        a: A

    assert result == {"a": A}
