from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # these are just type-time tests, not real life pytest tests. they are only run by mypy

    from basedtyping import Function
    from basedtyping.typetime_only import assert_type

    assert_function = assert_type[Function]

    def test_lambda_type() -> None:
        assert_function(lambda: ...)

    def test_function_type() -> None:
        def func() -> None:
            pass

        assert_function(func)

    def test_builtin_function() -> None:
        assert_function(len)

    def test_builtin_method() -> None:
        assert_function([].append)

    def test_wrapper_descriptor() -> None:
        assert_function(object.__init__)

    def test_method_wrapper() -> None:
        assert_function(object().__str__)

    def test_method_descriptor() -> None:
        assert_function(str.join)

    def test_class_method_descriptor() -> None:
        # method signature contains `Any`
        assert_function(dict.fromkeys)  # type: ignore[misc]
