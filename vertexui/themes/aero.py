"""Frutiger Aero - glass, water and tech optimism, about 2007.

Sky blue over grass green, sunlit yellow, crisp translucent white, and a
deep slate blue for type. Generous radii, pill shapes, soft outer glows,
and a bright specular sweep across the top half of everything.

    from vertexui import themes
    app = compose.App(profile=themes.AERO)

A note on the glassmorphism, because it is the one thing here that cannot
be done the way it is usually described. A draw list cannot blur what is
behind it - there is no way to sample the framebuffer mid-frame. But the
blur in this aesthetic was always of a soft gradient, and a blurred soft
gradient is just a softer gradient. So the background painter lays down
sky, grass, sun and caustics with no hard edges anywhere, and the cards
are translucent white over it. The result is frosted glass by
construction rather than by post-processing, and it costs nothing.

The spinner is a water bubble: a translucent sphere with a rim light and
a bright caustic floor, breathing on its own clock, shedding micro
bubbles upward and sending ripple rings out from its base.
"""

import math

from imgui_bundle import ImVec2, imgui

from .. import layouts, paint, profiles, skins
from .. import theme as theme_mod
from ..theme import Theme, rgb

# --- palette -----------------------------------------------------------
SKY = rgb("#8fd4f2")
SKY_DEEP = rgb("#2f9fd4")
GRASS = rgb("#7ec850")
GRASS_DEEP = rgb("#3f9c3a")
SUN = rgb("#ffd84d")
GLASS = rgb("#ffffff")
SLATE = rgb("#153a52")

AERO = Theme(
    name="frutiger-aero",
    bg=rgb("#bfe6f7"), panel=rgb("#d9f0fb"), surface=rgb("#eaf7fe"),
    surface_hover=rgb("#f6fdff"), border=rgb("#9ed3ec"),
    accent=rgb("#1b9ae0"), accent_bright=rgb("#5fcaf5"),
    accent_dim=rgb("#c3e8f8"),
    text=SLATE, text_dim=rgb("#3f6c87"), text_mute=rgb("#7ba6bd"),
    ok=rgb("#46a83c"), warn=rgb("#e8a800"), danger=rgb("#e05542"),
    info=rgb("#1b9ae0"),
    rounding=15.0, rounding_panel=19.0, border_width=1.0,
)


# --- primitives --------------------------------------------------------

def _grad_rect(dl, x, y, w, h, top, bottom, rounding=0.0):
    paint.grad_rect(dl, x, y, w, h, top, bottom, rounding)


def _gloss(dl, x, y, w, h, rounding, strength=1.0, share=0.46):
    paint.gloss(dl, x, y, w, h, rounding, GLASS, strength, share)


def _halo(dl, x, y, w, h, rounding, col, amount, rings=5, spread=9.0):
    paint.halo(dl, x, y, w, h, rounding, col, amount, rings, spread)


def _caustics(dl, x, y, w, h, col, now, lines=26):
    """Water light: elongated arcs drifting and breathing.

    Not a texture and not noise - caustics are bright curved filaments
    with dark between them, and drawing a few dozen arcs gets that
    character far more cheaply than any procedural field would.
    """
    for i in range(lines):
        k = i / lines
        cx = x + w * ((k * 1.7 + math.sin(now * 0.11 + i) * 0.06) % 1.0)
        cy = y + h * (0.12 + 0.86 * ((k * 2.3 + now * 0.012) % 1.0))
        rad = w * (0.03 + 0.05 * abs(math.sin(i * 2.1)))
        a0 = math.sin(now * 0.23 + i * 1.3) * 1.4
        dl.path_arc_to(ImVec2(cx, cy), rad, a0, a0 + 1.5 + 0.5 * math.sin(i),
                       14)
        dl.path_stroke(col, 1.0 + 1.4 * abs(math.sin(i * 0.7 + now * 0.3)), 0)


# --- painters ----------------------------------------------------------

