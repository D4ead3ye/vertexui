"""Vector icons drawn with the draw list - no font, no atlas, no files.

Icon fonts are the usual answer and they are a bad fit for a toolkit: they
need an asset shipped alongside, they break when a glyph range is missing,
and they render as tofu boxes when they fail. These are drawn from
primitives, so they are crisp at any DPI, take the theme's colour, and
cannot go missing.

    icons.draw("play", dl, x, y, 16, colour)
    if widgets.button("Start", icon="play"):
        ...

Add your own by putting a function in ICONS - anything with the signature
(dl, cx, cy, r, col) where (cx, cy) is the centre and r the half-size.
"""

import math

from imgui_bundle import ImVec2, imgui


def _p(cx, cy, dx, dy):
    return ImVec2(cx + dx, cy + dy)


def play(dl, cx, cy, r, col):
    dl.add_triangle_filled(_p(cx, cy, -r * 0.55, -r), _p(cx, cy, -r * 0.55, r),
                           _p(cx, cy, r * 0.8, 0), col)


def stop(dl, cx, cy, r, col):
    dl.add_rect_filled(_p(cx, cy, -r * 0.72, -r * 0.72),
                       _p(cx, cy, r * 0.72, r * 0.72), col, r * 0.22)


def pause(dl, cx, cy, r, col):
    w = r * 0.3
    dl.add_rect_filled(_p(cx, cy, -r * 0.6, -r * 0.8), _p(cx, cy, -r * 0.6 + w, r * 0.8),
                       col, w * 0.4)
    dl.add_rect_filled(_p(cx, cy, r * 0.3, -r * 0.8), _p(cx, cy, r * 0.3 + w, r * 0.8),
                       col, w * 0.4)


def check(dl, cx, cy, r, col):
    dl.add_line(_p(cx, cy, -r * 0.62, r * 0.05), _p(cx, cy, -r * 0.18, r * 0.52),
                col, max(1.6, r * 0.24))
    dl.add_line(_p(cx, cy, -r * 0.18, r * 0.52), _p(cx, cy, r * 0.66, -r * 0.55),
                col, max(1.6, r * 0.24))


def cross(dl, cx, cy, r, col):
    d = r * 0.6
    w = max(1.6, r * 0.22)
    dl.add_line(_p(cx, cy, -d, -d), _p(cx, cy, d, d), col, w)
    dl.add_line(_p(cx, cy, d, -d), _p(cx, cy, -d, d), col, w)


def warning(dl, cx, cy, r, col):
    dl.add_triangle_filled(_p(cx, cy, 0, -r), _p(cx, cy, -r, r * 0.78),
                           _p(cx, cy, r, r * 0.78), col)


def info(dl, cx, cy, r, col):
    dl.add_circle(ImVec2(cx, cy), r, col, 0, max(1.4, r * 0.18))
    dl.add_circle_filled(_p(cx, cy, 0, -r * 0.42), max(1.0, r * 0.12), col)
    dl.add_line(_p(cx, cy, 0, -r * 0.08), _p(cx, cy, 0, r * 0.5), col, max(1.4, r * 0.18))


def gear(dl, cx, cy, r, col, teeth=8):
    for i in range(teeth):
        a = i * math.tau / teeth
        dl.add_line(_p(cx, cy, math.cos(a) * r * 0.62, math.sin(a) * r * 0.62),
                    _p(cx, cy, math.cos(a) * r, math.sin(a) * r),
                    col, max(1.8, r * 0.26))
    dl.add_circle(ImVec2(cx, cy), r * 0.55, col, 0, max(1.6, r * 0.2))


def folder(dl, cx, cy, r, col):
    dl.add_rect_filled(_p(cx, cy, -r, -r * 0.5), _p(cx, cy, -r * 0.1, -r * 0.2),
                       col, r * 0.12)
    dl.add_rect_filled(_p(cx, cy, -r, -r * 0.32), _p(cx, cy, r, r * 0.7), col, r * 0.16)


