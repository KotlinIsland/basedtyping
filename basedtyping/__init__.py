"""The main ``basedtyping`` module. the types/functions defined here can be used at both type-time and at runtime."""
from __future__ import annotations

from types import UnionType
from typing import TYPE_CHECKING, Callable, Generic, Sequence, TypeVar, Union, cast

from basedtyping.runtime_only import OldUnionType

if not TYPE_CHECKING:
    # TODO: remove the TYPE_CHECKING block once these are typed in basedtypeshed
    from typing import _collect_type_vars, _tp_cache

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


class ReifiedGenericError(TypeError):
    pass


class NotReifiedError(ReifiedGenericError):
    """Raised when a ``ReifiedGeneric`` is instantiated without passing type parameters:

    ie: ``foo: Foo[int] = Foo()`` instead of ``foo = Foo[int]()``

    or when a ``ReifiedGeneric`` is instantiated with a non-reified ``TypeVar``
    as a type parameter instead of a concrete type.

    ie: ``Foo[T]()`` instead of ``Foo[int]()``
    """


class NotEnoughTypeParametersError(ReifiedGenericError):
    """Raised when type parameters are passed to a ``ReifiedGeneric`` with an incorrect number of type parameters:

    for example:
    >>> class Foo(ReifiedGeneric[tuple[T, U]]):
    ...     ...
    ...
    ... foo = Foo[int]() # wrong
    ... foo = Foo[int, str]() # correct
    """


