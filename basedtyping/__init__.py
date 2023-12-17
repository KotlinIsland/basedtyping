"""The main ``basedtyping`` module. the types/functions defined here can be used at both type-time and at runtime."""

from __future__ import annotations

import sys
from typing import (  # type: ignore[attr-defined]
    TYPE_CHECKING,
    Any,
    Callable,
    Final,
    ForwardRef,
    Generic,
    NoReturn,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    _GenericAlias,
    _remove_dups_flatten,
    _SpecialForm,
    _tp_cache,
    _type_check,
    cast,
    _alias,
)

import _collections_abc
import typing_extensions
from typing_extensions import Never, ParamSpec, Self, TypeAlias, TypeGuard, TypeVarTuple

from basedtyping.runtime_only import OldUnionType

if not TYPE_CHECKING:
    if sys.version_info >= (3, 11):
        from typing import _collect_parameters
    else:
        from typing import _collect_type_vars as _collect_parameters

__all__ = (
    "Function",
    "T",
    "in_T",
    "out_T",
    "Ts",
    "P",
    "Fn",
    "ReifiedGenericError",
    "NotReifiedError",
    "ReifiedGeneric",
    "NotEnoughTypeParametersError",
    "issubform",
    "Untyped",
    "Intersection",
    "TypeForm",
)

if TYPE_CHECKING:
    _tp_cache_typed: Callable[[T], T]
else:
    _tp_cache_typed = _tp_cache


class _BasedSpecialForm(_SpecialForm, _root=True):  # type: ignore[misc]
    _name: str

    def __init_subclass__(cls, _root=False):  # noqa: FBT002
        super().__init_subclass__(_root=_root)  # type: ignore[call-arg]

    def __init__(self, *args: object, **kwargs: object):
        self.alias = kwargs.pop("alias", _BasedGenericAlias)
        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        return "basedtyping." + self._name

    def __and__(self, other: object) -> object:
        return Intersection[self, other]

    def __rand__(self, other: object) -> object:
        return Intersection[other, self]

    if sys.version_info < (3, 9):

        @_tp_cache_typed
        def __getitem__(self, item: object) -> object:
            return self.alias(self, item)  # type: ignore[operator]


