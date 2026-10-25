"""ENA World - a 2000s multimedia CD-ROM that has been left running.

Beige computer plastic, charcoal title strips, blood red, olive drab and
rust. No sky, no landscape, no gradient: the ground is a sheet of plastic
with a CAD grid printed on it, granite noise through it and scanlines
over it, and the only places anything is dark are the wells cut into it.

    from vertexui import themes
    app = compose.App(profile=themes.ENA)

The register is Encarta and Macromedia Flash rather than the web: formal
cold serif headers over monospace body text, 2px outset bevels, pitch
black 3px drop shadows with no blur in them, black-and-white checker
strips, and low-poly wireframe brackets in the margins. Everything is
instant - there is no transition anywhere in this theme, because a CD-ROM
in 2001 had no frames to spare for one.

Four things carry it:

**Plastic, not a window ground.** `bg` is the beige of a 1998 case, so
the application *is* the chassis and the dark areas are wells cut into
it. Every other dark theme here puts panels on a void; this puts holes
in a surface, which is why its cards read as moulded rather than as
floating.

**Hover is a pixelated inversion.** A 2px checker of charcoal laid over
the control, thresholded so there is no in-between state. No glow, no
blur, nothing that fades - an inversion is what a 1-bit interface did and
it costs one frame.

**The bevel is the whole visual language.** Outset for anything you can
press, inset for anything that holds a value, and the press flips it.
Drawn with the full four tones, because two is why most imitations read
as a flat rectangle with a highlight.

**The spinner is a wireframe solid in a viewport**, flat-shaded from the
muted palette with every edge inked, stepping at 12fps - the rotating
model in the corner of a reference CD-ROM.
"""

import math

from imgui_bundle import ImVec2, imgui

from .. import fonts, layouts, paint, profiles, skins
from .. import theme as theme_mod
from ..theme import Theme, rgb

# --- palette: industrial, legacy, muted ---------------------------------
PLASTIC = rgb("#d4d0c8")     # beige computer plastic - the chassis
PLASTIC_D = rgb("#bcb8b0")
OFFWHITE = rgb("#f0eff1")    # stark off-white - fields and paper
CHARCOAL = rgb("#1e1e24")    # deep slate - title strips and wells
ASPHALT = rgb("#121212")     # the black every border and shadow uses
CHROME = rgb("#9a9a93")      # metallic grey
CHROME_HI = rgb("#ffffff")
CHROME_SH = rgb("#808080")
CRIMSON = rgb("#8b0000")     # desaturated blood red
OLIVE = rgb("#4a5d4e")       # olive drab
RUST = rgb("#8b4513")        # dark rust orange

WORLD = Theme(
    name="ena-world",
    bg=PLASTIC, panel=PLASTIC_D, surface=PLASTIC, surface_hover=rgb("#e0ddd6"),
    border=ASPHALT,
    accent=CRIMSON, accent_bright=rgb("#a81414"), accent_dim=rgb("#4a0b0b"),
    text=rgb("#121212"), text_dim=rgb("#4a4740"), text_mute=rgb("#7d796f"),
    ok=OLIVE, warn=RUST, danger=CRIMSON, info=rgb("#5e5e57"),
    rounding=0.0, rounding_panel=0.0, border_width=2.0,
)

DROP = 3.0                   # box-shadow: 3px 3px 0 #000, exactly
STEP = 12.0                  # the framerate the one moving thing runs at


def _q(phase, rate=STEP):
    """Quantise to that framerate. The only motion in this theme is the
    viewport solid, and it steps rather than turning."""
    return math.floor(phase * rate) / rate


def _snap(v, grid=3.0):
    return math.floor(v / grid) * grid


