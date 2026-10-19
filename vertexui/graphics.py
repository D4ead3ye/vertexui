"""Drawn data graphics - the part that stops a panel being a list of text.

Every one of these is drawn on the draw list from the theme's own colours,
takes layout space like any other item, and needs no plotting library, no
texture and no asset. They exist because the quickest way to make two
tools built on one toolkit look like two different tools is to let each
one show its data in the shape that data actually has.

    graphics.sparkline(history, 200, 34)
    graphics.gauge(temp, 0, 300, label="NOZZLE", unit="C")
    graphics.levels([l, r], 120, 70)

Sizes: pass `width=0` to fill the available width. Everything advances the
cursor, so these sit in a column with ordinary widgets and inside cards.

A note on argument order, because it has cost this codebase real time:
this binding is `add_rect(p_min, p_max, col, rounding, thickness, flags)`,
`add_polyline(points, col, thickness, flags)` with no defaults, and
`path_stroke(col, thickness, flags)` - none of which match the C++ order.
"""

import math

import numpy as np
from imgui_bundle import ImVec2, imgui

from . import fonts
from . import theme as theme_mod


def series_colours(t=None, n=6):
    """Distinguishable colours drawn from the theme, in a stable order.

    Derived rather than listed, so a project that swaps the accent gets a
    set that still belongs to its palette.
    """
    t = t or theme_mod.current()
    base = [t.accent, t.info, t.ok, t.warn, t.accent_bright,
            theme_mod.lerp(t.info, t.text, 0.45)]
    return [base[i % len(base)] for i in range(n)]


def _col(c, a=1.0):
    return imgui.get_color_u32(theme_mod.with_alpha(c, a))


def _span(values, lo, hi):
    """Range to plot over, never zero-width."""
    v = np.asarray(values, dtype=np.float64)
    a = float(np.min(v)) if lo is None else float(lo)
    b = float(np.max(v)) if hi is None else float(hi)
    if b - a < 1e-9:
        a, b = a - 0.5, b + 0.5
    return a, b


def _ground(dl, o, w, h, t, alpha=0.5, rounding=None):
    r = t.rounding * 0.6 if rounding is None else rounding
    dl.add_rect_filled(ImVec2(o.x, o.y), ImVec2(o.x + w, o.y + h),
                       _col(theme_mod.sink(t.surface, 0.5, t), alpha), r)


def _avail(width):
    return width if width > 0 else max(24.0, imgui.get_content_region_avail().x)


def _under(dl, pts, base_y, col):
    """Fill between a polyline and a baseline.

    Not `add_convex_poly_filled`: the area under a wiggly line is not
    convex, and that call assumes it is - the result is a fan of wedges
    radiating from the first vertex rather than a fill. Quads per segment
    are convex by construction and cost the same.
    """
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        dl.add_quad_filled(ImVec2(a.x, a.y), ImVec2(b.x, b.y),
                           ImVec2(b.x, base_y), ImVec2(a.x, base_y), col)


# --- lines -------------------------------------------------------------

def sparkline(values, width=0.0, height=34.0, colour=None, fill=True,
              head=True, lo=None, hi=None, ground=True, thickness=1.6):
    """A line with no axes, for a number's recent history.

    The head dot is the point of it: without one the eye has to find the
    right-hand end before it can read "now", and the whole advantage of a
    sparkline over a number is that it is read at a glance.
    """
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    o = imgui.get_cursor_screen_pos()
    w = _avail(width)
    c = colour if colour is not None else t.accent
    v = np.asarray(values, dtype=np.float64).ravel()
    if ground:
        _ground(dl, o, w, height, t)
    if v.size >= 2:
        a, b = _span(v, lo, hi)
        xs = o.x + np.linspace(2.0, w - 2.0, v.size)
        ys = o.y + height - 2.0 - (v - a) / (b - a) * (height - 4.0)
        pts = [ImVec2(float(x), float(y)) for x, y in zip(xs, ys)]
        if fill:
            _under(dl, pts, o.y + height, _col(c, 0.16))
        dl.add_polyline(pts, _col(c, 0.95), thickness, 0)
        if head:
            dl.add_circle_filled(pts[-1], 2.6, _col(c, 1.0))
            dl.add_circle_filled(pts[-1], 5.2, _col(c, 0.22))
    imgui.dummy(ImVec2(w, height))


