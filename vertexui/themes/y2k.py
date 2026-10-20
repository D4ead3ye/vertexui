"""Y2K Cyber - Win98 chrome, neon, and a CD that will not stop spinning.

Pitch black ground, liquid chrome panels, hot pink and electric cyan over
deep purple. Zero radius anywhere, chamfered corners, hard offset shadows
with no blur at all, and the inset/outset bevels that every operating
system drew between 1995 and 2001.

    from vertexui import themes
    app = compose.App(profile=themes.Y2K)

Cards are floating windows: a gradient title bar carrying the module name
in monospace with the minimise and close squares at its right, a dot-grid
ground, and a chrome frame. Buttons are metal blocks that drop the instant
you touch them - `press_snap`, because this look is *about* not being
smooth, and an eased press makes it read as a modern button wearing a
costume.

The spinner is a CD-ROM: holographic rainbow sweeping round the disc, a
chrome hub, the spindle hole, and the laser LED blinking beside it.
"""

import math

from imgui_bundle import ImVec2, imgui

from .. import layouts, paint, profiles, skins
from .. import theme as theme_mod
from ..theme import Theme, rgb

# --- palette -----------------------------------------------------------
CHROME_HI = rgb("#f2f4f8")
CHROME = rgb("#9aa2ae")
CHROME_LO = rgb("#4a5260")
STEEL = rgb("#1c1f26")
PINK = rgb("#ff2d95")
CYAN = rgb("#28e7f0")
PURPLE = rgb("#7b3ff2")
VOID = rgb("#05050a")

CYBER = Theme(
    name="y2k-cyber",
    bg=VOID, panel=rgb("#0a0b12"), surface=rgb("#12141c"),
    surface_hover=rgb("#1b1e29"), border=rgb("#39404f"),
    accent=PINK, accent_bright=rgb("#ff6fbb"), accent_dim=rgb("#5c0f39"),
    text=rgb("#e8ecf5"), text_dim=rgb("#8e97a8"), text_mute=rgb("#5a6273"),
    ok=rgb("#2bf58a"), warn=rgb("#ffd12e"), danger=rgb("#ff3b3b"),
    info=CYAN,
    rounding=0.0, rounding_panel=0.0, border_width=1.0,
)

SHADOW_OFF = 5.0           # hard offset, no blur - 1999 had no blur
CHAMFER = 7.0


# --- primitives --------------------------------------------------------

def _chamfer(x, y, w, h, c=CHAMFER):
    """Two corners cut, from the shared helper."""
    return paint.chamfered(x, y, w, h, c)


def _bevel(dl, x, y, w, h, t, out=True, depth=2.0):
    paint.bevel(dl, x, y, w, h,
                theme_mod.u32(CHROME_HI, 0.85 if out else 0.30),
                theme_mod.u32(VOID, 0.85 if out else 0.55), out, depth)


def _brushed(dl, x, y, w, h, top, bottom):
    paint.grad_rect(dl, x, y, w, h, top, bottom, 0.0)


def _dots(dl, x, y, w, h, col, step=8.0):
    paint.dots(dl, x, y, w, h, col, step)


# --- painters ----------------------------------------------------------

def plate(dl, x, y, w, h, t, edge, style, shadow):
    """A floating window: hard shadow, chrome frame, dot-grid ground."""
    if style == "flat":
        return False
    if shadow and style in ("raised", "plated"):
        # one hard-edged offset block - no blur, no stack of fading rects
        dl.add_convex_poly_filled(
            _chamfer(x + SHADOW_OFF, y + SHADOW_OFF, w, h),
            theme_mod.u32(PURPLE, 0.55))
        dl.add_convex_poly_filled(
            _chamfer(x + SHADOW_OFF - 2, y + SHADOW_OFF - 2, w, h),
            theme_mod.u32(VOID, 0.75))

    body = _chamfer(x, y, w, h)
    if style != "outlined":
        dl.add_convex_poly_filled(body, theme_mod.u32(t.surface))
        _dots(dl, x + 2, y + 2, w - 4, h - 4, theme_mod.u32(CHROME, 0.10))
    # chrome frame: an outset bevel inside a thin dark keyline
    dl.add_polyline(body + [body[0]], theme_mod.u32(CHROME_LO), 1.0, 0)
    _bevel(dl, x + 1, y + 1, w - 2, h - 2, t, out=True, depth=2)
    if edge is not None:
        dl.add_rect_filled(ImVec2(x + 3, y + 3), ImVec2(x + w - 3, y + 5),
                           theme_mod.u32(edge, 0.95))
    return True


