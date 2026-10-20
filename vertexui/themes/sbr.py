"""Steel Ball Run - Araki western, golden ratio, parchment and ink.

A printed-page identity. The ground is desert parchment, cards are panels
held in engraved brass frames with notched corners and ornate bracket
flourishes, shading is halftone screentone and cross-hatched ink rather
than blur, and the accent is Araki magenta with turquoise as its foil.
Type is serif throughout, because this is meant to read as printed matter
and not as software.

    from vertexui import themes
    app = compose.App(profile=themes.SBR)

The manga vocabulary is load-bearing, not decoration: halftone where a
flat theme would use a tint, focus lines and rising menacing marks where
a flat theme would use a glow, variable-weight ink where a flat theme
would use one border. That is the difference between a western palette
and the thing the palette came from.

The spinner is Gyro's steel ball, and Gyro's are green - a green metal
that desaturates toward white at the highlight, which is what stops it
reading as painted plastic.

PHI is load-bearing too: the notch size, the nameplate height, the frame
inset, the flourish length, the aura radii and the background spiral are
all steps of it, so the proportions stay consistent when any one number
moves.
"""

import math

from imgui_bundle import ImVec2, imgui

from .. import layouts, paint, profiles, skins
from .. import theme as theme_mod
from ..theme import Theme, rgb

PHI = (1.0 + 5.0 ** 0.5) / 2.0          # 1.618...
INV = 1.0 / PHI                         # 0.618...

# --- palette -----------------------------------------------------------
PARCHMENT = Theme(
    name="steel-ball-run",
    bg=rgb("#e0d2b0"), panel=rgb("#ebdfc3"), surface=rgb("#f5edda"),
    surface_hover=rgb("#e9dcbd"), border=rgb("#8e6f3e"),
    accent=rgb("#cf1163"), accent_bright=rgb("#ff3d96"),
    accent_dim=rgb("#e8bed2"),
    text=rgb("#251a0f"), text_dim=rgb("#634d2e"), text_mute=rgb("#967f57"),
    ok=rgb("#1b7a55"), warn=rgb("#b5820d"), danger=rgb("#9d1b24"),
    info=rgb("#11858c"),
    rounding=0.0, rounding_panel=0.0, border_width=1.0,
)

BRASS = rgb("#b08d4f")
BRASS_LIT = rgb("#eed6a3")
BRASS_DARK = rgb("#6d5324")
TURQUOISE = rgb("#11858c")
INK = rgb("#1d1409")

# Gyro's. Green metal: saturated in the shadow, desaturating toward white
# at the highlight, which is what separates metal from painted plastic.
GREEN_DARK = rgb("#0e2b1b")
GREEN_MID = rgb("#2e9160")
GREEN_LIT = rgb("#d8f2e2")


# --- geometry ----------------------------------------------------------

def _notched(x, y, w, h, cut):
    """From the shared helpers - an octagon reads as stamped metal."""
    return paint.notched(x, y, w, h, cut)


def _hatch(dl, x, y, w, h, col, step=5.0, thickness=1.0):
    paint.hatch(dl, x, y, w, h, col, step, thickness)


def _halftone(dl, x, y, w, h, col, step=6.0, fade=True):
    paint.halftone(dl, x, y, w, h, col, step, fade)


def _menacing(dl, x, y, s, col, thickness=None):
    """A menacing mark - the GO of Araki's goGOgo.

    Drawn from strokes rather than typed: the glyph needs a Japanese
    range in the font atlas, which is a megabyte of texture for one
    decorative character, and at this size three lines read exactly the
    same.
    """
    t = thickness if thickness is not None else max(1.2, s * 0.14)
    # the katakana KO: top bar turning down the right side, then a base
    dl.add_polyline([ImVec2(x, y), ImVec2(x + s, y),
                     ImVec2(x + s * 0.88, y + s * 0.84)], col, t, 0)
    dl.add_line(ImVec2(x + s * 0.06, y + s * 0.84),
                ImVec2(x + s * 0.88, y + s * 0.84), col, t)
    # the dakuten that turns KO into GO
    for i in (0, 1):
        dx = x + s * (1.14 + i * 0.20)
        dy = y + s * (0.02 + i * 0.08)
        dl.add_line(ImVec2(dx, dy), ImVec2(dx - s * 0.10, dy + s * 0.26),
                    col, t * 0.85)


