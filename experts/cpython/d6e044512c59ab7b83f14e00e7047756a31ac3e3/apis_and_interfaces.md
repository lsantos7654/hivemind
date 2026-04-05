# CPython APIs and Interfaces

## Entry Points

### Python Interpreter Entry Points (`Programs/python.c`)

```c
// Unix/macOS/Linux entry point
int main(int argc, char **argv) {
    return Py_BytesMain(argc, argv);
}

// Windows entry point
int wmain(int argc, wchar_t **argv) {
    return Py_Main(argc, argv);
}
```

### Embedding API (`Include/cpython/initconfig.h`, `Include/Python.h`)

The modern embedding API uses `PyConfig` for full control:

```c
#include <Python.h>

int main(int argc, char *argv[]) {
    PyStatus status;
    PyConfig config;

    PyConfig_InitPythonConfig(&config);   // or PyConfig_InitIsolatedConfig()
    config.parse_argv = 1;

    status = PyConfig_SetBytesArgv(&config, argc, argv);
    if (PyStatus_Exception(status)) goto fail;

    status = Py_InitializeFromConfig(&config);
    if (PyStatus_Exception(status)) goto fail;

    PyConfig_Clear(&config);

    int exitcode = Py_RunMain();  // runs __main__ from sys.argv
    return exitcode;

fail:
    PyConfig_Clear(&config);
    if (PyStatus_IsExit(status)) return status.exitcode;
    Py_ExitStatusException(status);
}
```

Key embedding functions:
- `Py_Initialize()` / `Py_InitializeEx(int initsigs)` — simple init
- `Py_Finalize()` / `Py_FinalizeEx()` — shutdown
- `Py_InitializeFromConfig(PyConfig*)` — full-control init
- `Py_RunMain()` — run interpreter from `sys.argv[0]`
- `PyConfig_InitPythonConfig(PyConfig*)` — init config for user-facing interpreter
- `PyConfig_InitIsolatedConfig(PyConfig*)` — init config for embedded use (no env vars, no site)
- `PyStatus_Exception(PyStatus)` — check if status is error or exit

## Core C API

### Object Protocol (`Include/abstract.h`)

```c
// Calling objects
PyObject *PyObject_Call(PyObject *callable, PyObject *args, PyObject *kwargs);
PyObject *PyObject_CallNoArgs(PyObject *callable);
PyObject *PyObject_CallOneArg(PyObject *callable, PyObject *arg);
PyObject *PyObject_CallMethodNoArgs(PyObject *obj, PyObject *name);
PyObject *PyObject_CallMethodOneArg(PyObject *obj, PyObject *name, PyObject *arg);

// Vectorcall protocol (fast path, no args tuple needed)
PyObject *PyObject_Vectorcall(PyObject *callable, PyObject *const *args,
                              size_t nargsf, PyObject *kwnames);

// Attribute access
PyObject *PyObject_GetAttr(PyObject *o, PyObject *attr_name);
int       PyObject_SetAttr(PyObject *o, PyObject *attr_name, PyObject *v);
int       PyObject_HasAttr(PyObject *o, PyObject *attr_name);

// Comparison
int PyObject_RichCompareBool(PyObject *o1, PyObject *o2, int opid);
    // opid: Py_LT, Py_LE, Py_EQ, Py_NE, Py_GT, Py_GE

// Type checking
int PyObject_IsInstance(PyObject *inst, PyObject *cls);
int PyObject_IsSubclass(PyObject *derived, PyObject *cls);

// Sequence protocol
PyObject *PySequence_GetItem(PyObject *o, Py_ssize_t i);
Py_ssize_t PySequence_Length(PyObject *o);
PyObject *PySequence_List(PyObject *o);
PyObject *PySequence_Tuple(PyObject *o);

// Mapping protocol
PyObject *PyMapping_GetItemString(PyObject *o, const char *key);
int       PyMapping_SetItemString(PyObject *o, const char *key, PyObject *v);
```