def head(dl, x, y, w, t, icon, title, right, right_col, dot):
    """A Win98 title bar: gradient fill, module name, window squares."""
    from .. import fonts
    bar_h = 22.0
    bx, by, bw = x + 3, y + 3, w - 6
    _brushed(dl, bx, by, bw, bar_h, PURPLE, rgb("#2a1060"))
    dl.add_rect_filled(ImVec2(bx, by), ImVec2(bx + bw * 0.45, by + bar_h),
                       theme_mod.u32(PINK, 0.30))
    _bevel(dl, bx, by, bw, bar_h, t, out=True, depth=1)

    # the module name, in the idiom the brief asks for
    label = f"// {(title or 'MODULE').upper().replace(' ', '_')}.EXE"
    with fonts.use("mono"):
        ts = imgui.calc_text_size(label)
        dl.add_text(ImVec2(bx + 7, by + (bar_h - ts.y) * 0.5),
                    theme_mod.u32(CHROME_HI), label)

    # minimise and close, as small square chrome buttons
    sq = 13.0
    sx = bx + bw - 6 - sq
    for i, mark in enumerate(("x", "-")):
        px = sx - i * (sq + 3)
        _brushed(dl, px, by + 4, sq, sq, CHROME, CHROME_LO)
        _bevel(dl, px, by + 4, sq, sq, t, out=True, depth=1)
        cy = by + 4 + sq * 0.5
        if mark == "-":
            dl.add_rect_filled(ImVec2(px + 3, cy + 2),
                               ImVec2(px + sq - 3, cy + 3.4),
                               theme_mod.u32(VOID))
        else:
            dl.add_line(ImVec2(px + 3.5, cy - 3), ImVec2(px + sq - 3.5, cy + 3),
                        theme_mod.u32(VOID), 1.6)
            dl.add_line(ImVec2(px + sq - 3.5, cy - 3), ImVec2(px + 3.5, cy + 3),
                        theme_mod.u32(VOID), 1.6)

    if right:
        with fonts.use("mono"):
            rw = imgui.calc_text_size(right).x
            dl.add_text(ImVec2(sx - (sq + 3) - 10 - rw, by + (bar_h - ts.y) * 0.5),
                        theme_mod.u32(right_col or CYAN), right)
    return y + bar_h + 8.0


def frame(dl, x, y, w, h, t, kind):
    """Metal blocks for buttons, hard inset wells for fields."""
    if kind == "input":
        dl.add_rect_filled(ImVec2(x, y), ImVec2(x + w, y + h),
                           theme_mod.u32(rgb("#05070c")))
        _bevel(dl, x, y, w, h, t, out=False, depth=2)
        return True
    if not kind.startswith("button"):
        return False
    primary = kind.endswith("primary")
    top = theme_mod.lerp(PINK, CHROME_HI, 0.35) if primary else CHROME
    bot = theme_mod.lerp(PINK, VOID, 0.45) if primary else CHROME_LO
    body = _chamfer(x, y, w, h, 5.0)
    dl.add_convex_poly_filled(body, theme_mod.u32(bot))
    _brushed(dl, x + 1, y + 1, w - 2, h * 0.52, top,
             theme_mod.lerp(top, bot, 0.65))
    _bevel(dl, x, y, w, h, t, out=True, depth=2)
    return True


def hover_aura(dl, x0, y0, x1, y1, t, amount, kind):
    """A CRT glitch: scanline tear plus a chromatic split of the edge.

    Driven by the clock rather than by `amount` alone, so it flickers
    irregularly - a glitch that pulses smoothly is not a glitch.
    """
    import time as _time
    w, h = x1 - x0, y1 - y0
    beat = _time.time()
    flick = 0.55 + 0.45 * math.sin(beat * 37.0)
    a = amount * flick

    # the pink/cyan separation that says "this is a signal, not a surface"
    dl.add_rect(ImVec2(x0 - 2, y0 - 1), ImVec2(x1 - 1, y1 - 1),
                theme_mod.u32(CYAN, 0.55 * a), 0.0, 1.0)
    dl.add_rect(ImVec2(x0 + 1, y0 + 1), ImVec2(x1 + 2, y1 + 1),
                theme_mod.u32(PINK, 0.65 * a), 0.0, 1.0)
    # a torn scanline sliding down the control
    band = (beat * 160.0) % max(1.0, h + 12.0) - 6.0
    if 0 <= band <= h - 2:
        off = math.sin(beat * 53.0) * 3.0 * amount
        dl.add_rect_filled(ImVec2(x0 + off, y0 + band),
                           ImVec2(x1 + off, y0 + band + 2.0),
                           theme_mod.u32(CHROME_HI, 0.22 * amount))
    # neon box-shadow on the outside
    for i, col in ((1, PINK), (3, PURPLE)):
        dl.add_rect(ImVec2(x0 - i, y0 - i), ImVec2(x1 + i, y1 + i),
                    theme_mod.u32(col, 0.30 * amount / i), 0.0, 1.0)


