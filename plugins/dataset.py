#! /usr/bin/env python3
import pandas as pd
import numpy as np
import skimage.transform as tf
from typing import *
from enum import Enum

su = sys.startup
fp, = su.require_plugins("fp")
from fp import Dispatch, reduce
import operator

class pt(NamedTuple):
    """2d coordinates"""
    x: float
    y: float
    
    def __add__(self, other: "pt") -> "pt":
        return pt(self.x + other.x, self.y + other.y)
        
    def __sub__(self, other: "pt") -> "pt":
        return pt(self.x - other.x, self.y - other.y)
    
    def __neg__(self) -> "pt":
        return pt(-self.x, -self.y)
    
    def l2(self) -> float:
        return self.x * np.sqrt(1 + self.y/self.x)
    

class Gaussian(NamedTuple):
    mu: float = 0
    sigma: float = 1


class LSegment(NamedTuple):
    start: pt
    stop: pt
    
    def l2(self) -> float:
        return (self.start - self.stop).l2()

  
class LSpline(NamedTuple):
    bps: List[pt]
    
    def segments(self):
        return (LSegment(b, e) for b, e in zip(self.bps[:-1], self.bps[1:]))
    
    def l2(self) -> np.array:
        return np.array([seg.l2() for seg in self.segments()])


class Op(NamedTuple):
    op: callable
    terms: list

SumOp = lambda *xs: Op(operator.add, list(xs))
    
def affine(
    rads: float = 0, 
    center: pt = pt(0, 0), 
    shear: pt = pt(0, 0), 
    scale: pt = pt(1, 1),
    shift: pt = pt(0, 0),
) -> tf.AffineTransform:
    """
    unfortunately, `AffineTransform` provides no means to specify 
    the rotation center. this constructor compencates for that.
    """
    assert scale.x >= 0 and scale.y >= 0
    a = np.cos(rads)
    b = np.sin(rads)
    return tf.AffineTransform(matrix=np.array([
        a,  
        b + shear.x, 
        (scale.x - a) * center.x - b * center.y + shift.x,
        -b, 
        a + shear.y, 
        (scale.y - a) * center.y + b * center.x + shift.y,
        0, 0, 1
    ]).reshape(3, 3))


@Dispatch.new(LSegment)
def render(x: LSegment, N: int) -> np.array:
    return np.linspace(x.start, x.stop, N)    


@render.register(LSpline)
def render(x: LSpline, N: int) -> np.array:
    render_ = render.registry[LSegment]
    lengths = x.l2()
    pts = np.int64(lengths / sum(lengths) * N) # плохой механизм, точки выпадают
    return np.concatenate([ 
        render_(bp, n) for n, bp in zip(pts, x.segments())
    ], axis=0)
    
@render.register(Gaussian)
def render(x: Gaussian, N: int) -> np.array:
    return np.random.normal(x.mu, x.sigma, N)
    
@render.register(Op)
def render(x: Op, N: int) -> np.array:
    return reduce(x.op, (render(t, N) for t in x.terms))
    
    
    

