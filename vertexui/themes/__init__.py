"""Bundled themes - profiles that carry a skin as well as a palette.

A `profiles` entry is configuration: colours, shape, type, density, which
layout. A theme here is that plus drawing - its own card, its own button,
its own spinner, its own window ground - built on `skins`.

    from vertexui import themes
    app = compose.App(profile=themes.SBR)

They register themselves into `profiles.ALL`, so they show up in the
settings panel's theme picker and in `tools/matrix.py` alongside the seven
built-in profiles, and `profiles.get("steel-ball-run")` finds them.
"""

from .. import profiles as _profiles
from .aero import AERO_PROFILE as AERO
from .sbr import SBR
from .y2k import Y2K
from .ymo import YMO

__all__ = ["AERO", "SBR", "Y2K", "YMO", "ALL", "names", "get"]

ALL = {t.name: t for t in (SBR, Y2K, AERO, YMO)}


def names():
    return list(ALL)


def get(name):
    return ALL.get(name)


# Make them first-class: anything that walks profiles finds these too.
for _name, _theme in ALL.items():
    _profiles.ALL.setdefault(_name, _theme)
    if _name not in _profiles.ORDER:
        _profiles.ORDER.append(_name)