def _bevel(dl, x, y, w, h, out=True, face=None, width=2):
    """The classic border, in the order Windows drew it: an outer pair
    and an inner pair, light down one diagonal, dark down the other.

    Two tones is the usual shortcut and it is why most imitations read as
    a flat rectangle with a highlight. The second pair is what gives the
    edge a thickness you can see.
    """
    if face is not None:
        dl.add_rect_filled(ImVec2(x, y), ImVec2(x + w, y + h),
                           theme_mod.u32(face), 0.0)
    pairs = ((CHROME_HI, ASPHALT), (PLASTIC, CHROME_SH)) if out else \
            ((CHROME_SH, CHROME_HI), (ASPHALT, PLASTIC))
    for i, (hi, lo) in enumerate(pairs[:max(1, int(width))]):
        a, b, c, d = x + i, y + i, x + w - i, y + h - i
        dl.add_line(ImVec2(a, b), ImVec2(c, b), theme_mod.u32(hi), 1.0)
        dl.add_line(ImVec2(a, b), ImVec2(a, d), theme_mod.u32(hi), 1.0)
        dl.add_line(ImVec2(a, d - 1), ImVec2(c, d - 1), theme_mod.u32(lo), 1.0)
        dl.add_line(ImVec2(c - 1, b), ImVec2(c - 1, d), theme_mod.u32(lo), 1.0)


def _checker(dl, x, y, w, h, col, cell=8.0, offset=0.0):
    """Black-and-white chess, flat. No perspective: the vanishing-point
    version of this is synthwave, which is the wrong decade entirely."""
    for r in range(int(h / cell) + 2):
        for c in range(int(w / cell) + 1):
            if (r + c) % 2:
                continue
            px, py = x + c * cell, y + r * cell - offset
            if py + cell < y or py > y + h:
                continue
            dl.add_rect_filled(ImVec2(px, max(y, py)),
                               ImVec2(min(x + w, px + cell),
                                      min(y + h, py + cell)), col, 0.0)


def _noise(dl, x, y, w, h, col, n=260, cell=2.0):
    """Granite: low-contrast speckle from a fixed seed, so it is a
    texture printed on the plastic and not a particle effect."""
    seed = 0x5EED
    iw, ih = max(1, int(w)), max(1, int(h))
    for _ in range(n):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        px = x + (seed >> 6) % iw
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        py = y + (seed >> 6) % ih
        dl.add_rect_filled(ImVec2(px, py), ImVec2(px + cell, py + cell),
                           col, 0.0)


def _jagged(dl, x, y, w, col, tooth=5.0, depth=3.0):
    """A divider with teeth. A 1px rule is a modern divider; this is the
    one a CD-ROM chapter break used, and it costs the same."""
    n = max(2, int(w / tooth))
    pts = [ImVec2(x + i * (w / n), y + (depth if i % 2 else 0.0))
           for i in range(n + 1)]
    dl.add_polyline(pts, col, 1.0, 0)


def _bracket(dl, x, y, s, col, flip_x=False, flip_y=False):
    """A low-poly wireframe corner. Decorative, and the one piece of the
    CAD register that sits on the panels rather than behind them."""
    sx, sy = (-1.0 if flip_x else 1.0), (-1.0 if flip_y else 1.0)
    dl.add_polyline([ImVec2(x, y + sy * s), ImVec2(x, y),
                     ImVec2(x + sx * s, y)], col, 1.0, 0)
    dl.add_line(ImVec2(x + sx * s * 0.25, y + sy * s * 0.25),
                ImVec2(x + sx * s * 0.8, y + sy * s * 0.8), col, 1.0)


def _pixel_icon(dl, x, y, px, col, rows=(0b01110, 0b10001, 0b10101,
                                         0b10001, 0b01110)):
    """A five-by-five bitmap, drawn as squares. Anti-aliasing is the one
    thing this interface must not have, and a vector icon scaled down has
    nothing but."""
    for r, bits in enumerate(rows):
        for c in range(5):
            if bits >> (4 - c) & 1:
                dl.add_rect_filled(ImVec2(x + c * px, y + r * px),
                                   ImVec2(x + c * px + px, y + r * px + px),
                                   col, 0.0)


# Cryptic sub-headers: the word, and something that is not quite its
# translation - the register a reference CD-ROM's chapter list was in.
SUB = {
    "status": "境界状態", "state": "境界状態",
    "region": "地域", "map": "地域",
    "signal": "信号", "feed": "信号",
    "archive": "記録", "log": "記録", "index": "目次",
    "turbulence": "異次元", "drift": "異次元",
    "depth": "深層", "core": "深層",
    "stability": "安定度", "integrity": "安定度",
    "exits": "出口", "doors": "出口",
    "void": "虚無", "viewport": "画面",
    "memory": "記憶", "noise": "雑音",
    "readings": "測量", "survey": "測量",
    "transfer": "転送", "options": "設定",
}


