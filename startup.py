#! /usr/bin/env python3
"""
a startup script for ipython & jupyter
---
to make it work, go to ipython startup directory
and create symlink `000.ipy` to this file or
put `%run "path/to/this/file"` into `000.ipy`.
to get ipython startup directory run
`get_ipython().profile_dir.startup_dir` inside ipython/jupyter
"""

import sys
import os
from pathlib import Path
from typing import *
import importlib
import shutil as sh
import ctypes as _ctypes


_T = TypeVar("_T")
_module_t = type(sys)

class Module(type):
    """
    metaclass that helps to cleate
    """
    def __new__(cls, name, bases, dct) -> _module_t:
        assert not bases, "no inheritance, please"
        m = _module_t(name, doc=dct.get("__doc__"))
        for k, v in dct.items():
            setattr(m, k, v)
        return m

#! /usr/bin/env python3
import sys, os
from pathlib import Path
from typing import *

#! /usr/bin/env python3
"""
a startup script for ipython & jupyter
---
to make it work, go to ipython startup directory
and create symlink `000.ipy` to this file or
put `%run "path/to/this/file"` into `000.ipy`.
to get ipython startup directory run
`get_ipython().profile_dir.startup_dir` inside ipython/jupyter
"""

import sys
import os
from pathlib import Path
from typing import *
import importlib
import shutil as sh
import ctypes as _ctypes


_T = TypeVar("_T")
_module_t = type(sys)


def do_it(f: Callable[[], _T]) -> _T:
    "return f() # for complex object initialization"
    return f()


class Module(type):
    """
    metaclass that helps to cleate
    """
    def __new__(cls, name, bases, dct) -> _module_t:
        assert not bases, "no inheritance, please"
        m = _module_t(name, doc=dct.get("__doc__"))
        for k, v in dct.items():
            setattr(m, k, v)
        return m


def get_by_id(id: int):
    """get object based on id. can result in a crash (segfault)"""
    return _ctypes.cast(id, ctypes.py_object).value

def exec_(code, frame: int = 0):
    """
    frame = 0 -- execute code in this frame
    frame >= 1 -- further up the stack
    """
    frame += 1
    exec(code, sys._getframe(frame).f_globals, sys._getframe(frame).f_locals)


def include(p: Union[Path, str], frame: int = 0):
    """
    include file by "code copy-pasting" (as #include in C)
    frame = 0 to include at call site, frame >= 1 to include further up the stack
    """
    with open(p, "rt") as f:
        src = f.read()
    code = compile(src, str(p), mode="exec")
    exec_(code, frame + 1)


def import_(p: Union[Path, str]) -> "module":
    """
    import module by path.
    this function is user-defined, injected into `sys` module on ipython startup
    """
    name = Path(p).stem
    spec = importlib.util.spec_from_file_location(name, str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

USER_PLUGIN_DIR = Path(
    os.getenv("IPYTHON_USER_PLUGIN_DIR") 
    or "~/Scripts/ipython/plugins"
).expanduser().resolve()


def user_plugin(name: str = None, *, register: bool = False) -> 'module':
    """
    plugin_names = user_plugin()          # get plugin list
    my_plugin = user_plugin("my_plugin")  # get plugin module
    
    `register` means that plugin is added to sys.modules
    """ 
    if not name:
        return [x.stem for x in USER_PLUGIN_DIR.iterdir() 
            if x.suffix==".py"]
    path = (USER_PLUGIN_DIR / name).with_suffix(".py")
    mod = import_(path)
    if register:
        sys.modules[name] = mod
    return mod


def require_plugins(*names: str) -> List['module']:
    "get plugins from sys.modules or load and register them"
    plugins = user_plugin()
    missing = [n for n in names if not (n in plugins or n in sys.modules)]
    assert not missing, f"not found: {missing}"
    mods = []
    for name in names:
        if name not in sys.modules:
            user_plugin(name, register = True)
        mods.append(sys.modules[name])
    return mods


class Err(Exception):
    """a data-oriented exception to provide more FP-like error handling"""
    __slots__ = ("data", )

    def __init__(self, data):
        super().__init__()
        self.data = data

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return f"Err(data={repr(self.data)})"
    __str__ = __repr__


def is_err(x) -> bool:
    """:return type(x) == Err"""
    return type(x) == Err


@do_it
def ipyformat(): # especially useful for function pretty-printing
    try:
        from IPython.core.formatters import PlainTextFormatter as _PTF
    except ImportError as e:
        return Err(str(e))
    else:
        return _PTF()


# now we bundle up useful things and inject them into sys module
class startup(metaclass=Module): # this is not exactly how `Module` should be used
    """Startup Utils. Pseudo-module that contains startup functions."""
    do_it = do_it
    Module = Module
    Err = Err
    is_err = is_err
    
    ipyformat = ipyformat
    get_by_id = get_by_id
    
    exec_ = exec_
    include = include
    import_ = import_

    require_plugins = require_plugins
    user_plugin = user_plugin
    

sys.startup = startup

