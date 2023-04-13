import typing as _t
from typing import Callable as _F
from itertools import product

_T = _t.TypeVar("_T")

def zip_w_next(itr: _t.Iterable[_T]) -> _t.Iterator[_t.Tuple[_T, _T]]:
    first = True
    prev = None
    for i in itr:
        if first:
            first = False
            prev = i
            continue
        yield (prev, i)
        prev = i
