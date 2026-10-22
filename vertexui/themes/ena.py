"""ENA World - a PS1 outworld: chess-grid floors and reality corruption.

The environment, not the character. Deep dreamcore indigo, low-poly
violet marble, uncanny slate, and two accents that do not belong in the
same room: magenta corruption and sky cyan. Zero radius anywhere, 2px
absolute-black borders, and hard 5px offset shadows with no blur in them,
because a 1998 renderer had no blur to give.

    from vertexui import themes
    app = compose.App(profile=themes.ENA)

Three things carry the identity:

**Nothing is square on all four corners.** Panels take an asymmetric
polygon - a large chamfer at one corner, a small one diagonally opposite
- and a hard diagonal division cuts across the body. Surrealist
architecture is buildings that *almost* obey, so a panel that is merely
rectangular reads as software; one cut on a slant reads as a place.

**Everything stutters at 12fps.** The floor scrolls, the monolith turns
and the static re-seeds on a quantised clock, while the rest of the
toolkit eases at whatever the profile says. This is the opposite of YMO,
whose ground does not move at all, and of Aero, which never stops
easing: here motion exists but it is not allowed to be smooth.

**Hover is a 1-bit inversion.** No glow, no fade, no interpolation -
the control flips to white ink, a magenta ghost of it appears offset,
and it snaps back. `press_snap` is on for the same reason.

The spinner is a low-poly monolith: a real octahedron rotated in three
dimensions, back-face culled, flat-shaded between cyan and magenta by
face normal, stepped at 12fps and shedding pixelated fragments of the
frames it has already been.
"""

import math

from imgui_bundle import ImVec2, imgui

from .. import fonts, layouts, paint, profiles, skins
from .. import theme as theme_mod
from ..theme import Theme, rgb

# --- palette ------------------------------------------------------------
VOID = rgb("#120a2a")        # cosmic void, the night the world hangs in
MARBLE = rgb("#2a1b40")      # morphic marble, the primary panel
SLATE = rgb("#1a2636")       # grid realm, the retro terminal frame
MAGENTA = rgb("#e6005c")     # reality corruption
CYAN = rgb("#00f0ff")        # low-poly sky
WHITE = rgb("#ffffff")
INK = rgb("#000000")         # absolute, not "very dark" - that is the look

WORLD = Theme(
    name="ena-world",
    bg=VOID, panel=SLATE, surface=MARBLE,
    surface_hover=rgb("#3c2a58"), border=INK,
    accent=MAGENTA, accent_bright=rgb("#ff3d85"), accent_dim=rgb("#5c0025"),
    text=WHITE, text_dim=rgb("#a99fc4"), text_mute=rgb("#6c6390"),
    ok=CYAN, warn=rgb("#ffd400"), danger=MAGENTA, info=CYAN,
    rounding=0.0, rounding_panel=0.0, border_width=2.0,
)

DROP = 5.0                   # the offset shadow, exactly as specified
EDGE = 2.0                   # every border, everywhere
STEP = 12.0                  # frames per second the world is allowed


def _q(phase, rate=STEP):
    """Quantise a phase to the world's framerate. Everything that moves
    goes through this - a smooth easing curve and a 12fps rotation in the
    same picture reads as a bug, not as a style."""
    return math.floor(phase * rate) / rate


def _snap(v, grid=3.0):
    """Nail a coordinate to a low-resolution grid, which is what makes a
    trail fragment read as a pixel rather than as a small square."""
    return math.floor(v / grid) * grid


def _poly(x, y, w, h, big=18.0, small=7.0):
    """The panel outline: a large chamfer top-right, a small one bottom-
    left. Asymmetric on purpose - mirrored cuts come back round to
    looking like a deliberate frame, and this should not look framed."""
    return [ImVec2(x, y), ImVec2(x + w - big, y), ImVec2(x + w, y + big),
            ImVec2(x + w, y + h), ImVec2(x + small, y + h),
            ImVec2(x, y + h - small)]


def _checker(dl, x, y, w, h, col, cell=10.0, phase=0.0):
    """A chess grid, clipped to a box. Drawn as the dark squares only, so
    whatever is underneath shows through the light ones."""
    off = _q(phase) * cell * 2.0 % (cell * 2.0)
    rows = int(h / cell) + 2
    cols = int(w / cell) + 2
    for r in range(rows):
        for c in range(cols):
            if (r + c) % 2:
                continue
            px, py = x + c * cell, y + r * cell - off
            if py + cell < y or py > y + h:
                continue
            dl.add_rect_filled(ImVec2(px, max(y, py)),
                               ImVec2(min(x + w, px + cell),
                                      min(y + h, py + cell)), col, 0.0)


