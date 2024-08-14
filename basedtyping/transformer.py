"""utilities to create standard compatible annotations"""

from __future__ import annotations

import ast
import sys
import types
import typing
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from functools import partial
from typing import cast

import typing_extensions
from typing_extensions import override

import basedtyping


@dataclass
class EvalFailedError(TypeError):
    """Raised when `CringeTransformer.eval_type` fails"""

    message: str
    ref: typing.ForwardRef
    transformer: CringeTransformer


# ruff: noqa: S101 erm, i wanted to use assert TODO: do something better
class CringeTransformer(ast.NodeTransformer):
    """Transforms `1 | 2` into `Literal[1] | Literal[2]` etc"""

    def __init__(
        self,
        globalns: dict[str, object] | None,
        localns: dict[str, object] | None,
        *,
        string_literals: bool,
    ):
        self.string_literals = string_literals

        # This logic for handling Nones is copied from typing.ForwardRef._evaluate
        if globalns is None and localns is None:
            globalns = localns = {}
        elif globalns is None:
            assert localns is not None
            globalns = localns
        elif localns is None:
            assert globalns is not None
            localns = globalns

        fair_and_unique_uuid_roll = "c4357574960843a2a8f9eb0c11aa88e5"
        self.typing_name = f"_typing_extensions_{fair_and_unique_uuid_roll}"
        self.basedtyping_name = f"_basedtyping_{fair_and_unique_uuid_roll}"
        self.globalns = globalns

        self.localns = localns | {
            self.typing_name: typing_extensions,
            self.basedtyping_name: basedtyping,
        }

    @override
    def visit(self, node: ast.AST) -> ast.AST:
        return cast(ast.AST, super().visit(node))

    def eval_type(
        self,
        node: ast.FunctionType | ast.Expression | ast.expr,
        *,
        original_ref: typing.ForwardRef | None = None,
    ) -> object:
        if isinstance(node, ast.expr):
            node = ast.copy_location(ast.Expression(node), node)
        ref = typing.ForwardRef(ast.unparse(node))
        if original_ref:
            for attr in ("is_argument", " is_class", "module"):
                attr = f"__forward_{attr}__"
                if hasattr(original_ref, attr):
                    setattr(ref, attr, cast(object, getattr(original_ref, attr)))
        if not isinstance(node, ast.FunctionType):
            ref.__forward_code__ = compile(node, "<node>", "eval")
        try:
            type_ = typing._type_convert(  # type: ignore[attr-defined]
                cast(object, eval(ref.__forward_code__, self.globalns, self.localns))  # noqa: S307
            )
            if sys.version_info >= (3, 13):
                return typing._eval_type(  # type: ignore[attr-defined]
                    type_, self.globalns, self.localns, type_params=()
                )
            else:  # noqa: RET505 mypy prefers it in different branches TODO: raise an issue
                return typing._eval_type(  # type: ignore[attr-defined]
                    type_, self.globalns, self.localns
                )
        except TypeError as e:
            raise EvalFailedError(str(e), ref, self) from e

    def _typing(self, attr: str) -> ast.Attribute:
        result = ast.Attribute(
            value=ast.Name(id=self.typing_name, ctx=ast.Load()), attr=attr, ctx=ast.Load()
        )
        return ast.fix_missing_locations(result)

    def _basedtyping(self, attr: str) -> ast.Attribute:
        result = ast.Attribute(
            value=ast.Name(id=self.basedtyping_name, ctx=ast.Load()), attr=attr, ctx=ast.Load()
        )
        return ast.fix_missing_locations(result)

    def _literal(self, value: ast.Constant | ast.Name | ast.Attribute) -> ast.Subscript:
        return self.subscript(self._typing("Literal"), value)

    def subscript(self, value: ast.expr, slice_: ast.expr) -> ast.Subscript:
        result = ast.Subscript(value=value, slice=slice_, ctx=ast.Load())
        return ast.fix_missing_locations(result)

    _implicit_tuple = False

    @contextmanager
    def implicit_tuple(self, *, value=True) -> typing.Iterator[None]:
        implicit_tuple = self._implicit_tuple
        self._implicit_tuple = value
        try:
            yield
        finally:
            self._implicit_tuple = implicit_tuple

    @override
    def visit_Subscript(self, node: ast.Subscript) -> ast.AST:
        node_type = self.eval_type(node.value)
        if self.eval_type(node.value) is typing_extensions.Literal:
            return node
        if node_type is typing_extensions.Annotated:
            slice_ = node.slice
            if isinstance(slice_, ast.Tuple):
                temp = self.visit(slice_.elts[0])
                assert isinstance(temp, ast.expr)
                slice_.elts[0] = temp
            else:
                temp = self.visit(slice_)
                assert isinstance(temp, ast.expr)
                node.slice = temp
            return node
        with self.implicit_tuple():
            result = self.generic_visit(node)
            assert isinstance(result, ast.Subscript)
            node = result

        node_type = self.eval_type(node.value)
        if node_type is types.FunctionType:
            slice2_ = node.slice
            node = self.subscript(self._typing("Callable"), slice2_)
        return node

    @override
    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        node = self.generic_visit(node)
        assert isinstance(node, ast.expr)
        node_type = self.eval_type(node)
        if isinstance(node_type, Enum):
            assert isinstance(node, (ast.Name, ast.Attribute))
            return self._literal(node)
        return node

    @override
    def visit_Name(self, node: ast.Name) -> ast.AST:
        name_type = self.eval_type(node)
        if isinstance(name_type, Enum):
            return self._literal(node)
        return node

    @override
    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        value = cast(object, node.value)
        if not self.string_literals and isinstance(value, str):
            return self._transform(basedtyping.ForwardRef(value)).body
        if isinstance(value, int) or (self.string_literals and isinstance(value, str)):
            return self._literal(node)
        return node

    @override
    def visit_Tuple(self, node: ast.Tuple) -> ast.AST:
        with self.implicit_tuple(value=False):
            result = self.generic_visit(node)
        if not self._implicit_tuple:
            return self.subscript(self._typing("Tuple"), cast(ast.expr, result))
        return result

    @override
    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        if len(node.ops) == 1 and isinstance(node.ops[0], ast.Is):
            result = self.subscript(
                self._typing("TypeIs"), cast(ast.expr, self.generic_visit(node.comparators[0]))
            )
            return self.generic_visit(result)
        return self.generic_visit(node)

    @override
    def visit_IfExp(self, node: ast.IfExp) -> ast.AST:
        if (
            isinstance(node.body, ast.Compare)
            and len(node.body.comparators) == 1
            and isinstance(node.body.ops[0], ast.Is)
        ):
            node.body = self.subscript(
                self._typing("TypeGuard"),
                cast(ast.expr, self.generic_visit(node.body.comparators[0])),
            )
        return self.generic_visit(node)

    def visit_FunctionType(self, node: ast.FunctionType) -> ast.AST:  # noqa: N802 https://github.com/KotlinIsland/basedmypy/issues/763
        node = self.generic_visit(node)
        assert isinstance(node, ast.FunctionType)
        return ast.Expression(
            self.subscript(
                self._typing("Callable"),
                ast.Tuple([ast.List(node.argtypes, ctx=ast.Load()), node.returns], ctx=ast.Load()),
            )
        )

    @override
    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        node = self.generic_visit(node)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitAnd):
            node = self.subscript(
                self._basedtyping("Intersection"),
                ast.Tuple([node.left, node.right], ctx=ast.Load()),
            )
        return node

    def _transform(self, value: typing.ForwardRef) -> ast.Expression:
        tree: ast.AST
        try:
            tree = ast.parse(value.__forward_arg__, mode="eval")
        except SyntaxError:
            arg = value.__forward_arg__.lstrip()
            if arg.startswith(("def ", "def(")):
                arg = arg[3:].lstrip()
            tree = ast.parse(arg, mode="func_type")

        tree = self.visit(tree)
        assert isinstance(tree, ast.Expression)
        return tree


def eval_type_based(
    value: object,
    globalns: dict[str, object] | None = None,
    localns: dict[str, object] | None = None,
    *,
    string_literals: bool,
) -> object:
    """Like `typing._eval_type`, but supports based typing features.
    Specifically, this transforms `1 | 2` into `typing.Union[Literal[1], Literal[2]]`
    and `(int) -> str` into `typing.Callable[[int], str]` etc.
    """
    if not isinstance(value, typing.ForwardRef):
        return value
    transformer = CringeTransformer(globalns, localns, string_literals=string_literals)
    tree = transformer._transform(value)
    return transformer.eval_type(tree, original_ref=value)


if typing.TYPE_CHECKING:

    def _eval_direct(
        value: object,  # noqa: ARG001
        globalns: dict[str, object] | None = None,  # noqa: ARG001
        localns: dict[str, object] | None = None,  # noqa: ARG001
    ) -> object:
        ...
else:
    _eval_direct = partial(eval_type_based, string_literals=False)