def plate(dl, x, y, w, h, t, edge, style, shadow):
    """A translucent glass plate floating over the scene."""
    if style == "flat":
        return False
    r = t.rounding_panel

    if shadow and style in ("raised", "plated"):
        # a soft drop shadow, blue rather than black - a shadow on a sunlit
        # surface takes the colour of the sky bouncing into it
        for i, a in ((9.0, 0.05), (5.0, 0.07), (2.0, 0.09)):
            dl.add_rect_filled(ImVec2(x + 1, y + i * 0.6),
                               ImVec2(x + w - 1, y + h + i * 0.5),
                               theme_mod.u32(SLATE, a), r + i)

    if style != "outlined":
        # the glass itself: whiter and more opaque at the top, thinning
        # toward the foot so what is behind shows through more
        _grad_rect(dl, x, y, w, h,
                   theme_mod.with_alpha(GLASS, 0.62),
                   theme_mod.with_alpha(GLASS, 0.30), r)
        _gloss(dl, x, y, w, h, r, 1.0, 0.44)

    # a soft white border gradient rather than a line of one colour
    dl.add_rect(ImVec2(x, y), ImVec2(x + w, y + h),
                theme_mod.u32(GLASS, 0.75), r, 1.6)
    dl.add_rect(ImVec2(x + 1.6, y + 1.6), ImVec2(x + w - 1.6, y + h - 1.6),
                theme_mod.u32(SKY_DEEP, 0.18), r - 1.6, 1.0)

    if edge is not None and style in ("raised", "plated"):
        # a glossy pill of colour along the top, not a flat strip
        ph = 5.0
        _grad_rect(dl, x + r * 0.8, y + 2.5, w - r * 1.6, ph,
                   theme_mod.lerp(edge, GLASS, 0.45), edge, ph * 0.5)
    return True


def frame(dl, x, y, w, h, t, kind):
    """Glass pills for buttons, sunken wells for fields, pebbles for
    badges."""
    if kind.startswith("badge"):
        # a polished sea pebble: tinted body, bright crown, dark base
        from ..theme import current
        tt = current()
        name = kind.split(":", 1)[1] if ":" in kind else "info"
        col = tt.status(name) if name in ("ok", "warn", "error", "info") \
            else tt.accent
        r = h * 0.5
        _grad_rect(dl, x, y, w, h, theme_mod.lerp(col, GLASS, 0.72),
                   theme_mod.lerp(col, GLASS, 0.30), r)
        dl.add_rect(ImVec2(x, y), ImVec2(x + w, y + h),
                    theme_mod.u32(GLASS, 0.8), r, 1.2)
        _grad_rect(dl, x + 3, y + 1.5, w - 6, h * 0.42,
                   theme_mod.with_alpha(GLASS, 0.75),
                   theme_mod.with_alpha(GLASS, 0.0), r * 0.7)
        return True

    if kind == "input":
        r = h * 0.5 if h < 46 else t.rounding
        _grad_rect(dl, x, y, w, h, theme_mod.with_alpha(GLASS, 0.30),
                   theme_mod.with_alpha(GLASS, 0.62), r)
        # inner shadow at the top, which is what makes a well look sunken
        dl.add_rect(ImVec2(x + 1, y + 1), ImVec2(x + w - 1, y + h * 0.7),
                    theme_mod.u32(SKY_DEEP, 0.16), r, 2.0)
        dl.add_rect(ImVec2(x, y), ImVec2(x + w, y + h),
                    theme_mod.u32(GLASS, 0.7), r, 1.4)
        return True

    if not kind.startswith("button"):
        return False
    primary = kind.endswith("primary")
    r = h * 0.5                       # a pill, always
    base = t.accent if primary else GLASS
    _grad_rect(dl, x, y, w, h,
               theme_mod.lerp(base, GLASS, 0.40 if primary else 0.62),
               theme_mod.lerp(base, SKY_DEEP, 0.30) if primary
               else theme_mod.with_alpha(GLASS, 0.42), r)
    _gloss(dl, x, y, w, h, r, 1.0, 0.50)
    dl.add_rect(ImVec2(x, y), ImVec2(x + w, y + h),
                theme_mod.u32(GLASS, 0.85), r, 1.4)
    dl.add_rect(ImVec2(x + 1.4, y + 1.4), ImVec2(x + w - 1.4, y + h - 1.4),
                theme_mod.u32(SKY_DEEP, 0.20 if primary else 0.12), r, 1.0)
    return True


def hover_aura(dl, x0, y0, x1, y1, t, amount, kind):
    """The gloss intensifies and a halo blooms underneath."""
    w, h = x1 - x0, y1 - y0
    r = h * 0.5 if kind != "input" else t.rounding
    # the halo sits low, as if the surface were lit from below the glass
    _halo(dl, x0, y0 + h * 0.18, w, h, r, t.accent_bright, amount, 5, 10.0)
    dl.add_rect_filled(ImVec2(x0 + w * 0.12, y1 - 2),
                       ImVec2(x1 - w * 0.12, y1 + 7 * amount),
                       theme_mod.u32(t.accent_bright, 0.18 * amount), 8.0)
    _gloss(dl, x0, y0, w, h, r, 0.55 * amount, 0.52)


