#! /usr/bin/env python3
import sys
import numpy as np
import typing as _t
import operator

su = sys.startup
itr,  = su.require_plugins("iterators")


def is_monotonic(
        x: np.ndarray, *, 
        increasing = True, 
        strict = True,
    ) -> bool:
    if strict:
        op = operator.lt if increasing else operator.gt
    else:
        op = operator.le if increasing else operator.ge
    return np.all(op(x[:-1], x[1:]))


def __test_is_monotonic():
    a = np.array
    assert is_monotonic(a([1, 2, 3, 4]))
    assert not is_monotonic(a([1, 2, 2, 4]))
    assert is_monotonic(a([1, 2, 2, 4]), strict=False)
    assert is_monotonic(a([4, 3, 2, 1]), increasing=False)


class Window:
    """
    Sliding window iterator over 1D array. example:
    ```
    x = list(range(1, 11)) # it can work with other slice-able things
    print([w for w in Window(x, window=5)])
    ```
    """

    def __init__(self, array: np.ndarray, window: int, start: int = 0, stop: int = None):
        stop = (len(array) - window + 1) if stop is None else stop 
        assert start >= 0 and stop > 0, "start, stop must be positive or None"
        self.window = window
        # ^^^ +1 because ranges do not include last point
        self.range = range(start, stop)
        self.array = array

    def __iter__(self) -> _t.Iterator[np.ndarray]:
        return (self.array[i:i + self.window] for i in self.range)
    
    @staticmethod
    def apply(fn: callable, array: np.ndarray, window: int, start: int = 0, stop: int = None) -> np.ndarray:
        """applies fn to the sliding window and stacks results"""
        return np.stack([fn(w) for w in Window(array, window, start, stop)])
    
    # did you know, you can nest classes? OOP world is very perverted
    class Fn(_t.NamedTuple):
        """partially applies `Window.apply`, fixing function and window"""
        fn: callable
        window: int

        def __call__(self, x: np.ndarray, start: int = 0, stop: int = None):
            return Window.apply(self.fn, x, self.window, start, stop)


# why python devs had to be such smartasses about built-ins? no `module` keyword, 
# no structs, no import by path, no multiple dispatch functions etc,
# but a bunch of useless junk like getters, setters, multiple inheritance, etc
# who even uses those?
class extrema(metaclass=su.Module):
    """
    module with extremum-finding functions.
    most useful functions:
    * find
    common function arguments:
    x: np.ndarray, 1D, discrete curve
    extr: extrema array (indices for x)
    w2: int, half-window (for scanning, etc)
    is_max: bool, search for maximum or minimum
    """
    # uses: Window, fp.Static
    def crude_find(
        x: np.ndarray, 
        w2: int, *, 
        is_max: bool = True,
    ) -> np.ndarray:
        argfind = np.argmax if is_max else np.argmin
        w = w2*2
        extr = Window.apply(argfind, x, w)
        extr = extr + np.arange(len(extr))
        return np.unique(extr)


    def filter_(
        extr: _t.Iterable[int], 
        x: np.ndarray, 
        w2: int, *, 
        is_max: bool = True,
    ) -> np.ndarray:
        fn_extr = np.max if is_max else np.min
        n = len(x)
        extr2 = []
        for ex in extr:
            b, e = ex - w2, ex + w2
            b = b if b >= 0 else 0
            e = e if e < n else n
            if fn_extr(x[b:e]) == x[ex]:
                extr2.append(ex)
        return np.unique(extr2)

    def refine(
        extr: _t.Iterable[int], 
        x: np.ndarray, 
        w2: int, *, 
        n_iter: int = 5, 
        is_max: bool = True,
    ) -> np.ndarray:
        """
        iteratively adjust position of extrema `extr` on the curve `x`.
        for each extremum index `ex` search `x[ex-w2:ex+w2]` area for a better extremum
        """
        argfind = np.argmax if is_max else np.argmin
        n = len(x)
        extr2 = []
        for ex in extr:
            for _ in range(n_iter):
                b, e = ex - w2, ex + w2
                b = b if b >= 0 else 0
                e = e if e < n else n
                ex, ex_prev = (argfind(x[b:e]) + b), ex
                if ex == ex_prev:
                    break
            extr2.append(ex)
        return np.unique(extr2)

    def find(
        x: np.ndarray, 
        w2: int, *, 
        is_max: bool = True, 
        refine_n_iter: int = 5,
    ) -> np.ndarray:
        """The primary function. x |> crude_find |> filter |> refine"""
        assert len(x) > w2*2, "x seems to short or w/2 is too big"
        extr = extrema.crude_find(x, w2, is_max=is_max)
        extr = extrema.filter_(extr, x, w2, is_max=is_max)
        extr = extrema.refine(extr, x, w2, n_iter=refine_n_iter, is_max=is_max)
        return extr
    
    def join(emn: np.ndarray, emx: np.ndarray) -> _t.Tuple[np.ndarray, np.ndarray]:
        """
        join local minima indices `emn` and local maxima indices `emx`
        to produce single sorted array of indices `extr` and boolean mask `is_max`
        to convert back:
        ```
        extr, is_max = join(emn, emx)
        emn, emx = extr[~is_max], extr[is_max]
        ```
        """
        is_max = np.array([False] * len(emn) + [True] * len(emx))
        extr = np.concatenate([emn, emx], axis=0)
        sorter = np.argsort(extr)
        return extr[sorter], is_max[sorter]