def spinner(dl, cx, cy, r, t, phase):
    """A CD-ROM on its spindle.

    The holographic sweep is wedges round the disc whose hue depends on
    the angle *plus* the spin, so the rainbow travels over a surface that
    is itself turning - which is what a real disc does and is the whole
    reason it reads as holographic rather than as a painted wheel.
    """
    spin = phase * 7.0
    disc = rgb("#171a22")
    dl.add_circle_filled(ImVec2(cx, cy), r, theme_mod.u32(disc), 56)

    # The holograph is two narrow lobes sweeping round, not a colour
    # wheel: a disc is dark silver nearly everywhere and brilliant only
    # where the light happens to catch it, and a rainbow drawn evenly all
    # the way round reads as a pie chart.
    seg = 72
    for i in range(seg):
        a0 = i / seg * math.tau
        a1 = (i + 1) / seg * math.tau
        # |cos| is already two lobes 180 degrees apart, which is what a
        # disc shows. A second term looked like more holograph and was
        # really four wide lobes, i.e. a colour wheel.
        sheen = abs(math.cos(a0 - spin)) ** 16
        if sheen < 0.015:
            continue
        hue = (a0 / math.tau * 3.0 + spin * 0.18) % 1.0
        dl.add_triangle_filled(
            ImVec2(cx, cy),
            ImVec2(cx + math.cos(a0) * r, cy + math.sin(a0) * r),
            ImVec2(cx + math.cos(a1) * r, cy + math.sin(a1) * r),
            theme_mod.u32(theme_mod.lerp(disc, _rainbow(hue), 0.80 * sheen)))

    # pressed data tracks
    for k in (0.95, 0.86, 0.77, 0.68, 0.58, 0.49):
        dl.add_circle(ImVec2(cx, cy), r * k, theme_mod.u32(VOID, 0.20), 48, 1.0)
    # the clear inner ring, the chrome hub, and the spindle hole
    dl.add_circle_filled(ImVec2(cx, cy), r * 0.44,
                         theme_mod.u32(theme_mod.lerp(disc, VOID, 0.4), 0.95))
    dl.add_circle(ImVec2(cx, cy), r * 0.44, theme_mod.u32(CHROME, 0.35), 40, 1.0)
    dl.add_circle_filled(ImVec2(cx, cy), r * 0.33, theme_mod.u32(CHROME_HI, 0.9))
    dl.add_circle_filled(ImVec2(cx, cy), r * 0.27, theme_mod.u32(CHROME_LO))
    dl.add_circle_filled(ImVec2(cx, cy), r * 0.15, theme_mod.u32(VOID))
    # a glint on the hub, turning with the disc
    gx, gy = cx + math.cos(spin) * r * 0.21, cy + math.sin(spin) * r * 0.21
    dl.add_circle_filled(ImVec2(gx, gy), r * 0.05,
                         theme_mod.u32(CHROME_HI, 0.9))
    dl.add_circle(ImVec2(cx, cy), r, theme_mod.u32(CHROME_LO), 56, 1.3)
    # the laser LED, blinking beside it
    if math.sin(phase * 14.0) > 0.1:
        lx, ly = cx + r * 1.35, cy + r * 0.72
        dl.add_circle_filled(ImVec2(lx, ly), r * 0.26,
                             theme_mod.u32(rgb("#ff1a1a"), 0.28))
        dl.add_circle_filled(ImVec2(lx, ly), r * 0.11,
                             theme_mod.u32(rgb("#ff5252"), 0.95))
    return True