### Reference Counting (`Include/object.h`, `Include/refcount.h`)

```c
// Increment reference count
Py_INCREF(PyObject *op);
Py_XINCREF(PyObject *op);  // NULL-safe variant

// Decrement reference count (may deallocate)
Py_DECREF(PyObject *op);
Py_XDECREF(PyObject *op);  // NULL-safe variant

// Clear a pointer (XDECREF + set to NULL)
Py_CLEAR(PyObject *op);

// Steal reference (used for new references passed to containers)
// No macro; use Py_DECREF on old value after transferring ownership.

// New reference: caller owns a refcount (must DECREF when done)
// Borrowed reference: no ownership transfer (do NOT DECREF)
```

### Type Objects (`Include/object.h`, `Include/cpython/object.h`)

```c
// PyTypeObject — the C struct for Python types
typedef struct _typeobject {
    PyObject_VAR_HEAD
    const char *tp_name;          // "module.TypeName"
    Py_ssize_t  tp_basicsize;     // sizeof(InstanceStruct)
    Py_ssize_t  tp_itemsize;      // for variable-sized objects; else 0
    destructor  tp_dealloc;
    Py_ssize_t  tp_vectorcall_offset;
    PyNumberMethods  *tp_as_number;
    PySequenceMethods *tp_as_sequence;
    PyMappingMethods  *tp_as_mapping;
    hashfunc    tp_hash;
    ternaryfunc tp_call;
    reprfunc    tp_str;
    // ... many more slots ...
    reprfunc    tp_repr;
    richcmpfunc tp_richcompare;
    iternextfunc tp_iternext;
    PyMethodDef *tp_methods;
    PyMemberDef *tp_members;
    PyGetSetDef *tp_getset;
    PyTypeObject *tp_base;
    PyObject    *tp_dict;
    initproc    tp_init;
    allocfunc   tp_alloc;
    newfunc     tp_new;
    freefunc    tp_free;
    // ...
} PyTypeObject;

// Register a type with the type system
int PyType_Ready(PyTypeObject *type);

// Check type
int PyType_IsSubtype(PyTypeObject *a, PyTypeObject *b);
```

### Module Creation (`Include/moduleobject.h`, `Include/modsupport.h`)

**Single-phase init (simple):**
```c
static PyMethodDef MyMethods[] = {
    {"hello", my_hello, METH_NOARGS, "Say hello."},
    {"add",   my_add,   METH_VARARGS, "Add two ints."},
    {NULL, NULL, 0, NULL}  // sentinel
};

static struct PyModuleDef mymodule = {
    PyModuleDef_HEAD_INIT,
    "mymodule",   // m_name
    NULL,         // m_doc
    -1,           // m_size: -1 = no per-module state; use module dict
    MyMethods,
    NULL,         // m_slots (NULL = single-phase init)
    NULL,         // m_traverse
    NULL,         // m_clear
    NULL          // m_free
};

PyMODINIT_FUNC PyInit_mymodule(void) {
    return PyModule_Create(&mymodule);
}
```

**Multi-phase init (PEP 489, recommended for subinterpreters):**
```c
static int mymodule_exec(PyObject *m) {
    if (PyModule_AddIntConstant(m, "ANSWER", 42) < 0) return -1;
    return 0;
}

static PyModuleDef_Slot mymodule_slots[] = {
    {Py_mod_exec, mymodule_exec},
    {Py_mod_multiple_interpreters, Py_MOD_PER_INTERPRETER_GIL_SUPPORTED},
    {0, NULL}
};

static struct PyModuleDef mymodule = {
    PyModuleDef_HEAD_INIT, "mymodule", NULL, 0,
    MyMethods, mymodule_slots, NULL, NULL, NULL
};

PyMODINIT_FUNC PyInit_mymodule(void) {
    return PyModuleDef_Init(&mymodule);
}
```

### Argument Parsing (`Include/modsupport.h`)