def _static(dl, x, y, w, h, now, col_a, col_b, n=140):
    """Dithered static. Deterministic from an integer seed so the field
    is stable within a frame step and jumps between them - television
    noise, not a particle system."""
    seed = int(_q(now, 6.0) * 6.0) & 0xFFFF
    for i in range(n):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        px = x + (seed >> 7) % max(1, int(w))
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        py = y + (seed >> 7) % max(1, int(h))
        dl.add_rect_filled(ImVec2(px, py), ImVec2(px + 2, py + 2),
                           col_a if (seed & 7) else col_b, 0.0)


# --- painters -----------------------------------------------------------

def plate(dl, x, y, w, h, t, edge, style, shadow):
    """A slab of the world: cut polygon, black ink, a shadow with no blur."""
    if style == "flat":
        return False
    body = _poly(x, y, w, h)
    if shadow and style in ("raised", "plated"):
        dl.add_convex_poly_filled([ImVec2(p.x + DROP, p.y + DROP)
                                   for p in body], theme_mod.u32(INK))
    if style != "outlined":
        dl.add_convex_poly_filled(body, theme_mod.u32(t.surface))
        # the grid realm bleeding through the marble, very low
        _checker(dl, x + EDGE, y + EDGE, w - EDGE * 2, h - EDGE * 2,
                 theme_mod.u32(INK, 0.16), 9.0)
        paint.grad_rect(dl, x + EDGE, y + h * 0.45, w - EDGE * 2,
                        h * 0.55 - EDGE, theme_mod.with_alpha(VOID, 0.0),
                        theme_mod.with_alpha(VOID, 0.55), 0.0)
    # the hard diagonal division - surrealist architecture, one slant
    dl.add_line(ImVec2(x + w * 0.58, y + h), ImVec2(x + w, y + h * 0.34),
                theme_mod.u32(CYAN, 0.22), 1.0)
    dl.add_polyline(body + [body[0]], theme_mod.u32(INK), EDGE, 0)
    if edge is not None:
        dl.add_rect_filled(ImVec2(x + EDGE, y + EDGE),
                           ImVec2(x + EDGE + 5, y + h - EDGE),
                           theme_mod.u32(edge), 0.0)
    return True


# Cryptic environmental descriptors, the way a sign in this world is
# labelled: the word, and something that is not quite its translation.
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
    "jobs": "作業", "tasks": "作業",
    "survey": "測量", "readings": "測量",
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
    """A black signboard with a cut corner and a sub-header that is not
    quite a translation."""
    bar = 26.0
    bx, by, bw = x + EDGE, y + EDGE, w - EDGE * 2
    cut = 14.0
    dl.add_convex_poly_filled(
        [ImVec2(bx, by), ImVec2(bx + bw, by), ImVec2(bx + bw, by + bar - cut),
         ImVec2(bx + bw - cut, by + bar), ImVec2(bx, by + bar)],
        theme_mod.u32(INK))
    if dot is not None:
        dl.add_rect_filled(ImVec2(bx + 7, by + bar * 0.5 - 4),
                           ImVec2(bx + 15, by + bar * 0.5 + 4),
                           theme_mod.u32(dot), 0.0)
    tx = bx + (22.0 if dot is not None else 9.0)
    with fonts.use("title"):
        label = (title or "").upper()
        ts = imgui.calc_text_size(label)
        dl.add_text(ImVec2(tx + 1, by + (bar - ts.y) * 0.5 + 1),
                    theme_mod.u32(MAGENTA, 0.8), label)   # 1px misregister
        dl.add_text(ImVec2(tx, by + (bar - ts.y) * 0.5),
                    theme_mod.u32(WHITE), label)
    sub = _sub(title)
    if sub:
        with fonts.use("cjk"):
            sz = imgui.calc_text_size(sub)
            dl.add_text(ImVec2(tx + ts.x + 10, by + (bar - sz.y) * 0.5),
                        theme_mod.u32(CYAN, 0.85), sub)
    if right:
        with fonts.use("mono"):
            rw = imgui.calc_text_size(right)
            dl.add_text(ImVec2(bx + bw - 16 - rw.x, by + (bar - rw.y) * 0.5),
                        theme_mod.u32(right_col if right_col is not None
                                      else CYAN), right)
    dl.add_rect_filled(ImVec2(bx, by + bar), ImVec2(bx + bw, by + bar + 2),
                       theme_mod.u32(MAGENTA, 0.9), 0.0)
    return y + bar + 12.0


