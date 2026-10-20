"""Drawing helpers for skins and hand-drawn widgets.

Every one of these got written independently inside the first two or
three themes before it lived here - a gradient fill in all three, a dot
field in two, a glow in two, a chamfered polygon in two. That is the same
signal the application survey turned up, arriving from inside the toolkit
this time, so it gets the same answer.

    from vertexui import paint
    paint.grad_rect(dl, x, y, w, h, top, bottom, rounding=8)
    paint.gloss(dl, x, y, w, h, 8)
    paint.halftone(dl, x, y, w, h, ink)

Nothing here reads the theme. They take colours and sizes so a skin can
use them for anything, which is the only way a helper survives contact
with a look it was not written for.
"""

import math

from imgui_bundle import ImVec2, imgui

from . import theme as theme_mod

__all__ = ["grad_rect", "grad_poly", "gloss", "halo", "dots", "halftone",
           "hatch", "scanlines", "bevel", "notched", "chamfered", "pill",
           "spiral"]


# --- fills -------------------------------------------------------------

def grad_rect(dl, x, y, w, h, top, bottom, rounding=0.0, horizontal=False):
    """A rounded rect with a gradient.

    ImGui's own multi-colour rect is square-cornered. The way round it is
    to draw the rounded fill normally and then re-colour the vertices it
    just emitted - `KeepAlpha` leaves the anti-aliased corner coverage
    alone, so the fringe picks up the gradient with everything else.
    """
    i0 = dl.vtx_buffer.size()
    dl.add_rect_filled(ImVec2(x, y), ImVec2(x + w, y + h),
                       theme_mod.u32(top), rounding)
    i1 = dl.vtx_buffer.size()
    if i1 > i0:
        a = ImVec2(x, y)
        b = ImVec2(x + w, y) if horizontal else ImVec2(x, y + h)
        imgui.internal.shade_verts_linear_color_gradient_keep_alpha(
            dl, i0, i1, a, b, theme_mod.u32(top), theme_mod.u32(bottom))


def grad_poly(dl, points, top, bottom):
    """The same trick for an arbitrary convex polygon - a notched card, a
    chamfered panel. Takes its axis from the polygon's own bounds."""
    if not points:
        return
    y0 = min(p.y for p in points)
    y1 = max(p.y for p in points)
    x0 = min(p.x for p in points)
    i0 = dl.vtx_buffer.size()
    dl.add_convex_poly_filled(points, theme_mod.u32(top))
    i1 = dl.vtx_buffer.size()
    if i1 > i0:
        imgui.internal.shade_verts_linear_color_gradient_keep_alpha(
            dl, i0, i1, ImVec2(x0, y0), ImVec2(x0, y1),
            theme_mod.u32(top), theme_mod.u32(bottom))


def gloss(dl, x, y, w, h, rounding, colour, strength=1.0, share=0.46,
          band=True):
    """A specular sweep across the top of a surface.

    Two parts, and both are needed: a wash over the top `share` of the
    shape, and a narrow diagonal band crossing it. The wash alone reads as
    a gradient; the band is what says the surface is hard and catching a
    light source.
    """
    gh = h * share
    grad_rect(dl, x + 1, y + 1, w - 2, gh,
              theme_mod.with_alpha(colour, 0.52 * strength),
              theme_mod.with_alpha(colour, 0.0), rounding)
    if band:
        dl.push_clip_rect(ImVec2(x, y), ImVec2(x + w, y + gh + 1), True)
        bw = w * 0.42
        bx = x + w * 0.04
        dl.add_convex_poly_filled(
            [ImVec2(bx, y + gh), ImVec2(bx + bw * 0.55, y),
             ImVec2(bx + bw, y), ImVec2(bx + bw * 0.45, y + gh)],
            theme_mod.u32(colour, 0.20 * strength))
        dl.pop_clip_rect()
    dl.add_line(ImVec2(x + rounding * 0.7, y + 1.2),
                ImVec2(x + w - rounding * 0.7, y + 1.2),
                theme_mod.u32(colour, 0.85 * strength), 1.4)


def halo(dl, x, y, w, h, rounding, colour, amount=1.0, rings=5, spread=9.0):
    """A soft outer glow as nested outlines of falling alpha - the nearest
    a draw list gets to a blur, and at this radius indistinguishable."""
    for i in range(rings, 0, -1):
        g = spread * i / rings
        dl.add_rect(ImVec2(x - g, y - g), ImVec2(x + w + g, y + h + g),
                    theme_mod.u32(colour,
                                  amount * 0.16 * (1.0 - i / (rings + 1))),
                    rounding + g, 2.0)


def bevel(dl, x, y, w, h, light, dark, out=True, depth=2.0):
    """The inset/outset 3D border.

    Light from the top-left: an outset edge is lit on the top and left and
    shaded on the bottom and right, and an inset one is that reversed.
    That single rule is the whole of 1990s interface depth.
    """
    a, b = (light, dark) if out else (dark, light)
    for i in range(int(depth)):
        dl.add_line(ImVec2(x + i, y + i), ImVec2(x + w - i, y + i), a, 1.0)
        dl.add_line(ImVec2(x + i, y + i), ImVec2(x + i, y + h - i), a, 1.0)
        dl.add_line(ImVec2(x + i, y + h - i), ImVec2(x + w - i, y + h - i), b, 1.0)
        dl.add_line(ImVec2(x + w - i, y + i), ImVec2(x + w - i, y + h - i), b, 1.0)


