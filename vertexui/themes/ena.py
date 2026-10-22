"""ENA World - webcore: a washed dreamscape with Win95 zinc sitting in it.

The environment, not the character, and the *animations* rather than the
game. That means pale and chalky rather than neon: a bone-coloured void,
dithered skies, flat untextured low-poly shapes with black outlines, and
grey system furniture from 1995 standing in the middle of it as though
nobody thought it odd.

    from vertexui import themes
    app = compose.App(profile=themes.ENA)

This is the toolkit's third light theme and the only grey one. It is also
the one place the Win95 four-tone bevel is drawn properly - white, face,
shadow, black - which is what `zinc` means and is a different object from
Y2K's chrome: that is a dark, loud, gradient-lit 1999, this is a flat,
quiet, dusty 1995 that has been left out in the sun.

Four things carry it:

**Everything is dithered, nothing is smooth.** Gradients are hard bands
with a 50% checker between them, because an 8-bit display could not do
better and the look is built out of that limit. `_dither` does it in
about a thousand rectangles rather than the two hundred thousand a real
per-pixel dither would need.

**Panels are group boxes, not windows.** The title sits in a gap broken
out of the top rule - the Win95 GroupBox - so a screen of panels reads as
a control panel rather than as a desktop. One corner is still cut on a
slant, because the architecture in this world almost obeys.

**Hover is a dotted focus rectangle.** The marching 1px dots and a navy
wash, thresholded so there is no in-between state. Press flips the bevel
and shifts the content a pixel down and right, which is what a real
Win95 button did and why it felt like it moved.

**The spinner is an hourglass**, flat-shaded in chalk with a black
outline and stepped at 12fps, shedding the poses it has already been.
"""

import math

from imgui_bundle import ImVec2, imgui

from .. import fonts, layouts, paint, profiles, skins
from .. import theme as theme_mod
from ..theme import Theme, rgb

# --- palette: chalk, zinc, and one black ---------------------------------
BONE = rgb("#d7d2c4")        # the washed void everything hangs in
GREIGE = rgb("#bab3a2")
ZINC = rgb("#c0c0c0")        # the 1995 button face, to the digit
ZINC_HI = rgb("#ffffff")
ZINC_SH = rgb("#808080")
SOOT = rgb("#17140f")        # the outline on everything
NAVY = rgb("#000080")        # the selection colour of that decade
ROSE = rgb("#c2607a")        # dusty salmon
MUSTARD = rgb("#d2a03c")
MINT = rgb("#7fa89a")
MOSS = rgb("#7d945a")
BRICK = rgb("#a8402f")
LILAC = rgb("#bfb6cb")       # the sky, before it dithers down to rose

WORLD = Theme(
    name="ena-world",
    bg=BONE, panel=GREIGE, surface=ZINC, surface_hover=rgb("#cdcdcd"),
    border=SOOT,
    accent=ROSE, accent_bright=rgb("#d4879c"), accent_dim=rgb("#8d4256"),
    text=rgb("#17140f"), text_dim=rgb("#55503f"), text_mute=rgb("#857e6b"),
    ok=MOSS, warn=MUSTARD, danger=BRICK, info=MINT,
    rounding=0.0, rounding_panel=0.0, border_width=1.0,
)

DROP = 3.0                   # flat offset shadow; 5px reads as soot on bone
STEP = 12.0                  # frames per second the world is allowed
CUT = 14.0                   # the one corner that is not square


def _q(phase, rate=STEP):
    """Quantise to the world's framerate. Everything that moves goes
    through this - a smooth ease and a 12fps step in the same picture
    reads as a bug rather than as a style."""
    return math.floor(phase * rate) / rate


def _snap(v, grid=3.0):
    return math.floor(v / grid) * grid


