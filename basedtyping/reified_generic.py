from __future__ import annotations

from typing import TYPE_CHECKING, Generic, NoReturn, Protocol, TypeVar, cast

from basedtyping.generics import T
from basedtyping.internal_typing_stubs import _GenericAlias
from basedtyping.runtime_checks import is_subclass


class _ReifiedGenericAlias(_GenericAlias, _root=True):
    def __call__(self, *args: NoReturn, **kwargs: NoReturn) -> object:
        """copied from _GenericAlias but modified to call _actual_call instead of __call__"""
        if not self._inst:
            raise TypeError(
                f"Type {self._name} cannot be instantiated; "
                f"use {self.__origin__.__name__}() instead"
            )
        result = cast(_ReifiedGenericMetaclass, self.__origin__)._actual_call(
            *args, **kwargs
        )
        try:
            result.__orig_class__ = self  # type:ignore[attr-defined]
        except AttributeError:
            pass
        return result

    def _type_vars(self) -> tuple[TypeVar, ...]:
        """gets a ``tuple`` of all the ``TypeVar``s defined in the `__origin__`.

        basically you should always use this instead of ``self.__parameters__``"""
        return cast(tuple[TypeVar, ...], getattr(self.__origin__, "__parameters__"))

    def _type_var_check(self, args: tuple[type, ...]) -> bool:
        for parameter, self_arg, subclass_arg in zip(
            self._type_vars(),
            self.__args__,
            args,
            strict=True,
        ):
            if parameter.__covariant__ and not is_subclass(subclass_arg, self_arg):
                return False
            if parameter.__contravariant__ and not is_subclass(self_arg, subclass_arg):
                return False
            if self_arg is not subclass_arg:
                return False
        return True

    def __subclasscheck__(self, subclass: object) -> bool:
        # could be any random class, check it first
        if not isinstance(subclass, _GenericAlias) or not is_subclass(
            subclass.__origin__, self.__origin__
        ):
            return False
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
    __parameters__: tuple[TypeVar, ...]


class NotReifiedException(Exception):
    pass


class _ReifiedGenericMetaclass(type, OrigClass):
    def _actual_call(cls, *args: NoReturn, **kwargs: NoReturn) -> object:
        """the actual  __call__ method for the generdic alias's ``__origin__``"""
        return cast(object, super().__call__(*args, **kwargs))

    def __call__(cls, *args: NoReturn, **kwargs: NoReturn) -> object:
        """a placeholder ``__call__`` method that only gets called if the ``ReifiedGeneric`` being instanciated isn't a ``_ReifiedGenericAlias``"""
        raise NotReifiedException(
            f"cannot instanciate ReifiedGeneric '{cls.__name__}' because its generics were not reified. "
            "the generics must be explicitly specified in the instanciation such that it can create a generic alias with the reified generics.\n\n"
            "for example:\n\n"
            "foo: Foo[int] = Foo()  # wrong\n"
            "foo = Foo[int]()  # correct"
        )


class ReifiedGeneric(Generic[T], metaclass=_ReifiedGenericMetaclass):
    """a ``Generic`` where the types of the ``TypeVars`` are checked to be reified (and visible at type-time),
    ie. can be accessed at runtime

    for example:

    >>> class Foo(ReifiedGeneric[T]):
    ...     def create_instance(self) -> T:
    ...         cls = self.__orig_class__.__args__[0]
    ...         return cls()
    ...
    ...  foo: Foo[int] = Foo() # error: generic cannot be reified
    ...  foo = Foo[int]() # no error, as the generic was reified via the generic alias

    to define multiple generics, use a tuple type:

    >>> class Foo(ReifiedGeneric[tuple[T, U]]):
    ...     ...
    ...
    ... foo = Foo[int, str]()

    since the generics are guaranteed to be reified, that means ``isinstance`` and ``issubclass`` checks work as well:

    >>> isinstance(Foo[int, str](), Foo[int, int])  # type:ignore[misc]
    False

    note: basedmypy currently doesn't allow generics in ``isinstance`` and ``issubclass`` checks, so for now you have to use
    ``basedtyping.runtime_checks.is_subclass`` for subclass checks and ``# type:ignore[misc]`` for instance checks. this issue
    is tracked [here](https://github.com/KotlinIsland/basedmypy/issues/5)
    """

    # TODO: somehow make this an instance property, but doing that with an `__init__` messes up the MRO (see the ReifiedList test)
    # currently mypy can't even tell the difference anyway https://github.com/python/mypy/issues/11832
    __orig_class__: OrigClass

    if not TYPE_CHECKING:
        # mypy doesn't check the signature of __class_getitem__ but complains when it doesn't match its signature in another base class
        # this is purely a runtime thing anyway so we can just do this

        def __class_getitem__(cls, item: T) -> type[ReifiedGeneric[T]]:
            generic_alias = super().__class_getitem__(item)
            return _ReifiedGenericAlias(
                generic_alias.__origin__, generic_alias.__args__
            )
