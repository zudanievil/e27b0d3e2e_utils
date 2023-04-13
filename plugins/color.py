#! /usr/bin/env python3

"""useful color-related functions"""

import sys, os
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from typing import NamedTuple as _NT

MAPS = dict(
  seqential = ['Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds','YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu', 'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn'],
  uniform_sequential = ['viridis', 'plasma', 'inferno', 'magma', 'cividis'],
  pseudo_sequential = ['binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink', 'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia', 'hot', 'afmhot', 'gist_heat', 'copper'],
  diverging = ['PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu', 'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic'],
  cyclic = ['twilight', 'twilight_shifted', 'hsv'],
  qualitative = ['Pastel1', 'Pastel2', 'Paired', 'Accent', 'Dark2', 'Set1', 'Set2', 'Set3', 'tab10', 'tab20', 'tab20b', 'tab20c'],
  misc = ['flag', 'prism', 'ocean', 'gist_earth', 'terrain', 'gist_stern', 'gnuplot', 'gnuplot2', 'CMRmap','cubehelix', 'brg', 'gist_rainbow', 'rainbow', 'jet', 'turbo', 'nipy_spectral', 'gist_ncar'],
)

_gradient = np.linspace(0, 1, 256)
_gradient = np.vstack((_gradient, _gradient))


def plot_color_gradients(category_or_list):
    # from: https://matplotlib.org/stable/tutorials/colors/colormaps.html
    if type(category_or_list) == str:
        cmaps = MAPS[category_or_list]
    else:
        cmaps = category_or_list
    cmaps = [
        (x, mpl.colormaps[x]) if type(x) == str 
        else (f"#{i}", x)
        for i, x in enumerate(cmaps)
    ]
    # Create figure and adjust figure height to number of colormaps
    nrows = len(cmaps)
    figh = 0.35 + 0.15 + (nrows + (nrows - 1) * 0.1) * 0.22
    fig, axs = plt.subplots(nrows=nrows + 1, figsize=(6.4, figh))
    fig.subplots_adjust(top=1 - 0.35 / figh, bottom=0.15 / figh,
                        left=0.2, right=0.99)
    for ax, (name, cmap) in zip(axs, cmaps):
        ax.imshow(_gradient, aspect='auto', cmap=cmap)
        ax.text(-0.01, 0.5, name, va='center', ha='right', fontsize=10,
                transform=ax.transAxes)
    # Turn off *all* ticks & spines, not just the ones with colormaps.
    for ax in axs:
        ax.set_axis_off()
    return fig


class Color(_NT):
    rgb: np.ndarray
    alpha: float = 1.
    
    def with_(self, rgb = None, alpha = None) -> "Color":
        assert not rgb is None and alpha is None
        return Color(self.rgb, alpha) if rgb is None else Color(rgb, self.alpha)

        
def rgb(r, g, b) -> Color:
    return Color(np.array([r,g,b]))
    
def hsl(h, s, l) -> Color: ...

def gamma(c: Color, factor: float, gamma: float):
    return c.with_(rgb=np.power(c.rgb * factor, gamma))

def wavelength(w) -> Color:
    "from: https://405nm.com/wavelength-to-color/"
    if w < 380 or w >= 809:
        return None
        
    elif 380 <= w < 440:
        c = rgb(r=-(w - 440) / (440 - 380), g=0., b=1.)
    elif 440 <= w < 490:
        c = rgb(r=0., g=(w - 440) / (490 - 440), b=1.)
    elif 490 <= w < 510:
        c = rgb(r=0., g=1., b=-(w - 510) / (510 - 490))
    elif 510 <= w < 580:
        c = rgb((w - 510) / (580 - 510), g=1., b=0.)
    elif 580 <= w < 645:
        c = rgb(r=1., g=-(w - 645) / (645 - 580), b=0.0)
    elif 645 <= w < 809:
        c = rgb(1., 0., 0.)
    
    if 380 <= w < 420:
        f = .3 + .7*(w - 380) / (420 - 380)
    elif 420 <= w < 645:
        f = 1.
    elif 645 <= w < 809:
        f = .3 + .7*(809 - w) / (809 - 644);
    g = 0.80
    
    c1 = np.where(c>0., gamma(c, f, g).rgb, 0.)
    return c.with_(rgb=c1)
    
    
    
# def lighten(c: Color, t=0.5) -> Color:...
# def darken(c: Color, t=0.5) -> Color:...
# def as_type(t: type, c: Color):...
# def to_space(cspace: str, c: Color):...

__rgb_to_gray = np.array([0.21, 0.71, 0.08])
def grayscale(c: Color) -> float:
    return __rgb_to_gray @ c.rgb


# table precomputed from https://github.com/hatoo/blackbody/
# for K = np.arange(1300, 3301, 100)
__t_to_rgb = np.array([
2.1561354e-3,1.7803945e-4,0,5.2513247e-3,5.659361e-4,0,1.11067165e-2,
1.4771952e-3,0,2.0967307e-2,3.3162034e-3,0,3.6076967e-2,6.6082915e-3,
0,5.7504408e-2,1.195906e-2,0,8.600103e-2,1.9994628e-2,0,1.21914566e-1,
3.129632e-2,9.884327e-4,1.6516554e-1,4.6341084e-2,2.8962828e-3,2.1527435e-1,
6.5457694e-2,6.076903e-3,2.714289e-1,8.8801555e-2,1.0898059e-2,3.3256987e-1,
1.16348386e-1,1.771186e-2,3.9748088e-1,1.4790559e-1,2.682952e-2,4.6488124e-1,
1.8313211e-1,3.8501196e-2,5.3349376e-1,2.2157055e-1,5.2901797e-2,6.021079e-1,
2.6267743e-1,7.012358e-2,6.6962135e-1,3.0585575e-1,9.017473e-2,7.3506474e-1,
3.504873e-1,1.12983376e-1,7.9762226e-1,3.9595428e-1,1.3840525e-1,8.566284e-1,
4.416649e-1,1.6623387e-1,9.115716e-1,4.870644e-1,1.9621278e-1
], dtype="f4").reshape((-1, 3))

def blackbody(K):
    if not 1300 <= K <= 3300:
        return None
    elif K == 3300:
        return Color(__t_to_rgb[-1])
    i, w = (K // 100 - 13), (K % 100 / 100)
    c = (1-w) * __t_to_rgb[i] + w * __t_to_rgb[i+1]
    return Color(c)