def _focus_lines(dl, cx, cy, r0, r1, col, n=18, thickness=1.4, phase=0.0):
    """Radiating impact lines - the manga answer to a glow."""
    for i in range(n):
        a = phase + i / n * math.tau
        jitter = 0.78 + 0.22 * math.sin(i * 2.7 + phase * 3.0)
        dl.add_line(ImVec2(cx + math.cos(a) * r0, cy + math.sin(a) * r0),
                    ImVec2(cx + math.cos(a) * r1 * jitter,
                           cy + math.sin(a) * r1 * jitter), col, thickness)


def _flourish(dl, x, y, s, col, sx=1, sy=1, thickness=1.6):
    """An ornate bracket for a card's corner.

    `sx`/`sy` are -1 to mirror it onto the other corners, so one routine
    draws all four and they stay symmetrical when the size changes.
    """
    dl.add_line(ImVec2(x, y), ImVec2(x + s * sx, y), col, thickness)
    dl.add_line(ImVec2(x, y), ImVec2(x, y + s * sy), col, thickness)
    # the spur that turns a corner into an ornament
    dl.add_line(ImVec2(x + s * 0.62 * sx, y),
                ImVec2(x + s * 0.62 * sx, y + s * 0.30 * sy), col, thickness * 0.8)
    dl.add_line(ImVec2(x, y + s * 0.62 * sy),
                ImVec2(x + s * 0.30 * sx, y + s * 0.62 * sy), col, thickness * 0.8)
    dl.add_circle_filled(ImVec2(x + s * 0.62 * sx, y + s * 0.62 * sy),
                         thickness * 0.95, col)


def _spiral(dl, cx, cy, turns, outer, col, thickness=1.0, phase=0.0):
    """The golden spiral, from the shared helper - PHI is its default."""
    paint.spiral(dl, cx, cy, turns, outer, col, thickness, phase, growth=PHI)


# --- painters ----------------------------------------------------------

