from typing import TYPE_CHECKING

from basedtyping.callables import Function
from basedtyping.type_checks import assert_type

if TYPE_CHECKING:

    def test_function_type() -> None:
        assert_type[Function](lambda: ...)
