from basedtyping.runtime_checks import is_subclass

# pylint:disable=no-self-use


class TestIsSubclass:
    def test_normal(self) -> None:
        assert is_subclass(int, int | str)

    def test_union_first_arg(self) -> None:
        assert not is_subclass(int | str, int)
        assert is_subclass(int | str, object)