def press(dl, x0, y0, x1, y1, t, amount):
    """Squash: the glass compresses and the light pools at the foot."""
    w, h = x1 - x0, y1 - y0
    r = h * 0.5
    dl.add_rect_filled(ImVec2(x0, y0), ImVec2(x1, y1),
                       theme_mod.u32(SKY_DEEP, 0.14 * amount), r)
    _grad_rect(dl, x0 + 2, y0 + h * 0.45, w - 4, h * 0.55 - 2,
               theme_mod.with_alpha(GLASS, 0.0),
               theme_mod.with_alpha(GLASS, 0.40 * amount), r * 0.8)


def spinner(dl, cx, cy, r, t, phase):
    """A water bubble: breathing, shedding micro bubbles, rippling."""
    breathe = 0.5 + 0.5 * math.sin(phase * 1.7)
    rr = r * (0.88 + 0.12 * breathe)

    # ripple rings leaving the base, each on its own phase
    for i in range(3):
        k = ((phase * 0.55 + i / 3.0) % 1.0)
        rad = rr * (0.7 + k * 1.5)
        dl.add_circle(ImVec2(cx, cy + rr * 0.72), rad,
                      theme_mod.u32(SKY_DEEP, 0.36 * (1.0 - k)),
                      32, 1.0 + 1.4 * (1.0 - k))

    # the body, lit from the upper left and thinning at the rim
    dl.add_circle_filled(ImVec2(cx, cy), rr, theme_mod.u32(SKY, 0.42), 44)
    steps = 12
    for i in range(steps, 0, -1):
        k = i / steps
        off = rr * 0.26 * (1.0 - k)
        dl.add_circle_filled(ImVec2(cx - off * 0.7, cy - off * 0.7), rr * k,
                             theme_mod.u32(GLASS, 0.055))
    # the bright caustic pooling at the bottom of a drop, and the blue
    # it throws onto whatever is underneath
    dl.add_circle_filled(ImVec2(cx, cy + rr * 0.95), rr * 0.62,
                         theme_mod.u32(SKY_DEEP, 0.10))
    dl.add_circle_filled(ImVec2(cx, cy + rr * 0.32), rr * 0.46,
                         theme_mod.u32(GLASS, 0.30))
    # rim: a bubble is brightest where you look through the most water
    dl.add_circle(ImVec2(cx, cy), rr, theme_mod.u32(GLASS, 0.85), 44, 1.8)
    dl.path_arc_to(ImVec2(cx, cy), rr * 0.93, math.radians(20),
                   math.radians(140), 24)
    dl.path_stroke(theme_mod.u32(SKY_DEEP, 0.62), 1.9, 0)
    # an inner edge, because the thing that makes a bubble read is water
    # being thickest where you look through it edge-on
    dl.add_circle(ImVec2(cx, cy), rr * 0.86, theme_mod.u32(SKY_DEEP, 0.22),
                  40, 1.2)
    # the two highlights every drawn drop has
    dl.add_circle_filled(ImVec2(cx - rr * 0.34, cy - rr * 0.38), rr * 0.20,
                         theme_mod.u32(GLASS, 0.92))
    dl.add_circle_filled(ImVec2(cx + rr * 0.30, cy + rr * 0.34), rr * 0.09,
                         theme_mod.u32(GLASS, 0.55))

    # micro bubbles rising out of it
    for i in range(5):
        k = ((phase * 0.42 + i * 0.23) % 1.0)
        bx = cx + math.sin(phase * 1.1 + i * 2.0) * rr * 0.42
        by = cy - rr * 0.6 - k * rr * 1.9
        br = max(0.7, rr * 0.11 * (1.0 - k * 0.5))
        fade = (1.0 - k) * 0.8
        dl.add_circle_filled(ImVec2(bx, by), br, theme_mod.u32(GLASS, fade))
        dl.add_circle(ImVec2(bx, by), br, theme_mod.u32(SKY_DEEP, fade * 0.5),
                      12, 1.0)
    return True


