"""The main ``basedtyping`` module. the types/functions defined here can be used at both type-time and at runtime."""
from __future__ import annotations

from types import GenericAlias, UnionType
from typing import (
    TYPE_CHECKING,
    Callable,
    Generic,
    NoReturn,
    Protocol,
    Sequence,
    TypeVar,
    _GenericAlias,
    _SpecialForm,
    cast,
)

from basedtyping.runtime_only import OldUnionType

if TYPE_CHECKING:
    Function = Callable[..., object]  # type: ignore[misc]
    """Any ``Callable``. useful when using mypy with ``disallow-any-explicit``
    due to https://github.com/python/mypy/issues/9496

    Cannot actually be called unless it's narrowed, so it should only really be used as
    a bound in a ``TypeVar``.
    """
else:
    # for isinstance checks
    Function = Callable

# Unlike the generics in other modules, these are meant to be imported to save you from the boilerplate

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
T_cont = TypeVar("T_cont", contravariant=True)
Fn = TypeVar("Fn", bound=Function)


Never = NoReturn
"""A value that can never exist. This is the narrowest possible form."""


class _ReifiedGenericAlias(_GenericAlias, _root=True):
    def __call__(self, *args: object, **kwargs: object) -> _ReifiedGenericMetaclass:
        """Copied from ``super().__call__`` but modified to call ``type.__call__``
        instead of ``__origin__.__call__``, and throw an error if there are any TypeVars
        """
        if not self._inst:
            raise TypeError(
                f"Type {self._name} cannot be instantiated; "
                f"use {self.__origin__.__name__}() instead"
            )
        self._check_generics_reified()
        # hack so that the reified generics are available within `__init__`
        # TODO: better way of doing this instead of modifying the original class and deleting it after
        self.__origin__.__orig_class__ = self  # type: ignore[attr-defined]
        result = cast(
            _ReifiedGenericMetaclass, type.__call__(self.__origin__, *args, **kwargs)  # type: ignore[misc]
        )
        delattr(self.__origin__, "__orig_class__")
        result.__orig_class__ = self  # type: ignore[attr-defined]
        return result

    def __mro_entries__(self, bases: tuple[type, ...]) -> tuple[type, ...]:
        result = super().__mro_entries__(bases)
        # fail when subtyping and specifying concrete type parameters
        if result == (self.__origin__,) and any(  # type: ignore[misc]
            not isinstance(arg, TypeVar)  # type: ignore[misc]
            for arg in (
                self.__args__[0].__args__  # type: ignore[misc]
                if isinstance(self.__args__[0], GenericAlias | _GenericAlias)  # type: ignore[misc, unreachable]
                else self.__args__
            )
        ):
            raise NotImplementedError(
                "Concrete subtyping of ReifiedGenerics is not yet supported"
            )
        return result

    def _check_generics_reified(self) -> None:
        if self.__parameters__:
            raise NotReifiedParameterError(
                f"Type {self.__origin__.__name__} cannot be instantiated; TypeVars "
                f"cannot be used to instantiate a reified class: {self.__parameters__}"
            )

    def _type_vars(self) -> tuple[TypeVar, ...]:
        """Returns a ``tuple`` of all the type parameters defined in the `__origin__`."""
        return cast(tuple[TypeVar, ...], self.__origin__.__parameters__)  # type: ignore[attr-defined]

    def _type_var_check(self, args: tuple[type, ...]) -> bool:
        self._check_generics_reified()
        for parameter, self_arg, subclass_arg in zip(
            self._type_vars(),
            self.__args__,
            args,
            strict=True,
        ):
            if parameter.__contravariant__:
                if not issubform(self_arg, subclass_arg):
                    return False
            elif parameter.__covariant__:
                if not issubform(subclass_arg, self_arg):
                    return False
            elif subclass_arg != self_arg:
                return False
        return True

    def __subclasscheck__(self, subclass: object) -> bool:
        # could be any random class, check it first
        if not isinstance(subclass, _ReifiedGenericAlias) or not issubform(
            subclass.__origin__, self.__origin__
        ):
            return False
        subclass._check_generics_reified()
        return self._type_var_check(subclass.__args__)

    def __instancecheck__(self, instance: object) -> bool:
        # could be any random instance, check it first
        if not isinstance(instance, self.__origin__) or not isinstance(
            instance, ReifiedGeneric
        ):
            return False
        return self._type_var_check(instance.__orig_class__.__args__)