def refresh(dl, cx, cy, r, col):
    dl.path_arc_to(ImVec2(cx, cy), r * 0.72, math.radians(60), math.radians(330), 24)
    dl.path_stroke(col, max(1.6, r * 0.2))
    a = math.radians(40)
    tip = _p(cx, cy, math.cos(a) * r * 0.72, math.sin(a) * r * 0.72)
    dl.add_triangle_filled(tip, _p(cx, cy, r * 0.28, r * 0.28),
                           _p(cx, cy, r * 0.86, r * 0.18), col)


def search(dl, cx, cy, r, col):
    dl.add_circle(_p(cx, cy, -r * 0.15, -r * 0.15), r * 0.55, col, 0, max(1.5, r * 0.18))
    dl.add_line(_p(cx, cy, r * 0.25, r * 0.25), _p(cx, cy, r * 0.75, r * 0.75),
                col, max(1.6, r * 0.2))


def dot(dl, cx, cy, r, col):
    dl.add_circle_filled(ImVec2(cx, cy), r * 0.45, col)


def chevron(dl, cx, cy, r, col):
    w = max(1.6, r * 0.2)
    dl.add_line(_p(cx, cy, -r * 0.5, -r * 0.25), _p(cx, cy, 0, r * 0.3), col, w)
    dl.add_line(_p(cx, cy, 0, r * 0.3), _p(cx, cy, r * 0.5, -r * 0.25), col, w)


def bolt(dl, cx, cy, r, col):
    dl.add_triangle_filled(_p(cx, cy, r * 0.15, -r), _p(cx, cy, -r * 0.55, r * 0.15),
                           _p(cx, cy, 0, r * 0.15), col)
    dl.add_triangle_filled(_p(cx, cy, 0, r * 0.15), _p(cx, cy, -r * 0.15, r),
                           _p(cx, cy, r * 0.55, -r * 0.15), col)


def sound_on(dl, cx, cy, r, col):
    dl.add_triangle_filled(_p(cx, cy, -r * 0.2, -r * 0.45), _p(cx, cy, -r * 0.2, r * 0.45),
                           _p(cx, cy, -r * 0.75, 0), col)
    dl.add_rect_filled(_p(cx, cy, -r * 0.75, -r * 0.28), _p(cx, cy, -r * 0.35, r * 0.28), col)
    for i, rad in enumerate((0.42, 0.68)):
        dl.path_arc_to(ImVec2(cx - r * 0.2, cy), r * rad + r * 0.1,
                       math.radians(-55), math.radians(55), 12)
        dl.path_stroke(col, max(1.3, r * 0.15))


def sound_off(dl, cx, cy, r, col):
    dl.add_triangle_filled(_p(cx, cy, -r * 0.2, -r * 0.45), _p(cx, cy, -r * 0.2, r * 0.45),
                           _p(cx, cy, -r * 0.75, 0), col)
    dl.add_rect_filled(_p(cx, cy, -r * 0.75, -r * 0.28), _p(cx, cy, -r * 0.35, r * 0.28), col)
    w = max(1.4, r * 0.17)
    dl.add_line(_p(cx, cy, r * 0.1, -r * 0.4), _p(cx, cy, r * 0.8, r * 0.4), col, w)
    dl.add_line(_p(cx, cy, r * 0.8, -r * 0.4), _p(cx, cy, r * 0.1, r * 0.4), col, w)


ICONS = {
    "play": play, "stop": stop, "pause": pause, "check": check, "cross": cross,
    "warning": warning, "info": info, "gear": gear, "folder": folder,
    "refresh": refresh, "search": search, "dot": dot, "chevron": chevron,
    "bolt": bolt, "sound_on": sound_on, "sound_off": sound_off,
}

# The names a status kind maps to, so toasts and badges agree.
STATUS_ICONS = {"ok": "check", "warn": "warning", "error": "cross", "info": "info"}


def draw(name, dl, cx, cy, r, col):
    """Draw icon `name` centred at (cx, cy). Unknown names draw nothing
    rather than raising - a missing icon should not take a frame down."""
    fn = ICONS.get(name)
    if fn is not None:
        fn(dl, cx, cy, r, col)


def names():
    return sorted(ICONS)