def _bevel95(dl, x, y, w, h, out=True, face=None):
    """The four-tone border, in the order Windows drew it: an outer pair
    and an inner pair, light down one diagonal and dark down the other.

    Two tones is the common shortcut and it is why most imitations look
    like a flat rectangle with a highlight. The second pair is what makes
    the edge read as a moulding with a thickness.
    """
    if face is not None:
        dl.add_rect_filled(ImVec2(x, y), ImVec2(x + w, y + h),
                           theme_mod.u32(face), 0.0)
    o_hi, o_lo = (ZINC_HI, SOOT) if out else (ZINC_SH, ZINC_HI)
    i_hi, i_lo = (ZINC, ZINC_SH) if out else (SOOT, ZINC)
    for inset, hi, lo in ((0.0, o_hi, o_lo), (1.0, i_hi, i_lo)):
        a, b = x + inset, y + inset
        c, d = x + w - inset, y + h - inset
        dl.add_line(ImVec2(a, b), ImVec2(c, b), theme_mod.u32(hi), 1.0)
        dl.add_line(ImVec2(a, b), ImVec2(a, d), theme_mod.u32(hi), 1.0)
        dl.add_line(ImVec2(a, d - 1), ImVec2(c, d - 1), theme_mod.u32(lo), 1.0)
        dl.add_line(ImVec2(c - 1, b), ImVec2(c - 1, d), theme_mod.u32(lo), 1.0)


# the 4x4 ordered matrix, which is the one every 8-bit display used
_BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def _dither(dl, x, y, w, h, top, bottom, steps=12, cell=6.0):
    """A gradient the way a 256-colour display had to make one: hard
    bands with an ordered checker between each pair.

    A true per-pixel dither over a window is a quarter of a million
    rectangles a frame, which Python will not do. Banding it and
    dithering only the seams costs about a thousand and is
    indistinguishable at this cell size - the blockiness is the point,
    not a compromise.
    """
    band = h / steps
    cols = int(w / cell) + 1
    for i in range(steps):
        k = i / max(1, steps - 1)
        by = y + i * band
        dl.add_rect_filled(ImVec2(x, by), ImVec2(x + w, by + band + 1),
                           theme_mod.u32(theme_mod.lerp(top, bottom, k)), 0.0)
        if i == steps - 1:
            break
        nxt = theme_mod.lerp(top, bottom, (i + 1) / max(1, steps - 1))
        # Four rows at rising thresholds, so the seam crosses over in
        # stages. One row reads as a line and two still read as a line
        # with a shadow; it takes four before the eye gives up and calls
        # it a gradient that a 256-colour display could not quite make.
        # A true per-pixel dither over the sky is ~50k rectangles a frame
        # and Python will not do that, so the bands are few and only the
        # seams are dithered - which at this cell size looks the same.
        for row, lim in ((4, 3), (3, 6), (2, 10), (1, 13)):
            seam = by + band - cell * row
            for c in range(cols):
                if _BAYER[(i + row) % 4][c % 4] > lim:
                    continue
                px = x + c * cell
                dl.add_rect_filled(ImVec2(px, seam),
                                   ImVec2(min(x + w, px + cell), seam + cell),
                                   theme_mod.u32(nxt), 0.0)


def _checker(dl, x, y, w, h, col, cell=10.0, offset=0.0):
    """A flat chess plane. No perspective: the vanishing-point version of
    this is synthwave, which is a different decade and a different mood."""
    rows, cols = int(h / cell) + 2, int(w / cell) + 1
    for r in range(rows):
        for c in range(cols):
            if (r + c) % 2:
                continue
            px, py = x + c * cell, y + r * cell - offset
            if py + cell < y or py > y + h:
                continue
            dl.add_rect_filled(ImVec2(px, max(y, py)),
                               ImVec2(min(x + w, px + cell),
                                      min(y + h, py + cell)), col, 0.0)


def _dotted(dl, x0, y0, x1, y1, col, dash=2.0):
    """The focus rectangle. Every Win95 control had one and nothing since
    has replaced what it did: say *this one* without changing its
    colour, its size or its position."""
    for x in range(int(x0), int(x1), int(dash * 2)):
        dl.add_rect_filled(ImVec2(x, y0), ImVec2(x + dash, y0 + 1), col, 0.0)
        dl.add_rect_filled(ImVec2(x, y1 - 1), ImVec2(x + dash, y1), col, 0.0)
    for y in range(int(y0), int(y1), int(dash * 2)):
        dl.add_rect_filled(ImVec2(x0, y), ImVec2(x0 + 1, y + dash), col, 0.0)
        dl.add_rect_filled(ImVec2(x1 - 1, y), ImVec2(x1, y + dash), col, 0.0)