def _sub(title):
    if not title or not fonts.has("cjk"):
        return ""
    for word in str(title).lower().replace("-", " ").replace("/", " ").split():
        hit = SUB.get(word.strip(":.,"))
        if hit:
            return hit
    return ""


# --- painters -----------------------------------------------------------

def plate(dl, x, y, w, h, t, edge, style, shadow):
    """A moulded panel: pitch-black offset shadow, outset bevel, plastic
    face, and wireframe brackets at the corners the title does not use."""
    if style == "flat":
        return False
    if shadow and style in ("raised", "plated"):
        dl.add_rect_filled(ImVec2(x + DROP, y + DROP),
                           ImVec2(x + w + DROP, y + h + DROP),
                           theme_mod.u32(ASPHALT), 0.0)
    _bevel(dl, x, y, w, h, out=True,
           face=t.surface if style != "outlined" else None)
    dl.add_rect(ImVec2(x, y), ImVec2(x + w, y + h), theme_mod.u32(ASPHALT),
                0.0, 1.0)
    br = theme_mod.u32(CHROME_SH, 0.9)
    _bracket(dl, x + 5, y + h - 5, 9.0, br, flip_y=True)
    _bracket(dl, x + w - 5, y + h - 5, 9.0, br, flip_x=True, flip_y=True)
    if edge is not None:
        dl.add_rect_filled(ImVec2(x + 3, y + 3), ImVec2(x + 7, y + h - 3),
                           theme_mod.u32(edge), 0.0)
    return True


def head(dl, x, y, w, t, icon, title, right, right_col, dot):
    """A title strip: charcoal, a bitmap icon, a serif caption, and the
    two chunky boxes every window of that decade had at its right."""
    bar = 23.0
    bx, by, bw = x + 3, y + 3, w - 6
    cut = 9.0
    dl.add_convex_poly_filled(
        [ImVec2(bx, by), ImVec2(bx + bw, by), ImVec2(bx + bw, by + bar - cut),
         ImVec2(bx + bw - cut, by + bar), ImVec2(bx, by + bar)],
        theme_mod.u32(CHARCOAL))
    dl.add_rect_filled(ImVec2(bx, by), ImVec2(bx + 3, by + bar),
                       theme_mod.u32(dot if dot is not None else CRIMSON), 0.0)
    _pixel_icon(dl, bx + 8, by + 6, 2.0,
                theme_mod.u32(dot if dot is not None else CHROME))
    tx = bx + 24.0
    with fonts.use("title"):
        label = title or ""
        ts = imgui.calc_text_size(label)
        dl.add_text(ImVec2(tx, by + (bar - ts.y) * 0.5),
                    theme_mod.u32(OFFWHITE), label)
    sub = _sub(title)
    if sub:
        with fonts.use("cjk"):
            sz = imgui.calc_text_size(sub)
            dl.add_text(ImVec2(tx + ts.x + 8, by + (bar - sz.y) * 0.5),
                        theme_mod.u32(CHROME), sub)

    # minimise and close, as small bevelled plastic squares
    sq = 13.0
    sx = bx + bw - 6 - sq
    for i, mark in enumerate(("x", "-")):
        px = sx - i * (sq + 3)
        _bevel(dl, px, by + 5, sq, sq, out=True, face=PLASTIC)
        cy = by + 5 + sq * 0.5
        if mark == "-":
            dl.add_rect_filled(ImVec2(px + 3, cy + 2),
                               ImVec2(px + sq - 3, cy + 4),
                               theme_mod.u32(ASPHALT), 0.0)
        else:
            dl.add_line(ImVec2(px + 3.5, cy - 3), ImVec2(px + sq - 3.5, cy + 3),
                        theme_mod.u32(ASPHALT), 1.6)
            dl.add_line(ImVec2(px + sq - 3.5, cy - 3), ImVec2(px + 3.5, cy + 3),
                        theme_mod.u32(ASPHALT), 1.6)
    if right:
        with fonts.use("mono"):
            rw = imgui.calc_text_size(right)
            dl.add_text(ImVec2(sx - (sq + 3) - 10 - rw.x,
                               by + (bar - rw.y) * 0.5),
                        theme_mod.u32(right_col if right_col is not None
                                      else CHROME), right)
    _jagged(dl, bx, by + bar + 4, bw, theme_mod.u32(CHROME_SH, 0.8))
    return y + bar + 14.0