class OrigClass(Protocol):
    __args__: tuple[type, ...]
    """The reified type(s)"""
    __parameters__: tuple[TypeVar, ...]
    """Any unbound ``TypeVar``s (this should always be empty by the time the
    ``ReifiedGeneric`` is instantiated)
    """


class ReifiedGenericError(TypeError):
    pass


class NoParametersError(ReifiedGenericError):
    """Raised when a ``ReifiedGeneric`` is instantiated without passing type parameters.

    ie: ``foo: Foo[int] = Foo()`` instead of ``foo = Foo[int]()``
    """


class NotReifiedParameterError(ReifiedGenericError):
    """Raised when a ``ReifiedGeneric`` is instantiated with a non-reified ``TypeVar``
    as a type parameter instead of a concrete type.

    ie: ``Foo[T]()`` instead of ``Foo[int]()``
    """


class _ReifiedGenericMetaclass(type, OrigClass):
    def __call__(cls, *args: object, **kwargs: object) -> object:
        """A placeholder ``__call__`` method that gets called when the class is
        instantiated directly, instead of first supplying the type parameters.
        """
        raise NoParametersError(
            f"Cannot instantiate ReifiedGeneric '{cls.__name__}' because its type "
            "parameters were not supplied. "
            "The type parameters must be explicitly specified in the instantiation so "
            "that the type data can be made available at runtime.\n\n"
            "For example:\n\n"
            "foo: Foo[int] = Foo()  # wrong\n"
            "foo = Foo[int]()  # correct"
        )


class ReifiedGeneric(Generic[T], metaclass=_ReifiedGenericMetaclass):
    """A ``Generic`` where the type parameters are available at runtime and is
    usable in ``isinstance`` and ``issubclass`` checks.

    For example:

    >>> class Foo(ReifiedGeneric[T]):
    ...     def create_instance(self) -> T:
    ...         cls = self.__orig_class__.__args__[0]
    ...         return cls()
    ...
    ...  foo: Foo[int] = Foo() # error: generic cannot be reified
    ...  foo = Foo[int]() # no error, as types have been supplied in a runtime position

    To define multiple generics, use a tuple type:

    >>> class Foo(ReifiedGeneric[tuple[T, U]]):
    ...     pass
    ...
    ... foo = Foo[int, str]()

    Since the type parameters are guaranteed to be reified, that means ``isinstance``
    and ``issubclass`` checks work as well:

    >>> isinstance(Foo[int, str](), Foo[int, int])  # type: ignore[misc]
    False

    note: basedmypy currently doesn't allow generics in ``isinstance`` and ``issubclass`` checks, so for now you have to use
    ``basedtyping.issubform`` for subclass checks and ``# type: ignore[misc]`` for instance checks. this issue
    is tracked [here](https://github.com/KotlinIsland/basedmypy/issues/5)
    """

    # TODO: somehow make this an instance property, but doing that with an `__init__` messes up the MRO (see the ReifiedList test)
    # currently mypy can't even tell the difference anyway https://github.com/python/mypy/issues/11832
    __orig_class__: OrigClass

    if not TYPE_CHECKING:
        # mypy doesn't check the signature of __class_getitem__ but complains when it doesn't match its signature in another base class
        # this is purely a runtime thing anyway so we can just do this

        def __class_getitem__(cls, item) -> type[ReifiedGeneric[T]]:
            generic_alias = super().__class_getitem__(item)
            return _ReifiedGenericAlias(
                generic_alias.__origin__, generic_alias.__args__
            )


# TODO: make this work with any "form", not just unions
#  should be (form: TypeForm, forminfo: TypeForm)
def issubform(
    form: type | UnionType | _SpecialForm, forminfo: type | UnionType | _SpecialForm
) -> bool:
    """EXPERIMENTAL: Warning, this function currently only supports unions and ``Never``.

    Returns ``True`` if ``form`` is a subform (specialform or subclass) of ``forminfo``.

    Like  ``issubclass`` but supports typeforms (type-time types)

    for example:

    >>> issubclass(int | str, object)
    TypeError: issubclass() arg 1 must be a class

    >>> issubform(int | str, str)
    False

    >>> issubform(int | str, object)
    True
    """
    # type ignores because issubclass doesn't support _SpecialForm, but we do
    if isinstance(form, UnionType | OldUnionType):
        for t in cast(Sequence[type], cast(UnionType, form).__args__):
            if not issubform(t, forminfo):
                return False
        return True
    if form is Never:
        return True
    if forminfo is Never:
        return False
    return issubclass(form, forminfo)  # type: ignore[arg-type]
