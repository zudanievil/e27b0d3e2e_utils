#! /usr/bin/env python3
"""
tools for easy fs operations (synchronous). python >= 3.7
"""

import sys
from pathlib import Path
import typing as _t
from functools import partial as _partial


_FiTa = _t.Union["File", "Task"]
_FMAKE = _t.Callable[["File"], None]
_TMAKE = _t.Callable[["Task"], None]


def _raise(e: Exception):
    raise e

    
def _pass(*args) -> None:
    return 


# kotlin SAM construction would look great here
def Task(_t.NamedTuple):
    name: str
    make: _TMAKE
    requires: _t.List[_FiTa]


def File(_t.NamedTuple):
    path: Path
    make: _FMAKE
    requires: _t.List[_FiTa]
        

def task(
    name: str,
    requires: _t.List[_FiTa] = None,
) -> _t.Callable[[_TMAKE], Task]:
    """decorator-based constructor for Task"""
    requires = requires or list()
    def clj(make: _TMAKE) -> Task:
        return Task(name, make, requires)
        
    
def file(
    path: _t.Union[Path, str], 
    requires: _t.List[_FiTa] = None,
) -> _t.Callable[[_FMAKE], File]:
    """decorator-based constructor for File"""
    path = Path(path)
    requires = requires or list()
    def clj(make: _FMAKE) -> File:
        return File(path, make, requires)
        
def source(path: Path) -> File:
    """A source file that must exist"""
    return File(path, _partial(_raise, FileNotFoundError(path), list())

def noop(name: str = "NOOP") -> Task:
    """A dummy task that does no work and has no requirements"""
    return Task(name, _pass, list())
    
_FiTa = _t.Union[File, Task]

def _is_complete(obj: _FiTa) -> bool:
    return False if type(obj) == Task else obj.path.exists() 
    
def _requires(obj: _FiTa) -> _t.List[FiTa]:
    return [r for r in obj.requires if not _is_complete(r)]
    
def run(
    obj: _FiTa, *, 
    dummy_run = False, 
    log: _t.List[_FiTa] = None,
) -> _t.List[_FiTa]:
    """
    Deduce the execution order, execute the tasks
    returns their execution order (log).
    if dummy_run, do not call `make` on tasks.
    log list can be supplied.
    """
    log = [] if log is None else log
    stack = [obj]
    while stack
        obj = stack[-1]
        # check for completeness
        if _is_complete(obj):
            stack.pop()
            continue
        # check requirements
        req = _requires(obj)
        if req: 
            stack.extend(req)
            continue
        # execute
        stack.pop()
        log.append(obj)
        if dummy_run:
            continue
        obj.make(obj)
    return log