def plate(dl, x, y, w, h, t, edge, style, shadow):
    """A panel on the page: ink, brass, screentone and corner ornament."""
    if style == "flat":
        return False
    cut = max(5.0, min(w, h) * 0.04 * PHI)

    if shadow and style in ("raised", "plated"):
        # Cross-hatched ink, offset down and right like a printed block.
        off = 5.0
        poly = _notched(x + off, y + off, w, h, cut)
        dl.add_convex_poly_filled(poly, theme_mod.u32(INK, 0.18))
        _hatch(dl, x + off, y + h - 2, w, off + 3,
               theme_mod.u32(INK, 0.26), 4.0, 1.0)

    body = _notched(x, y, w, h, cut)
    if style != "outlined":
        dl.add_convex_poly_filled(body, theme_mod.u32(t.surface))
        i0 = dl.vtx_buffer.size()
        dl.add_convex_poly_filled(body, theme_mod.u32(t.surface))
        i1 = dl.vtx_buffer.size()
        if i1 > i0:
            imgui.internal.shade_verts_linear_color_gradient_keep_alpha(
                dl, i0, i1, ImVec2(x, y), ImVec2(x, y + h),
                theme_mod.u32(theme_mod.lerp(t.surface, BRASS_LIT, 0.12)),
                theme_mod.u32(theme_mod.lerp(t.surface, BRASS, 0.18)))
        # screentone, heavier toward the foot of the panel
        _halftone(dl, x + 2, y + h * 0.42, w - 4, h * 0.58 - 2,
                  theme_mod.u32(INK, 0.09), 6.0)

    # Ink first, brass inside it: a heavy outline with a lighter companion
    # is how a panel border is actually inked, and one even line is the
    # thing that made this look flat.
    dl.add_polyline(body + [body[0]], theme_mod.u32(INK, 0.88), 2.4, 0)
    dl.add_polyline(body + [body[0]], theme_mod.u32(BRASS, 0.95), 1.3, 0)
    inner = _notched(x + 4, y + 4, w - 8, h - 8, cut * INV)
    dl.add_polyline(inner + [inner[0]], theme_mod.u32(BRASS_DARK, 0.50), 1.0, 0)

    # ornate brackets, one routine mirrored into all four corners
    # Sized to fit the margin the nameplate leaves clear on each side; a
    # bigger bracket runs under the plate and reads as a mistake.
    fs = max(9.0, min(16.0, min(w, h) * 0.075))
    pad = 6.0
    for sx, sy, px, py in ((1, 1, x + pad, y + pad),
                           (-1, 1, x + w - pad, y + pad),
                           (1, -1, x + pad, y + h - pad),
                           (-1, -1, x + w - pad, y + h - pad)):
        _flourish(dl, px, py, fs, theme_mod.u32(BRASS_DARK, 0.75), sx, sy, 1.5)

    if edge is not None and style in ("raised", "plated"):
        tab_h = max(3.5, h * 0.012 * PHI * 2)
        dl.add_convex_poly_filled(
            _notched(x + cut, y, w - cut * 2, tab_h, tab_h * INV),
            theme_mod.u32(edge, 0.95))
        _hatch(dl, x + cut, y, w - cut * 2, tab_h,
               theme_mod.u32(INK, 0.22), 5.0, 1.0)
    return True


def head(dl, x, y, w, t, icon, title, right, right_col, dot):
    """An engraved brass nameplate rather than a label and a rule."""
    from .. import fonts, icons
    from ..widgets import caps, caps_width

    bar_h = 26.0 * INV * PHI            # 26 - kept as a phi expression
    bx, by, bw = x + 24.0, y + 5.0, w - 48.0
    plate_poly = _notched(bx, by, bw, bar_h, bar_h * 0.34)
    i0 = dl.vtx_buffer.size()
    dl.add_convex_poly_filled(plate_poly, theme_mod.u32(BRASS_LIT))
    i1 = dl.vtx_buffer.size()
    if i1 > i0:
        imgui.internal.shade_verts_linear_color_gradient_keep_alpha(
            dl, i0, i1, ImVec2(bx, by), ImVec2(bx, by + bar_h),
            theme_mod.u32(BRASS_LIT), theme_mod.u32(BRASS))
    dl.add_polyline(plate_poly + [plate_poly[0]], theme_mod.u32(INK, 0.75),
                    1.4, 0)
    # the lit top edge of a struck plate
    dl.add_line(ImVec2(bx + bar_h * 0.34, by + 1.2),
                ImVec2(bx + bw - bar_h * 0.34, by + 1.2),
                theme_mod.u32(rgb("#fff3d6"), 0.75), 1.2)

    tx = bx + 11.0
    if icon:
        icons.draw(icon, dl, tx + 2, by + bar_h * 0.5, 6.5,
                   theme_mod.u32(INK, 0.8))
        tx += 18.0
    with fonts.use("label"):
        caps(dl, tx, by + (bar_h - 11) * 0.5, (title or "").upper(),
             theme_mod.u32(INK, 0.9), 2.0)
        if right:
            rw = caps_width(right.upper(), 1.6)
            rx = bx + bw - 12.0 - rw
            if dot is not None:
                dl.add_circle_filled(ImVec2(rx - 10, by + bar_h * 0.5), 3.2,
                                     theme_mod.u32(dot))
            caps(dl, rx, by + (bar_h - 11) * 0.5, right.upper(),
                 theme_mod.u32(right_col or BRASS_DARK, 0.95), 1.6)
    return y + bar_h + 12.0


