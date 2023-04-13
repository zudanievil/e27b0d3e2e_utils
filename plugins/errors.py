#! /usr/bin/env python3
import sys, os
from pathlib import Path
from typing import *

su = sys.startup

@su.do_it
def __exception():
    try:
        raise Exception
    except Exception as e:
        return e

_traceback_t = type(e.__traceback__)


def unroll_stack(exc: Exception) -> List[_traceback_t]:
    """
    python stack traces are c-style singly-linked lists. 
    unfortunately, python does not provide normal
    means to work with such constructs, so they need to be put into 
    a conventional python list.
    """
    tbs = [e.__traceback__]
    while True:
        nxt = tbs[-1].tb_next
        if nxt is None:
            return tbs
        tbs.append(nxt)

_T = TypeVar("_T")
_T1 = TypeVar("_T1")
_T2 = TypeVar("_T2")
_E = TypeVar("_E", bound=Exception)
Fn = Callable

_handler_t = Fn[[_E, tuple, dict], _T2]
_fn_t = Fn[..., _T1]

class ErrorHandler(Generic[_T1, _T2, _E]):
    __slots__ = ("main", "handler")

    def __init__(self, main: _fn_t, handler: _handler_t):
        self.main = main
        self.handler = handler

    @classmethod
    def attach_handler(cls, handler: _handler_t):
        def clj(main: _fn_t) -> ErrorHandler[_T1, _T2, _E]:
            return cls(main, handler)
        return clj

    def __call__(self, *args, **kwargs) -> Union[_T1, _T2]:
        try:
            return self.main(*args, **kwargs)
        except Exception as e:
            return self.handler(e, args, kwargs)