def plot(series, width=0.0, height=120.0, lo=None, hi=None, grid=4,
         legend=True, fill=False, labels=None):
    """Several named series on shared axes.

    `series` is {name: values} or a sequence of sequences. Use this when
    the question is "how do these compare"; use a sparkline per card when
    it is "is this one climbing".
    """
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    o = imgui.get_cursor_screen_pos()
    w = _avail(width)
    if isinstance(series, dict):
        names, data = list(series.keys()), list(series.values())
    else:
        data = list(series)
        names = list(labels or [f"series {i}" for i in range(len(data))])
    cols = series_colours(t, len(data))
    _ground(dl, o, w, height, t, 0.6)

    flat = np.concatenate([np.asarray(d, np.float64).ravel()
                           for d in data if len(d)]) if data else np.zeros(1)
    a, b = _span(flat, lo, hi)
    for g in range(grid + 1):
        y = o.y + 4 + (height - 8) * g / grid
        dl.add_line(ImVec2(o.x + 2, y), ImVec2(o.x + w - 2, y),
                    _col(t.border, 0.55 if g in (0, grid) else 0.3), 1.0)
    with fonts.use("label"):
        dl.add_text(ImVec2(o.x + 6, o.y + 3), _col(t.text_mute, 0.9), f"{b:.4g}")
        dl.add_text(ImVec2(o.x + 6, o.y + height - 16),
                    _col(t.text_mute, 0.9), f"{a:.4g}")

    for i, d in enumerate(data):
        v = np.asarray(d, np.float64).ravel()
        if v.size < 2:
            continue
        xs = o.x + np.linspace(4.0, w - 4.0, v.size)
        ys = o.y + height - 6.0 - (v - a) / (b - a) * (height - 12.0)
        pts = [ImVec2(float(x), float(y)) for x, y in zip(xs, ys)]
        if fill:
            _under(dl, pts, o.y + height - 4, _col(cols[i], 0.13))
        dl.add_polyline(pts, _col(cols[i], 0.95), 1.7, 0)
        dl.add_circle_filled(pts[-1], 2.6, _col(cols[i]))
    imgui.dummy(ImVec2(w, height))

    if legend:
        for i, n in enumerate(names):
            if i:
                imgui.same_line(0, 12)
            p = imgui.get_cursor_screen_pos()
            dl.add_rect_filled(ImVec2(p.x, p.y + 6), ImVec2(p.x + 9, p.y + 9),
                               _col(cols[i]), 1.5)
            imgui.dummy(ImVec2(12, 14))
            imgui.same_line(0, 3)
            imgui.text_colored(t.text_mute, n)
        imgui.new_line()


# --- bars --------------------------------------------------------------

def bars(values, width=0.0, height=60.0, colour=None, gap=2.0, lo=None,
         hi=None, highlight=None, ground=True):
    """Vertical bars. `highlight` indexes one to pick out in the accent."""
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    o = imgui.get_cursor_screen_pos()
    w = _avail(width)
    v = np.asarray(values, np.float64).ravel()
    c = colour if colour is not None else t.accent
    if ground:
        _ground(dl, o, w, height, t)
    if v.size:
        a, b = _span(v, lo if lo is not None else min(0.0, float(np.min(v))), hi)
        bw = max(1.0, (w - 4.0) / v.size - gap)
        for i, x in enumerate(v):
            frac = (x - a) / (b - a)
            bx = o.x + 2.0 + i * (bw + gap)
            top = o.y + height - 2.0 - frac * (height - 4.0)
            hot = (highlight is not None and i == highlight)
            dl.add_rect_filled(ImVec2(bx, top), ImVec2(bx + bw, o.y + height - 2),
                               _col(t.accent_bright if hot else c,
                                    1.0 if hot else 0.72),
                               min(2.0, bw * 0.3))
    imgui.dummy(ImVec2(w, height))


def histogram(values, bins=24, width=0.0, height=70.0, colour=None):
    """Distribution rather than sequence - the shape of a set of samples."""
    v = np.asarray(values, np.float64).ravel()
    if v.size == 0:
        imgui.dummy(ImVec2(_avail(width), height))
        return
    counts, _ = np.histogram(v, bins=max(2, int(bins)))
    bars(counts, width, height, colour, gap=1.0, lo=0.0)


def levels(values, width=0.0, height=70.0, peaks=None, lo=0.0, hi=1.0,
           warn_at=0.8):
    """Channel meters - vertical, with optional peak marks.

    Goes hot near the top, because a meter that stays one colour makes you
    read the number to find out whether it is clipping.
    """
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    o = imgui.get_cursor_screen_pos()
    v = np.asarray(values, np.float64).ravel()
    n = max(1, v.size)
    w = _avail(width)
    cw = (w - (n - 1) * 5.0) / n
    for i in range(n):
        x = o.x + i * (cw + 5.0)
        dl.add_rect_filled(ImVec2(x, o.y), ImVec2(x + cw, o.y + height),
                           _col(theme_mod.sink(t.surface, 0.6, t), 0.9), 2.0)
        frac = float(np.clip((v[i] - lo) / max(1e-9, hi - lo), 0.0, 1.0))
        col = t.danger if frac >= warn_at else (
            t.warn if frac >= warn_at * 0.75 else t.ok)
        if frac > 0.002:
            dl.add_rect_filled(
                ImVec2(x, o.y + height * (1.0 - frac)),
                ImVec2(x + cw, o.y + height), _col(col, 0.92), 2.0)
        if peaks is not None and i < len(peaks):
            pf = float(np.clip((peaks[i] - lo) / max(1e-9, hi - lo), 0.0, 1.0))
            py = o.y + height * (1.0 - pf)
            dl.add_line(ImVec2(x, py), ImVec2(x + cw, py), _col(t.text, 0.8), 1.6)
    imgui.dummy(ImVec2(w, height))