def frame(dl, x, y, w, h, t, kind):
    """Buttons as struck brass plates; fields as inked wells."""
    if kind == "input":
        poly = _notched(x, y, w, h, 5.0)
        dl.add_convex_poly_filled(
            poly, theme_mod.u32(theme_mod.lerp(t.surface, BRASS_LIT, 0.35)))
        _halftone(dl, x + 2, y + 2, w - 4, h - 4, theme_mod.u32(INK, 0.07),
                  5.0, fade=False)
        dl.add_polyline(poly + [poly[0]], theme_mod.u32(INK, 0.7), 1.6, 0)
        return True
    if not kind.startswith("button"):
        return False
    cut = max(3.0, min(w, h) * 0.055 * PHI)
    body = _notched(x, y, w, h, cut)
    primary = kind.endswith("primary")
    top = theme_mod.lerp(t.accent, BRASS_LIT, 0.22) if primary else BRASS_LIT
    bot = theme_mod.lerp(t.accent, INK, 0.32) if primary else \
        theme_mod.lerp(BRASS, INK, 0.28)
    i0 = dl.vtx_buffer.size()
    dl.add_convex_poly_filled(body, theme_mod.u32(top))
    i1 = dl.vtx_buffer.size()
    if i1 > i0:
        imgui.internal.shade_verts_linear_color_gradient_keep_alpha(
            dl, i0, i1, ImVec2(x, y), ImVec2(x, y + h),
            theme_mod.u32(top), theme_mod.u32(bot))
    dl.add_polyline(body + [body[0]], theme_mod.u32(INK, 0.8), 1.7, 0)
    dl.add_line(ImVec2(x + cut, y + 1.6), ImVec2(x + w - cut, y + 1.6),
                theme_mod.u32(rgb("#fff3d6"), 0.7), 1.3)
    return True


def hover_aura(dl, x0, y0, x1, y1, t, amount, kind):
    """Focus lines and rising menacing marks, not a soft glow.

    A glow is a lighting effect and this interface has no lights in it.
    The page's own way of saying "look here" is to point every line at the
    thing and let the air around it go ominous.
    """
    import time as _time
    now = _time.time()
    cx, cy = (x0 + x1) * 0.5, (y0 + y1) * 0.5
    half = max(x1 - x0, y1 - y0) * 0.5

    _focus_lines(dl, cx, cy, half * 1.10, half * (1.10 + 0.34 * amount),
                 theme_mod.u32(t.accent, 0.42 * amount), 20, 1.5,
                 phase=now * 0.55)
    cut = max(3.0, min(x1 - x0, y1 - y0) * 0.055 * PHI)
    for i, (col, a) in enumerate(((t.accent_bright, 0.55), (TURQUOISE, 0.26))):
        g = (i + 1) * 2.6
        poly = _notched(x0 - g, y0 - g, (x1 - x0) + g * 2, (y1 - y0) + g * 2,
                        cut + g * INV)
        dl.add_polyline(poly + [poly[0]], theme_mod.u32(col, a * amount),
                        2.0 - i * 0.6, 0)
    # three marks drifting up out of the control, each on its own clock
    for i in range(3):
        k = ((now * 0.55 + i * 0.33) % 1.0)
        s = 8.0 + 3.0 * i
        mx = x1 - 14.0 - i * 15.0
        my = y0 - 4.0 - k * 26.0
        fade = amount * (1.0 - k) * 0.85
        if fade > 0.02:
            _menacing(dl, mx, my, s, theme_mod.u32(INK, fade))