class solve(metaclass=su.Module):
    """
    solutions to common equalities
    """
    def poly2(a, b, c):
        """solve `ax**2 + bx + c == 0` for x ∈ ℝ"""
        assert np.all(a != 0), "a must not be 0"
        d = b**2 - 4*a*c
        if np.all(d < 0):
            raise NotImplementedError
        a2 = 2*a
        e = -b / a2
        if np.all(d==0):
            return e, e
        else:
            f = np.sqrt(d) / a2
            return (e + f), (e - f)

    def poly1(a, b):
        """solve `ax + b == 0` for x ∈ ℝ"""
        assert np.all(a != 0), "a must not be 0"
        return -b/a

# uses: itr.zip_w_next
class spline(metaclass=su.Module):
    """
    a bunch of spline-related stuff
    """
    def lerp(p1, p2, t) -> np.ndarray:
        """
        linear interpolation: p1 * (1-t) + p2 * t.
        p1, p2: (d,) shaped arrays
        t: (n, 1) shaped array or scalar
        returns (n, d) shaped array or a scalar
        """
        return p1 * (1-t) + p2 * t

    def multi_lerp(pts, t):
        """
        iterative linear interpolation between n points (gives n-spline segment)
        `pts` should support iter() and len() (list, array, tuple)
        """
        lerp = spline.lerp
        while len(pts)> 1:
            pts = [lerp(p1, p2, t) for p1, p2 in itr.zip_w_next(pts)]
        return pts[0]

    class Q(_t.NamedTuple):
        """
        Interpolate line with a quadratic spline based on a few samples.
        Points are used as spline handles, midpoints are used as knots. 
        2D example:
        ```
        import numpy as np; import matplotlib.pyplot as plt
        pts = np.stack([np.linspace(1, 10, 15), np.random.normal(size=15)], axis=-1)
        q = MidpointQSpline.from_midpoints(pts)
        qr = q.render()
        
        plt.figure(figsize = (10, 10),)
        plt.plot(pts[:, 0], pts[:, 1], color="blue", marker="o", lw=0.3, label = "DATA")
        plt.scatter(q.knots[1:-1, 0], q.knots[1:-1, 1], color = "red", label = "midpoints", marker="+")
        plt.plot(qr[:, 0], qr[:, 1], lw=1, color="magenta", label = "interpolated")
        plt.legend(fontsize=15)
        ```
        """
        handles: np.ndarray
        knots: np.ndarray

        def __iter__(self):
            return zip(itr.zip_w_next(self.knots), self.handles)
        
        @classmethod
        def from_midpoints(cls, data: np.ndarray):
            "data shape must be (n, d), where n is number of points d is number of dimensions"
            assert data.ndim == 2
            knots = np.stack([
                data[0], 
                *((p1+p2)/2 for p1, p2 in itr.zip_w_next(data)), 
                data[-1],
            ])
            return cls(data.copy(), knots)
        
        def project_variable(self, x: np.ndarray, var_no: int = 0):
            """
            project x (1-d array) values onto t-space (distance along the spline)
            trim values that do not fall into handles range
            knots in this dimension must be monothonic
            """
            handles = self.handles[:, var_no]
            knots = self.knots[:, var_no]
            assert is_monotonic(knots) or is_monotonic(knots, increasing=False), f"self.knots[{var_no}] are not monotonic"
            x = x[(np.min(handles) <= x) & (x < np.max(handles))]
            t = np.empty_like(x)
            segms = [ (k1<=x) & (x<k2) for k1, k2 in itr.zip_w_next(knots)]
            segms[-1] = segms[-1] | (x == knots[-1])
            for i, (segm, (k1, k2), h) in enumerate(zip(segms, itr.zip_w_next(knots), handles)):
                t[segm] = i + self.invert_segment(k1, h, k2, x[segm])
            return t
        
        def __repr__(self) -> str:
            return f"<{self.__class__.__name__} at {hex(id(self))}>"
                 
        @staticmethod
        def invert_segment(
            x1: float, 
            x2: float, 
            x3: float, 
            xs: np.ndarray,
        ) -> np.ndarray:
            """
            return values of spline parameter t 
            for knots `x1, x3`, handle `x2` 
            and observed values `xs` at certain segment.
            """    
            a = x1 - 2 * x2 + x3
            b = 2 * (x2 - x1)
            c = x1 - xs
            if a == 0:
                return solve.poly1(b, c)
            t1, t2 = solve.poly2(a, b, c)
            return t1 if np.all((0 <= t1) & (t1 < 1)) else t2
        
        def sample_at(self, t: np.ndarray, *, no_concatenation = False, strict=False):
            """
            no_concatenation: return segments separately 
            (for debugging, plotting)
            strict: raise error when number of segments does not match. 
            if `strict` is False, trim `t` to the appropriate length
            """
            assert np.all(t >=0) and t.ndim == 1
            n_segm = int(np.max(t)) + 1
            if n_segm <= self.n_segm():
                if strict:
                    raise ValueError(f"t implies {n_segm} segments," 
                    f"spline has only {self.n_segm()}")
                else:
                    n_segm = self.n_segm()
                    t = t[t < n_segm]
            multi_lerp = spline.multi_lerp
            segments = []
            for b, e in itr.zip_w_next(range(n_segm + 1)):
                t_segm = t[(b <= t) & (t < e)] - b
                if len(t_segm) == 0:
                    continue
                t_segm = t_segm[..., np.newaxis]
                k1 = self.knots[b]
                h = self.handles[b]
                k2 = self.knots[e]
                segm = multi_lerp([k1, h, k2], t_segm)
                segments.append(segm)
            if no_concatenation:
                return segments
            return np.concatenate(segments, axis=0)     
        
        def n_segm(self) -> int:
            return len(self.handles)
        
        def n_dim(self) -> int:
            return self.handles.shape[1]
        
        def render(self, points_per_segment: int = 10) -> np.ndarray:
            "return (n * points_per_segment, d) shaped array"
            multi_lerp = spline.multi_lerp
            t = np.linspace([0, ], [1, ], points_per_segment)
            segments = [multi_lerp([k1, h, k2], t) for (k1, k2), h in self]
            return np.concatenate(segments, axis=0)


class TableFn:
    """
    UNFINISHED. creates empyrical function that 
    uses linear interpolation to approximate a curve
    """
    def __init__(self): ...
    def __call__(self): ...