def _poly(x, y, w, h):
    """Square but for one corner. Only one, and never mirrored - a pair
    of matching cuts comes back round to looking like a deliberate frame,
    and the architecture here should look like it almost obeys."""
    return [ImVec2(x, y), ImVec2(x + w - CUT, y), ImVec2(x + w, y + CUT),
            ImVec2(x + w, y + h), ImVec2(x, y + h)]


# --- painters -----------------------------------------------------------

def plate(dl, x, y, w, h, t, edge, style, shadow):
    """A group box: zinc face, etched rule, one corner off."""
    if style == "flat":
        return False
    body = _poly(x, y, w, h)
    if shadow and style in ("raised", "plated"):
        dl.add_convex_poly_filled([ImVec2(p.x + DROP, p.y + DROP)
                                   for p in body], theme_mod.u32(SOOT, 0.45))
    if style != "outlined":
        dl.add_convex_poly_filled(body, theme_mod.u32(t.surface))
        # a wash of the void coming up through the zinc, dithered
        _checker(dl, x + 2, y + h * 0.52, w - 4, h * 0.48 - 2,
                 theme_mod.u32(GREIGE, 0.55), 8.0)
    _bevel95(dl, x, y, w, h, out=True)
    dl.add_polyline(body + [body[0]], theme_mod.u32(SOOT), 1.0, 0)
    if edge is not None:
        dl.add_rect_filled(ImVec2(x + 3, y + 3), ImVec2(x + 7, y + h - 3),
                           theme_mod.u32(edge), 0.0)
    return True


# Cryptic environmental descriptors - the word, and something that is not
# quite its translation, the way a sign in this world is labelled.
SUB = {
    "status": "境界状態", "state": "境界状態",
    "region": "地域", "map": "地域",
    "signal": "信号", "feed": "信号",
    "archive": "記録", "log": "記録",
    "turbulence": "異次元", "drift": "異次元",
    "depth": "深層", "core": "深層",
    "stability": "安定度", "integrity": "安定度",
    "exits": "出口", "doors": "出口",
    "void": "虚無", "sky": "空",
    "memory": "記憶", "noise": "雑音",
    "readings": "測量", "survey": "測量",
    "jobs": "作業", "tasks": "作業",
}


def _sub(title):
    if not title or not fonts.has("cjk"):
        return ""
    for word in str(title).lower().replace("-", " ").replace("/", " ").split():
        hit = SUB.get(word.strip(":.,"))
        if hit:
            return hit
    return ""


def head(dl, x, y, w, t, icon, title, right, right_col, dot):
    """The Win95 group-box label: the title sits in a gap broken out of
    the top rule, rather than in a bar of its own.

    A title *bar* makes every panel a little window and a screen of them
    a desktop - which Y2K already is. A group box makes the same screen a
    control panel, which is the furniture this world actually has in it.
    """
    gap_x = x + 14.0
    with fonts.use("semi"):
        label = (title or "").upper()
        ts = imgui.calc_text_size(label)
    sub = _sub(title)
    sw = 0.0
    if sub:
        with fonts.use("cjk"):
            sw = imgui.calc_text_size(sub).x + 7.0
    pad = 7.0
    run = ts.x + sw + pad * 2
    ly = y + 12.0

    # the etched rule, broken where the label goes
    for seg in ((x + 5, gap_x - pad), (gap_x + run - pad, x + w - 5 - CUT)):
        if seg[1] - seg[0] < 2:
            continue
        dl.add_line(ImVec2(seg[0], ly), ImVec2(seg[1], ly),
                    theme_mod.u32(ZINC_SH), 1.0)
        dl.add_line(ImVec2(seg[0], ly + 1), ImVec2(seg[1], ly + 1),
                    theme_mod.u32(ZINC_HI), 1.0)
    if dot is not None:
        dl.add_rect_filled(ImVec2(gap_x - 1, ly - 4), ImVec2(gap_x + 7, ly + 4),
                           theme_mod.u32(dot), 0.0)
        dl.add_rect(ImVec2(gap_x - 1, ly - 4), ImVec2(gap_x + 7, ly + 4),
                    theme_mod.u32(SOOT), 0.0, 1.0)
        gap_x += 13.0
    with fonts.use("semi"):
        dl.add_text(ImVec2(gap_x, ly - ts.y * 0.5), theme_mod.u32(t.text),
                    label)
    if sub:
        with fonts.use("cjk"):
            sz = imgui.calc_text_size(sub)
            dl.add_text(ImVec2(gap_x + ts.x + 7, ly - sz.y * 0.5),
                        theme_mod.u32(ROSE), sub)
    if right:
        with fonts.use("mono"):
            rw = imgui.calc_text_size(right)
            rx = x + w - 12 - CUT - rw.x
            dl.add_rect_filled(ImVec2(rx - 5, ly - rw.y * 0.5),
                               ImVec2(rx + rw.x + 4, ly + rw.y * 0.5),
                               theme_mod.u32(t.surface), 0.0)
            dl.add_text(ImVec2(rx, ly - rw.y * 0.5),
                        theme_mod.u32(right_col if right_col is not None
                                      else t.text_dim), right)
    return y + 26.0


