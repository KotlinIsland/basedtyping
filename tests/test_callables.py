from typing import TYPE_CHECKING

from basedtyping.callables import Function
from basedtyping.type_checks import assert_type

if TYPE_CHECKING:
    # these are just type-time tests, not real life pytest tests. they are only run by mypy
    def test_function_type() -> None:
        assert_type[Function](lambda: ...)
