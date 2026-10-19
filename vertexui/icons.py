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


# --- a second set -------------------------------------------------------
# Three projects shipped their own icon packs before these were here, and
# they overlapped: trash, download, cube, upload, plus/minus, eye, pencil,
# sort_up/sort_down, gauge and terminal each got drawn more than once. The
# originals stay a deliberately small set of interface verbs; these are the
# nouns and actions that turned out to be unavoidable.


def trash(dl, cx, cy, r, col):
    w = max(1.4, r * 0.17)
    dl.add_line(_p(cx, cy, -r * 0.8, -r * 0.55), _p(cx, cy, r * 0.8, -r * 0.55),
                col, w)
    dl.add_rect_filled(_p(cx, cy, -r * 0.28, -r * 0.8),
                       _p(cx, cy, r * 0.28, -r * 0.62), col, r * 0.08)
    dl.add_rect(_p(cx, cy, -r * 0.58, -r * 0.45), _p(cx, cy, r * 0.58, r * 0.85),
                col, r * 0.18, w)
    for dx in (-r * 0.22, r * 0.22):
        dl.add_line(_p(cx, cy, dx, -r * 0.25), _p(cx, cy, dx, r * 0.6), col, w * 0.8)


def download(dl, cx, cy, r, col):
    w = max(1.5, r * 0.19)
    dl.add_line(_p(cx, cy, 0, -r * 0.9), _p(cx, cy, 0, r * 0.25), col, w)
    dl.add_triangle_filled(_p(cx, cy, -r * 0.42, r * 0.12),
                           _p(cx, cy, r * 0.42, r * 0.12),
                           _p(cx, cy, 0, r * 0.62), col)
    dl.add_line(_p(cx, cy, -r * 0.75, r * 0.82), _p(cx, cy, r * 0.75, r * 0.82),
                col, w)


def upload(dl, cx, cy, r, col):
    w = max(1.5, r * 0.19)
    dl.add_line(_p(cx, cy, 0, r * 0.35), _p(cx, cy, 0, -r * 0.8), col, w)
    dl.add_triangle_filled(_p(cx, cy, -r * 0.42, -r * 0.3),
                           _p(cx, cy, r * 0.42, -r * 0.3),
                           _p(cx, cy, 0, -r * 0.82), col)
    dl.add_line(_p(cx, cy, -r * 0.75, r * 0.82), _p(cx, cy, r * 0.75, r * 0.82),
                col, w)


def plus(dl, cx, cy, r, col):
    w = max(1.6, r * 0.22)
    dl.add_line(_p(cx, cy, -r * 0.7, 0), _p(cx, cy, r * 0.7, 0), col, w)
    dl.add_line(_p(cx, cy, 0, -r * 0.7), _p(cx, cy, 0, r * 0.7), col, w)


def minus(dl, cx, cy, r, col):
    dl.add_line(_p(cx, cy, -r * 0.7, 0), _p(cx, cy, r * 0.7, 0),
                col, max(1.6, r * 0.22))


def pencil(dl, cx, cy, r, col):
    dl.add_triangle_filled(_p(cx, cy, -r * 0.85, r * 0.85),
                           _p(cx, cy, -r * 0.6, r * 0.3),
                           _p(cx, cy, -r * 0.3, r * 0.6), col)
    dl.add_quad_filled(_p(cx, cy, -r * 0.5, r * 0.44), _p(cx, cy, r * 0.46, -r * 0.52),
                       _p(cx, cy, r * 0.74, -r * 0.24), _p(cx, cy, -r * 0.22, r * 0.72),
                       col)
    dl.add_line(_p(cx, cy, r * 0.5, -r * 0.78), _p(cx, cy, r * 0.84, -r * 0.44),
                col, max(1.5, r * 0.2))


def eye(dl, cx, cy, r, col):
    """An almond of two arcs.

    The radius and centre offset are not free: for a half-width w and
    half-height h the arc radius is (w^2 + h^2) / 2h and its centre sits
    (R - h) away. Picking them by eye leaves the two arcs not meeting,
    which is what the first attempt did.
    """
    w, h = r * 0.92, r * 0.46
    rad = (w * w + h * h) / (2.0 * h)
    off = rad - h
    span = math.degrees(math.asin(min(1.0, w / rad)))
    th = max(1.4, r * 0.16)
    dl.path_arc_to(ImVec2(cx, cy + off), rad,
                   math.radians(270 - span), math.radians(270 + span), 24)
    dl.path_stroke(col, th, 0)
    dl.path_arc_to(ImVec2(cx, cy - off), rad,
                   math.radians(90 - span), math.radians(90 + span), 24)
    dl.path_stroke(col, th, 0)
    dl.add_circle_filled(ImVec2(cx, cy), r * 0.26, col)