def spinner(dl, cx, cy, r, t, phase, spin=1.0):
    """Gyro's steel ball. Green, because Gyro's are.

    It turns about a vertical axis, so the etched grooves are meridians:
    each one is an ellipse whose half-width is the cosine of how far round
    it has turned, which sells the rotation with no 3D at all. The poles
    stay put, which is where the brass caps live.
    """
    # `spin` is the rate; `heat` is how far past resting it is. Nothing
    # below reads the clock directly - the phase already carries the rate,
    # so the whole thing winds up and down together.
    heat = max(0.0, min(1.0, (spin - 1.0) / 4.0))
    turn = phase * 2.2
    pulse = 0.5 + 0.5 * math.sin(phase * 2.0 * INV)

    # the page reacting to it: focus lines, not a bloom
    # kept inside widgets.SPINNER_BLEED so the lines never reach a
    # neighbour - they are decoration, not layout
    _focus_lines(dl, cx, cy, r * (1.14 - 0.10 * heat),
                 r * (1.34 + 0.10 * pulse),
                 theme_mod.u32(t.accent, 0.30 + 0.45 * heat),
                 22 + int(16 * heat), 1.4 + 1.0 * heat, phase=-turn * 0.35)
    if heat > 0.02:
        # afterimages: the ball smeared round its own axis, which is what
        # a drawn frame does instead of a motion blur
        for i in range(1, 4):
            a = -turn * 0.12 * i
            gx = cx + math.cos(a) * r * 0.10 * heat * i
            gy = cy + math.sin(a) * r * 0.10 * heat * i
            dl.add_circle_filled(ImVec2(gx, gy), r * (1.0 - 0.04 * i),
                                 theme_mod.u32(GREEN_MID, 0.12 * heat))
        # and the marks, because this is what they are for
        for i in range(3):
            k = ((phase * 0.5 + i * 0.33) % 1.0)
            _menacing(dl, cx + r * (0.95 - i * 0.3), cy - r * (0.9 + k * 0.5),
                      r * (0.26 + 0.06 * i),
                      theme_mod.u32(INK, heat * (1.0 - k) * 0.7))
    dl.add_circle_filled(ImVec2(cx, cy), r * 1.22,
                         theme_mod.u32(TURQUOISE, 0.08 + 0.05 * (1 - pulse)))

    # a logarithmic trail of particles falling behind the spin
    for i in range(8):
        a = -turn * 0.5 - i * 0.40
        rad = r * (1.02 + i * 0.055)       # <= 1.41r
        fade = (1.0 - i / 8.0) * (0.5 + 0.45 * heat)
        dl.add_circle_filled(
            ImVec2(cx + math.cos(a) * rad, cy + math.sin(a) * rad * 0.55),
            max(0.7, r * 0.085 * (1.0 - i / 10.0)),
            theme_mod.u32(t.accent_bright if i % 2 else TURQUOISE, fade))

    # the sphere: saturated green in shadow, desaturating toward white at
    # the highlight - a ramp straight to white reads as painted plastic
    steps = 22
    for i in range(steps, 0, -1):
        k = i / steps
        off = r * 0.46 * (1.0 - k)
        lit = (1.0 - k) ** 1.1
        shade = theme_mod.lerp(GREEN_DARK, GREEN_MID, min(1.0, lit * 2.1)) \
            if lit < 0.48 else theme_mod.lerp(GREEN_MID, GREEN_LIT,
                                              (lit - 0.48) / 0.52)
        dl.add_circle_filled(ImVec2(cx - off * 0.72, cy - off * 0.72),
                             r * k, theme_mod.u32(shade))
    # Bounce light along the shaded edge. Without it a sphere reads as a
    # flat disc with a dot on it, however good the ramp is - the dark side
    # of a polished thing is never the darkest part of the picture.
    dl.path_arc_to(ImVec2(cx, cy), r * 0.90, math.radians(15),
                   math.radians(115), 26)
    dl.path_stroke(theme_mod.u32(GREEN_LIT, 0.30), 2.0, 0)

    # etched grooves as meridians, squashed by their own rotation
    for g in range(5):
        half = math.cos(turn + g * (math.pi / 5.0))
        ww = abs(half) * r * 0.94
        if ww < 0.8:
            continue
        pts = []
        for sdx in range(21):
            a = -math.pi * 0.5 + sdx / 20.0 * math.pi
            pts.append(ImVec2(cx + math.cos(a) * ww * (1 if half > 0 else -1),
                              cy + math.sin(a) * r * 0.94))
        dl.add_polyline(pts, theme_mod.u32(GREEN_DARK,
                                           0.30 + 0.34 * abs(half)), 1.3, 0)
        dl.add_polyline([ImVec2(p.x + 1.0, p.y) for p in pts],
                        theme_mod.u32(GREEN_LIT, 0.16 * abs(half)), 1.0, 0)

    # equator, specular, rim light
    eq = []
    for sdx in range(25):
        a = sdx / 24.0 * math.tau
        eq.append(ImVec2(cx + math.cos(a) * r * 0.94,
                         cy + math.sin(a) * r * 0.20))
    dl.add_polyline(eq, theme_mod.u32(GREEN_DARK, 0.34), 1.2, 0)
    dl.add_circle_filled(ImVec2(cx - r * 0.33, cy - r * 0.37), r * 0.16,
                         theme_mod.u32(GREEN_LIT, 0.92))
    dl.path_arc_to(ImVec2(cx, cy), r * 0.93, math.radians(165),
                   math.radians(290), 24)
    dl.path_stroke(theme_mod.u32(GREEN_LIT, 0.40), 1.6, 0)

    # brass caps on the poles, which is what the grooves run between
    for sign in (-1, 1):
        py = cy + sign * r * 0.80
        dl.add_circle_filled(ImVec2(cx, py), r * 0.17, theme_mod.u32(BRASS_DARK))
        dl.add_circle_filled(ImVec2(cx, py), r * 0.11, theme_mod.u32(BRASS_LIT, 0.95))
    dl.add_circle(ImVec2(cx, cy), r, theme_mod.u32(INK, 0.55), 40, 1.4)
    return True


