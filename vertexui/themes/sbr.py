"""Steel Ball Run - Araki western, golden ratio, parchment and brass.

A print-first identity: the ground is desert parchment, cards are pages
held in engraved brass frames with notched corners, shadows are
cross-hatched ink rather than blur, and the accent is Araki's magenta with
turquoise as its foil. Type is serif throughout, because the interface is
meant to read as printed matter and not as software.

    from vertexui import themes
    app = compose.App(profile=themes.SBR)

The spinner is Gyro's steel ball: a lit metal sphere with etched grooves
turning on its axis, green accents at the poles, a magenta and turquoise
aura, and a logarithmic spiral of particles behind it.

PHI is load-bearing rather than decorative - the card header height, the
notch size, the frame inset, the spiral and the aura radii are all steps
of it, which is what keeps the proportions of the thing consistent when
any one number changes.
"""

import math

from imgui_bundle import ImVec2, imgui

from .. import layouts, profiles, skins
from .. import theme as theme_mod
from ..theme import Theme, rgb

PHI = (1.0 + 5.0 ** 0.5) / 2.0          # 1.618...
INV = 1.0 / PHI                         # 0.618...

# --- palette -----------------------------------------------------------
# Parchment-dominant, so the page is the subject and ink is the contrast.
# Araki magenta carries meaning; turquoise answers it; brass is structure.
PARCHMENT = Theme(
    name="steel-ball-run",
    bg=rgb("#e2d5b6"), panel=rgb("#ece1c7"), surface=rgb("#f4ecd9"),
    surface_hover=rgb("#e8dbbd"), border=rgb("#9c7b4a"),
    accent=rgb("#c2185b"), accent_bright=rgb("#e8428c"),
    accent_dim=rgb("#e6c3d4"),
    text=rgb("#2b1e13"), text_dim=rgb("#6a5436"), text_mute=rgb("#9a8460"),
    ok=rgb("#1f7a5e"), warn=rgb("#b07d12"), danger=rgb("#a3202b"),
    info=rgb("#17888c"),
    rounding=0.0, rounding_panel=0.0, border_width=1.0,
)

BRASS = rgb("#b08d4f")
BRASS_LIT = rgb("#e0c389")
TURQUOISE = rgb("#17888c")
STEEL_DARK = rgb("#35353d")
STEEL_LIT = rgb("#eceef4")
INK = rgb("#2b1e13")


# --- geometry ----------------------------------------------------------

def _notched(x, y, w, h, cut):
    """An octagon - a rectangle with its corners cut off.

    Notched rather than rounded: a cut corner reads as something stamped
    or machined, where a radius reads as something moulded, and this
    theme is brass plate and printed paper.
    """
    cut = max(2.0, min(cut, min(w, h) * 0.3))
    return [ImVec2(x + cut, y), ImVec2(x + w - cut, y),
            ImVec2(x + w, y + cut), ImVec2(x + w, y + h - cut),
            ImVec2(x + w - cut, y + h), ImVec2(x + cut, y + h),
            ImVec2(x, y + h - cut), ImVec2(x, y + cut)]


def _hatch(dl, x, y, w, h, col, step=5.0, thickness=1.0):
    """Diagonal ink hatching, clipped to a box. What this theme uses
    instead of a soft shadow - a blur is a photograph of a shadow, and
    this interface is drawn."""
    dl.push_clip_rect(ImVec2(x, y), ImVec2(x + w, y + h), True)
    k = -h
    while k < w:
        dl.add_line(ImVec2(x + k, y + h), ImVec2(x + k + h, y), col, thickness)
        k += step
    dl.pop_clip_rect()


def _spiral(dl, cx, cy, turns, outer, col, thickness=1.0, phase=0.0, steps=200):
    """A golden spiral, drawn inward from `outer`.

    It widens by phi every quarter turn, which is the definition and also
    the catch: over three turns that is phi**12, so the only sane way to
    draw one to a given size is to start at the outside and let it shrink
    toward the centre. `phase` rotates it; it must not touch the radius,
    or the motif pulses in and out instead of turning.
    """
    pts = []
    for i in range(steps):
        a = i / (steps - 1) * turns * math.tau
        r = outer * (PHI ** (-a / (math.pi * 0.5)))
        if r < 0.4:
            break
        pts.append(ImVec2(cx + math.cos(a + phase) * r,
                          cy + math.sin(a + phase) * r))
    if len(pts) > 1:
        dl.add_polyline(pts, col, thickness, 0)


