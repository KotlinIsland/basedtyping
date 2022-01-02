from basedtyping.runtime_checks import issubform

# pylint:disable=no-self-use


class TestIsSubform:
    def test_normal(self) -> None:
        assert issubform(int, int | str)

    def test_union_first_arg(self) -> None:
        assert not issubform(int | str, int)
        assert issubform(int | str, object)
