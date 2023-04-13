#! /usr/bin/env python3
"""
module for ANSI terminal colors
"""

class M:
    """
    color modifiers. 
    everything except `reset` can be inversed like:
    `m.no + m.inverse`
    """
    reset =     0
    bold =      1
    underline = 4
    inverse =   7
    no =        20

class C:
    """
    color codes + `bg` (background) and `light` modifiers.
    some terminals do not support `light` modifiers.
    modifiers are added to files. example:
    ```
    s1 = C.olor(M.bold, C.black, C.yellow + C.light + C.bg)
    print("XyZ " + s1 + "AbC" + C.reset + " DeF")
    ```
    """
    bg =      10
    light =   60
    
    black =   30
    red =     31
    green =   32
    yellow =  33
    blue =    34
    magenta = 35
    cyan =    36
    white =   37
    
    @staticmethod
    def olor(*opts: int) -> str:
        "format color string"
        return "\033[" + ";".join(map(str, opts)) + "m"
    reset = "\033[" + str(M.reset) + "m"

class ColoredText:
    __slots__ = ("s", "c",)
    "Colored string"
    def __init__(self, s: str, c: str):
        self.s = s; self.c = c 
    def __str__(self) -> str:
        return self.c + self.s + C.reset
        
CT = ColoredText

class ColoredTextFactory:
    __slots__ = ("c", )
    def __init__(self, *opts, c: str=None) -> str:
        self.c = c or C.olor(*opts)
    def __call__(self, *ss, sep="") -> CT:
        "join strings and ColoredText into a single ColoredText"
        c = self.c; r = C.reset
        s = sep.join(
            c+s if type(s) is str else r+str(s)
            for s in ss
        )
        return CT(s=s, c="")

CTF = ColoredTextFactory


