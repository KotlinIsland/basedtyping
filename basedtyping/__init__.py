"""The main ``basedtyping`` module. the types/functions defined here can be used at
both type-time and at runtime.
"""

from __future__ import annotations

import ast
import sys
import types
import typing
import warnings
from typing import (  # type: ignore[attr-defined]
    TYPE_CHECKING,
    Any,
    Callable,
    Final,
    Generic,
    Mapping,
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
    cast,
)

import typing_extensions
from typing_extensions import Never, ParamSpec, Self, TypeAlias, TypeGuard, TypeVarTuple, override

from basedtyping import transformer
from basedtyping.runtime_only import OldUnionType

# TODO: `Final[Literal[False]]` basedmypy will still whinge on usages
#  https://github.com/KotlinIsland/basedmypy/issues/782
BASEDMYPY_TYPE_CHECKING: Final = False
"""special constants, are always `False`, but will always assume it to be true
by the respective tool
"""


if not TYPE_CHECKING:
    if sys.version_info >= (3, 11):
        from typing import _collect_parameters
    else:
        from typing import _collect_type_vars as _collect_parameters

__all__ = (
    "AnyCallable",
    "FunctionType",
    "TCallable",
    "TFunction",
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
    "as_functiontype",
    "ForwardRef",
    "BASEDMYPY_TYPE_CHECKING",
)

if TYPE_CHECKING:
    _tp_cache_typed: Callable[[T], T]
else:
    _tp_cache_typed = _tp_cache


class _BasedSpecialForm(_SpecialForm, _root=True):  # type: ignore[misc]
    _name: str

    @override
    def __init_subclass__(cls, _root=False):
        super().__init_subclass__(_root=_root)  # type: ignore[call-arg]

    def __init__(self, *args: object, **kwargs: object):
        self.alias = kwargs.pop("alias", _BasedGenericAlias)
        super().__init__(*args, **kwargs)

    @override
    def __repr__(self) -> str:
        return "basedtyping." + self._name

    def __and__(self, other: object) -> object:
        return Intersection[self, other]

    def __rand__(self, other: object) -> object:
        return Intersection[other, self]


class _BasedGenericAlias(_GenericAlias, _root=True):
    def __and__(self, other: object) -> object:
        return Intersection[self, other]

    def __rand__(self, other: object) -> object:
        return Intersection[other, self]


if TYPE_CHECKING:
    Function = Callable[..., object]  # type: ignore[no-any-explicit]
    """deprecated, use `AnyCallable`/`AnyFunction` instead. Any ``Callable``.

    useful when using mypy with ``disallow-any-explicit``
    due to https://github.com/python/mypy/issues/9496

    Cannot actually be called unless it's narrowed, so it should only really be used as
    a bound in a ``TypeVar``.
    """
else:
    # for isinstance checks
    Function = Callable

# Unlike the generics in other modules, these are meant to be imported to save you
#  from the boilerplate
T = TypeVar("T")
in_T = TypeVar("in_T", contravariant=True)
out_T = TypeVar("out_T", covariant=True)
Ts = TypeVarTuple("Ts")
P = ParamSpec("P")

AnyCallable = Callable[..., object]  # type: ignore[no-any-explicit]
"""Any ``Callable``. useful when using mypy with ``disallow-any-explicit``
due to https://github.com/python/mypy/issues/9496

Cannot actually be called unless it's narrowed, so it should only really be used as
a bound in a ``TypeVar``.
"""


if not BASEDMYPY_TYPE_CHECKING and TYPE_CHECKING:
    FunctionType: TypeAlias = Callable[P, T]
else:
    # TODO: BasedSpecialGenericAlias  # noqa: TD003
    FunctionType: _SpecialForm = typing._CallableType(types.FunctionType, 2)  # type: ignore[attr-defined]

AnyFunction = FunctionType[..., object]  # type: ignore[no-any-explicit]

TCallable = TypeVar("TCallable", bound=AnyCallable)
TFunction = TypeVar("TFunction", bound=AnyFunction)
Fn = TypeVar("Fn", bound=AnyCallable)
"""deprecated, use `TCallable` or `TFunction` instead"""


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
    """Raised when type parameters are passed to a ``ReifiedGeneric`` with an
     incorrect number of type parameters:

    for example:
    >>> class Foo(ReifiedGeneric[Tuple[T, U]]):
    ...     ...
    ...
    ... foo = Foo[int]() # wrong
    ... foo = Foo[int, str]() # correct
    """


