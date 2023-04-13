#! /usr/bin/env python3

"""
FP-adjacent stuff:
* promise (synchronous Future)
* dispatch (alternative to OO dispatch)
* val_dispatch (for state graph traversal)
* compose (functional composition)

and some functools imports
"""

#TODO: flatmap, filtermap, context (for `with`) 
import sys
from functools import partial, reduce, lru_cache
import typing as _t
from typing import Callable as Fn

su = sys.startup
Err = su.Err
is_err = su.is_err
ipyformat = su.ipyformat

__all__ = [
    "promise", 
    "ValDispatch", 
    "Dispatch", 
    "compose", 
    "_none", 
    "partial", 
    "reduce", 
    "lru_cache"
]

class promise:
    """
    decorator that deferres function computation
    usage: ```
    @promise
    def my_function...
    ```
    """
    __slots__ = ("f", )
    def __init__(self, f: Fn):
        self.f = f
    
    def __call__(self, *args, **kwargs) -> partial:
        return partial(self.f, *args, **kwargs)
    
    def __repr__(self,) -> str:
        return f"@promise {repr(self.f)}"

class ValDispatch:
    """
    Typical in controllers and self-regulating programs. Example:
    ```
    PAUSE, RESUME = 1, 2
    @ValDispatch.new(PAUSE)
    def switch(_, channel: int):...
    @switch.register(RESUME)
    def switch(_, channel: int):...
    # more states can be added later
    # without changing the existing code
    def main():
        switch(RESUME, channel=5)
    ```
    Most useful when you have a huge
    and messy state transition graph --
    10+ possible states, and each transition
    is associated with its own function.
    """
    __slots__ = ("name", "registry", "doc")

    def __init__(self, name: str, doc: str = ""):
        self.name = name
        self.doc = doc
        self.registry = dict()

    def register(self, val) -> Fn[[Fn], "ValDispatch"]:
        """Decorator. Adds function to registry."""
        def clj(f: Fn) -> ValDispatch:
            self.registry[val] = f
            return self
        return clj

    @classmethod
    def new(cls, val, doc: str = None) -> Fn[[Fn], "ValDispatch"]:
        """Decorator. Internalises __name__ and __doc__ of a function"""
        def clj(f: Fn) -> ValDispatch:
            d = cls(f.__name__, doc or f.__doc__)
            d.registry[val] = f
            return d
        return clj

    def dispatch(self, val) -> Fn:
        return self.registry[val]

    def __call__(self, *args, **kwargs):
        return self.dispatch(args[0])(*args, **kwargs)

    def __repr__(self,) -> str:
        return f"<ValDispatch {self.name} at {hex(id(self))}>"

    def repr_detailed(self) -> str:
        if is_err(ipyformat):
            return ipyformat.data
        return (
            f"ValDispatch {self.name}\nregistry:\n\t" +
            "\n\t".join(f"{k}={ipyformat(v)}" for k, v in self.registry.items())
        )
class Dispatch:
    """
    Useful when defining operations on type unions.
    A good alternative for class-based interfaces,
    because it can extend any type. Example
    ```
    @dispatch.new(Circle)
    def draw(circ: Circle) -> SVG:...
    @draw.register(Polygon)
    def draw(poly: Plygon) -> SVG:...
    @draw.register(Group)
    def draw(group: Group) -> SVG:...
    ```
    Especially useful when interface types are not
    known in advance or will be extended by plugins/other users.
    """
    __slots__ = ("name", "registry", "doc")

    def __init__(self, name: str, doc: str = ""):
        self.name = name
        self.doc = doc
        self.registry = dict()

    def register(self, t: type) -> Fn[[Fn], "Dispatch"]:
        """Decorator. Adds function to registry."""
        def clj(f: Fn) -> Dispatch:
            self.registry[t] = f
            return self
        return clj

    @classmethod
    def new(cls, t: type, doc: str = None) -> Fn[[Fn], "Dispatch"]:
        """Decorator. Internalises __name__ and __doc__ of a function"""
        def clj(f: Fn) -> Dispatch:
            d = cls(f.__name__, doc or f.__doc__)
            d.registry[t] = f
            return d
        return clj

    def dispatch(self, t: type) -> Fn:
        return self.registry[t]

    def __call__(self, *args, **kwargs):
        return self.dispatch(type(args[0]))(*args, **kwargs)

    def __repr__(self,) -> str:
        return f"<Dispatch {self.name} at {hex(id(self))}>"

    def repr_detailed(self) -> str:
        if is_err(ipyformat):
            return ipyformat.data
        return (
            f"Dispatch {self.name}\nregistry:\n\t" +
            "\n\t".join(f"{k}={ipyformat(v)}" for k, v in self.registry.items())
        )


def _none(*_, **__):
    """return None"""
    return None


class Classifier:
    """
    works as dynamically extendable match statement
    apply functions from a list until they return a non-None result
    """
    __slots__ = ("name", "doc", "arms", "else_")

    def __init__(self, name: str, doc: str = ""):
        self.name = name
        self.doc = doc
        self.arms = []
        self.else_ = _none

    def add_else(self, else_: Fn) -> "Classifier":
        self.else_ = else_
        return self

    def add_arm(self, *, insert_at: int = None) -> Fn[[Fn], "Classifier"]:
        """Decorator. Add arm at the last position or at another specified position"""
        def clj(arm: Fn) -> "Classifier":
            (self.arms.append(arm) if insert_at is None
             else self.arms.insert(insert_at, arm))
            return self
        return clj

    @classmethod
    def new(cls, doc: str = None) -> Fn[[Fn], "Classifier"]:
        """Decorator. Internalises __name__ and __doc__ of a function"""
        def clj(f: Fn) -> Classifier:
            d = cls(f.__name__, doc or f.__doc__)
            d.arms.append(f)
            return d
        return clj

    def __call__(self, *args, **kwargs):
        for arm in self.arms:
            res = arm(*args, **kwargs)
            if res is not None:
                return res
        return self.else_(*args, **kwargs)

    def __repr__(self,) -> str:
        return f"<Classifier {self.name} at {hex(id(self))}>"

    def repr_detailed(self) -> str:
        if is_err(ipyformat):
            return ipyformat.data
        return (
            f"Classifier {self.name}\narms:\n\t" +
            "\n\t".join(ipyformat(arm) for arm in self.arms) +
            f"\nelse: {ipyformat(self.else_)}"
        )

class compose:
    """function composition"""
    __slots__ = ("fs", )
    def __init__(self, *fs: Fn):
        self.fs = fs
    
    def __call__(self, x):
        for f in self.fs:
            x = f(x)
        return x

    def __gt__(self, f: Fn) -> "compose":
        """a copy with another function at the rear"""
        return compose(*self.fs, f)

    def __lt__(self, f: Fn) -> "compose":
        """a copy with another function at the front"""
        return compose(f, *self.fs) 
    
    def __repr__(self):
        return (
            "composition(" + 
            " |> ".join(repr(f) for f in self.fs) + 
            ")")

            
    