def frame(dl, x, y, w, h, t, kind):
    """Raised keys and sunken fields, both with the full bevel."""
    if kind == "input":
        _bevel95(dl, x, y, w, h, out=False, face=rgb("#ffffff"))
        return True
    if not kind.startswith("button"):
        return False
    primary = kind.endswith("primary")
    _bevel95(dl, x, y, w, h, out=True, face=ROSE if primary else ZINC)
    dl.add_rect(ImVec2(x, y), ImVec2(x + w, y + h), theme_mod.u32(SOOT),
                0.0, 1.0)
    return True


def hover_aura(dl, x0, y0, x1, y1, t, amount, kind):
    """A dotted focus rectangle and a navy wash, with nothing in between.

    `amount` arrives eased and is thresholded away: this furniture has no
    intermediate states, and a glow would be a lighting effect in a
    picture that has no lights in it.
    """
    if amount < 0.5:
        return
    dl.add_rect_filled(ImVec2(x0 + 2, y0 + 2), ImVec2(x1 - 2, y1 - 2),
                       theme_mod.u32(NAVY, 0.14), 0.0)
    _dotted(dl, x0 + 3, y0 + 3, x1 - 3, y1 - 3, theme_mod.u32(SOOT, 0.85))


def press(dl, x0, y0, x1, y1, t, amount):
    """The bevel flips and the face moves a pixel down and right, which
    is the whole reason a 1995 button felt like it travelled."""
    if amount < 0.5:
        return
    _bevel95(dl, x0, y0, x1 - x0, y1 - y0, out=False)
    dl.add_rect_filled(ImVec2(x0 + 2, y0 + 2), ImVec2(x1 - 2, y1 - 2),
                       theme_mod.u32(ZINC_SH, 0.22), 0.0)


def tabs(dl, x, y, w, h, t, rects, index, hots):
    """A tab control: the live one stands a little taller and breaks the
    line into the body, so the page below is visibly the same object."""
    if not rects:
        return False
    base = y + h
    for i, (tx, tw) in enumerate(rects):
        on = i == index
        ty = y + (0.0 if on else 3.0)
        th = h - (0.0 if on else 3.0)
        face = (rgb("#d2d2d2") if on
                else theme_mod.lerp(GREIGE, ZINC, 0.1 + 0.35 * hots[i]))
        _bevel95(dl, tx, ty, tw, th + 2, out=True, face=face)
        dl.add_rect(ImVec2(tx, ty), ImVec2(tx + tw, ty + th + 2),
                    theme_mod.u32(SOOT), 0.0, 1.0)
        if on:
            dl.add_rect_filled(ImVec2(tx + 2, base - 1),
                               ImVec2(tx + tw - 2, base + 2),
                               theme_mod.u32(rgb("#d2d2d2")), 0.0)
            dl.add_rect_filled(ImVec2(tx + 3, y + 3), ImVec2(tx + tw - 3,
                                                             y + 5),
                               theme_mod.u32(ROSE), 0.0)
    dl.add_line(ImVec2(x - 10, base), ImVec2(x + w + 10, base),
                theme_mod.u32(SOOT), 1.0)
    return True


