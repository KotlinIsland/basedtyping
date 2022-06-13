"""The main ``basedtyping`` module. the types/functions defined here can be used at both type-time and at runtime."""
from __future__ import annotations

import sys
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ForwardRef,
    Generic,
    NoReturn,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    _SpecialForm,
    cast,
)

from typing_extensions import Final, TypeAlias, TypeGuard

from basedtyping.runtime_only import OldUnionType

if not TYPE_CHECKING:
    # TODO: remove the TYPE_CHECKING block once these are typed in basedtypeshed
    from typing import _collect_type_vars, _tp_cache


if TYPE_CHECKING:
    Function = Callable[..., object]  # type: ignore[no-any-explicit]
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


def _type_convert(arg: object) -> object:
    """For converting None to type(None), and strings to ForwardRef.

    Stolen from typing.
    """
    if arg is None:
        return type(None)
    if isinstance(arg, str):
        return ForwardRef(arg)
    return arg


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
    >>> class Foo(ReifiedGeneric[Tuple[T, U]]):
    ...     ...
    ...
    ... foo = Foo[int]() # wrong
    ... foo = Foo[int, str]() # correct
    """


class _ReifiedGenericMetaclass(type):
    # these should really only be on the class not the metaclass, but since it needs to be accessible from both instances and the class itself, its duplicated here

    __reified_generics__: Tuple[type, ...]
    """should be a generic but cant due to https://github.com/python/mypy/issues/11672"""

    __type_vars__: Tuple[TypeVar, ...]
    """``TypeVar``s that have not yet been reified. so this Tuple should always be empty by the time the ``ReifiedGeneric`` is instanciated"""

    _orig_type_vars: Tuple[TypeVar, ...]
    """used internally to check the ``__type_vars__`` on the current ``ReifiedGeneric`` against the original one it was copied from
    in ``ReifiedGeneric.__class_getitem__``"""

    _can_do_instance_and_subclass_checks_without_generics: bool
    """Used internally for ``isinstance`` and ``issubclass`` checks, ``True`` when the class can currenty be used in said checks without generics in them"""

    def _orig_class(cls) -> _ReifiedGenericMetaclass:
        """Gets the original class that ``ReifiedGeneric.__class_getitem__`` copied from"""
        result = cls.__bases__[0]
        if result is ReifiedGeneric:
            return cls
        return result  # type: ignore[return-value]

    def _type_var_check(cls, args: Tuple[type, ...]) -> bool:
        if not cls._generics_are_reified():
            if cls._has_non_reified_type_vars():
                cls._raise_generics_not_reified()
            return True
        assert len(cls._orig_class().__parameters__) == len(cls.__reified_generics__) == len(args)  # type: ignore[no-any-expr, attr-defined]
        for parameter, self_arg, subclass_arg in zip(
            # normal generics use __parameters__, we use __type_vars__ because the Generic base class deletes properties
            # named __parameters__ when copying to a new class
            cast(
                Tuple[TypeVar, ...],
                cls._orig_class().__parameters__,  # type: ignore[attr-defined]
            ),
            cls.__reified_generics__,
            args,
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

    def _generics_are_reified(cls) -> bool:
        return hasattr(cls, "__type_vars__") and not bool(cls.__type_vars__)

    def _has_non_reified_type_vars(cls) -> bool:
        return hasattr(cls, "__type_vars__") and bool(cls.__type_vars__)

    def _raise_generics_not_reified(cls) -> NoReturn:
        raise NotReifiedError(
            f"Type {cls.__name__} cannot be instantiated; TypeVars cannot be used"
            f" to instantiate a reified class: {cls._orig_type_vars}"
        )

    def _check_generics_reified(cls) -> None:
        if not cls._generics_are_reified() or cls._has_non_reified_type_vars():
            cls._raise_generics_not_reified()

    def _is_subclass(cls, subclass: object) -> TypeGuard[_ReifiedGenericMetaclass]:
        """For ``__instancecheck__`` and ``__subclasscheck__``. checks whether the
        "origin" type (ie. without the generics) is a subclass of this reified generic
        """
        # could be any random instance, check it's a reified generic first:
        return type.__instancecheck__(  # type: ignore[no-any-expr]
            _ReifiedGenericMetaclass,  # type: ignore[no-any-expr]
            subclass,
            # then check that the instance is an instance of this particular reified generic:
        ) and type.__subclasscheck__(  # type: ignore[no-any-expr]
            cls._orig_class(),
            # https://github.com/python/mypy/issues/11671
            cast(  # pylint:disable=protected-access
                _ReifiedGenericMetaclass, subclass
            )._orig_class(),
        )

    def __subclasscheck__(cls, subclass: object) -> bool:
        if not cls._is_subclass(subclass):
            return False
        if cls._can_do_instance_and_subclass_checks_without_generics:
            return True
        # if one of the classes doesn't have any generics, we treat it as the widest possible values for those generics (like star projection)
        if not hasattr(subclass, "__reified_generics__"):
            # TODO: subclass could be wider, but we don't know for sure because cls could have generics matching its bound
            raise NotImplementedError(
                "Cannot perform a subclass check where the first class"
                f" ({cls.__name__!r}) has type parameters and the second class"
                f" ({subclass.__name__!r}) doesn't"
            )
        if not hasattr(cls, "__reified_generics__"):
            # subclass would be narrower, so we can safely return True
            return True
        subclass._check_generics_reified()
        return cls._type_var_check(subclass.__reified_generics__)

    def __instancecheck__(cls, instance: object) -> bool:
        if not cls._is_subclass(type(instance)):
            return False
        if cls._can_do_instance_and_subclass_checks_without_generics:
            return True
        return cls._type_var_check(
            cast(ReifiedGeneric[object], instance).__reified_generics__
        )

    def __call__(cls, *args: object, **kwargs: object) -> object:
        """A placeholder ``__call__`` method that gets called when the class is
        instantiated directly, instead of first supplying the type parameters.
        """
        if (
            # instantiating a ReifiedGeneric without specifying any TypeVars
            not hasattr(cls, "_orig_type_vars")
            # instantiating a subtype of a ReifiedGeneric without specifying any TypeVars
            or cls._orig_type_vars == cls.__type_vars__
        ):
            raise NotReifiedError(
                f"Cannot instantiate ReifiedGeneric {cls.__name__!r} because its type"
                " parameters were not supplied. The type parameters must be explicitly"
                " specified in the instantiation so that the type data can be made"
                " available at runtime.\n\n"
                "For example:\n\n"
                "foo: Foo[int] = Foo()  #wrong\n"
                "foo = Foo[T]()  #wrong\n"
                "foo = Foo[int]()  # correct"
            )
        cls._check_generics_reified()
        return super().__call__(*args, **kwargs)  # type: ignore[no-any-expr]


GenericItems: TypeAlias = Union[type, TypeVar, Tuple[Union[type, TypeVar], ...]]
"""The ``items`` argument passed to ``__class_getitem__`` when creating or using a ``Generic``"""


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

    To define multiple generics, use a Tuple type:

    >>> class Foo(ReifiedGeneric[Tuple[T, U]]):
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

    __reified_generics__: Tuple[type, ...]
    """Should be a generic but cant due to https://github.com/KotlinIsland/basedmypy/issues/142"""
    __type_vars__: Tuple[TypeVar, ...]
    """``TypeVar``\\s that have not yet been reified. so this Tuple should always be empty by the time the ``ReifiedGeneric`` is instantiated"""

    @_tp_cache  # type: ignore[name-defined, no-any-expr, misc]
    def __class_getitem__(  # type: ignore[no-any-decorated]
        cls, item: GenericItems
    ) -> Type[ReifiedGeneric[T]]:
        # when defining the generic (ie. `class Foo(ReifiedGeneric[T]):`) we want the normal behavior
        if cls is ReifiedGeneric:
            # https://github.com/KotlinIsland/basedtypeshed/issues/7
            return super().__class_getitem__(item)  # type: ignore[no-any-expr, misc, no-any-return]

        items = item if isinstance(item, tuple) else (item,)

        # if we're subtyping a class that already has reified generics:
        superclass_reified_generics = tuple(
            generic
            for generic in (
                cls.__reified_generics__ if hasattr(cls, "__reified_generics__") else ()
            )
            # TODO: investigate this unreachable, redundant-expr
            if not isinstance(generic, TypeVar)  # type: ignore[unused-ignore, unreachable, redundant-expr, no-any-expr]
        )

        # normal generics use __parameters__, we use __type_vars__ because the Generic base class deletes properties
        # named __parameters__ when copying to a new class
        orig_type_vars = (
            cls.__type_vars__
            if hasattr(cls, "__type_vars__")
            else cast(
                Tuple[TypeVar, ...], cls.__parameters__  # type: ignore[attr-defined]
            )
        )

        # add any reified generics from the superclass if there is one
        items = superclass_reified_generics + items
        expected_length = len(orig_type_vars)
        actual_length = len(items) - len(superclass_reified_generics)
        if expected_length != len(items) - len(superclass_reified_generics):
            raise NotEnoughTypeParametersError(
                "Incorrect number of type parameters specified. expected length:"
                f" {expected_length}, actual length {actual_length}"
            )
        ReifiedGenericCopy: Type[ReifiedGeneric[T]] = type(
            cls.__name__,
            (
                cls,  # make the copied class extend the original so normal instance checks work
            ),
            # TODO: proper type
            dict(  # type: ignore[no-any-expr]
                __reified_generics__=tuple(  # type: ignore[no-any-expr]
                    _type_convert(t) for t in items  # type: ignore[unused-ignore, no-any-expr]
                ),
                _orig_type_vars=orig_type_vars,
                __type_vars__=_collect_type_vars(  # type: ignore[name-defined, no-any-expr]
                    items, cast(type, TypeVar)
                ),
            ),
        )
        # can't set it in the dict above otherwise __init_subclass__ overwrites it
        ReifiedGenericCopy._can_do_instance_and_subclass_checks_without_generics = (  # pylint:disable=protected-access
            False
        )
        return ReifiedGenericCopy

    def __init_subclass__(cls) -> None:  # pylint:disable=arguments-differ
        cls._can_do_instance_and_subclass_checks_without_generics = True
        super().__init_subclass__()


if sys.version_info >= (3, 10):
    from types import UnionType

    _UnionTypes = (UnionType, OldUnionType)
    _Forms: TypeAlias = type | UnionType | _SpecialForm  # type: ignore[unused-ignore, no-any-expr]
else:
    _UnionTypes = (OldUnionType,)
    _Forms: TypeAlias = Union[type, _SpecialForm]

# TODO: make this work with any "form", not just unions
#  should be (form: TypeForm, forminfo: TypeForm)
# TODO: form/forminfo can include _UnionGenericAlias
def issubform(form: _Forms, forminfo: _Forms) -> bool:
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
    if isinstance(form, _UnionTypes):
        # Morally, form is an instance of "UnionType | _UnionGenericAlias"
        #  But _UnionGenericAlias doesn't have any representation at type time.
        for t in cast(Sequence[type], form.__args__):  # type: ignore[union-attr]
            if not issubform(t, forminfo):
                return False
        return True
    if sys.version_info < (3, 10) and isinstance(forminfo, OldUnionType):
        # Morally, forminfo is an instance of "_UnionGenericAlias"
        #  But _UnionGenericAlias doesn't have any representation at type time.
        for t in cast(Sequence[type], forminfo.__args__):  # type: ignore[unused-ignore, union-attr]
            if issubform(form, t):
                return True
        return False
    if form is Never:
        return True
    if forminfo is Never:
        return False
    return issubclass(form, forminfo)  # type: ignore[arg-type]


if TYPE_CHECKING:
    # We pretend that it's an alias to Any so that it's slightly more compatible with
    #  other tools, basedmypy will still utilize the SpecialForm over the TypeAlias.
    Untyped: TypeAlias = Any  # type: ignore[no-any-explicit]
else:
    if sys.version_info >= (3, 9):

        @_SpecialForm  # `_SpecialForm`s init isn't typed
        def Untyped(self: _SpecialForm, parameters: object) -> NoReturn:
            """Special type indicating that something isn't typed.

            This is more specialized than ``Any`` and can help with gradually typing modules.
            """
            raise TypeError(f"{self} is not subscriptable")

    else:
        Untyped: Final = _SpecialForm(
            "Untyped",
            doc=(
                "Special type indicating that something isn't typed.\nThis is more"
                " specialized than ``Any`` and can help with gradually typing modules."
            ),
        )