# --- painters ----------------------------------------------------------

def plate(dl, x, y, w, h, t, edge, style, shadow):
    """A page in a brass frame."""
    if style == "flat":
        return False                      # leave the plainest style alone
    cut = max(4.0, min(w, h) * 0.04 * PHI)

    if shadow and style in ("raised", "plated"):
        # Cross-hatched ink, offset down and right like a printed block.
        off = 5.0
        poly = _notched(x + off, y + off, w, h, cut)
        dl.add_convex_poly_filled(poly, theme_mod.u32(INK, 0.16))
        _hatch(dl, x + off, y + h - 2, w, off + 2,
               theme_mod.u32(INK, 0.22), 4.0, 1.0)

    body = _notched(x, y, w, h, cut)
    if style != "outlined":
        dl.add_convex_poly_filled(body, theme_mod.u32(t.surface))
        # parchment is not flat: a faint warm wash toward the bottom
        i0 = dl.vtx_buffer.size()
        dl.add_convex_poly_filled(body, theme_mod.u32(t.surface))
        i1 = dl.vtx_buffer.size()
        if i1 > i0:
            imgui.internal.shade_verts_linear_color_gradient_keep_alpha(
                dl, i0, i1, ImVec2(x, y), ImVec2(x, y + h),
                theme_mod.u32(theme_mod.lerp(t.surface, BRASS_LIT, 0.10)),
                theme_mod.u32(theme_mod.lerp(t.surface, BRASS, 0.16)))

    # Double line: a heavier brass frame with a hairline inside it, which
    # is the engraving convention this is borrowed from.
    dl.add_polyline(body + [body[0]], theme_mod.u32(BRASS, 0.95), 1.8, 0)
    inner = _notched(x + 3, y + 3, w - 6, h - 6, cut * INV)
    dl.add_polyline(inner + [inner[0]],
                    theme_mod.u32(theme_mod.lerp(BRASS, INK, 0.35), 0.45), 1.0, 0)

    if edge is not None and style in ("raised", "plated"):
        # a stamped brass tab across the top, cut to match the corners
        tab_h = max(3.0, h * 0.012 * PHI * 2)
        dl.add_convex_poly_filled(
            _notched(x + cut, y, w - cut * 2, tab_h, tab_h * INV),
            theme_mod.u32(edge, 0.92))
    return True


def frame(dl, x, y, w, h, t, kind):
    """Buttons as engraved brass plates."""
    if not kind.startswith("button"):
        return False
    cut = max(3.0, min(w, h) * 0.055 * PHI)
    body = _notched(x, y, w, h, cut)
    primary = kind.endswith("primary")
    top = theme_mod.lerp(t.accent, BRASS_LIT, 0.20) if primary else BRASS_LIT
    bot = theme_mod.lerp(t.accent, INK, 0.30) if primary else \
        theme_mod.lerp(BRASS, INK, 0.25)
    i0 = dl.vtx_buffer.size()
    dl.add_convex_poly_filled(body, theme_mod.u32(top))
    i1 = dl.vtx_buffer.size()
    if i1 > i0:
        imgui.internal.shade_verts_linear_color_gradient_keep_alpha(
            dl, i0, i1, ImVec2(x, y), ImVec2(x, y + h),
            theme_mod.u32(top), theme_mod.u32(bot))
    dl.add_polyline(body + [body[0]], theme_mod.u32(INK, 0.55), 1.4, 0)
    # the lit bevel along the top edge that makes it read as metal
    dl.add_line(ImVec2(x + cut, y + 1.5), ImVec2(x + w - cut, y + 1.5),
                theme_mod.u32(BRASS_LIT, 0.75), 1.4)
    return True


