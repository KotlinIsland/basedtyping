"""This module only works at runtime. the types defined here do not work as type annotations
and are only intended for runtime checks, for example ``isinstance``.

This is the similar to the ``types`` module.
"""

from __future__ import annotations

import functools
import operator
import sys
import types
from _ast import AST, Attribute, BinOp, BitAnd, Constant, Load, Name, Subscript, Tuple
from ast import NodeTransformer, parse
from types import GenericAlias
from typing import (
    Final,
    Final as Final_ext,
    ForwardRef,
    Literal,
    Union,
    Unpack,
    _eval_type,
    _Final,
    _GenericAlias,
    _should_unflatten_callable_args,
    _strip_annotations,
    _type_check,
)

LiteralType: Final = type(Literal[1])
"""A type that can be used to check if type hints are a ``typing.Literal`` instance"""

# TODO: this is type[object], we need it to be 'SpecialForm[Union]' (or something)
OldUnionType: Final_ext[type[object]] = type(Union[str, int])
"""A type that can be used to check if type hints are a ``typing.Union`` instance."""


def get_type_hints(obj, globalns=None, localns=None, include_extras=False):
    if getattr(obj, "__no_type_check__", None):
        return {}
    # Classes require a special treatment.
    if isinstance(obj, type):
        hints = {}
        for base in reversed(obj.__mro__):
            if globalns is None:
                base_globals = getattr(
                    sys.modules.get(base.__module__, None), "__dict__", {}
                )
            else:
                base_globals = globalns
            ann = base.__dict__.get("__annotations__", {})
            if isinstance(ann, types.GetSetDescriptorType):
                ann = {}
            base_locals = dict(vars(base)) if localns is None else localns
            if localns is None and globalns is None:
                # This is surprising, but required.  Before Python 3.10,
                # get_type_hints only evaluated the globalns of
                # a class.  To maintain backwards compatibility, we reverse
                # the globalns and localns order so that eval() looks into
                # *base_globals* first rather than *base_locals*.
                # This only affects ForwardRefs.
                base_globals, base_locals = base_locals, base_globals
            p = BasedTypeParser()
            for name, value in ann.items():
                if value is None:
                    value = type(None)
                if isinstance(value, str):
                    value = p.visit(parse(value, mode="eval"))
                    # value = unparse(p.visit(parse(value)))
                    value = ForwardRef(value, is_argument=False, is_class=True)
                value = _eval_type(value, base_globals, base_locals)
                hints[name] = value
        return (
            hints
            if include_extras
            else {k: _strip_annotations(t) for k, t in hints.items()}
        )

    if globalns is None:
        if isinstance(obj, types.ModuleType):
            globalns = obj.__dict__
        else:
            nsobj = obj
            # Find globalns for the unwrapped object.
            while hasattr(nsobj, "__wrapped__"):
                nsobj = nsobj.__wrapped__
            globalns = getattr(nsobj, "__globals__", {})
        if localns is None:
            localns = globalns
    elif localns is None:
        localns = globalns
    hints = getattr(obj, "__annotations__", None)
    if hints is None:
        # Return empty annotations for something that _could_ have them.
        if isinstance(obj, _allowed_types):
            return {}
        else:
            raise TypeError(f"{obj!r} is not a module, class, method, or function.")
    hints = dict(hints)
    for name, value in hints.items():
        if value is None:
            value = type(None)
        if isinstance(value, str):
            # class-level forward refs were handled above, this must be either
            # a module-level annotation or a function argument annotation
            value = ForwardRef(
                value, is_argument=not isinstance(obj, types.ModuleType), is_class=False
            )
        hints[name] = _eval_type(value, globalns, localns)
    return (
        hints
        if include_extras
        else {k: _strip_annotations(t) for k, t in hints.items()}
    )