# --- radial ------------------------------------------------------------

def gauge(value, lo=0.0, hi=1.0, radius=46.0, label="", unit="", colour=None,
          thickness=9.0, sweep=250.0):
    """An arc dial with the number in the middle.

    The arc is worth the pixels over a bar when the range matters as much
    as the value - a bar says "how much", a dial says "how much out of
    what", and you can read "near the top" from across a room.
    """
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    o = imgui.get_cursor_screen_pos()
    size = radius * 2.0 + 6.0
    cx, cy = o.x + size * 0.5, o.y + size * 0.5 + 2.0
    c = colour if colour is not None else t.accent
    frac = float(np.clip((value - lo) / max(1e-9, hi - lo), 0.0, 1.0))
    a0 = math.radians(90.0 + (360.0 - sweep) * 0.5)
    a1 = a0 + math.radians(sweep)

    dl.path_arc_to(ImVec2(cx, cy), radius, a0, a1, 64)
    dl.path_stroke(_col(theme_mod.sink(t.surface, 0.4, t), 0.95), thickness, 0)
    if frac > 0.001:
        dl.path_arc_to(ImVec2(cx, cy), radius, a0, a0 + (a1 - a0) * frac, 64)
        dl.path_stroke(_col(c, 0.95), thickness, 0)
        ang = a0 + (a1 - a0) * frac
        dl.add_circle_filled(
            ImVec2(cx + math.cos(ang) * radius, cy + math.sin(ang) * radius),
            thickness * 0.42, _col(t.accent_bright if colour is None else c))
    with fonts.use("big"):
        txt = f"{value:.4g}"
        ts = imgui.calc_text_size(txt)
        dl.add_text(ImVec2(cx - ts.x * 0.5, cy - ts.y * 0.62), _col(t.text), txt)
    with fonts.use("label"):
        if unit:
            us = imgui.calc_text_size(unit)
            dl.add_text(ImVec2(cx - us.x * 0.5, cy + radius * 0.28),
                        _col(t.text_mute), unit)
        if label:
            ls = imgui.calc_text_size(label)
            dl.add_text(ImVec2(cx - ls.x * 0.5, o.y + size - 2),
                        _col(t.text_dim), label)
    imgui.dummy(ImVec2(size, size + (14 if label else 0)))


def ring(value, lo=0.0, hi=1.0, radius=34.0, thickness=7.0, colour=None,
         centre=None):
    """A closed donut. For a proportion that genuinely wraps - a budget
    used, a disk filled - where a dial's gap would imply a scale end."""
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    o = imgui.get_cursor_screen_pos()
    size = radius * 2.0 + 4.0
    cx, cy = o.x + size * 0.5, o.y + size * 0.5
    c = colour if colour is not None else t.accent
    frac = float(np.clip((value - lo) / max(1e-9, hi - lo), 0.0, 1.0))
    dl.add_circle(ImVec2(cx, cy), radius,
                  _col(theme_mod.sink(t.surface, 0.4, t), 0.95), 64, thickness)
    if frac > 0.001:
        a0 = -math.pi * 0.5
        dl.path_arc_to(ImVec2(cx, cy), radius, a0, a0 + 2 * math.pi * frac, 64)
        dl.path_stroke(_col(c, 0.95), thickness, 0)
    txt = centre if centre is not None else f"{frac * 100:.0f}%"
    with fonts.use("semi"):
        ts = imgui.calc_text_size(txt)
        dl.add_text(ImVec2(cx - ts.x * 0.5, cy - ts.y * 0.5), _col(t.text), txt)
    imgui.dummy(ImVec2(size, size))


# --- fields ------------------------------------------------------------

def heatmap(matrix, cell=14.0, gap=1.0, colour=None, lo=None, hi=None):
    """A grid of cells, darkest to brightest. For anything with two axes -
    a week by hour, a core by sample, a confusion matrix."""
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    o = imgui.get_cursor_screen_pos()
    m = np.asarray(matrix, np.float64)
    if m.ndim == 1:
        m = m[None, :]
    c = colour if colour is not None else t.accent
    a, b = _span(m, lo, hi)
    rows, colsn = m.shape
    for r in range(rows):
        for q in range(colsn):
            f = float((m[r, q] - a) / (b - a))
            x = o.x + q * (cell + gap)
            y = o.y + r * (cell + gap)
            dl.add_rect_filled(
                ImVec2(x, y), ImVec2(x + cell, y + cell),
                _col(theme_mod.lerp(theme_mod.sink(t.surface, 0.55, t), c, f),
                     0.35 + 0.65 * f), 2.0)
    imgui.dummy(ImVec2(colsn * (cell + gap), rows * (cell + gap)))