def background(dl, x, y, w, h, t, now):
    """Parchment, the golden rectangle, a spiral, ink and sound effects."""
    dl.add_rect_filled(ImVec2(x, y), ImVec2(x + w, y + h),
                       theme_mod.u32(t.bg))
    # a wash of screentone over the whole page, so nothing is flat paper
    _halftone(dl, x, y, w, h, theme_mod.u32(INK, 0.035), 11.0, fade=False)

    # The golden rectangle the spiral comes from, subdivided - this is the
    # part that reads as "golden ratio" at a glance, where the spiral
    # alone reads as a stray arc.
    gx, gy = x + w * 0.07, y + h * 0.10
    gw, gh = w * 0.86, h * 0.80
    faint = theme_mod.u32(BRASS_DARK, 0.13)
    for _ in range(7):
        if gw < 18.0 or gh < 18.0:
            break
        if gw >= gh:
            dl.add_line(ImVec2(gx + gh, gy), ImVec2(gx + gh, gy + gh), faint, 1.0)
            gx, gw = gx + gh, gw - gh
        else:
            dl.add_line(ImVec2(gx, gy + gw), ImVec2(gx + gw, gy + gw), faint, 1.0)
            gy, gh = gy + gw, gh - gw

    cx, cy = x + w * INV, y + h * (1.0 - INV)
    outer = min(w, h) * 0.40
    _spiral(dl, cx, cy, 3.0, outer, theme_mod.u32(BRASS_DARK, 0.26), 1.7,
            phase=now * 0.045)
    _spiral(dl, cx, cy, 3.0, outer, theme_mod.u32(t.accent, 0.11), 3.2,
            phase=now * 0.045 + 0.10)

    # hatching in the margins, like the edge of a printed page
    _hatch(dl, x, y, w * 0.09, h * 0.26, theme_mod.u32(INK, 0.055), 7.0)
    _hatch(dl, x + w * 0.90, y + h * 0.66, w * 0.10, h * 0.34,
           theme_mod.u32(INK, 0.055), 7.0)

    # menacing marks climbing the right-hand margin, and a second pair
    # drifting up the left - the sound effect overlay the brief asks for
    for i in range(5):
        k = ((now * 0.07 + i * 0.21) % 1.0)
        s = 13.0 + i * 5.0
        _menacing(dl, x + w * 0.945 - i * 5.0, y + h * (0.92 - k * 0.78), s,
                  theme_mod.u32(INK, 0.09 * (1.0 - abs(k - 0.5) * 1.1)))
    for i in range(3):
        k = ((now * 0.05 + i * 0.3) % 1.0)
        s = 10.0 + i * 4.0
        _menacing(dl, x + w * 0.035, y + h * (0.88 - k * 0.7), s,
                  theme_mod.u32(INK, 0.07 * (1.0 - abs(k - 0.5) * 1.1)))

    # speed lines along the foot of the page
    for i in range(30):
        k = i / 29.0
        lx = x + w * k
        ln = h * 0.04 * (0.3 + 0.7 * abs(math.sin(k * 9.0 + now * 0.25)))
        dl.add_line(ImVec2(lx, y + h), ImVec2(lx + ln * 0.4, y + h - ln),
                    theme_mod.u32(INK, 0.08), 1.0)
    return True