def background(dl, x, y, w, h, t, now):
    """Sky into grass, a sun, caustic light and drifting bubbles."""
    # sky down to a horizon, then grass - the whole Frutiger landscape in
    # two gradients and a band of light where they meet
    horizon = y + h * 0.66
    _grad_rect(dl, x, y, w, horizon - y, rgb("#aee4f8"), rgb("#e4f7ff"))
    _grad_rect(dl, x, horizon, w, (y + h) - horizon,
               theme_mod.lerp(GRASS, rgb("#eafbe4"), 0.55), GRASS_DEEP)

    # the sun, high and to the right
    sx, sy = x + w * 0.80, y + h * 0.14
    for i in range(7, 0, -1):
        dl.add_circle_filled(ImVec2(sx, sy), h * 0.055 * i,
                             theme_mod.u32(SUN, 0.030))
    dl.add_circle_filled(ImVec2(sx, sy), h * 0.030, theme_mod.u32(SUN, 0.35))

    # a bloom along the horizon, which is what sells the two gradients as
    # one scene rather than two stacked rectangles
    _grad_rect(dl, x, horizon - h * 0.07, w, h * 0.14,
               theme_mod.with_alpha(GLASS, 0.0),
               theme_mod.with_alpha(GLASS, 0.55))
    _grad_rect(dl, x, horizon, w, h * 0.09,
               theme_mod.with_alpha(GLASS, 0.5),
               theme_mod.with_alpha(GLASS, 0.0))

    _caustics(dl, x, horizon - h * 0.06, w, (y + h) - horizon + h * 0.06,
              theme_mod.u32(GLASS, 0.16), now, 24)
    _caustics(dl, x, y, w, horizon - y, theme_mod.u32(GLASS, 0.09), now * 0.6, 12)

    # bubbles drifting up the whole frame
    for i in range(14):
        k = ((now * 0.045 + i * 0.137) % 1.0)
        bx = x + w * ((i * 0.173 + math.sin(now * 0.12 + i) * 0.02) % 1.0)
        by = (y + h) - k * h * 1.05
        br = 3.0 + 7.0 * ((i * 7 % 5) / 5.0)
        a = 0.16 * (1.0 - abs(k - 0.5) * 1.2)
        dl.add_circle_filled(ImVec2(bx, by), br, theme_mod.u32(GLASS, a))
        dl.add_circle(ImVec2(bx, by), br, theme_mod.u32(GLASS, a * 2.0), 16, 1.0)
        dl.add_circle_filled(ImVec2(bx - br * 0.3, by - br * 0.3), br * 0.25,
                             theme_mod.u32(GLASS, a * 2.4))
    return True


def tabs(dl, x, y, w, h, t, rects, index, hots):
    """Glass tabs: the selected one is a lit pill, the rest are water."""
    if not rects:
        return False
    for i, (tx, tw) in enumerate(rects):
        on = i == index
        r = (h - 8) * 0.5
        ty, th = y + 4, h - 8
        if on:
            paint.grad_rect(dl, tx, ty, tw, th,
                            theme_mod.lerp(t.accent, GLASS, 0.40),
                            theme_mod.lerp(t.accent, SKY_DEEP, 0.25), r)
            paint.gloss(dl, tx, ty, tw, th, r, GLASS, 1.0, 0.52)
            dl.add_rect(ImVec2(tx, ty), ImVec2(tx + tw, ty + th),
                        theme_mod.u32(GLASS, 0.85), r, 1.3)
        elif hots[i] > 0.01:
            paint.grad_rect(dl, tx, ty, tw, th,
                            theme_mod.with_alpha(GLASS, 0.55 * hots[i]),
                            theme_mod.with_alpha(GLASS, 0.18 * hots[i]), r)
            dl.add_rect(ImVec2(tx, ty), ImVec2(tx + tw, ty + th),
                        theme_mod.u32(GLASS, 0.5 * hots[i]), r, 1.0)
    return True


SKIN = skins.Skin(
    name="frutiger-aero",
    plate=plate, frame=frame, hover_aura=hover_aura, press=press, tabs=tabs,
    spinner=spinner, background=background,
    press_depth=3.4,          # a squishy compression, not a click
    extras={"sky": SKY, "grass": GRASS, "sun": SUN, "glass": GLASS},
)

AERO_PROFILE = profiles.Profile(
    name="frutiger-aero", theme=AERO, layout=layouts.TABBED,
    face_ui="Segoe UI Variable", face_display="Segoe UI Semibold",
    face_mono="Consolas",
    base_size=17.5, density=1.12,
    card_style="raised", card_shadow=True,
    motion=0.85,              # unhurried, like everything else in 2007
    sound_set="breeze", volume=0.14,
    skin=SKIN,
    blurb="glass, water and tech optimism - sky over grass, about 2007",
)