def scatter(points, width=0.0, height=120.0, colour=None, size=2.6,
            bounds=None):
    """Points in a box. `points` is an (n, 2) array."""
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    o = imgui.get_cursor_screen_pos()
    w = _avail(width)
    p = np.asarray(points, np.float64).reshape(-1, 2)
    c = colour if colour is not None else t.accent
    _ground(dl, o, w, height, t, 0.6)
    if p.size:
        if bounds:
            x0, y0, x1, y1 = bounds
        else:
            x0, x1 = _span(p[:, 0], None, None)
            y0, y1 = _span(p[:, 1], None, None)
        xs = o.x + 4 + (p[:, 0] - x0) / (x1 - x0) * (w - 8)
        ys = o.y + height - 4 - (p[:, 1] - y0) / (y1 - y0) * (height - 8)
        for x, y in zip(xs, ys):
            dl.add_circle_filled(ImVec2(float(x), float(y)), size, _col(c, 0.75))
    imgui.dummy(ImVec2(w, height))


def waveform(samples, width=0.0, height=70.0, colour=None, mirror=True):
    """A symmetric envelope. For audio, where the shape is the signal and
    a line chart of the same samples would read as noise."""
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    o = imgui.get_cursor_screen_pos()
    w = _avail(width)
    v = np.asarray(samples, np.float64).ravel()
    c = colour if colour is not None else t.accent
    mid = o.y + height * 0.5
    dl.add_line(ImVec2(o.x, mid), ImVec2(o.x + w, mid), _col(t.border, 0.8), 1.0)
    if v.size:
        n = int(max(8, min(v.size, w / 2.0)))
        chunks = np.array_split(np.abs(v), n)
        amp = np.array([float(np.max(ch)) if len(ch) else 0.0 for ch in chunks])
        peak = float(np.max(amp)) or 1.0
        step = w / n
        for i, a in enumerate(amp):
            h = (a / peak) * (height * 0.5 - 2.0)
            x = o.x + i * step
            dl.add_rect_filled(
                ImVec2(x, mid - h), ImVec2(x + max(1.0, step - 1.0),
                                           mid + (h if mirror else 0.0)),
                _col(c, 0.55 + 0.45 * float(a / peak)), 1.0)
    imgui.dummy(ImVec2(w, height))


def timeline(events, width=0.0, height=44.0, span=None, now=None):
    """Events on a time axis. `events` is a sequence of (t, kind[, label]).

    Status-coloured, so a run of failures is a red cluster you see before
    you read anything.
    """
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    o = imgui.get_cursor_screen_pos()
    w = _avail(width)
    _ground(dl, o, w, height, t, 0.55)
    ev = list(events or ())
    if ev:
        ts = [float(e[0]) for e in ev]
        t0 = min(ts) if span is None else float(span[0])
        t1 = (max(ts) if now is None else float(now)) if span is None \
            else float(span[1])
        if t1 - t0 < 1e-9:
            t0, t1 = t0 - 1.0, t1 + 1.0
        mid = o.y + height * 0.5
        dl.add_line(ImVec2(o.x + 4, mid), ImVec2(o.x + w - 4, mid),
                    _col(t.border, 0.9), 1.0)
        for e in ev:
            x = o.x + 4 + (float(e[0]) - t0) / (t1 - t0) * (w - 8)
            col = t.status(e[1]) if len(e) > 1 else t.accent
            dl.add_line(ImVec2(x, mid - height * 0.3),
                        ImVec2(x, mid + height * 0.3), _col(col, 0.9), 2.0)
            dl.add_circle_filled(ImVec2(x, mid), 2.8, _col(col))
    imgui.dummy(ImVec2(w, height))


def pips(total, on, size=7.0, gap=5.0, colour=None):
    """A discrete count - retries left, stages done. Below about twelve
    this is read faster than a number, and never needs a label."""
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    o = imgui.get_cursor_screen_pos()
    c = colour if colour is not None else t.accent
    for i in range(int(total)):
        x = o.x + i * (size + gap) + size * 0.5
        lit = i < on
        dl.add_circle_filled(ImVec2(x, o.y + size * 0.6), size * 0.5,
                             _col(c if lit else t.text_mute, 1.0 if lit else 0.35))
    imgui.dummy(ImVec2(max(1.0, total * (size + gap)), size * 1.2))
