import typing as _t
from typing import Callable as _F
from itertools import *

_T = _t.TypeVar("_T")
_T1 = _t.TypeVar("_T1")


skipwhile = dropwhile
reduce = accumulate


def as_iterator(
    i: _t.Union[_t.Iterable[_T], _t.Iterator[_T]],
) -> _t.Iterator[_T]:
    return iter(i) if not hasattr(i, "__next__") else i

 
def is_iterator(any) -> bool:
    return hasattr(any, "__next__")

    
def is_iterable(any) -> bool:
    return hasattr(any, "__iter__")
    
    
def foreach(itr: _t.Iterable) -> None:
    for _ in itr:
        pass
        
        
def take(n: int, itr: _t.Iterable[_T]) -> _t.Iterator[_T]:
    return islice(itr, start=0, stop=n)


def skip(n: int, itr: _t.Iterable[_T]) -> _t.Iterator[_T]:
    return islice(itr, start=n)


def _identity(x):
    return x


def filtermap(
    fn: _F[[_T], _t.Optional[_T1]], 
    xs: _t.Iterable[_T],
) -> _t.Iterator[_T1]:
    for x in xs:
        y = fn(x)
        if y is None:
            continue
        yield y


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

       
def infinity(start = 0, step = 1):
    while True:
        yield start
        start = start + step
      
      
def unfold(
    start: _T, 
    update: _F[[_T], None],
    *, yield_first=False, 
    sentinel=None,
):  
    """
    apply `start = update(start); yield start` until `start==sentinel`. try it out: `fib10 = list(itr.unfold((1, 1), lambda x: (x[1], x[0] + x[1]), sentinel = (144, 233)))`
`
    """
    if yield_first:
        yield start
    while True:
        start = update(start)
        if start == sentinel:
            break
        yield start


# may be fun to implement: https://towardsdatascience.com/python-stack-frames-and-tail-call-optimization-4d0ea55b0542


class _Brace(_t.NamedTuple):
    """for flattened recursive objects"""
    level: int
    left: bool = True


def flatten(
    xs: _t.Iterable[_t.Union[_T, "recursive"]], *,
    recur_when: _F[[_t.Union[_T, "recursive"]], bool] = is_iterable,
    as_iterator = as_iterator,
    braces = False,
) -> _t.Iterator[_t.Union[_T, _Brace]]:  
    """try it:
    ```
    xs = [1, 2, [3, 4, 5], 6, [7, 8, [9, 10, [11]], 12], 13]
    for i in flatten(xs):
        print(i)
    ```
    uses loops instead of recursion:
    ```
    xs = [5, ]
    sys.setrecursionlimit(100)
    for _ in range(200):
        xs = [xs, ]
    for i in flatten(xs): # also try with braces=True
        print(i)
    ```
    """
    stack = [as_iterator(xs), ]
    if braces:
        yield _Brace(0, True)
    while stack:
        xs = stack[-1]
        lvl = len(stack)
        for x in xs:
            if recur_when(x):
                if braces:
                    yield _Brace(lvl, True)
                stack.append(as_iterator(x))
                break
            else:
                yield x
        else: # loop finished with no exceptions or breaks
            stack.pop()
            if braces:
                yield _Brace(lvl-1, False)


def unflatten(
    xs: _t.Iterable[_t.Union[_T, _Brace]],
    tree_cons: _F[[_t.List[_t.Union[_T, _T1]]], _T1] = list,
    leaf_cons: _F[[_T], _T1] = _identity,
) -> _t.List[_T1]:
    """
    unflatten the tree that was flattened with `flatten(tree, braces=True)` does not check brace levels.
    ```
    xs = [1, 2, [3, 4, 5], 6, [7, 8, [9, 10, [11, ]]], 12]
    fxs = [x for x in flatten(xs, braces=True)]
    assert xs == unflatten(fxs)[0] # several trees can be deserialized at once
    ```
    if you want to recieve trees of custom type `T1`, you should supply constructors `T -> T1` and `List[T | T1] -> T1` (if you dont get it, try `str` and `tuple` respectively with the example above).
    """
    root_hook = []
    stack = [root_hook, ]
    for x in xs:
        if type(x) == _Brace:
            if x.left:
                stack.append([])
            else:
                tree = tree_cons(stack.pop())
                stack[-1].append(tree)
        else:
            stack[-1].append(leaf_cons(x))
    assert len(stack) == 1, "number of braces does not match"
    return root_hook
            
   