class _ReifiedGenericMetaclass(type):
    # these should really only be on the class not the metaclass,
    #  but since it needs to be accessible from both instances and the class itself,
    #  its duplicated here

    __reified_generics__: tuple[type, ...]
    """should be a generic but cant due to https://github.com/python/mypy/issues/11672"""

    __type_vars__: tuple[TypeVar, ...]
    """``TypeVar``s that have not yet been reified. so this Tuple should always be empty
     by the time the ``ReifiedGeneric`` is instanciated"""

    _orig_type_vars: tuple[TypeVar, ...]
    """used internally to check the ``__type_vars__`` on the current ``ReifiedGeneric``
     against the original one it was copied from
     in ``ReifiedGeneric.__class_getitem__``"""

    _can_do_instance_and_subclass_checks_without_generics: bool
    """Used internally for ``isinstance`` and ``issubclass`` checks, ``True``
     when the class can currenty be used in said checks without generics in them"""

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
        if len(cls._orig_class().__parameters__) != len(cls.__reified_generics__) == len(args):  # type: ignore[attr-defined]
            raise RuntimeError
        for parameter, self_arg, subclass_arg in zip(
            # normal generics use __parameters__, we use __type_vars__ because the
            #  Generic base class deletes properties named __parameters__ when copying
            #  to a new class
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

    @override
    def __subclasscheck__(cls, subclass: object) -> bool:
        if not cls._is_subclass(subclass):
            return False
        if cls._can_do_instance_and_subclass_checks_without_generics:
            return True
        # if one of the classes doesn't have any generics, we treat it as the widest
        #  possible values for those generics (like star projection)
        if not hasattr(subclass, "__reified_generics__"):
            # TODO: subclass could be wider, but we don't know for sure because cls could have generics matching its bound  # noqa: TD003
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

    @override
    def __instancecheck__(cls, instance: object) -> bool:
        if not cls._is_subclass(type(instance)):
            return False
        if cls._can_do_instance_and_subclass_checks_without_generics:
            return True
        return cls._type_var_check(cast(ReifiedGeneric[object], instance).__reified_generics__)

    # need the generic here for pyright. see https://github.com/microsoft/pyright/issues/5488
    @override
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

    note: basedmypy currently doesn't allow generics in ``isinstance`` and
     ``issubclass`` checks, so for now you have to use ``basedtyping.issubform`` for
     subclass checks and ``# type: ignore[misc]`` for instance checks. this issue
     is tracked [here](https://github.com/KotlinIsland/basedmypy/issues/5)
    """

    __reified_generics__: tuple[type, ...]
    """Should be a generic but cant due to https://github.com/KotlinIsland/basedmypy/issues/142"""
    __type_vars__: tuple[TypeVar, ...]
    """``TypeVar``\\s that have not yet been reified. so this Tuple should always be\
    empty by the time the ``ReifiedGeneric`` is instantiated"""

    @_tp_cache  # type: ignore[no-any-expr, misc]
    def __class_getitem__(  # type: ignore[no-any-decorated]
        cls, item: GenericItems
    ) -> type[ReifiedGeneric[T]]:
        # when defining the generic (ie. `class Foo(ReifiedGeneric[T]):`) we
        #  want the normal behavior
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
            # TODO: investigate this unreachable, redundant-expr  # noqa: TD003
            if not isinstance(generic, TypeVar)  # type: ignore[unused-ignore, unreachable, redundant-expr, no-any-expr]
        )

        # normal generics use __parameters__, we use __type_vars__ because the
        #  Generic base class deletes properties named __parameters__ when copying
        #  to a new class
        orig_type_vars = (
            cls.__type_vars__
            if hasattr(cls, "__type_vars__")
            else cast(
                Tuple[TypeVar, ...],
                cls.__parameters__,  # type:ignore[attr-defined]
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
        reified_generic_copy: type[ReifiedGeneric[T]] = type(
            cls.__name__,
            (
                cls,  # make the copied class extend the original so normal instance checks work
            ),
            # TODO: proper type  # noqa: TD003
            {  # type: ignore[no-any-expr]
                "__reified_generics__": tuple(  # type: ignore[no-any-expr]
                    _type_convert(t)
                    for t in items  # type: ignore[unused-ignore, no-any-expr]
                ),
                "_orig_type_vars": orig_type_vars,
                "__type_vars__": _collect_parameters(items),  # type: ignore[name-defined]
            },
        )
        # can't set it in the dict above otherwise __init_subclass__ overwrites it
        reified_generic_copy._can_do_instance_and_subclass_checks_without_generics = False
        return reified_generic_copy

    @override
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


# TODO: make this work with any "form", not just unions  # noqa: TD003
#  should be (form: TypeForm, forminfo: TypeForm)
# TODO: form/forminfo can include _UnionGenericAlias  # noqa: TD003
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
            issubform(t, forminfo)
            for t in cast(Sequence[type], form.__args__)  # type: ignore[union-attr]
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


if BASEDMYPY_TYPE_CHECKING or not TYPE_CHECKING:

    @_BasedSpecialForm
    def Untyped(  # noqa: N802
        self: _BasedSpecialForm,
        parameters: object,  # noqa: ARG001
    ) -> NoReturn:
        """Special type indicating that something isn't typed.

        This is more specialized than ``Any`` and can help with gradually typing modules.
        """
        raise TypeError(f"{self} is not subscriptable")
else:
    # We pretend that it's an alias to Any so that it's slightly more compatible with
    #  other tools
    Untyped: TypeAlias = Any  # type: ignore[no-any-explicit]


class _IntersectionGenericAlias(_BasedGenericAlias, _root=True):
    @override
    def copy_with(self, args: object) -> Self:  # type: ignore[override] # TODO: put in the overloads  # noqa: TD003
        return cast(Self, Intersection[args])

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _IntersectionGenericAlias):
            return NotImplemented
        return set(self.__args__) == set(other.__args__)

    @override
    def __hash__(self) -> int:
        return hash(frozenset(self.__args__))

    def __instancecheck__(self, obj: object) -> bool:
        return self.__subclasscheck__(type(obj))

    def __subclasscheck__(self, cls: type[object]) -> bool:
        return all(issubclass(cls, arg) for arg in self.__args__)

    @override
    def __reduce__(self) -> (object, object):
        func, (_, args) = super().__reduce__()  # type: ignore[no-any-expr, misc]
        return func, (Intersection, args)


@_BasedSpecialForm
def Intersection(self: _BasedSpecialForm, parameters: object) -> object:  # noqa: N802
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
    parameters = tuple(_type_check(p, msg) for p in parameters)
    parameters = _remove_dups_flatten(parameters)  # type: ignore[no-any-expr]
    if len(parameters) == 1:  # type: ignore[no-any-expr]
        return parameters[0]  # type: ignore[no-any-expr]
    return _IntersectionGenericAlias(self, parameters)  # type: ignore[arg-type, no-any-expr]


class _TypeFormForm(_BasedSpecialForm, _root=True):  # type: ignore[misc]
    # TODO: decorator-ify  # noqa: TD003
    def __init__(self, doc: str):
        self._name = "TypeForm"
        self._doc = self.__doc__ = doc

    @override
    def __getitem__(self, parameters: object | tuple[object]) -> _BasedGenericAlias:
        if not isinstance(parameters, tuple):
            parameters = (parameters,)

        return _BasedGenericAlias(self, parameters)  # type: ignore[arg-type]


TypeForm = _TypeFormForm(
    doc="""\
         A type that can be used to represent a ``builtins.type`` or a ``SpecialForm``.
         For example:

             def f[T](t: TypeForm[T]) -> T: ...

             reveal_type(f(int | str))  # int | str
         """
)


def as_functiontype(fn: Callable[P, T]) -> FunctionType[P, T]:
    """Asserts that a ``Callable`` is a ``FunctionType`` and returns it

    best used as a decorator to fix other incorrectly typed decorators:

        def deco(fn: Callable[[], None]) -> Callable[[], None]: ...

        @as_functiontype
        @deco
        def foo(): ...
    """
    if not isinstance(fn, types.FunctionType):
        raise TypeError(f"{fn} is not a FunctionType")
    return cast(FunctionType[P, T], fn)


class ForwardRef(typing.ForwardRef, _root=True):  # type: ignore[call-arg,misc]
    """
    Like `typing.ForwardRef`, but lets older Python versions use newer typing features.
    Specifically, when evaluated, this transforms `X | Y` into `typing.Union[X, Y]`
    and `list[X]` into `typing.List[X]` etc. (for all the types made generic in PEP 585)
    if the original syntax is not supported in the current Python version.
    """

    # older typing.ForwardRef doesn't have this
    if sys.version_info < (3, 10):
        __slots__ = ("__forward_module__", "__forward_is_class__")
    elif sys.version_info < (3, 11):
        __slots__ = ("__forward_is_class__",)

    def __init__(self, arg: str, *, is_argument=True, module: object = None, is_class=False):
        if not isinstance(arg, str):  # type: ignore[redundant-expr]
            raise TypeError(f"Forward reference must be a string -- got {arg!r}")

        # If we do `def f(*args: *Ts)`, then we'll have `arg = '*Ts'`.
        # Unfortunately, this isn't a valid expression on its own, so we
        # do the unpacking manually.
        arg_to_compile = (
            f"({arg},)[0]"  # E.g. (*Ts,)[0] or (*tuple[int, int],)[0]
            if arg.startswith("*")
            else arg
        )
        try:
            with warnings.catch_warnings():
                # warnings come from some based syntax, i can't remember what
                warnings.simplefilter("ignore", category=SyntaxWarning)
                code = compile(arg_to_compile, "<string>", "eval")
        except SyntaxError:
            try:
                ast.parse(arg_to_compile.removeprefix("def "), mode="func_type")
            except SyntaxError:
                raise SyntaxError(f"invalid syntax in ForwardRef: {arg_to_compile}?") from None
            else:
                code = compile("'un-representable callable type'", "<string>", "eval")

        self.__forward_arg__ = arg
        self.__forward_code__ = code
        self.__forward_evaluated__ = False
        self.__forward_value__ = None
        self.__forward_is_argument__ = is_argument
        self.__forward_is_class__ = is_class
        self.__forward_module__ = module

    if sys.version_info >= (3, 13):

        @override
        def _evaluate(
            self,
            globalns: dict[str, object] | None,
            localns: Mapping[str, object] | None,
            type_params: tuple[TypeVar | ParamSpec | TypeVarTuple, ...] = (),
            *,
            recursive_guard: frozenset[str],
        ) -> object | None:
            return transformer._eval_direct(
                self, globalns, localns if localns is None else dict(localns)
            )

    elif sys.version_info >= (3, 12):

        @override
        def _evaluate(
            self,
            globalns: dict[str, object] | None,
            localns: Mapping[str, object] | None,
            type_params: tuple[TypeVar | typing.ParamSpec | typing.TypeVarTuple, ...] | None = None,
            *,
            recursive_guard: frozenset[str],
        ) -> object | None:
            return transformer._eval_direct(
                self, globalns, localns if localns is None else dict(localns)
            )

    else:

        @override
        def _evaluate(
            self,
            globalns: dict[str, object] | None,
            localns: Mapping[str, object] | None,
            recursive_guard: frozenset[str],
        ) -> object | None:
            return transformer._eval_direct(
                self, globalns, localns if localns is None else dict(localns)
            )


def _type_check(arg: object, msg: str) -> object:
    """Check that the argument is a type, and return it (internal helper).

    As a special case, accept None and return type(None) instead. Also wrap strings
    into ForwardRef instances. Consider several corner cases, for example plain
    special forms like Union are not valid, while Union[int, str] is OK, etc.
    The msg argument is a human-readable error message, e.g::

        "Union[arg, ...]: arg should be a type."

    We append the repr() of the actual value (truncated to 100 chars).
    """
    invalid_generic_forms = (Generic, typing.Protocol)

    arg = _type_convert(arg)
    if isinstance(arg, _GenericAlias) and arg.__origin__ in invalid_generic_forms:  # type: ignore[comparison-overlap]
        raise TypeError(f"{arg} is not valid as type argument")
    if arg in (Any, NoReturn, typing.Final, Untyped):
        return arg
    if isinstance(arg, _SpecialForm) or arg in (Generic, typing.Protocol):
        raise TypeError(f"Plain {arg} is not valid as type argument")
    if isinstance(arg, (type, TypeVar, ForwardRef)):
        return arg
    if not callable(arg):
        raise TypeError(f"{msg} Got {arg!r:.100}.")
    return arg