def frame(dl, x, y, w, h, t, kind):
    """Outset for anything you press, inset for anything that holds a
    value. That distinction is the entire grammar of this decade's UI and
    it is the one thing a flat theme cannot say."""
    if kind == "input":
        _bevel(dl, x, y, w, h, out=False, face=OFFWHITE)
        return True
    if not kind.startswith("button"):
        return False
    primary = kind.endswith("primary")
    dl.add_rect_filled(ImVec2(x + DROP, y + DROP),
                       ImVec2(x + w + DROP, y + h + DROP),
                       theme_mod.u32(ASPHALT), 0.0)
    _bevel(dl, x, y, w, h, out=True, face=CRIMSON if primary else PLASTIC)
    dl.add_rect(ImVec2(x, y), ImVec2(x + w, y + h), theme_mod.u32(ASPHALT),
                0.0, 1.0)
    return True


def hover_aura(dl, x0, y0, x1, y1, t, amount, kind):
    """A pixelated inversion, with nothing in between.

    `amount` arrives eased and is thresholded away: this interface has no
    intermediate states. What is left is a 2px checker of charcoal laid
    over the control - which is how a 1-bit display said *this one* - and
    a black keyline. Nothing glows, nothing blurs, nothing fades.
    """
    if amount < 0.5:
        return
    _checker(dl, x0 + 2, y0 + 2, x1 - x0 - 4, y1 - y0 - 4,
             theme_mod.u32(CHARCOAL, 0.42), 2.0)
    dl.add_rect(ImVec2(x0, y0), ImVec2(x1, y1), theme_mod.u32(ASPHALT),
                0.0, 1.0)


def press(dl, x0, y0, x1, y1, t, amount):
    """outset -> inset, which is the whole reason a 2001 button felt like
    it travelled: nothing moved, the light did."""
    if amount < 0.5:
        return
    _bevel(dl, x0, y0, x1 - x0, y1 - y0, out=False)
    dl.add_rect_filled(ImVec2(x0 + 2, y0 + 2), ImVec2(x1 - 2, y1 - 2),
                       theme_mod.u32(CHROME_SH, 0.26), 0.0)


def tabs(dl, x, y, w, h, t, rects, index, hots):
    """A tab control on a charcoal rail, the live one standing proud and
    breaking the line into the body below it."""
    if not rects:
        return False
    base = y + h
    dl.add_rect_filled(ImVec2(x - 10, y - 4), ImVec2(x + w + 10, base),
                       theme_mod.u32(CHARCOAL), 0.0)
    for i, (tx, tw) in enumerate(rects):
        on = i == index
        ty = y + (0.0 if on else 3.0)
        th = h - (0.0 if on else 3.0)
        face = PLASTIC if (on or hots[i] >= 0.5) else PLASTIC_D
        _bevel(dl, tx, ty, tw, th + 3, out=True, face=face)
        dl.add_rect(ImVec2(tx, ty), ImVec2(tx + tw, ty + th + 3),
                    theme_mod.u32(ASPHALT), 0.0, 1.0)
        if on:
            dl.add_rect_filled(ImVec2(tx + 3, ty + 3),
                               ImVec2(tx + tw - 3, ty + 5),
                               theme_mod.u32(CRIMSON), 0.0)
    dl.add_line(ImVec2(x - 10, base), ImVec2(x + w + 10, base),
                theme_mod.u32(ASPHALT), 1.0)
    return True