def hover_aura(dl, x0, y0, x1, y1, t, amount, kind):
    """Neon magenta, answered by turquoise. Drawn outward from the
    control so it reads as emission rather than as a border."""
    cut = max(3.0, min(x1 - x0, y1 - y0) * 0.055 * PHI)
    for i, (col, a) in enumerate(((t.accent_bright, 0.30),
                                  (TURQUOISE, 0.16), (t.accent_bright, 0.08))):
        g = (i + 1) * 2.4
        poly = _notched(x0 - g, y0 - g, (x1 - x0) + g * 2, (y1 - y0) + g * 2,
                        cut + g * INV)
        dl.add_polyline(poly + [poly[0]], theme_mod.u32(col, a * amount),
                        2.2 - i * 0.5, 0)


def spinner(dl, cx, cy, r, t, phase):
    """Gyro's steel ball.

    Steel, not brass - the frames of this theme are brass and the ball has
    to read as a different material or it disappears into them.

    It turns about a vertical axis, so the etched grooves are meridians:
    each one is an ellipse whose half-width is the cosine of how far round
    it has turned, which is what sells the rotation with no 3D at all. The
    poles stay put, which is where the green accents live.
    """
    spin = phase * 2.2
    pulse = 0.5 + 0.5 * math.sin(phase * 2.0 * INV)

    # aura: magenta answered by turquoise, breathing on the golden ratio
    dl.add_circle_filled(ImVec2(cx, cy), r * 1.62,
                         theme_mod.u32(t.accent_bright, 0.06 + 0.05 * pulse))
    dl.add_circle_filled(ImVec2(cx, cy), r * 1.26,
                         theme_mod.u32(TURQUOISE, 0.07 + 0.05 * (1 - pulse)))

    # a logarithmic trail of particles falling behind the spin
    for i in range(8):
        a = -spin * 0.5 - i * 0.40
        rad = r * (1.14 + i * 0.13)
        fade = (1.0 - i / 8.0) * 0.5
        dl.add_circle_filled(
            ImVec2(cx + math.cos(a) * rad, cy + math.sin(a) * rad * 0.55),
            max(0.7, r * 0.085 * (1.0 - i / 10.0)),
            theme_mod.u32(t.accent_bright if i % 2 else TURQUOISE, fade))

    # the sphere: many small steps, offset toward the light, so the ramp
    # reads as curvature rather than as a stack of rings
    steps = 16
    for i in range(steps, 0, -1):
        k = i / steps
        off = r * 0.30 * (1.0 - k)
        shade = theme_mod.lerp(STEEL_DARK, STEEL_LIT, (1.0 - k) ** 1.45)
        dl.add_circle_filled(ImVec2(cx - off * 0.72, cy - off * 0.72),
                             r * k, theme_mod.u32(shade))

    # etched grooves as meridians, squashed by their own rotation
    for g in range(5):
        half = math.cos(spin + g * (math.pi / 5.0))
        ww = abs(half) * r * 0.94
        if ww < 0.8:
            continue
        pts = []
        for sdx in range(21):
            a = -math.pi * 0.5 + sdx / 20.0 * math.pi
            pts.append(ImVec2(cx + math.cos(a) * ww * (1 if half > 0 else -1),
                              cy + math.sin(a) * r * 0.94))
        dl.add_polyline(pts, theme_mod.u32(STEEL_DARK,
                                           0.22 + 0.3 * abs(half)), 1.3, 0)
        dl.add_polyline([ImVec2(p.x + 1.0, p.y) for p in pts],
                        theme_mod.u32(STEEL_LIT, 0.14 * abs(half)), 1.0, 0)

    # equator, specular, rim light
    eq = []
    for sdx in range(25):
        a = sdx / 24.0 * math.tau
        eq.append(ImVec2(cx + math.cos(a) * r * 0.94,
                         cy + math.sin(a) * r * 0.20))
    dl.add_polyline(eq, theme_mod.u32(STEEL_DARK, 0.3), 1.2, 0)
    dl.add_circle_filled(ImVec2(cx - r * 0.33, cy - r * 0.37), r * 0.17,
                         theme_mod.u32(STEEL_LIT, 0.9))
    dl.path_arc_to(ImVec2(cx, cy), r * 0.93, math.radians(165),
                   math.radians(290), 24)
    dl.path_stroke(theme_mod.u32(STEEL_LIT, 0.45), 1.6, 0)

    # the green accents on the poles
    for sign in (-1, 1):
        py = cy + sign * r * 0.80
        dl.add_circle_filled(ImVec2(cx, py), r * 0.165,
                             theme_mod.u32(rgb("#2fbf6a"), 0.95))
        dl.add_circle_filled(ImVec2(cx, py), r * 0.165 * 0.45,
                             theme_mod.u32(rgb("#9affc4"), 0.9))
    dl.add_circle(ImVec2(cx, cy), r, theme_mod.u32(INK, 0.5), 40, 1.3)
    return True