def eye_off(dl, cx, cy, r, col):
    eye(dl, cx, cy, r, col)
    dl.add_line(_p(cx, cy, -r * 0.8, -r * 0.8), _p(cx, cy, r * 0.8, r * 0.8),
                col, max(1.6, r * 0.2))


def lock(dl, cx, cy, r, col):
    dl.add_rect_filled(_p(cx, cy, -r * 0.62, -r * 0.1), _p(cx, cy, r * 0.62, r * 0.78),
                       col, r * 0.16)
    dl.path_arc_to(ImVec2(cx, cy - r * 0.12), r * 0.42,
                   math.radians(180), math.radians(360), 18)
    dl.path_stroke(col, max(1.5, r * 0.19), 0)


def link(dl, cx, cy, r, col):
    """Two half-links facing each other across a bar."""
    th = max(1.5, r * 0.18)
    rad = r * 0.46
    dl.path_arc_to(ImVec2(cx - r * 0.38, cy), rad,
                   math.radians(50), math.radians(310), 22)
    dl.path_stroke(col, th, 0)
    dl.path_arc_to(ImVec2(cx + r * 0.38, cy), rad,
                   math.radians(230), math.radians(490), 22)
    dl.path_stroke(col, th, 0)
    dl.add_line(_p(cx, cy, -r * 0.3, 0), _p(cx, cy, r * 0.3, 0), col, th)


def filter_(dl, cx, cy, r, col):
    dl.add_triangle_filled(_p(cx, cy, -r * 0.85, -r * 0.7),
                           _p(cx, cy, r * 0.85, -r * 0.7),
                           _p(cx, cy, 0, r * 0.05), col)
    dl.add_rect_filled(_p(cx, cy, -r * 0.16, -r * 0.05),
                       _p(cx, cy, r * 0.16, r * 0.8), col, r * 0.08)


def list_(dl, cx, cy, r, col):
    w = max(1.4, r * 0.17)
    for i, dy in enumerate((-r * 0.6, 0, r * 0.6)):
        dl.add_circle_filled(_p(cx, cy, -r * 0.68, dy), max(1.0, r * 0.13), col)
        dl.add_line(_p(cx, cy, -r * 0.34, dy), _p(cx, cy, r * 0.8, dy), col, w)


def grid(dl, cx, cy, r, col):
    s = r * 0.36
    for dx in (-r * 0.46, r * 0.46):
        for dy in (-r * 0.46, r * 0.46):
            dl.add_rect_filled(_p(cx, cy, dx - s, dy - s), _p(cx, cy, dx + s, dy + s),
                               col, r * 0.1)


def sliders(dl, cx, cy, r, col):
    w = max(1.4, r * 0.16)
    for i, dy in enumerate((-r * 0.55, r * 0.05, r * 0.65)):
        dl.add_line(_p(cx, cy, -r * 0.85, dy), _p(cx, cy, r * 0.85, dy), col, w)
        kx = (-r * 0.25, r * 0.35, -r * 0.5)[i]
        dl.add_circle_filled(_p(cx, cy, kx, dy), r * 0.24, col)


def terminal(dl, cx, cy, r, col):
    w = max(1.5, r * 0.18)
    dl.add_line(_p(cx, cy, -r * 0.7, -r * 0.45), _p(cx, cy, -r * 0.2, 0), col, w)
    dl.add_line(_p(cx, cy, -r * 0.2, 0), _p(cx, cy, -r * 0.7, r * 0.45), col, w)
    dl.add_line(_p(cx, cy, r * 0.05, r * 0.5), _p(cx, cy, r * 0.75, r * 0.5), col, w)


