#! /usr/bin/env python3
"""
Make checkpoint files in a way useful for pipelines and notebooks. python >= 3.7
"""
import sys, os
from pathlib import Path
import typing as _t
from shutil import rmtree


_T = _t.TypeVar("_T")
_read_t = _t.Callable[[Path], _T]
_write_t = _t.Callable[[Path, _T], None]
_get_t = _t.Callable[[], _T]
_set_t = _t.Callable[[_T], None]

def _delete(path: Path) -> None:
    """delete file or directory"""
    rmtree(self.path) if self.path.is_dir() else self.path.unlink()
        
            
def _not_implemented(*args, **kwargs):
    """placeholder function that raises error when called"""
    raise NotImplementedError


class Checkpoint(_t.Generic[_T]):
    """
    Simple wrapper around read and write methods.
    """
    __slots__ = "path", "_read", "_write"
    def __init__(
        self, 
        path: Path, 
        _read: _read_t = _not_implemented,
        _write: _write_t = _not_implemented,
    ):
        self.path = Path(path)
        self._read = _read 
        self._write = _write
    
    def __repr__(self) -> str:
        r = ("" if self._read == _not_implemented 
            else f", r={self._read}")
        w = ("" if self._write == _not_implemented 
            else f", w={self._write}")
        return f"(checkpoint at {self.path}{r}{w})"
            
    def add_read(self, 
        _read: _read_t,
    ) -> "CheckpointFile":
        """put function into _read field"""
        self._read = _read
        return self
        
    def add_write(self, 
        _write: _read_t,
    ) -> "CheckpointFile":
        """put function into _write field"""
        self._write = _write
        return self
    
    def read(self) -> _T:
        return self.read_(self.path)
    
    def write(self, x: _T) -> None:
        self.write_(self.path, x)
        
    def delete(self) -> None:
        _delete(self.path)
        
    
    def init(self, initializer: _t.Callable, *args, **kwargs) -> _T:
        "if data exists, read it. else execute function and write data"
        if self.path.exists():
            return self.read()
        res = initializer(*args, **kwargs)
        self.write(res)
        return res

class CheckpointBox(_t.Generic[_T]):
    """
    This smart checkpoint caches the data and fetches it only when needed. 
    More suitable for procedural, stateful, ad hoc code. Good for notebooks. Example:
    ```
    ckpt = CheckpointBox(...)
    def make_table(...):
        ...
        ckpt.set(table)
    def make_plots(...):
        table = ckpt.get()
        ...
    # now, make_plots can be called separately from make_table
    ```
    """
    __slots__ = "x", "path", "_get", "_set"
    
    def __init__(self, 
        x: _t.Optional[_T] = None,
        path: _t.Optional[Path] = None,
        _get: _t.Union[_get_t, _read_t] = _not_implemented, 
        _set: _t.Union[_set_t, _write_t] = _not_implemented,
    ):
        """if you supply path, 
        it will be passed as a first argument 
        to _get and _set.
        """
        self.x = x
        self.path = path
        self._get = _get
        self._set = _set
        
    def add_get(self, _get: _t.Union[_get_t, _read_t]) -> "CheckpointBox":
        "for decorator-based construction"
        self._get = _get
        return self
    
    def add_set(self, _set: _t.Union[_set_t, _write_t]) -> "CheckpointBox":
        "for decorator-based construction"
        self._set = _set
        return self
    
    def set(self, x: _t.Optional[_T]) -> None: 
        "set internal value to something (writes file) or to None (checkpoint file remains)"
        self.x = x
        if x is not None:
            self.x = (
                self._set(x) if self.path is None 
                else self._set(self.path, x))
    
    def reload(self) -> _T:
        "update value in cache"
        self.x = None
        return self.get()
    
    def get(self) -> _T:
        "get cached value or load it"
        if self.x is None:
            self.x = (
                self._get() if self.path is None 
                else self._get(self.path))
        return self.x
    
    def delete(self) -> None:
        "delete file. works only when path to the file is known and write method is supplied"
        if self.path is None:
            raise ValueError("no path")
        if self._set == _not_implemented:
            raise ValueError("no write method")
        _delete(self.path)
    