# an octahedron squeezed toward an hourglass, and the faces that wrap it
_V = ((0.0, 1.0, 0.0), (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (-1.0, 0.0, 0.0),
      (0.0, 0.0, 1.0), (0.0, 0.0, -1.0))
_F = ((0, 2, 4), (0, 4, 3), (0, 3, 5), (0, 5, 2),
      (1, 4, 2), (1, 3, 4), (1, 5, 3), (1, 2, 5))
FACETS = (PLASTIC_D, OLIVE, RUST, CHROME, rgb("#6f6b63"), CRIMSON,
          rgb("#3a4a3d"), rgb("#55514a"))


def _project(ax, ay, r):
    ca, sa = math.cos(ay), math.sin(ay)
    cb, sb = math.cos(ax), math.sin(ax)
    out = []
    for vx, vy, vz in _V:
        vx, vy, vz = vx * 0.80, vy * 1.34, vz * 0.80
        x1, z1 = vx * ca + vz * sa, -vx * sa + vz * ca
        y1, z2 = vy * cb - z1 * sb, vy * sb + z1 * cb
        out.append((x1 * r, y1 * r, z2))
    return out


def solid(dl, cx, cy, r, phase, spin=1.0, wire=True):
    """The rotating model, flat-shaded with every edge inked.

    Public, because the viewport in a reference CD-ROM is content rather
    than chrome: an application wants one of these inside a framed box of
    its own as well as inside the busy indicator.
    """
    qp = _q(phase)
    pts = _project(qp * 1.7, qp * 2.6, r)
    faces = []
    for n, (a, b, c) in enumerate(_F):
        ax, ay, _ = pts[a]
        bx, by, _ = pts[b]
        kx, ky, _ = pts[c]
        if (bx - ax) * (ky - ay) - (by - ay) * (kx - ax) <= 0:
            continue              # back-facing, from the projected winding
        faces.append(((pts[a][2] + pts[b][2] + pts[c][2]) / 3.0, n,
                      (ax, ay), (bx, by), (kx, ky)))
    faces.sort(key=lambda f: f[0])
    for _d, n, pa, pb, pc in faces:
        va = ImVec2(cx + pa[0], cy + pa[1])
        vb = ImVec2(cx + pb[0], cy + pb[1])
        vc = ImVec2(cx + pc[0], cy + pc[1])
        dl.add_triangle_filled(va, vb, vc, theme_mod.u32(FACETS[n]))
        if wire:
            dl.add_triangle(va, vb, vc, theme_mod.u32(ASPHALT), 1.2)


def viewport(dl, cx, cy, half, phase, spin=1.0):
    """A framed window onto the model: inset bevel, charcoal ground, a
    faint checker through it and a wireframe bracket at each corner."""
    _bevel(dl, cx - half, cy - half, half * 2, half * 2, out=False,
           face=CHARCOAL)
    _checker(dl, cx - half + 2, cy - half + 2, half * 2 - 4, half * 2 - 4,
             theme_mod.u32(CHROME, 0.10), 4.0)
    solid(dl, cx, cy, half * 0.66, phase, spin)
    br = theme_mod.u32(CHROME, 0.75)
    for fx, fy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        _bracket(dl, cx + fx * (half - 3), cy + fy * (half - 3), 7.0,
                 br, flip_x=fx > 0, flip_y=fy > 0)


def spinner(dl, cx, cy, r, t, phase, spin=1.0):
    """The model in its viewport. It steps at 12fps, so a faster spin
    covers more angle per step and the thing comes apart into poses
    rather than blurring - which is the look, not a defect."""
    heat = max(0.0, min(1.0, (spin - 1.0) / 4.0))
    half = r * 1.32
    qp = _q(phase)
    _bevel(dl, cx - half, cy - half, half * 2, half * 2, out=False,
           face=CHARCOAL)
    _checker(dl, cx - half + 2, cy - half + 2, half * 2 - 4, half * 2 - 4,
             theme_mod.u32(CHROME, 0.10), 4.0)
    core = r * 0.88
    for back, alpha in ((2.0 / STEP, 0.18), (1.0 / STEP, 0.34)):
        for px, py, _pz in _project((qp - back) * 1.7, (qp - back) * 2.6,
                                    core):
            dl.add_rect_filled(ImVec2(_snap(cx + px), _snap(cy + py)),
                               ImVec2(_snap(cx + px) + 3, _snap(cy + py) + 3),
                               theme_mod.u32(CHROME, alpha), 0.0)
    solid(dl, cx, cy, core, phase, spin)
    br = theme_mod.u32(CHROME, 0.75)
    for fx, fy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        _bracket(dl, cx + fx * (half - 3), cy + fy * (half - 3), 7.0,
                 br, flip_x=fx > 0, flip_y=fy > 0)
    if heat > 0.02:
        for i in range(6):
            a = qp * 3.1 + i * 1.047
            rad = core * (1.10 + 0.16 * math.sin(qp * 2.0 + i))
            fx, fy = _snap(cx + math.cos(a) * rad), _snap(cy + math.sin(a) * rad)
            dl.add_rect_filled(ImVec2(fx, fy), ImVec2(fx + 3, fy + 3),
                               theme_mod.u32(CRIMSON, 0.8 * heat), 0.0)
    return True


def background(dl, x, y, w, h, t, now):
    """The chassis: plastic, a CAD grid, granite noise, scanlines, and
    two black-and-white checker strips down the trimmed edges.

    No sky and no landscape. The first version of this theme had both,
    plus a grid running to a vanishing point, and that reads as synthwave
    whatever the palette is - the perspective does it on its own.
    """
    dl.add_rect_filled(ImVec2(x, y), ImVec2(x + w, y + h),
                       theme_mod.u32(PLASTIC), 0.0)
    g = 16.0
    for i in range(int(w / g) + 1):
        dl.add_line(ImVec2(x + i * g, y), ImVec2(x + i * g, y + h),
                    theme_mod.u32(CHROME_SH, 0.17 if i % 5 == 0 else 0.08),
                    1.0)
    for i in range(int(h / g) + 1):
        dl.add_line(ImVec2(x, y + i * g), ImVec2(x + w, y + i * g),
                    theme_mod.u32(CHROME_SH, 0.17 if i % 5 == 0 else 0.08),
                    1.0)
    # granite: enough speckle to read as a surface. 260 points over a
    # window is invisible - it has to be in the low thousands before the
    # eye stops seeing dots and starts seeing a texture.
    _noise(dl, x, y, w, h, theme_mod.u32(ASPHALT, 0.09), n=900)
    _noise(dl, x, y, w, h, theme_mod.u32(CHROME_HI, 0.14), n=620)
    paint.scanlines(dl, x, y, w, h, theme_mod.with_alpha(ASPHALT, 0.05), 3.0)

    # the checker runs down the trim, not through the room: at ten pixels
    # of pitch black against bone it stopped being an edge treatment and
    # started being the loudest thing on screen
    strip = 6.0
    for sx in (x, x + w - strip):
        dl.add_rect_filled(ImVec2(sx, y), ImVec2(sx + strip, y + h),
                           theme_mod.u32(OFFWHITE), 0.0)
        _checker(dl, sx, y, strip, h, theme_mod.u32(CHARCOAL, 0.72), strip)
        dl.add_line(ImVec2(sx + (strip if sx == x else 0.0), y),
                    ImVec2(sx + (strip if sx == x else 0.0), y + h),
                    theme_mod.u32(CHROME_SH, 0.5), 1.0)
    for fy in (0.17, 0.5, 0.83):
        for sx in (x + strip + 7, x + w - strip - 7):
            cy = y + h * fy
            dl.add_line(ImVec2(sx - 4, cy), ImVec2(sx + 4, cy),
                        theme_mod.u32(ASPHALT, 0.45), 1.0)
            dl.add_line(ImVec2(sx, cy - 4), ImVec2(sx, cy + 4),
                        theme_mod.u32(ASPHALT, 0.45), 1.0)
    return True


SKIN = skins.Skin(
    name="ena-world",
    plate=plate, head=head, frame=frame, hover_aura=hover_aura, press=press,
    tabs=tabs, spinner=spinner, background=background,
    corner=lambda t: 0.0,
    press_depth=1.0,
    press_snap=True,          # 0ms, everywhere
    extras={"plastic": PLASTIC, "offwhite": OFFWHITE, "charcoal": CHARCOAL,
            "asphalt": ASPHALT, "chrome": CHROME, "crimson": CRIMSON,
            "olive": OLIVE, "rust": RUST, "bevel": _bevel,
            "checker": _checker, "noise": _noise, "jagged": _jagged,
            "bracket": _bracket, "icon": _pixel_icon, "solid": solid,
            "viewport": viewport, "quantise": _q, "sub": _sub},
)

ENA = profiles.Profile(
    name="ena-world", theme=WORLD, layout=layouts.TABBED,
    face_ui="Tahoma", face_display="Georgia", face_mono="Courier New",
    base_size=15.0, density=0.88,       # dense, and a little claustrophobic
    card_style="raised", card_shadow=True,
    motion=12.0,              # there are no transitions in this theme
    sound_set="crisp", volume=0.14,
    skin=SKIN,
    blurb="A 2000s multimedia CD-ROM - beige plastic, bevels, blood red",
)