def cube(dl, cx, cy, r, col):
    w = max(1.4, r * 0.16)
    top = [_p(cx, cy, 0, -r * 0.9), _p(cx, cy, r * 0.82, -r * 0.45),
           _p(cx, cy, 0, 0), _p(cx, cy, -r * 0.82, -r * 0.45)]
    dl.add_convex_poly_filled(top, col)
    dl.add_line(_p(cx, cy, -r * 0.82, -r * 0.45), _p(cx, cy, -r * 0.82, r * 0.45),
                col, w)
    dl.add_line(_p(cx, cy, r * 0.82, -r * 0.45), _p(cx, cy, r * 0.82, r * 0.45),
                col, w)
    dl.add_line(_p(cx, cy, 0, 0), _p(cx, cy, 0, r * 0.9), col, w)
    dl.add_line(_p(cx, cy, -r * 0.82, r * 0.45), _p(cx, cy, 0, r * 0.9), col, w)
    dl.add_line(_p(cx, cy, r * 0.82, r * 0.45), _p(cx, cy, 0, r * 0.9), col, w)


def cloud(dl, cx, cy, r, col):
    dl.add_circle_filled(_p(cx, cy, -r * 0.4, r * 0.05), r * 0.42, col)
    dl.add_circle_filled(_p(cx, cy, r * 0.05, -r * 0.25), r * 0.52, col)
    dl.add_circle_filled(_p(cx, cy, r * 0.5, r * 0.08), r * 0.38, col)
    dl.add_rect_filled(_p(cx, cy, -r * 0.42, r * 0.02), _p(cx, cy, r * 0.5, r * 0.46),
                       col, r * 0.18)


def clock_(dl, cx, cy, r, col):
    w = max(1.4, r * 0.16)
    dl.add_circle(ImVec2(cx, cy), r * 0.88, col, 0, w)
    dl.add_line(ImVec2(cx, cy), _p(cx, cy, 0, -r * 0.5), col, w)
    dl.add_line(ImVec2(cx, cy), _p(cx, cy, r * 0.42, r * 0.1), col, w)


def calendar(dl, cx, cy, r, col):
    w = max(1.3, r * 0.15)
    dl.add_rect(_p(cx, cy, -r * 0.82, -r * 0.62), _p(cx, cy, r * 0.82, r * 0.85),
                col, r * 0.14, w)
    dl.add_rect_filled(_p(cx, cy, -r * 0.82, -r * 0.62),
                       _p(cx, cy, r * 0.82, -r * 0.24), col, r * 0.1)
    for dx in (-r * 0.45, r * 0.45):
        dl.add_line(_p(cx, cy, dx, -r * 0.9), _p(cx, cy, dx, -r * 0.5), col, w * 1.3)
    for dx in (-r * 0.4, 0.0, r * 0.4):
        dl.add_circle_filled(_p(cx, cy, dx, r * 0.3), max(0.9, r * 0.11), col)


def user(dl, cx, cy, r, col):
    dl.add_circle_filled(_p(cx, cy, 0, -r * 0.38), r * 0.36, col)
    dl.path_arc_to(ImVec2(cx, cy + r * 0.95), r * 0.72,
                   math.radians(200), math.radians(340), 22)
    dl.path_stroke(col, max(1.6, r * 0.24), 0)


def star(dl, cx, cy, r, col):
    """Five points. Concave, so this needs the concave fill - a triangle
    fan from one vertex turns it into a pentagon."""
    pts = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        rad = r if i % 2 == 0 else r * 0.42
        pts.append(_p(cx, cy, math.cos(a) * rad, math.sin(a) * rad))
    dl.add_concave_poly_filled(pts, col)


def tag(dl, cx, cy, r, col):
    """A luggage tag. Filled it is indistinguishable from `play`, so it is
    drawn as an outline with its hole."""
    pts = [_p(cx, cy, -r * 0.8, -r * 0.7), _p(cx, cy, r * 0.2, -r * 0.7),
           _p(cx, cy, r * 0.85, 0), _p(cx, cy, r * 0.2, r * 0.7),
           _p(cx, cy, -r * 0.8, r * 0.7)]
    dl.add_polyline(pts + [pts[0]], col, max(1.4, r * 0.17), 0)
    dl.add_circle_filled(_p(cx, cy, -r * 0.42, 0), max(1.1, r * 0.15), col)


