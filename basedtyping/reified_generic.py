from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Protocol, TypeVar

from basedtyping.generics import T
from basedtyping.internal_typing_stubs import _GenericAlias
from basedtyping.runtime_checks import is_subclass


class _ReifiedGenericAlias(_GenericAlias, _root=True):
    def __subclasscheck__(self, subclass: object) -> bool:
        # could be any random class, check it first
        if not isinstance(subclass, _GenericAlias) or not is_subclass(
            subclass.__origin__, self.__origin__
        ):
            return False
        for parameter, self_arg, subclass_arg in zip(
            self.__parameters__, self.__args__, subclass.__args__
        ):
            if parameter.__covariant__ and not is_subclass(subclass_arg, self_arg):
                return False
            if parameter.__contravariant__ and not is_subclass(self_arg, subclass_arg):
                return False
            if self_arg is not subclass_arg:
                return False
        return True

    def __instancecheck__(self, instance: object) -> bool:
        # could be any random instance, check it first
        if not isinstance(instance, self.__origin__) or not isinstance(
            instance, ReifiedGeneric
        ):
            return False
        for parameter, self_arg, subclass_arg in zip(
            self.__parameters__, self.__args__, instance.__orig_class__.__args__
        ):
            if parameter.__covariant__ and not is_subclass(subclass_arg, self_arg):
                return False
            if parameter.__contravariant__ and not is_subclass(self_arg, subclass_arg):
                return False
            if self_arg is not subclass_arg:
                return False
        return True


class OrigClass(Protocol):
    __args__: tuple[type, ...]
    __parameters__: tuple[TypeVar, ...]


class _ReifiedGenericMetaclass(type, OrigClass):
    pass


class ReifiedGeneric(Generic[T], metaclass=_ReifiedGenericMetaclass):
    """
    TODO: fail if generics not provided
    """

    def __init__(self) -> None:
        self.__orig_class__: OrigClass

    # mypy doesn't check the signature of __class_getitem__ but complains when it doesn't match its signature in another base class
    # this is purely a runtime thing anyway so we can just do this
    if not TYPE_CHECKING:

        def __class_getitem__(cls, item: T) -> type[ReifiedGeneric[T]]:
            generic_alias = super().__class_getitem__(item)
            return _ReifiedGenericAlias(generic_alias.__origin__, generic_alias.__args__)