def background(dl, x, y, w, h, t, now):
    """Parchment, a golden spiral, and ink hatching in the corners."""
    dl.add_rect_filled(ImVec2(x, y), ImVec2(x + w, y + h),
                       theme_mod.u32(t.bg))
    # The golden rectangle the spiral is derived from, subdivided - this
    # is the part that actually reads as "golden ratio" at a glance,
    # where the spiral alone reads as a stray arc.
    gx, gy = x + w * 0.07, y + h * 0.10
    gw, gh = w * 0.86, h * 0.80
    faint = theme_mod.u32(BRASS, 0.10)
    for _ in range(7):
        if gw < 18.0 or gh < 18.0:
            break
        if gw >= gh:
            cutw = gh
            dl.add_line(ImVec2(gx + cutw, gy), ImVec2(gx + cutw, gy + gh),
                        faint, 1.0)
            gx, gw = gx + cutw, gw - cutw
        else:
            cuth = gw
            dl.add_line(ImVec2(gx, gy + cuth), ImVec2(gx + gw, gy + cuth),
                        faint, 1.0)
            gy, gh = gy + cuth, gh - cuth

    # the spiral itself, small enough that several turns are on screen
    cx, cy = x + w * INV, y + h * (1.0 - INV)
    outer = min(w, h) * 0.40
    _spiral(dl, cx, cy, 3.0, outer, theme_mod.u32(BRASS, 0.26), 1.6,
            phase=now * 0.045)
    _spiral(dl, cx, cy, 3.0, outer, theme_mod.u32(t.accent, 0.10), 3.2,
            phase=now * 0.045 + 0.10)
    # hatching in two corners, like the margin of a printed page
    _hatch(dl, x, y, w * 0.10, h * 0.22, theme_mod.u32(INK, 0.05), 7.0)
    _hatch(dl, x + w * 0.88, y + h * 0.7, w * 0.12, h * 0.3,
           theme_mod.u32(INK, 0.05), 7.0)
    # speed lines along the bottom edge, the manga energy the brief asks
    # for, kept to an intensity you only notice when you look for it
    for i in range(26):
        k = i / 25.0
        lx = x + w * k
        ln = h * 0.035 * (0.3 + 0.7 * abs(math.sin(k * 9.0 + now * 0.25)))
        dl.add_line(ImVec2(lx, y + h), ImVec2(lx + ln * 0.4, y + h - ln),
                    theme_mod.u32(INK, 0.07), 1.0)
    return True


SKIN = skins.Skin(
    name="steel-ball-run",
    plate=plate, frame=frame, hover_aura=hover_aura, spinner=spinner,
    background=background,
    press_depth=2.4,            # a firm, engraved stamp
    extras={"phi": PHI, "brass": BRASS, "turquoise": TURQUOISE},
)

SBR = profiles.Profile(
    name="steel-ball-run", theme=PARCHMENT, layout=layouts.TABBED,
    face_ui="Georgia", face_display="Palatino", face_mono="Consolas",
    base_size=17.0, density=1.0 * PHI * 0.66,   # ~1.07, a golden-ratio step
    card_style="raised", card_shadow=True,
    motion=1.0 * INV + 0.45,                     # ~1.07 - deliberate, not eager
    sound_set="soft taps", volume=0.14,
    skin=SKIN,
    blurb="Araki western - parchment, brass, notched corners, golden ratio",
)