# --- textures ----------------------------------------------------------

def dots(dl, x, y, w, h, colour, step=8.0, size=1.0):
    """A dot-matrix field. Clipped and stepped rather than per-pixel, so a
    full window costs a few thousand one-pixel rects and not a texture."""
    dl.push_clip_rect(ImVec2(x, y), ImVec2(x + w, y + h), True)
    col = theme_mod.u32(colour) if not isinstance(colour, int) else colour
    gy = y - (y % step)
    while gy < y + h:
        gx = x - (x % step)
        while gx < x + w:
            dl.add_rect_filled(ImVec2(gx, gy), ImVec2(gx + size, gy + size), col)
            gx += step
        gy += step
    dl.pop_clip_rect()


def halftone(dl, x, y, w, h, colour, step=6.0, fade=True):
    """Ben-day dots on a 45-degree lattice.

    Screentone is how a page gets a grey without a grey ink. With `fade`
    the dots grow toward the bottom, which is the same job a gradient does
    and the way print actually does it.
    """
    col = theme_mod.u32(colour) if not isinstance(colour, int) else colour
    dl.push_clip_rect(ImVec2(x, y), ImVec2(x + w, y + h), True)
    rows = int(h / step) + 2
    for r in range(rows):
        gy = y + r * step
        off = (r % 2) * step * 0.5
        k = (r / max(1, rows - 1)) if fade else 1.0
        size = 0.6 + 1.5 * (k ** 1.8)
        gx = x + off
        while gx < x + w:
            dl.add_rect_filled(ImVec2(gx, gy), ImVec2(gx + size, gy + size), col)
            gx += step
    dl.pop_clip_rect()


def hatch(dl, x, y, w, h, colour, step=5.0, thickness=1.0):
    """Diagonal ink hatching, clipped to a box - shading for a theme that
    draws rather than lights."""
    col = theme_mod.u32(colour) if not isinstance(colour, int) else colour
    dl.push_clip_rect(ImVec2(x, y), ImVec2(x + w, y + h), True)
    k = -h
    while k < w:
        dl.add_line(ImVec2(x + k, y + h), ImVec2(x + k + h, y), col, thickness)
        k += step
    dl.pop_clip_rect()


def scanlines(dl, x, y, w, h, colour, step=3.0, thickness=1.0):
    """Horizontal CRT lines over everything."""
    col = theme_mod.u32(colour) if not isinstance(colour, int) else colour
    gy = y
    while gy < y + h:
        dl.add_rect_filled(ImVec2(x, gy), ImVec2(x + w, gy + thickness), col)
        gy += step


# --- shapes ------------------------------------------------------------

def notched(x, y, w, h, cut):
    """An octagon - a rectangle with all four corners cut off. Reads as
    something stamped or machined, where a radius reads as moulded."""
    cut = max(2.0, min(cut, min(w, h) * 0.3))
    return [ImVec2(x + cut, y), ImVec2(x + w - cut, y),
            ImVec2(x + w, y + cut), ImVec2(x + w, y + h - cut),
            ImVec2(x + w - cut, y + h), ImVec2(x + cut, y + h),
            ImVec2(x, y + h - cut), ImVec2(x, y + cut)]


def chamfered(x, y, w, h, cut):
    """Two corners cut, not four. Asymmetric reads as a machined panel
    where symmetric reads as a plaque."""
    cut = max(2.0, min(cut, min(w, h) * 0.4))
    return [ImVec2(x, y), ImVec2(x + w - cut, y), ImVec2(x + w, y + cut),
            ImVec2(x + w, y + h), ImVec2(x + cut, y + h), ImVec2(x, y + h - cut)]


def pill(h):
    """The radius that makes a rect of this height a pill."""
    return h * 0.5


def spiral(dl, cx, cy, turns, outer, colour, thickness=1.0, phase=0.0,
           growth=None, steps=200):
    """A logarithmic spiral, drawn inward from `outer`.

    `growth` defaults to the golden ratio. It widens by that every quarter
    turn, which is the catch: over three turns that is growth**12, so the
    only sane way to draw one to a given size is from the outside in.
    `phase` rotates it and must not touch the radius, or it pulses.
    """
    g = growth if growth is not None else (1.0 + 5.0 ** 0.5) / 2.0
    col = theme_mod.u32(colour) if not isinstance(colour, int) else colour
    pts = []
    for i in range(steps):
        a = i / (steps - 1) * turns * math.tau
        r = outer * (g ** (-a / (math.pi * 0.5)))
        if r < 0.4:
            break
        pts.append(ImVec2(cx + math.cos(a + phase) * r,
                          cy + math.sin(a + phase) * r))
    if len(pts) > 1:
        dl.add_polyline(pts, col, thickness, 0)