def home(dl, cx, cy, r, col):
    dl.add_triangle_filled(_p(cx, cy, 0, -r * 0.92), _p(cx, cy, -r * 0.95, -r * 0.02),
                           _p(cx, cy, r * 0.95, -r * 0.02), col)
    dl.add_rect_filled(_p(cx, cy, -r * 0.62, -r * 0.08), _p(cx, cy, r * 0.62, r * 0.82),
                       col, r * 0.1)


def arrow_left(dl, cx, cy, r, col):
    w = max(1.5, r * 0.19)
    dl.add_line(_p(cx, cy, r * 0.75, 0), _p(cx, cy, -r * 0.5, 0), col, w)
    dl.add_triangle_filled(_p(cx, cy, -r * 0.8, 0), _p(cx, cy, -r * 0.2, -r * 0.45),
                           _p(cx, cy, -r * 0.2, r * 0.45), col)


def arrow_right(dl, cx, cy, r, col):
    w = max(1.5, r * 0.19)
    dl.add_line(_p(cx, cy, -r * 0.75, 0), _p(cx, cy, r * 0.5, 0), col, w)
    dl.add_triangle_filled(_p(cx, cy, r * 0.8, 0), _p(cx, cy, r * 0.2, -r * 0.45),
                           _p(cx, cy, r * 0.2, r * 0.45), col)


def sort_up(dl, cx, cy, r, col):
    dl.add_triangle_filled(_p(cx, cy, 0, -r * 0.6), _p(cx, cy, -r * 0.55, r * 0.3),
                           _p(cx, cy, r * 0.55, r * 0.3), col)


def sort_down(dl, cx, cy, r, col):
    dl.add_triangle_filled(_p(cx, cy, 0, r * 0.6), _p(cx, cy, -r * 0.55, -r * 0.3),
                           _p(cx, cy, r * 0.55, -r * 0.3), col)


def gauge_icon(dl, cx, cy, r, col):
    dl.path_arc_to(ImVec2(cx, cy + r * 0.3), r * 0.85,
                   math.radians(180), math.radians(360), 24)
    dl.path_stroke(col, max(1.5, r * 0.19), 0)
    dl.add_line(_p(cx, cy, 0, r * 0.3), _p(cx, cy, r * 0.42, -r * 0.3),
                col, max(1.5, r * 0.19))
    dl.add_circle_filled(_p(cx, cy, 0, r * 0.3), r * 0.16, col)


def copy_(dl, cx, cy, r, col):
    w = max(1.3, r * 0.15)
    dl.add_rect(_p(cx, cy, -r * 0.85, -r * 0.85), _p(cx, cy, r * 0.25, r * 0.25),
                col, r * 0.12, w)
    dl.add_rect(_p(cx, cy, -r * 0.25, -r * 0.25), _p(cx, cy, r * 0.85, r * 0.85),
                col, r * 0.12, w)


def external(dl, cx, cy, r, col):
    w = max(1.3, r * 0.15)
    dl.add_rect(_p(cx, cy, -r * 0.85, -r * 0.5), _p(cx, cy, r * 0.5, r * 0.85),
                col, r * 0.12, w)
    dl.add_line(_p(cx, cy, 0, -r * 0.1), _p(cx, cy, r * 0.8, -r * 0.85), col, w * 1.3)
    dl.add_triangle_filled(_p(cx, cy, r * 0.88, -r * 0.92), _p(cx, cy, r * 0.2, -r * 0.8),
                           _p(cx, cy, r * 0.78, -r * 0.2), col)


ICONS.update({
    "trash": trash, "download": download, "upload": upload, "plus": plus,
    "minus": minus, "pencil": pencil, "eye": eye, "eye_off": eye_off,
    "lock": lock, "link": link, "filter": filter_, "list": list_,
    "grid": grid, "sliders": sliders, "terminal": terminal, "cube": cube,
    "cloud": cloud, "clock": clock_, "calendar": calendar, "user": user,
    "star": star, "tag": tag, "home": home, "arrow_left": arrow_left,
    "arrow_right": arrow_right, "sort_up": sort_up, "sort_down": sort_down,
    "gauge": gauge_icon, "copy": copy_, "external": external,
})


def register(name, fn):
    """Add an icon at runtime.

    A project with its own vocabulary should put it here rather than
    shipping a second icon module - every widget that takes an icon name
    then finds it, including cards, badges and the rail layout.
    """
    ICONS[name] = fn
    return fn