def frame(dl, x, y, w, h, t, kind):
    """Blocks with ink borders and a shadow that has no blur in it."""
    if kind == "input":
        dl.add_rect_filled(ImVec2(x, y), ImVec2(x + w, y + h),
                           theme_mod.u32(SLATE), 0.0)
        _checker(dl, x, y, w, h, theme_mod.u32(INK, 0.22), 7.0)
        dl.add_rect(ImVec2(x, y), ImVec2(x + w, y + h), theme_mod.u32(INK),
                    0.0, EDGE)
        dl.add_rect_filled(ImVec2(x, y + h - 2), ImVec2(x + w, y + h),
                           theme_mod.u32(CYAN, 0.45), 0.0)
        return True
    if not kind.startswith("button"):
        return False
    primary = kind.endswith("primary")
    cut = min(10.0, h * 0.42)
    body = [ImVec2(x, y), ImVec2(x + w - cut, y), ImVec2(x + w, y + cut),
            ImVec2(x + w, y + h), ImVec2(x + cut, y + h),
            ImVec2(x, y + h - cut)]
    dl.add_convex_poly_filled([ImVec2(p.x + 4, p.y + 4) for p in body],
                              theme_mod.u32(INK))
    dl.add_convex_poly_filled(body, theme_mod.u32(MAGENTA if primary
                                                  else MARBLE))
    if not primary:
        _checker(dl, x + EDGE, y + EDGE, w - EDGE * 2, h - EDGE * 2,
                 theme_mod.u32(INK, 0.18), 7.0)
    dl.add_polyline(body + [body[0]], theme_mod.u32(INK), EDGE, 0)
    return True


def hover_aura(dl, x0, y0, x1, y1, t, amount, kind):
    """A 1-bit inversion and a hard translation, with nothing in between.

    `amount` arrives eased, so it is thresholded away: this interface
    does not have intermediate states. What is left is the control's
    ghost shifted three pixels in magenta, a white keyline over it, and
    corruption bars torn out of the top edge.
    """
    if amount < 0.5:
        return
    dl.add_rect(ImVec2(x0 + 3, y0 + 3), ImVec2(x1 + 3, y1 + 3),
                theme_mod.u32(MAGENTA), 0.0, EDGE)
    dl.add_rect(ImVec2(x0 - 1, y0 - 1), ImVec2(x1 + 1, y1 + 1),
                theme_mod.u32(WHITE), 0.0, EDGE)
    # torn bands, snapped to the low-resolution grid
    h = y1 - y0
    for i, f in enumerate((0.18, 0.46, 0.74)):
        yy = _snap(y0 + h * f, 3.0)
        dl.add_rect_filled(ImVec2(x0 + 4 + i * 9, yy),
                           ImVec2(x0 + 4 + i * 9 + 16, yy + 3),
                           theme_mod.u32(CYAN if i % 2 else MAGENTA, 0.9), 0.0)


def press(dl, x0, y0, x1, y1, t, amount):
    """translate(3px, 3px): the block lands on its own shadow."""
    if amount < 0.5:
        return
    dl.add_rect_filled(ImVec2(x0, y0), ImVec2(x1, y1),
                       theme_mod.u32(INK, 0.45), 0.0)
    dl.add_rect(ImVec2(x0, y0), ImVec2(x1, y1), theme_mod.u32(CYAN), 0.0, EDGE)


def tabs(dl, x, y, w, h, t, rects, index, hots):
    """Doors along a street: blocks on ink, the open one in corruption."""
    if not rects:
        return False
    dl.add_rect_filled(ImVec2(x - 10, y - 3), ImVec2(x + w + 10, y + h + 5),
                       theme_mod.u32(INK), 0.0)
    for i, (tx, tw) in enumerate(rects):
        on = i == index
        cut = 11.0
        body = [ImVec2(tx, y), ImVec2(tx + tw - cut, y),
                ImVec2(tx + tw, y + cut), ImVec2(tx + tw, y + h),
                ImVec2(tx, y + h)]
        fill = MAGENTA if on else (SLATE if hots[i] < 0.5 else MARBLE)
        dl.add_convex_poly_filled(body, theme_mod.u32(fill))
        if not on:
            _checker(dl, tx + EDGE, y + EDGE, tw - EDGE * 2, h - EDGE * 2,
                     theme_mod.u32(INK, 0.3), 7.0)
        dl.add_polyline(body + [body[0]], theme_mod.u32(INK), EDGE, 0)
        if on:
            dl.add_rect_filled(ImVec2(tx, y + h - 3),
                               ImVec2(tx + tw, y + h), theme_mod.u32(CYAN), 0.0)
    return True


