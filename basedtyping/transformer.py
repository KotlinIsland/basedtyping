from __future__ import annotations

import ast
import types
import typing
import uuid
from contextlib import contextmanager
from enum import Enum
from typing import Any
import basedtyping


class CringeTransformer(ast.NodeTransformer):
    """
    Transforms `1 | 2` into `Literal[1] | Literal[2]` etc
    TODO: list[(int, str)] -> list[tuple[int, str]], is this even possible with ast? check src
    """

    def __init__(
        self,
        globalns: dict[str, Any] | None,
        localns: dict[str, Any] | None,
        *,
        string_literals: bool,
    ):
        self.string_literals = string_literals

        # This logic for handling Nones is copied from typing.ForwardRef._evaluate
        if globalns is None and localns is None:
            globalns = localns = {}
        elif globalns is None:
            # apparently pyright doesn't infer this automatically
            assert localns is not None
            globalns = localns
        elif localns is None:
            # apparently pyright doesn't infer this automatically
            assert globalns is not None
            localns = globalns

        self.typing_name = f"typing_extensions_{uuid.uuid4().hex}"
        self.basedtyping_name = f"basedtyping_{uuid.uuid4().hex}"
        self.globalns = globalns
        import typing_extensions

        self.localns = {
            **localns,
            self.typing_name: typing_extensions,
            self.basedtyping_name: basedtyping,
        }

    def eval_type(
        self, node: ast.Expression | ast.expr, *, original_ref: typing.ForwardRef | None = None
    ) -> object:
        if not isinstance(node, ast.Expression):
            node = ast.copy_location(ast.Expression(node), node)
        ref = typing.ForwardRef(ast.dump(node))
        if original_ref:
            for attr in ("is_argument", " is_class", "module"):
                attr = f"__forward_{attr}__"
                if hasattr(original_ref, attr):
                    setattr(ref, attr, getattr(original_ref, attr))
        ref.__forward_code__ = compile(node, "<node>", "eval")
        try:
            return typing._eval_type(ref, self.globalns, self.localns)
        except TypeError:
            return None

    def _typing(self, attr: str):
        result = ast.Attribute(
            value=ast.Name(id=self.typing_name, ctx=ast.Load()), attr=attr, ctx=ast.Load()
        )
        return ast.fix_missing_locations(result)

    def _basedtyping(self, attr: str):
        result = ast.Attribute(
            value=ast.Name(id=self.basedtyping_name, ctx=ast.Load()), attr=attr, ctx=ast.Load()
        )
        return ast.fix_missing_locations(result)

    def _literal(self, value: ast.Constant | ast.Name | ast.Attribute):
        return self.subscript(self._typing("Literal"), value)

    def subscript(self, value, slice):
        result = ast.Subscript(value=value, slice=slice, ctx=ast.Load())
        return ast.fix_missing_locations(result)

    _implicit_tuple = False

    @contextmanager
    def implicit_tuple(self):
        implicit_tuple = self._implicit_tuple
        self._implicit_tuple = True
        try:
            yield
        finally:
            self._implicit_tuple = implicit_tuple

    def visit_Subscript(self, node: ast.Subscript) -> ast.AST:
        with self.implicit_tuple():
            node = self.generic_visit(node)
        # TODO: FunctionType -> Callable
        node_type = self.eval_type(node.value)
        if node_type is types.FunctionType:
            node = self.subscript(self._typing("Callable"), node.slice)
        return node

    def visit_Attribute(self, node) -> ast.Name:
        node = self.generic_visit(node)
        node_type = self.eval_type(node)
        if isinstance(node_type, Enum):
            node = self._literal(node)
        return node

    def visit_Name(self, node) -> ast.Name:
        node = self.generic_visit(node)
        name_type = self.eval_type(node)
        if isinstance(name_type, Enum):
            node = self._literal(node)
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        node = self.generic_visit(node)
        if isinstance(node.value, int | bool) or (
            self.string_literals and isinstance(node.value, str)
        ):
            node = self._literal(node)
        return node

    def visit_Tuple(self, node: ast.Tuple) -> ast.AST:
        node = self.generic_visit(node)
        if not self._implicit_tuple:
            return self.subscript(self._typing("Tuple"), node)
        return node

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        if len(node.ops) == 1 and isinstance(node.ops[0], ast.Is):
            node = self.subscript(self._typing("TypeIs"), self.generic_visit(node.comparators[0]))
        return self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> ast.AST:
        if (
            isinstance(node.body, ast.Compare)
            and len(node.body.comparators) == 1
            and isinstance(node.body.ops[0], ast.Is)
        ):
            node.body = self.subscript(
                self._typing("TypeGuard"), self.generic_visit(node.body.comparators[0])
            )
        return self.generic_visit(node)

    def visit_FunctionType(self, node: ast.FunctionType) -> ast.AST:
        node = self.generic_visit(node)
        return self.subscript(
            self._typing("Callable"),
            ast.Tuple([ast.List(node.argtypes, ctx=ast.Load()), node.returns], ctx=ast.Load()),
        )

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        node = self.generic_visit(node)
        if isinstance(node.op, ast.BitAnd):
            node = self.subscript(
                self._basedtyping("Intersection"),
                ast.Tuple([node.left, node.right], ctx=ast.Load()),
            )
        return node


def _eval_direct(
    value: typing.ForwardRef,
    globalns: dict[str, Any] | None = None,
    localns: dict[str, Any] | None = None,
):
    return eval_type_based(value, globalns, localns, string_literals=False)


def eval_type_based(
    value: object,
    globalns: typing.Mapping[str, object] | None = None,
    localns: typing.Mapping[str, object] | None = None,
    *,
    string_literals: bool,
) -> object:
    """
    Like `typing._eval_type`, but lets older Python versions use newer typing features.
    Specifically, this transforms `X | Y` into `typing.Union[X, Y]`
    and `list[X]` into `typing.List[X]` etc. (for all the types made generic in PEP 585)
    if the original syntax is not supported in the current Python version.
    """
    try:
        tree = ast.parse(value.__forward_arg__, mode="eval")
    except SyntaxError:
        tree = ast.parse(value.__forward_arg__.removeprefix("def").lstrip(), mode="func_type")

    transformer = CringeTransformer(globalns, localns, string_literals=string_literals)
    tree = transformer.visit(tree)
    return transformer.eval_type(tree, original_ref=value)
