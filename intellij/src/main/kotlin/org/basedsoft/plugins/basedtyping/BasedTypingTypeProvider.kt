package org.basedsoft.plugins.basedtyping

import com.intellij.openapi.util.Ref
import com.intellij.psi.PsiElement
import com.intellij.psi.util.siblings
import com.jetbrains.python.PyTokenTypes
import com.jetbrains.python.codeInsight.typing.PyTypingTypeProvider
import com.jetbrains.python.psi.*
import com.jetbrains.python.psi.resolve.PyResolveContext
import com.jetbrains.python.psi.types.*
import com.jetbrains.python.psi.types.PyLiteralType.Companion.fromLiteralParameter

private class BasedTypingTypeProvider : PyTypeProviderBase() {
    override fun getReferenceType(referenceTarget: PsiElement, context: TypeEvalContext, anchor: PsiElement?): Ref<PyType>? {
        if (referenceTarget !is PyTargetExpression) return null
        val annotation = referenceTarget.annotation?.value ?: return null
        return Ref.create(getType(annotation, context))
    }

    override fun getParameterType(param: PyNamedParameter, func: PyFunction, context: TypeEvalContext): Ref<PyType>? {
        return param.annotation?.value?.let {
            getType(it, context).ref()
        } ?: getOverload(param, func, context).ref()
    }

    override fun getReturnType(callable: PyCallable, context: TypeEvalContext): Ref<PyType>? {
        if (callable !is PyFunction) return null

        return callable.annotation?.value?.let { annotation ->
            getType(annotation, context).ref()
        } ?: getOverloadReturn(callable, context).ref()
    }

    override fun getCallType(function: PyFunction, callSite: PyCallSiteExpression, context: TypeEvalContext): Ref<PyType>? {
        val annotation = function.annotation?.value ?: return null
        return Ref.create(getType(annotation, context, simple = true))
    }

    /**
     * Needed to work around a limitation in PyTypingTypeProvider
     */
    override fun getReferenceExpressionType(referenceExpression: PyReferenceExpression, context: TypeEvalContext): PyType? {
        val param = referenceExpression.followAssignmentsChain(PyResolveContext.defaultContext(context)).element
        if (param !is PyNamedParameter) return null
        val annotation = param.annotation?.value ?: return null
        return getType(annotation, context)
    }
    /**
     * Needed to work around a limitation in PyTypingTypeProvider
     */
    override fun getCallableType(callable: PyCallable, context: TypeEvalContext): PyType? {
        if (callable !is PyFunction) return null
        return BasedPyFunctionTypeImpl(callable)
    }
}

/**
 * Needed to work around a limitation in PyTypingTypeProvider
 */
class BasedPyFunctionTypeImpl(val callable: PyFunction) : PyFunctionTypeImpl(callable) {
    override fun getReturnType(context: TypeEvalContext): PyType? {
        return callable.annotation?.value?.let { getType(it, context) } ?: super.getReturnType(context)
    }
}

fun getType(expression: PyExpression, context: TypeEvalContext, simple: Boolean = false): PyType? {
    return getLiteralType(expression, context)
            ?: getUnionType(expression, context)
            ?: getTupleType(expression, context)
            ?: if (simple) null else PyTypingTypeProvider.getType(expression, context)?.get()
}

fun getLiteralType(target: PyExpression, context: TypeEvalContext): PyType? {
    if (target is PyNumericLiteralExpression || target is PyBoolLiteralExpression) {
        return fromLiteralParameter(target, context)
    }
    return null
}

fun getUnionType(target: PyExpression, context: TypeEvalContext): PyType? {
    if (target !is PyBinaryExpression) return null
    return when (target.operator) {
        PyTokenTypes.OR -> target.rightExpression?.let { right ->
            PyUnionType.union(
                    getType(target.leftExpression, context),
                    getType(right, context),
            )
        }
        // HACK
        PyTokenTypes.AND -> getType(target.leftExpression, context)
        else -> null
    }
}

fun getTupleType(target: PyExpression, context: TypeEvalContext): PyType? {
    return when (target) {
        is PyParenthesizedExpression -> target.containedExpression ?: return null
        is PyTupleExpression -> target
        else -> return null
    }.children.map { getType(it as PyExpression, context) }.let { PyTupleType.create(target, it) }
}

fun PyFunction.collectOverloads() =
        siblings(forward = false)
        .filterIsInstance(PyFunction::class.java)
        .filter { it.name == name }

fun getOverload(param: PyNamedParameter, func: PyFunction, context: TypeEvalContext) =
        func.collectOverloads()
            .map { funcItem ->
                funcItem.parameterList.findParameterByName(param.name!!)?.annotation?.value?.let {
                    getType(it, context)
                }
            }
            .filterNotNull()
            .toSet()
            .takeIf { it.isNotEmpty() }
            ?.let { PyUnionType.union(it) }

fun getOverloadReturn(func: PyFunction, context: TypeEvalContext) =
    func.collectOverloads()
            .map { funcItem ->
                funcItem.annotation?.value?.let {
                    getType(it, context)
                }
            }
            .filterNotNull()
            .toSet()
            .takeIf { it.isNotEmpty() }
            ?.let { PyUnionType.union(it) }

fun PyType?.ref() = this?.let { Ref.create(it) }