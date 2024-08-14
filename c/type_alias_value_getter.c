#define PY_SSIZE_T_CLEAN
#include <Python.h>

typedef struct {
    PyObject_HEAD
    PyObject *name;
    PyObject *type_params;
    PyObject *compute_value;
    PyObject *value;
    PyObject *module;
} typealiasobject;

static PyObject *
foo_test(PyObject *self, PyObject *args)
{
    PyObject *alias;
    if (!PyArg_ParseTuple(args, "O", &alias))
        return NULL;
    typealiasobject *ta = (typealiasobject *)alias;
    return Py_NewRef(ta->compute_value);
}

static PyMethodDef foo_methods[] = {
    /* The cast of the function is necessary since PyCFunction values
     * only take two PyObject* parameters, and keywdarg_parrot() takes
     * three.
     */
    {"test", (PyCFunction)(void(*)(void))foo_test, METH_VARARGS,
     "debug alias."},
    {NULL, NULL, 0, NULL}   /* sentinel */
};

static struct PyModuleDef foo = {
    PyModuleDef_HEAD_INIT,
    "foo",
    NULL,
    -1,
    foo_methods
};

PyMODINIT_FUNC
PyInit_foo(void)
{
    PyModule_Create(&foo);
};