# an octahedron squeezed toward an hourglass, and the faces that wrap it
_V = ((0.0, 1.0, 0.0), (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (-1.0, 0.0, 0.0),
      (0.0, 0.0, 1.0), (0.0, 0.0, -1.0))
_F = ((0, 2, 4), (0, 4, 3), (0, 3, 5), (0, 5, 2),
      (1, 4, 2), (1, 3, 4), (1, 5, 3), (1, 2, 5))
CHALK = (rgb("#efe9da"), ROSE, MUSTARD, rgb("#52786d"), rgb("#7e7769"),
         MOSS, rgb("#9c4a62"), rgb("#4a463c"))


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


def spinner(dl, cx, cy, r, t, phase, spin=1.0):
    """An hourglass, flat-shaded in chalk and stepped at 12fps.

    Flat means flat: one solid colour per face off a fixed chalk set, a
    black outline on every edge, and no light source anywhere - which is
    what an untextured 1995 polygon actually looked like and is why
    shading it by a normal would have been wrong.

    The stutter is the rotation itself, not a filter over a smooth one,
    so a faster spin covers more angle per step and the solid comes apart
    into poses instead of blurring.
    """
    heat = max(0.0, min(1.0, (spin - 1.0) / 4.0))
    core = r * 0.92
    qp = _q(phase)

    _checker(dl, cx - core * 0.85, cy + core * 0.98, core * 1.7, 5.0,
             theme_mod.u32(SOOT, 0.35), 5.0)

    for back, alpha in ((2.0 / STEP, 0.16), (1.0 / STEP, 0.30)):
        for px, py, _pz in _project((qp - back) * 1.7, (qp - back) * 2.6,
                                    core):
            dl.add_rect_filled(ImVec2(_snap(cx + px), _snap(cy + py)),
                               ImVec2(_snap(cx + px) + 3, _snap(cy + py) + 3),
                               theme_mod.u32(SOOT, alpha), 0.0)

    pts = _project(qp * 1.7, qp * 2.6, core)
    faces = []
    for n, (a, b, c) in enumerate(_F):
        ax, ay, _ = pts[a]
        bx, by, _ = pts[b]
        kx, ky, _ = pts[c]
        if (bx - ax) * (ky - ay) - (by - ay) * (kx - ax) <= 0:
            continue          # back-facing, from the projected winding
        faces.append(((pts[a][2] + pts[b][2] + pts[c][2]) / 3.0, n,
                      (ax, ay), (bx, by), (kx, ky)))
    faces.sort(key=lambda f: f[0])
    for _d, n, pa, pb, pc in faces:
        va = ImVec2(cx + pa[0], cy + pa[1])
        vb = ImVec2(cx + pb[0], cy + pb[1])
        vc = ImVec2(cx + pc[0], cy + pc[1])
        dl.add_triangle_filled(va, vb, vc, theme_mod.u32(CHALK[n]))
        dl.add_triangle(va, vb, vc, theme_mod.u32(SOOT), 1.2)

    if heat > 0.02:
        for i in range(8):
            a = qp * 3.1 + i * 0.785
            rad = core * (1.22 + 0.30 * math.sin(qp * 2.0 + i))
            fx, fy = _snap(cx + math.cos(a) * rad), _snap(cy + math.sin(a) * rad)
            dl.add_rect_filled(ImVec2(fx, fy), ImVec2(fx + 3, fy + 3),
                               theme_mod.u32(SOOT, 0.75 * heat), 0.0)
    return True


# flat silhouettes on the horizon: (x share, width share, height share)
SKYLINE = ((0.07, 0.06, 0.26), (0.18, 0.035, 0.14), (0.31, 0.08, 0.38),
           (0.49, 0.045, 0.19), (0.62, 0.10, 0.31), (0.79, 0.055, 0.23),
           (0.92, 0.07, 0.16))


def _dingbat(dl, x, y, s, kind, col):
    """Clip art. Every page in 1996 had some and none of it was explained,
    which is the exact register this world's signage is in."""
    if kind == 0:                                   # a star
        pts = []
        for i in range(10):
            rr = s * (0.5 if i % 2 else 1.0)
            a = -math.pi / 2 + i * math.pi / 5
            pts.append(ImVec2(x + math.cos(a) * rr, y + math.sin(a) * rr))
        dl.add_concave_poly_filled(pts, col)
    elif kind == 1:                                 # a right-pointing arrow
        dl.add_convex_poly_filled(
            [ImVec2(x - s, y - s * 0.35), ImVec2(x, y - s * 0.35),
             ImVec2(x, y - s * 0.8), ImVec2(x + s, y),
             ImVec2(x, y + s * 0.8), ImVec2(x, y + s * 0.35),
             ImVec2(x - s, y + s * 0.35)], col)
    else:                                           # a lozenge
        dl.add_convex_poly_filled(
            [ImVec2(x, y - s), ImVec2(x + s, y), ImVec2(x, y + s),
             ImVec2(x - s, y)], col)


def background(dl, x, y, w, h, t, now):
    """A dithered sky, a flat chequer plane, leaning shapes and clip art.

    The floor does not recede to a point. A perspective grid running to a
    vanishing point is synthwave - a different decade and a much louder
    mood - and it was the single thing that made the first version of
    this theme read as cyberpunk rather than as webcore.
    """
    horizon = y + h * 0.56
    _dither(dl, x, y, w, horizon - y, LILAC, rgb("#e3ad9c"), steps=5,
            cell=8.0)
    dl.add_rect_filled(ImVec2(x, horizon), ImVec2(x + w, y + h),
                       theme_mod.u32(BONE), 0.0)

    for fx, fw, fh in SKYLINE:
        bw, bh = w * fw, (horizon - y) * fh
        bx = x + w * fx - bw * 0.5
        top = horizon - bh
        lean = bw * (0.20 if int(fx * 100) % 2 else -0.20)
        body = [ImVec2(bx + lean, top), ImVec2(bx + bw + lean, top + bh * 0.07),
                ImVec2(bx + bw, horizon), ImVec2(bx, horizon)]
        dl.add_convex_poly_filled(body, theme_mod.u32(rgb("#8c8294")))
        side = bw * 0.34
        dl.add_convex_poly_filled(
            [ImVec2(bx + bw + lean - side, top + bh * 0.05),
             ImVec2(bx + bw + lean, top + bh * 0.07),
             ImVec2(bx + bw, horizon), ImVec2(bx + bw - side, horizon)],
            theme_mod.u32(rgb("#6d6477")))
        dl.add_polyline(body + [body[0]], theme_mod.u32(SOOT, 0.85), 1.0, 0)

    # the floor: flat tiles, scrolling on the world's own stuttering clock
    _checker(dl, x, horizon, w, y + h - horizon,
             theme_mod.u32(rgb("#6f6a5e"), 0.78), 26.0,
             offset=(_q(now, STEP) * 6.0) % 52.0)
    dl.add_line(ImVec2(x, horizon), ImVec2(x + w, horizon),
                theme_mod.u32(SOOT, 0.7), 1.0)

    # Web 1.0 marginalia, parked where content does not reach
    for i, (fx, fy, k, col) in enumerate((
            (0.021, 0.20, 0, MUSTARD), (0.016, 0.74, 2, ROSE),
            (0.982, 0.31, 1, MINT), (0.977, 0.83, 0, MOSS))):
        _dingbat(dl, x + w * fx, y + h * fy, 8.0, k, theme_mod.u32(col, 0.9))
    # the hazard bar every unfinished page had along the bottom
    paint.hatch(dl, x, y + h - 9, w, 9, theme_mod.u32(MUSTARD, 0.75), 9.0, 4.0)
    dl.add_line(ImVec2(x, y + h - 10), ImVec2(x + w, y + h - 10),
                theme_mod.u32(SOOT, 0.6), 1.0)
    return True


SKIN = skins.Skin(
    name="ena-world",
    plate=plate, head=head, frame=frame, hover_aura=hover_aura, press=press,
    tabs=tabs, spinner=spinner, background=background,
    corner=lambda t: 0.0,
    press_depth=1.0,
    press_snap=True,          # 1995 buttons did not ease either
    extras={"bone": BONE, "zinc": ZINC, "soot": SOOT, "navy": NAVY,
            "rose": ROSE, "mint": MINT, "mustard": MUSTARD, "moss": MOSS,
            "bevel": _bevel95, "dither": _dither, "checker": _checker,
            "dotted": _dotted, "quantise": _q, "sub": _sub},
)

ENA = profiles.Profile(
    name="ena-world", theme=WORLD, layout=layouts.TABBED,
    face_ui="Tahoma", face_display="Impact", face_mono="Courier New",
    base_size=15.5, density=0.92,
    card_style="raised", card_shadow=True,
    motion=3.2,               # what little eases, eases fast
    sound_set="crisp", volume=0.14,
    skin=SKIN,
    blurb="Webcore - a dithered chalk dreamscape with Win95 zinc in it",
)