def tabs(dl, x, y, w, h, t, rects, index, hots):
    """Tabs as inked index cards, the selected one on top of the pile."""
    if not rects:
        return False
    dl.add_line(ImVec2(x - 8, y + h - 1), ImVec2(x + w + 8, y + h - 1),
                theme_mod.u32(INK, 0.55), 1.6)
    for i, (tx, tw) in enumerate(rects):
        on = i == index
        top = y + (2 if on else 6)
        body = paint.notched(tx, top, tw, h - (top - y) + 1, 7.0)
        if on:
            paint.grad_poly(dl, body, theme_mod.lerp(t.surface, BRASS_LIT, 0.3),
                            t.surface)
        else:
            lift = 0.10 + 0.22 * hots[i]
            paint.grad_poly(dl, body,
                            theme_mod.lerp(t.bg, BRASS_LIT, lift),
                            theme_mod.lerp(t.bg, BRASS, lift * 0.6))
        dl.add_polyline(body + [body[0]],
                        theme_mod.u32(INK, 0.8 if on else 0.4),
                        1.8 if on else 1.1, 0)
        if on:
            # the card in front hides the rule beneath it
            dl.add_line(ImVec2(tx + 2, y + h - 1), ImVec2(tx + tw - 2, y + h - 1),
                        theme_mod.u32(t.surface), 2.4)
            dl.add_rect_filled(ImVec2(tx + 7, top + 2),
                               ImVec2(tx + tw - 7, top + 4),
                               theme_mod.u32(t.accent, 0.95))
    return True


SKIN = skins.Skin(
    name="steel-ball-run",
    plate=plate, head=head, frame=frame, hover_aura=hover_aura, tabs=tabs,
    spinner=spinner, background=background,
    press_depth=2.4,            # a firm, engraved stamp
    extras={"phi": PHI, "brass": BRASS, "turquoise": TURQUOISE,
            "green": GREEN_MID},
)

SBR = profiles.Profile(
    name="steel-ball-run", theme=PARCHMENT, layout=layouts.TABBED,
    face_ui="Georgia", face_display="Palatino", face_mono="Consolas",
    base_size=17.0, density=1.0 * PHI * 0.66,   # ~1.07, a golden-ratio step
    card_style="raised", card_shadow=True,
    motion=1.0 * INV + 0.45,                     # ~1.07 - deliberate, not eager
    sound_set="soft taps", volume=0.14,
    skin=SKIN,
    blurb="Araki western - parchment, brass, ink, screentone, golden ratio",
)