```c
// Parse positional args
int PyArg_ParseTuple(PyObject *args, const char *format, ...);

// Parse positional + keyword args
int PyArg_ParseTupleAndKeywords(PyObject *args, PyObject *kwargs,
    const char *format, char **kwlist, ...);

// Common format characters:
// "i" — int*         "l" — long*         "L" — long long*
// "f" — float*       "d" — double*
// "s" — const char** (UTF-8, borrowed)
// "s#"— const char**, Py_ssize_t* (bytes + length)
// "y" — const char** (bytes-like, no encoding)
// "O" — PyObject**   "O!" — PyObject** (with type check)
// "p" — int* (bool predicate)   "|" — optional args begin

// Build a return value
PyObject *Py_BuildValue(const char *format, ...);
// Format: "i", "d", "s", "O", "(ii)", "[OO]", "{ss}", etc.
```

### Error Handling (`Include/cpython/abstract.h`, `Python/errors.c`)

```c
// Set an exception
PyErr_SetString(PyExc_ValueError, "bad value");
PyErr_SetObject(PyExc_TypeError, some_obj);
PyErr_Format(PyExc_RuntimeError, "error at line %d", lineno);

// Check for exception
if (PyErr_Occurred()) { /* propagate */ return NULL; }

// Clear exception
PyErr_Clear();

// Fetch and restore exception
PyObject *type, *value, *tb;
PyErr_Fetch(&type, &value, &tb);
// ... do something ...
PyErr_Restore(type, value, tb);

// Standard exceptions (all PyObject*)
PyExc_Exception, PyExc_ValueError, PyExc_TypeError,
PyExc_AttributeError, PyExc_KeyError, PyExc_IndexError,
PyExc_RuntimeError, PyExc_MemoryError, PyExc_StopIteration,
PyExc_OSError, PyExc_ImportError, PyExc_RecursionError, ...
```

### Import System (`Include/import.h`)

```c
// Import a module by name
PyObject *PyImport_ImportModule(const char *name);
PyObject *PyImport_ImportModuleNoBlock(const char *name); // deprecated

// Import with from-list
PyObject *PyImport_ImportModuleLevelObject(PyObject *name, PyObject *globals,
    PyObject *locals, PyObject *fromlist, int level);

// Get sys.modules dict
PyObject *PyImport_GetModuleDict(void);

// Register a built-in module (call before Py_Initialize)
int PyImport_AppendInittab(const char *name, PyObject* (*initfunc)(void));

// Lazy imports (Python 3.15+)
int PyImport_SetLazyImportsMode(PyImport_LazyImportsMode mode);
```

### Thread State and GIL (`Include/pystate.h`, `Include/cpython/pystate.h`)

```c
// GIL release/acquire (for C threads doing IO or pure C work)
Py_BEGIN_ALLOW_THREADS    // releases GIL
// ... thread-safe C code ...
Py_END_ALLOW_THREADS      // reacquires GIL

// Alternatively:
PyThreadState *_save = PyEval_SaveThread();  // release
// ...
PyEval_RestoreThread(_save);                 // acquire

// Create a new thread state for a C thread
PyThreadState *tstate = PyThreadState_New(interp);
PyEval_AcquireThread(tstate);
// ... Python calls ...
PyEval_ReleaseThread(tstate);
PyThreadState_Delete(tstate);

// Get current thread state
PyThreadState *tstate = PyThreadState_Get();
PyInterpreterState *interp = PyInterpreterState_Get();
```

### Evaluation (`Include/ceval.h`)

