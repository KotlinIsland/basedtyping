"""stubs for the internal "type machinery" defined in the typing module.

not a .pyi file because we don't want to replace the types for the entire typing module"""

import typing

from basedtyping.generics import Self

if typing.TYPE_CHECKING:

    class _Final:
        """Mixin to prohibit subclassing"""

        __slots__ = ("__weakref__",)

        def __init_subclass__(
            cls, /, *args: object, **kwds: object
        ):  # pylint:disable=unused-argument
            ...

    class _BaseGenericAlias(_Final, _root=True):
        __origin__: type

        def __init__(
            self, origin: type, *, inst: bool = True, name: str | None = None
        ) -> None:
            self._inst = inst
            self._name = name
            self.__origin__ = origin

    _Params = typing.Union[type, tuple[type, ...]]

    class _GenericAlias(_BaseGenericAlias, _root=True):
        def __init__(  # pylint:disable=super-init-not-called
            self,
            origin: type,
            params: _Params,  # pylint:disable=unused-argument
            *,
            inst: bool = True,  # pylint:disable=unused-argument
            name: str | None = None,
            _typevar_types: type[typing.TypeVar] = typing.TypeVar,
            _paramspec_tvars: bool = False,
        ):
            self.__args__: tuple[type, ...]
            self.__parameters__: tuple[typing.TypeVar, ...]
            self._typevar_types = _typevar_types
            self._paramspec_tvars = _paramspec_tvars
            if not name:
                self.__module__ = origin.__module__

        # def __eq__(self, other: object) -> bool:
        #     ...

        def __hash__(self) -> int:
            ...

        def __or__(self, right: object) -> typing._SpecialForm:
            ...

        def __ror__(self, left: object) -> typing._SpecialForm:
            ...

        def __getitem__(self: Self, params: _Params) -> Self:
            ...

        def copy_with(  # pylint:disable=no-self-use
            self: Self, params: _Params  # pylint:disable=unused-argument
        ) -> Self:
            ...

        # TODO: wtf is this
        # def __reduce__(self):
        #     if self._name:
        #         origin = globals()[self._name]
        #     else:
        #         origin = self.__origin__
        #     args = tuple(self.__args__)
        #     if len(args) == 1 and not isinstance(args[0], tuple):
        #         args, = args
        #     return operator.getitem, (origin, args)

        def __mro_entries__(  # pylint:disable=no-self-use
            self, bases: tuple[type, ...]  # pylint:disable=unused-argument
        ) -> tuple[type, ...]:
            ...

else:
    _GenericAlias = typing._GenericAlias  # pylint:disable=protected-access
    _Final = typing._Final  # pylint:disable=protected-access
    _BaseGenericAlias = typing._BaseGenericAlias  # pylint:disable=protected-access