# an octahedron, and the eight faces that wrap it
_V = ((0.0, 1.0, 0.0), (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (-1.0, 0.0, 0.0),
      (0.0, 0.0, 1.0), (0.0, 0.0, -1.0))
_F = ((0, 2, 4), (0, 4, 3), (0, 3, 5), (0, 5, 2),
      (1, 4, 2), (1, 3, 4), (1, 5, 3), (1, 2, 5))


def _project(ax, ay, r):
    """Rotate the solid and flatten it. Orthographic, because perspective
    on something this small is a rounding error with extra arithmetic."""
    ca, sa = math.cos(ay), math.sin(ay)
    cb, sb = math.cos(ax), math.sin(ax)
    out = []
    for vx, vy, vz in _V:
        vx, vy, vz = vx * 0.86, vy * 1.32, vz * 0.86     # toward an hourglass
        x1, z1 = vx * ca + vz * sa, -vx * sa + vz * ca
        y1, z2 = vy * cb - z1 * sb, vy * sb + z1 * cb
        out.append((x1 * r, y1 * r, z2))
    return out


def spinner(dl, cx, cy, r, t, phase, spin=1.0):
    """A low-poly monolith, stepped at 12fps and shedding what it was.

    The stutter is the point and it is not a filter over a smooth
    animation: the rotation itself is quantised, so a faster spin covers
    more angle per step and the thing visibly comes apart into poses
    rather than blurring. Trail fragments are the previous steps'
    vertices snapped to a 3px grid, which is what makes them read as
    pixels instead of as small squares.
    """
    heat = max(0.0, min(1.0, (spin - 1.0) / 4.0))
    core = r * 0.95
    qp = _q(phase)

    # the shadow the monolith throws on the grid, also stepped
    dl.add_rect_filled(ImVec2(cx - core * 0.7, cy + core * 0.95),
                       ImVec2(cx + core * 0.7, cy + core * 1.15),
                       theme_mod.u32(INK, 0.55), 0.0)

    # what it was, one and two steps ago
    for back, alpha in ((2.0 / STEP, 0.20), (1.0 / STEP, 0.38)):
        pts = _project((qp - back) * 1.7, (qp - back) * 2.6, core)
        col = theme_mod.u32(MAGENTA if heat > 0.5 else CYAN,
                            alpha * (0.5 + 0.5 * heat))
        for px, py, _pz in pts:
            dl.add_rect_filled(ImVec2(_snap(cx + px), _snap(cy + py)),
                               ImVec2(_snap(cx + px) + 3, _snap(cy + py) + 3),
                               col, 0.0)

    pts = _project(qp * 1.7, qp * 2.6, core)
    faces = []
    for a, b, c in _F:
        ax, ay, _ = pts[a]
        bx, by, _ = pts[b]
        kx, ky, _ = pts[c]
        # back-face cull from the winding of the projected triangle
        if (bx - ax) * (ky - ay) - (by - ay) * (kx - ax) <= 0:
            continue
        depth = (pts[a][2] + pts[b][2] + pts[c][2]) / 3.0
        faces.append((depth, (ax, ay), (bx, by), (kx, ky)))
    faces.sort(key=lambda f: f[0])
    for depth, pa, pb, pc in faces:
        k = max(0.0, min(1.0, (depth + 1.0) * 0.5))
        shade = theme_mod.lerp(CYAN, MAGENTA, k)
        shade = theme_mod.lerp(INK, shade, 0.62 + 0.38 * k)
        dl.add_triangle_filled(ImVec2(cx + pa[0], cy + pa[1]),
                               ImVec2(cx + pb[0], cy + pb[1]),
                               ImVec2(cx + pc[0], cy + pc[1]),
                               theme_mod.u32(shade))
        dl.add_triangle(ImVec2(cx + pa[0], cy + pa[1]),
                        ImVec2(cx + pb[0], cy + pb[1]),
                        ImVec2(cx + pc[0], cy + pc[1]),
                        theme_mod.u32(INK, 0.8), 1.0)

    if heat > 0.02:
        # at speed the world stops keeping up: fragments tear off sideways
        for i in range(8):
            a = (qp * 3.1 + i * 0.785)
            rad = core * (1.25 + 0.35 * math.sin(qp * 2.0 + i))
            fx, fy = _snap(cx + math.cos(a) * rad), _snap(cy + math.sin(a) * rad)
            dl.add_rect_filled(ImVec2(fx, fy), ImVec2(fx + 3, fy + 3),
                               theme_mod.u32(MAGENTA if i % 2 else CYAN,
                                             0.85 * heat), 0.0)
    return True


# silhouettes on the horizon: (x share, width share, height share)
SKYLINE = ((0.06, 0.07, 0.30), (0.19, 0.04, 0.17), (0.32, 0.09, 0.44),
           (0.50, 0.05, 0.22), (0.63, 0.11, 0.36), (0.80, 0.06, 0.26),
           (0.91, 0.08, 0.19))


def background(dl, x, y, w, h, t, now):
    """The outworld: a dithered sky, a chess floor running to a horizon,
    impossible architecture standing on it, and static over everything.

    The floor scrolls on the same 12fps clock as the monolith, so the
    whole place moves as one object with a bad framerate rather than as
    several things animating independently.
    """
    dl.add_rect_filled(ImVec2(x, y), ImVec2(x + w, y + h),
                       theme_mod.u32(VOID), 0.0)
    horizon = y + h * 0.52
    paint.grad_rect(dl, x, y, w, horizon - y, VOID, rgb("#2e1050"), 0.0)
    paint.dots(dl, x, y, w, horizon - y, theme_mod.u32(WHITE, 0.07), 17.0)

    for fx, fw, fh in SKYLINE:
        bw, bh = w * fw, (horizon - y) * fh
        bx = x + w * fx - bw * 0.5
        top = horizon - bh
        # each one leans: nothing here stands straight
        lean = bw * (0.22 if int(fx * 100) % 2 else -0.22)
        dl.add_convex_poly_filled(
            [ImVec2(bx + lean, top), ImVec2(bx + bw + lean, top + bh * 0.08),
             ImVec2(bx + bw, horizon), ImVec2(bx, horizon)],
            theme_mod.u32(rgb("#0b0618")))

    # the grid realm, running to a vanishing point. Each row's half-width
    # is a function of its own depth, which is what makes the columns
    # converge; spacing the columns evenly and scaling the row instead
    # gives a staircase, which is what this did first.
    rows, cols = 15, 16
    floor = y + h - horizon
    scroll = _q(now, STEP) % 1.0
    cx = x + w * 0.5
    for i in range(rows):
        f0 = ((i + scroll) / rows) ** 2.4
        f1 = ((i + 1 + scroll) / rows) ** 2.4
        y0, y1 = horizon + floor * f0, horizon + floor * f1
        if y1 <= horizon or y0 >= y + h:
            continue
        hw0, hw1 = w * (0.03 + 1.25 * f0), w * (0.03 + 1.25 * f1)
        band = theme_mod.u32(rgb("#2a1a4c"), 0.30 + 0.55 * f0)
        for c in range(cols):
            if (c + i) % 2:
                continue
            a0, a1 = c / cols - 0.5, (c + 1) / cols - 0.5
            dl.add_convex_poly_filled(
                [ImVec2(cx + a0 * 2 * hw0, y0), ImVec2(cx + a1 * 2 * hw0, y0),
                 ImVec2(cx + a1 * 2 * hw1, y1), ImVec2(cx + a0 * 2 * hw1, y1)],
                band)
    dl.add_rect_filled(ImVec2(x, horizon - 1), ImVec2(x + w, horizon + 1),
                       theme_mod.u32(CYAN, 0.55), 0.0)

    _static(dl, x, y, w, h, now, theme_mod.u32(WHITE, 0.10),
            theme_mod.u32(MAGENTA, 0.16))
    paint.scanlines(dl, x, y, w, h, theme_mod.with_alpha(INK, 0.16), 3.0)
    return True


SKIN = skins.Skin(
    name="ena-world",
    plate=plate, head=head, frame=frame, hover_aura=hover_aura, press=press,
    tabs=tabs, spinner=spinner, background=background,
    corner=lambda t: 0.0,
    press_depth=3.0,
    press_snap=True,          # no interpolation anywhere in this world
    extras={"void": VOID, "marble": MARBLE, "slate": SLATE, "ink": INK,
            "magenta": MAGENTA, "cyan": CYAN, "white": WHITE,
            "checker": _checker, "quantise": _q, "snap": _snap, "sub": _sub},
)

ENA = profiles.Profile(
    name="ena-world", theme=WORLD, layout=layouts.TABBED,
    face_ui="Verdana", face_display="Impact", face_mono="Courier New",
    base_size=16.0, density=0.96,
    card_style="raised", card_shadow=True,
    motion=3.2,               # what little eases, eases fast
    sound_set="crisp", volume=0.15,
    skin=SKIN,
    blurb="A PS1 outworld - chess-grid floors, 12fps stutter, 1-bit hover",
)