class _BasedGenericAlias(_GenericAlias, _root=True):
    def __and__(self, other: object) -> object:
        return Intersection[self, other]

    def __rand__(self, other: object) -> object:
        return Intersection[other, self]


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
in_T = TypeVar("in_T", contravariant=True)
out_T = TypeVar("out_T", covariant=True)
Ts = TypeVarTuple("Ts")
P = ParamSpec("P")
Fn = TypeVar("Fn", bound=Function)


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

    __reified_generics__: tuple[type, ...]
    """should be a generic but cant due to https://github.com/python/mypy/issues/11672"""

    __type_vars__: tuple[TypeVar, ...]
    """``TypeVar``s that have not yet been reified. so this Tuple should always be empty by the time the ``ReifiedGeneric`` is instanciated"""

    _orig_type_vars: tuple[TypeVar, ...]
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

    def _type_var_check(cls, args: tuple[type, ...]) -> bool:
        if not cls._generics_are_reified():
            if cls._has_non_reified_type_vars():
                cls._raise_generics_not_reified()
            return True
        assert len(cls._orig_class().__parameters__) == len(cls.__reified_generics__) == len(args)  # type: ignore[attr-defined]
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

    def _check_generics_reified(cls):
        if not cls._generics_are_reified() or cls._has_non_reified_type_vars():
            cls._raise_generics_not_reified()

    def _is_subclass(cls, subclass: object) -> TypeGuard[_ReifiedGenericMetaclass]:
        """For ``__instancecheck__`` and ``__subclasscheck__``. checks whether the
        "origin" type (ie. without the generics) is a subclass of this reified generic
        """
        # could be any random instance, check it's a reified generic first:
        return type.__instancecheck__(
            _ReifiedGenericMetaclass,
            subclass,
            # then check that the instance is an instance of this particular reified generic:
        ) and type.__subclasscheck__(
            cls._orig_class(),
            # https://github.com/python/mypy/issues/11671
            cast(_ReifiedGenericMetaclass, subclass)._orig_class(),
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

    # need the generic here for pyright. see https://github.com/microsoft/pyright/issues/5488
    def __call__(cls: type[T], *args: object, **kwargs: object) -> T:
        """A placeholder ``__call__`` method that gets called when the class is
        instantiated directly, instead of first supplying the type parameters.
        """
        cls_narrowed = cast(Type[ReifiedGeneric[object]], cls)
        if (
            # instantiating a ReifiedGeneric without specifying any TypeVars
            not hasattr(cls_narrowed, "_orig_type_vars")
            # instantiating a subtype of a ReifiedGeneric without specifying any TypeVars
            or cls_narrowed._orig_type_vars == cls_narrowed.__type_vars__
        ):
            raise NotReifiedError(
                f"Cannot instantiate ReifiedGeneric {cls_narrowed.__name__!r} because"
                " its type parameters were not supplied. The type parameters must be"
                " explicitly specified in the instantiation so that the type data can"
                " be made available at runtime.\n\nFor example:\n\nfoo: Foo[int] ="
                " Foo()  #wrong\nfoo = Foo[T]()  #wrong\nfoo = Foo[int]()  # correct"
            )
        cls_narrowed._check_generics_reified()
        # see comment about cls above
        return cast(T, super().__call__(*args, **kwargs))  # type:ignore[misc]


GenericItems: TypeAlias = Union[type, TypeVar, Tuple[Union[type, TypeVar], ...]]
"""The ``items`` argument passed to ``__class_getitem__`` when creating or using a ``Generic``"""


class ReifiedGeneric(Generic[T], metaclass=_ReifiedGenericMetaclass):
    """A ``Generic`` where the type parameters are available at runtime and is
    usable in ``isinstance`` and ``issubclass`` checks.

    For example:

    >>> class Foo(ReifiedGeneric[T]):
    ...     def create_instance(self) -> T:
    ...         cls = self.__reified_generics__[0]
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

    __reified_generics__: tuple[type, ...]
    """Should be a generic but cant due to https://github.com/KotlinIsland/basedmypy/issues/142"""
    __type_vars__: tuple[TypeVar, ...]
    """``TypeVar``\\s that have not yet been reified. so this Tuple should always be empty by the time the ``ReifiedGeneric`` is instantiated"""

    @_tp_cache  # type: ignore[no-any-expr, misc]
    def __class_getitem__(  # type: ignore[no-any-decorated]
        cls, item: GenericItems
    ) -> type[ReifiedGeneric[T]]:
        # when defining the generic (ie. `class Foo(ReifiedGeneric[T]):`) we want the normal behavior
        if cls is ReifiedGeneric:
            # https://github.com/KotlinIsland/basedtypeshed/issues/7
            return super().__class_getitem__(item)  # type: ignore[misc, no-any-return]

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
                Tuple[TypeVar, ...], cls.__parameters__  # type:ignore[attr-defined]
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
        ReifiedGenericCopy: type[ReifiedGeneric[T]] = type(
            cls.__name__,
            (
                cls,  # make the copied class extend the original so normal instance checks work
            ),
            # TODO: proper type
            {  # type: ignore[no-any-expr]
                "__reified_generics__": tuple(  # type: ignore[no-any-expr]
                    _type_convert(t) for t in items  # type: ignore[unused-ignore, no-any-expr]
                ),
                "_orig_type_vars": orig_type_vars,
                "__type_vars__": _collect_parameters(items),  # type: ignore[name-defined]
            },
        )
        # can't set it in the dict above otherwise __init_subclass__ overwrites it
        ReifiedGenericCopy._can_do_instance_and_subclass_checks_without_generics = False
        return ReifiedGenericCopy

    def __init_subclass__(cls):
        cls._can_do_instance_and_subclass_checks_without_generics = True
        super().__init_subclass__()


if sys.version_info >= (3, 10):
    from types import UnionType

    _UnionTypes = (UnionType, OldUnionType)
    _Forms: TypeAlias = type | UnionType | _SpecialForm | typing_extensions._SpecialForm  # type: ignore[unused-ignore, no-any-expr]
else:
    _UnionTypes = (OldUnionType,)
    _Forms: TypeAlias = Union[type, _SpecialForm, typing_extensions._SpecialForm]


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
        return all(
            issubform(t, forminfo) for t in cast(Sequence[type], form.__args__)  # type: ignore[union-attr]
        )
    if sys.version_info < (3, 10) and isinstance(forminfo, OldUnionType):
        # Morally, forminfo is an instance of "_UnionGenericAlias"
        #  But _UnionGenericAlias doesn't have any representation at type time.
        return any(issubform(form, t) for t in cast(Sequence[type], forminfo.__args__))  # type: ignore[union-attr]
    if form is Never:
        return True
    if forminfo is Never:
        return False
    return issubclass(form, forminfo)  # type: ignore[arg-type]


if TYPE_CHECKING:
    # We pretend that it's an alias to Any so that it's slightly more compatible with
    #  other tools, basedmypy will still utilize the SpecialForm over the TypeAlias.
    Untyped: TypeAlias = Any  # type: ignore[no-any-explicit]
elif sys.version_info >= (3, 9):

    @_BasedSpecialForm
    def Untyped(
        self: _BasedSpecialForm, parameters: object  # noqa: ARG001
    ) -> NoReturn:
        """Special type indicating that something isn't typed.

        This is more specialized than ``Any`` and can help with gradually typing modules.
        """
        raise TypeError(f"{self} is not subscriptable")

else:
    Untyped: Final = _BasedSpecialForm(
        "Untyped",
        doc=(
            "Special type indicating that something isn't typed.\nThis is more"
            " specialized than ``Any`` and can help with gradually typing modules."
        ),
    )


class _IntersectionGenericAlias(_BasedGenericAlias, _root=True):
    def copy_with(self, args: object) -> Self:  # type: ignore[override] # TODO: put in the overloads
        return cast(Self, Intersection[args])

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _IntersectionGenericAlias):
            return NotImplemented
        return set(self.__args__) == set(other.__args__)

    def __hash__(self) -> int:
        return hash(frozenset(self.__args__))

    def __instancecheck__(self, obj: object) -> bool:
        return self.__subclasscheck__(type(obj))

    def __subclasscheck__(self, cls: type[object]) -> bool:
        return all(issubclass(cls, arg) for arg in self.__args__)

    def __reduce__(self) -> (object, object):
        func, (_, args) = super().__reduce__()  # type: ignore[no-any-expr, misc]
        return func, (Intersection, args)