def _eval_type(t, globalns, localns, recursive_guard=frozenset()):
    """Evaluate all forward references in the given type t.
    For use of globalns and localns see the docstring for get_type_hints().
    recursive_guard is used to prevent infinite recursion with a recursive
    ForwardRef.
    """
    if isinstance(t, ForwardRef):
        return t._evaluate(globalns, localns, recursive_guard)
    if isinstance(t, (_GenericAlias, GenericAlias, types.UnionType)):
        if isinstance(t, GenericAlias):
            args = tuple(
                ForwardRef(arg) if isinstance(arg, str) else arg for arg in t.__args__
            )
            is_unpacked = t.__unpacked__
            if _should_unflatten_callable_args(t, args):
                t = t.__origin__[(args[:-1], args[-1])]
            else:
                t = t.__origin__[args]
            if is_unpacked:
                t = Unpack[t]
        ev_args = tuple(
            _eval_type(a, globalns, localns, recursive_guard) for a in t.__args__
        )
        if ev_args == t.__args__:
            return t
        if isinstance(t, GenericAlias):
            return GenericAlias(t.__origin__, ev_args)
        if isinstance(t, types.UnionType):
            return functools.reduce(operator.or_, ev_args)
        else:
            return t.copy_with(ev_args)
    return t


class BasedForwardRef(_Final, _root=True):
    """Internal wrapper to hold a forward reference."""

    def __init__(self, arg, is_argument=True, module=None, *, is_class=False):
        if isinstance(arg, str):
            # If we do `def f(*args: *Ts)`, then we'll have `arg = '*Ts'`.
            # Unfortunately, this isn't a valid expression on its own, so we
            # do the unpacking manually.
            if arg[0] == "*":
                arg_to_compile = (  # E.g. (*Ts,)[0] or (*tuple[int, int],)[0]
                    f"({arg},)[0]"
                )
            else:
                arg_to_compile = arg
        elif isinstance(arg, AST):
            arg_to_compile = arg
        else:
            raise TypeError(f"Forward reference must be a string or AST -- got {arg!r}")
        try:
            code = compile(arg_to_compile, "<string>", "eval")
        except SyntaxError:
            raise SyntaxError(f"Forward reference must be an expression -- got {arg!r}")
        self.__forward_arg__ = arg
        self.__forward_code__ = code
        self.__forward_evaluated__ = False
        self.__forward_value__ = None
        self.__forward_is_argument__ = is_argument
        self.__forward_is_class__ = is_class
        self.__forward_module__ = module

    def _evaluate(self, globalns, localns, recursive_guard):
        if self.__forward_arg__ in recursive_guard:
            return self
        if not self.__forward_evaluated__ or localns is not globalns:
            if globalns is None and localns is None:
                globalns = localns = {}
            elif globalns is None:
                globalns = localns
            elif localns is None:
                localns = globalns
            if self.__forward_module__ is not None:
                globalns = getattr(
                    sys.modules.get(self.__forward_module__, None), "__dict__", globalns
                )
            import typing

            import basedtyping

            type_ = _type_check(
                eval(
                    self.__forward_code__,
                    globalns | {"__secret__": typing, "__basedsecret__": basedtyping},
                    localns,
                ),
                "Forward references must evaluate to types.",
                is_argument=self.__forward_is_argument__,
                allow_special_forms=self.__forward_is_class__,
            )
            self.__forward_value__ = _eval_type(
                type_, globalns, localns, recursive_guard | {self.__forward_arg__}
            )
            self.__forward_evaluated__ = True
        return self.__forward_value__


class BasedTypeParser(NodeTransformer):
    in_subscript = 0

    def __init__(self):
        self.load = Load()

    def visit_BinOp(self, node: BinOp) -> AST:
        if isinstance(node.op, BitAnd):
            extra = dict(lineno=node.lineno, col_offset=node.col_offset, ctx=self.load)
            return Subscript(
                Attribute(Name("__basedsecret__", **extra), "Intersection", **extra),
                Tuple([self.visit(node.left), self.visit(node.right)], **extra),
                **extra,
            )
        return self.generic_visit(node)

    def visit_Constant(self, node: Constant) -> AST:
        if isinstance(node.value, int):
            # todo enum

            extra = dict(lineno=node.lineno, col_offset=node.col_offset, ctx=self.load)
            return Subscript(
                Attribute(Name("__secret__", **extra), "Literal", **extra),
                node,
                **extra,
            )
        return self.generic_visit(node)

    def visit_Tuple(self, node: Tuple) -> AST:
        if self.in_subscript:
            self.in_subscript = False
            return self.generic_visit(node)
        extra = dict(lineno=node.lineno, col_offset=node.col_offset, ctx=self.load)
        return Subscript(Name("__secret__.Tuple"), self.generic_visit(node), **extra)

    def visit_Subscript(self, node: Subscript) -> AST:
        if isinstance(node.slice, Tuple):
            self.in_subscript = True
        try:
            return self.generic_visit(node)
        finally:
            self.in_subscript = False