```c
// Evaluate a code object
PyObject *PyEval_EvalCode(PyObject *co, PyObject *globals, PyObject *locals);

// Full call with args
PyObject *PyEval_EvalCodeEx(PyObject *co, PyObject *globals, PyObject *locals,
    PyObject *const *args, int argc, PyObject *const *kwds, int kwdc,
    PyObject *const *defs, int defc, PyObject *kwdefs, PyObject *closure);

// Recursion depth management
int Py_EnterRecursiveCall(const char *where);
void Py_LeaveRecursiveCall(void);
int Py_GetRecursionLimit(void);
void Py_SetRecursionLimit(int new_limit);

// Run code from string
PyObject *PyRun_String(const char *str, int start, PyObject *globals, PyObject *locals);
PyObject *PyRun_File(FILE *fp, const char *filename, int start,
                     PyObject *globals, PyObject *locals);
// start: Py_eval_input, Py_file_input, Py_single_input
```

### Memory Management (`Include/pymem.h`)

```c
// Python object allocator (uses Python's memory allocator)
void *PyMem_Malloc(size_t n);
void *PyMem_Realloc(void *p, size_t n);
void  PyMem_Free(void *p);

// Object allocator (aligned for PyObject)
void *PyObject_Malloc(size_t n);
void *PyObject_Realloc(void *p, size_t n);
void  PyObject_Free(void *p);

// Standard allocator (same as system malloc)
void *PyMem_RawMalloc(size_t n);
void *PyMem_RawRealloc(void *p, size_t n);
void  PyMem_RawFree(void *p);
```

## Stable ABI / Limited API

Define `Py_LIMITED_API` before including `Python.h` to restrict yourself to the stable ABI:

```c
#define Py_LIMITED_API 0x030d0000   // require Python 3.13+
#include <Python.h>
```

The stable ABI symbol list is tracked in `Misc/stable_abi.toml`. Extensions built against the limited API can be used with any Python version ≥ the requested minimum without recompilation.

## Argument Clinic

Argument Clinic is the code generator for C function argument parsing (`Tools/clinic/clinic.py`). It reads `.clinic` blocks embedded in `.c` files:

```c
/*[clinic input]
module mymodule

mymodule.hello
    name: str
    /

Say hello.
[clinic start generated code]*/
```

Run `make clinic` to regenerate. Clinic handles `PyArg_ParseTuple`, `PyArg_ParseTupleAndKeywords`, docstrings, and type checking automatically.

## sys.monitoring API (PEP 669)

Python 3.12+ provides a low-overhead monitoring API via `sys.monitoring`:

```python
import sys

DEBUGGER_ID = sys.monitoring.DEBUGGER_ID

def my_line_handler(code, line_number):
    print(f"Executing line {line_number} of {code.co_filename}")

sys.monitoring.use_tool_id(DEBUGGER_ID, "my_debugger")
sys.monitoring.set_events(DEBUGGER_ID, sys.monitoring.events.LINE)
sys.monitoring.register_callback(DEBUGGER_ID, sys.monitoring.events.LINE, my_line_handler)
```

## Sub-interpreters API

```python
import _interpreters  # C module at Modules/_interpretersmodule.c

interp_id = _interpreters.create()
_interpreters.run_string(interp_id, "print('hello from sub-interpreter')")
_interpreters.destroy(interp_id)
```

Cross-interpreter channels and queues are in `Modules/_interpchannelsmodule.c` and `Modules/_interpqueuesmodule.c`.

## Configuration and Extension Points

- **`sys.path`**: Search path for modules. Controlled at startup via `PyConfig.module_search_paths`.
- **`sys.meta_path`**: List of meta path finders (e.g., `importlib.machinery.PathFinder`). Extend to add custom import hooks.
- **`sys.path_hooks`**: Path entry finder factories.
- **`PyConfig.home`**: Sets the Python home directory (affects `sys.prefix`, `sys.exec_prefix`).
- **`PyConfig.pythonpath_env`**: Override `PYTHONPATH`.
- **`PyConfig.isolated`**: Isolated mode — ignore `PYTHON*` env vars, user site-packages.
- **`PEP 523` (`interp->eval_frame`)**: Replace the default frame evaluation function for tracing/JIT use.
- **`sys.settrace` / `sys.setprofile`**: Set trace/profile callbacks (per-thread).
- **`sys.addaudithook`**: Register audit event hooks (cannot be removed once set).