if sys.version_info > (3, 9):

    @_BasedSpecialForm
    def Intersection(self: _BasedSpecialForm, parameters: object) -> object:
        """Intersection type; Intersection[X, Y] means both X and Y.

        To define an intersection:
        - If using __future__.annotations, shortform can be used e.g. A & B
        - otherwise the fullform must be used e.g. Intersection[A, B].

        Details:
        - The arguments must be types and there must be at least one.
        - None as an argument is a special case and is replaced by
          type(None).
        - Intersections of intersections are flattened, e.g.::

            Intersection[Intersection[int, str], float] == Intersection[int, str, float]

        - Intersections of a single argument vanish, e.g.::

            Intersection[int] == int  # The constructor actually returns int

        - Redundant arguments are skipped, e.g.::

            Intersection[int, str, int] == Intersection[int, str]

        - When comparing intersections, the argument order is ignored, e.g.::

            Intersection[int, str] == Intersection[str, int]

        - You cannot subclass or instantiate an intersection.
        """
        if parameters == ():
            raise TypeError("Cannot take an Intersection of no types.")
        if not isinstance(parameters, tuple):
            parameters = (parameters,)
        msg = "Intersection[arg, ...]: each arg must be a type."
        parameters = tuple(_type_check(p, msg) for p in parameters)  # type: ignore[no-any-expr]
        parameters = _remove_dups_flatten(parameters)  # type: ignore[no-any-expr]
        if len(parameters) == 1:  # type: ignore[no-any-expr]
            return parameters[0]  # type: ignore[no-any-expr]
        return _IntersectionGenericAlias(self, parameters)  # type: ignore[arg-type, no-any-expr]

else:
    Intersection = _BasedSpecialForm(
        "Intersection", doc="", alias=_IntersectionGenericAlias
    )


class _TypeFormForm(_BasedSpecialForm, _root=True):  # type: ignore[misc]
    def __init__(self, doc: str):
        self._name = "TypeForm"
        self._doc = self.__doc__ = doc

    def __getitem__(self, parameters: object | tuple[object]) -> _BasedGenericAlias:
        if not isinstance(parameters, tuple):
            parameters = (parameters,)

        return _BasedGenericAlias(self, parameters)  # type: ignore[arg-type]


TypeForm = _TypeFormForm(doc="""\
                         A type that can be used to represent a ``builtins.type`` or a ``SpecialForm``.
                         For example:
                        
                             def f[T](t: TypeForm[T]) -> T: ...
                            
                             reveal_type(f(int | str))  # int | str
                         """)

# generic aliases
if TYPE_CHECKING:
    dict_keyiterator = _collections_abc.dict_keyiterator  # type: ignore[attr-defined]
    dict_valueiterator = _collections_abc.dict_valueiterator  # type: ignore[attr-defined]
    dict_itemiterator = _collections_abc.dict_itemiterator  # type: ignore[attr-defined]
    list_iterator = _collections_abc.list_iterator  # type: ignore[attr-defined]
    list_reverseiterator = _collections_abc.list_reverseiterator  # type: ignore[attr-defined]
    set_iterator = _collections_abc.set_iterator  # type: ignore[attr-defined]
    tuple_iterator = _collections_abc.tuple_iterator  # type: ignore[attr-defined]
    dict_keys = _collections_abc.dict_keys
    dict_values = _collections_abc.dict_values
    dict_items = _collections_abc.dict_items
else:
    dict_keyiterator = _alias(_collections_abc.dict_keyiterator, 2)
    dict_valueiterator = _alias(_collections_abc.dict_valueiterator, 2)
    dict_itemiterator = _alias(_collections_abc.dict_itemiterator, 2)
    list_iterator = _alias(_collections_abc.list_iterator, 1)
    list_reverseiterator = _alias(_collections_abc.list_reverseiterator, 1)
    set_iterator = _alias(_collections_abc.set_iterator, 1)
    tuple_iterator = _alias(_collections_abc.tuple_iterator, -1)
    dict_keys = _alias(_collections_abc.dict_keys, 2)
    dict_values = _alias(_collections_abc.dict_values, 2)
    dict_items = _alias(_collections_abc.dict_items, 2)