class _ReifiedGenericMetaclass(type):
    # these should really only be on the class not the metaclass, but since it needs to be accessible from both instances and the class itself, its duplicated here
    __reified_generics__: tuple[type, ...]
    """should be a generic but cant due to https://github.com/python/mypy/issues/11672"""
    __type_vars__: tuple[TypeVar, ...]
    """``TypeVar``s that have not yet been reified. so this tuple should always be empty by the time the ``ReifiedGeneric`` is instanciated"""
    _orig_type_vars: tuple[TypeVar, ...]
    """used internally to check the ``__type_vars__`` on the current ``ReifiedGeneric`` against the original one it was copied from
    in ``ReifiedGeneric.__class_getitem__``"""

    def _orig_class(cls) -> _ReifiedGenericMetaclass:
        """gets the original class that ``ReifiedGeneric.__class_getitem__`` copied from"""
        return cls.__bases__[0]  # type:ignore[return-value]

    def _type_var_check(cls, args: tuple[type, ...]) -> bool:
        cls._check_generics_reified()
        for parameter, self_arg, subclass_arg in zip(
            # normal generics use __parameters__, we use __type_vars__ because the Generic base class deletes properties
            # named __parameters__ when copying to a new class
            cast(
                tuple[TypeVar, ...],
                cls._orig_class().__parameters__,  # type:ignore[attr-defined]
            ),
            cls.__reified_generics__,
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

    def _check_generics_reified(cls) -> None:
        if cls.__type_vars__:
            raise NotReifiedError(
                f"Type {cls.__name__} cannot be instantiated; TypeVars cannot be used"
                f" to instantiate a reified class: {cls._orig_type_vars}"
            )

    def __subclasscheck__(cls, obj: object) -> bool:
        # could be any random class, check it first
        # first do a normal instance check, return false if the origin isn't the same
        # https://github.com/KotlinIsland/basedtypeshed/issues/7
        if not type.__instancecheck__(  # type:ignore[misc]
            _ReifiedGenericMetaclass,  # type:ignore[misc]
            cls._orig_class(),
        ):
            return False
        subclass = cast(_ReifiedGenericMetaclass, obj)
        subclass._check_generics_reified()
        return cls._type_var_check(subclass.__reified_generics__)

    def __instancecheck__(cls, instance: object) -> bool:
        # could be any random instance, check it first
        # https://github.com/KotlinIsland/basedtypeshed/issues/7
        if not type.__instancecheck__(  # type:ignore[misc]
            cls._orig_class(), instance
        ):
            return False
        return cls._type_var_check(
            cast(ReifiedGeneric[object], instance).__reified_generics__
        )

    def __call__(cls, *args: object, **kwargs: object) -> object:
        """A placeholder ``__call__`` method that gets called when the class is
        instantiated directly, instead of first supplying the type parameters.
        """
        if (
            # instanciating a ReifiedGeneric without specifying any TypeVars
            not hasattr(cls, "_orig_type_vars")
            # instanciating a subtype of a ReifiedGeneric without specifying any TypeVars
            or cls._orig_type_vars == cls.__type_vars__
        ):
            raise NotReifiedError(
                f"Cannot instantiate ReifiedGeneric '{cls.__name__}' because its type"
                " parameters were not supplied. The type parameters must be explicitly"
                " specified in the instantiation so that the type data can be made"
                " available at runtime.\n\n"
                "For example:\n\n"
                "foo: Foo[int] = Foo()  #wrong\n"
                "foo = Foo[T]()  #wrong\n"
                "foo = Foo[int]()  # correct"
            )
        cls._check_generics_reified()
        return super().__call__(*args, **kwargs)  # type:ignore[misc]


GenericItems = Union[type, TypeVar, tuple[type | TypeVar, ...]]
"""the ``items`` argument passed to ``__class_getitem__`` when creating or using a ``Generic``"""


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

    __reified_generics__: tuple[type, ...]
    """should be a generic but cant due to https://github.com/KotlinIsland/basedmypy/issues/142"""
    __type_vars__: tuple[TypeVar, ...]
    """``TypeVar``s that have not yet been reified. so this tuple should always be empty by the time the ``ReifiedGeneric`` is instanciated"""

    @_tp_cache  # type:ignore[name-defined,misc]
    def __class_getitem__(  # type:ignore[misc]
        cls, item: GenericItems
    ) -> type[ReifiedGeneric[T]]:
        if cls is ReifiedGeneric:
            # https://github.com/KotlinIsland/basedtypeshed/issues/7
            return super().__class_getitem__(item)  # type:ignore[misc,no-any-return]
        items = item if isinstance(item, tuple) else (item,)
        # normal generics use __parameters__, we use __type_vars__ because the Generic base class deletes properties
        # named __parameters__ when copying to a new class
        orig_type_vars = (
            cls.__type_vars__
            if hasattr(cls, "__type_vars__")
            else cast(
                tuple[TypeVar, ...], cls.__parameters__  # type:ignore[attr-defined]
            )
        )
        if (expected_length := len(orig_type_vars)) != (actual_length := len(items)):
            raise NotEnoughTypeParametersError(
                f"incorrect number of type parameters specified. {expected_length=},"
                f" {actual_length=}"
            )
        ReifiedGenericCopy: type[ReifiedGeneric[T]] = type(
            cls.__name__,
            (
                cls,
            ),  # make the copied class extend the original so normal instance checks work
            dict[str, GenericItems](
                __reified_generics__=items,
                _orig_type_vars=orig_type_vars,
            ),
        )
        # for some reason setting __parameters__ in the dict above doesn't work and it gets set to an empty tuple
        # so set it here instead
        ReifiedGenericCopy.__type_vars__ = (
            _collect_type_vars(  # type:ignore[name-defined]
                items, cast(type, TypeVar)
            )
        )
        return ReifiedGenericCopy


# TODO: make this work with any "form", not just unions
#  should be (form: TypeForm, forminfo: TypeForm)
def issubform(form: type | UnionType, forminfo: type | UnionType) -> bool:
    """EXPERIMENTAL: Warning, this function currently only supports unions.

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
    if isinstance(form, UnionType | OldUnionType):
        for t in cast(Sequence[type], cast(UnionType, form).__args__):
            if not issubclass(t, forminfo):
                return False
        return True
    return issubclass(form, forminfo)