def _rainbow(h):
    """Hue to colour, cheaply - six linear ramps, which at this size is
    indistinguishable from a real HSV conversion and a tenth the work."""
    i = int(h * 6.0) % 6
    f = h * 6.0 - int(h * 6.0)
    q, tt = 1.0 - f, f
    table = ((1, tt, 0), (q, 1, 0), (0, 1, tt), (0, q, 1), (tt, 0, 1), (1, 0, q))
    r, g, b = table[i]
    from imgui_bundle import ImVec4
    return ImVec4(float(r), float(g), float(b), 1.0)


def background(dl, x, y, w, h, t, now):
    """Pitch black, a dot-matrix field, a horizon grid and scanlines."""
    dl.add_rect_filled(ImVec2(x, y), ImVec2(x + w, y + h), theme_mod.u32(VOID))
    _dots(dl, x, y, w, h, theme_mod.u32(CHROME, 0.085), 9.0)

    # a perspective grid along the bottom, receding - the one piece of
    # 1999 iconography that still has to be earned with real maths
    horizon = y + h * 0.78
    for i in range(-11, 12):
        dl.add_line(ImVec2(x + w * 0.5 + i * w * 0.045, horizon),
                    ImVec2(x + w * 0.5 + i * w * 0.42, y + h),
                    theme_mod.u32(PURPLE, 0.16), 1.0)
    z = (now * 0.5) % 1.0
    for k in range(9):
        f = ((k + z) / 9.0) ** 2.6
        ly = horizon + (y + h - horizon) * f
        dl.add_line(ImVec2(x, ly), ImVec2(x + w, ly),
                    theme_mod.u32(PURPLE, 0.10 + 0.14 * f), 1.0)
    dl.add_line(ImVec2(x, horizon), ImVec2(x + w, horizon),
                theme_mod.u32(CYAN, 0.30), 1.0)

    # CRT scanlines over everything, and one bright roll bar drifting
    paint.scanlines(dl, x, y, w, h, theme_mod.with_alpha(VOID, 0.22), 3.0)
    roll = (now * 90.0) % (h + 160.0) - 80.0
    dl.add_rect_filled(ImVec2(x, y + roll), ImVec2(x + w, y + roll + 48.0),
                       theme_mod.u32(CHROME_HI, 0.022))
    return True


def tabs(dl, x, y, w, h, t, rects, index, hots):
    """A row of chrome tabs, the selected one standing proud."""
    if not rects:
        return False
    dl.add_rect_filled(ImVec2(x - 6, y + h - 2), ImVec2(x + w + 6, y + h),
                       theme_mod.u32(CHROME_LO, 0.9))
    for i, (tx, tw) in enumerate(rects):
        on = i == index
        top = CHROME if on else rgb("#2a2f3a")
        bot = CHROME_LO if on else rgb("#161a22")
        if hots[i] > 0.01 and not on:
            top = theme_mod.lerp(top, CHROME, 0.35 * hots[i])
        body = paint.chamfered(tx, y + (0 if on else 3), tw,
                               h - (2 if on else 5), 6.0)
        paint.grad_poly(dl, body, top, bot)
        dl.add_polyline(body + [body[0]], theme_mod.u32(VOID, 0.8), 1.0, 0)
        _bevel(dl, tx, y + (0 if on else 3), tw, h - (2 if on else 5), t,
               out=True, depth=1)
        if on:
            dl.add_rect_filled(ImVec2(tx + 4, y + 2), ImVec2(tx + tw - 4, y + 4),
                               theme_mod.u32(PINK, 0.9))
    return True


SKIN = skins.Skin(
    name="y2k-cyber",
    plate=plate, head=head, frame=frame, hover_aura=hover_aura, tabs=tabs,
    spinner=spinner, background=background,
    press_depth=3.0,
    press_snap=True,          # 1999 buttons do not ease
    extras={"mono_inputs": True, "chrome": CHROME, "pink": PINK,
            "cyan": CYAN, "purple": PURPLE},
)

Y2K = profiles.Profile(
    name="y2k-cyber", theme=CYBER, layout=layouts.TABBED,
    face_ui="Tahoma", face_display="Impact", face_mono="Consolas",
    base_size=16.0, density=0.92,
    card_style="raised", card_shadow=True,
    motion=2.6,               # everything snaps
    sound_set="crisp", volume=0.16,
    skin=SKIN,
    blurb="Win98 chrome, neon pink on pitch black, and a CD-ROM spinner",
)
