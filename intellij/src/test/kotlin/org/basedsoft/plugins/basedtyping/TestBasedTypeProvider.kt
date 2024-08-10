package org.basedsoft.plugins.basedtyping

import com.jetbrains.python.PythonFileType
import com.jetbrains.python.documentation.PythonDocumentationProvider
import com.jetbrains.python.fixtures.PyTestCase
import com.jetbrains.python.psi.PyExpression
import com.jetbrains.python.psi.PyTypedElement
import com.jetbrains.python.psi.types.TypeEvalContext


class PyTypeProviderTest : PyTestCase() {
    fun `test bare literal`() {
        "expr: 1 | 2" exprIs "Literal[1, 2]"
    }

    fun `test tuple literal`() {
        "expr: (int, str)" exprIs "tuple[int, str]"
    }

    fun `test intersection`() {
        "expr: int & str" exprIs "int"
    }

    fun `test callable`() {
        """
        expr: "(int, str) -> str"
        """.trimMargin() exprIs "(int, str) -> str"
    }

    fun `test infer overload`() {
        """
        from typing import overload
        @overload
        def f(a: int) -> str: ...
        @overload
        def f(a: str) -> int: ...
        def f(a):
            expr = a
        """ exprIs "str | int"
        """
        from typing import overload
        @overload
        def f(a: int) -> str: ...
        @overload
        def f(a: str) -> int: ...
        def f(a):
            return 1
        expr = f
        """ exprIs "(a: str | int) -> str | int"
    }

    fun `test constructor`() {
        """
        class A:
            def __init__(self) -> None: ...
        expr = A()
        """ exprIs "A"
    }

    fun `test narrowing`() {
        """
        a: object
        if isinstance(a, int):
            expr = a
        """ exprIs "int"
    }

    fun `test Final`() {
        """
        from typing import Final
        expr: Final = 1
        """ exprIs "int"
    }

    private infix fun String.exprIs(expectedType: String) {
        myFixture.configureByText(PythonFileType.INSTANCE, this.trimIndent())
        val expr = myFixture.findElementByText("expr", PyExpression::class.java)
        assertExpressionType(expectedType, expr)
    }

    private fun assertExpressionType(expectedType: String, expr: PyExpression) {
        val project = expr.project
        val containingFile = expr.containingFile
        assertType(expectedType, expr, TypeEvalContext.codeAnalysis(project, containingFile))
        assertProjectFilesNotParsed(containingFile)
        assertType(expectedType, expr, TypeEvalContext.userInitiated(project, containingFile))
    }

    fun assertType(
         expectedType: String,
         element: PyTypedElement,
         context: TypeEvalContext,
         message: String? = "Failed in $context context",
    ) {
        val actual = context.getType(element)
        val actualType = PythonDocumentationProvider.getTypeName(actual, context)
        assertEquals(message, expectedType, actualType)
    }
}

