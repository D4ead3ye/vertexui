"""YMO Technodelic - the 1979 sleeve, rebuilt as a synthesiser front panel.

Yellow band over a cobalt field, plum lettering with a warm offset shadow,
wine-coloured glyph boxes down the margins, and an offset screen over all
of it. The hardware half comes from what the record was made on: a
System-700 front panel is silkscreened legends on a coloured chassis,
hairline rules, zero radius anywhere, and block meters that go gold then
crimson.

    from vertexui import themes
    app = compose.App(profile=themes.YMO)

Three things make it not a palette swap:

**It draws its own alphabet.** The sleeve's lettering is a modular face
built from straight strokes and 45-degree corner cuts - the Y is the
4-shaped one. `type_` renders it from a stroke table, and the theme hangs
it on `skins.Skin.label`, so the tab captions and every card title are
lettered rather than typed. Nothing else here owns a typeface.

**The sub-labels are real kanji.** Japanese hardware labels a control
twice, and `fonts` now carries a `cjk` role, so 状態 sits beside STATUS
instead of a drawn approximation. On a machine with no CJK face the
sub-label is simply absent - `_sub` returns nothing and the header closes
up.

**The ground does not move.** The other three bundled themes all animate
their background; this one is printed matter, and print holds still. The
motion budget goes entirely into the controls and the spinner, which is a
bundle of flex leads that straightens out as it comes up to speed.
"""

import math

from imgui_bundle import ImVec2, imgui

from .. import fonts, layouts, paint, profiles, skins
from .. import theme as theme_mod
from ..theme import Theme, rgb

# --- palette, sampled off the sleeve ------------------------------------
SLEEVE = rgb("#f8bd03")       # the band across the top
SLEEVE_D = rgb("#c08f04")
COBALT = rgb("#1f448f")       # the field it sits on
COBALT_L = rgb("#2d5cb4")
COBALT_D = rgb("#16305f")
NAVY = rgb("#0d1830")         # the ground, one stop below the field
INK = rgb("#070d1c")          # hairlines, and the shadow the band casts
PLUM = rgb("#8c3f5f")         # the title lettering
SIENNA = rgb("#a9674e")       # its offset shadow, warm
VERMIL = rgb("#c45723")       # the lip, and every alarm on the panel
FAN = rgb("#e5923c")          # the fan - the warm half of a meter
LENS = rgb("#6d8a5f")         # smoked green glass
CREAM = rgb("#efe3ca")        # the screened legends

TECHNO = Theme(
    name="ymo-technodelic",
    bg=NAVY, panel=COBALT_D, surface=COBALT, surface_hover=COBALT_L,
    border=INK,
    accent=SLEEVE, accent_bright=rgb("#ffd451"), accent_dim=rgb("#6f5305"),
    text=CREAM, text_dim=rgb("#a9b6d2"), text_mute=rgb("#6d7fa4"),
    ok=rgb("#8aa972"), warn=FAN, danger=VERMIL, info=rgb("#79a7d6"),
    rounding=0.0, rounding_panel=0.0, border_width=1.0,
)


# --- the sleeve's alphabet ----------------------------------------------
#
# Straight strokes on a unit box, every bowl an octagon cut at 45 degrees.
# Coordinates run 0..1 across and 0..1 from cap height to baseline; the
# renderer scales x by ASPECT, so changing the proportion changes every
# letter at once. Caps only, which is what the sleeve has.

_C = 0.26                      # the corner cut everything is built from
_OCT = ((_C, 0), (1 - _C, 0), (1, _C), (1, 1 - _C), (1 - _C, 1), (_C, 1),
        (0, 1 - _C), (0, _C), (_C, 0))

_G = {
    "A": (((0, 1), (0, _C), (_C, 0), (1 - _C, 0), (1, _C), (1, 1)),
          ((0, 0.6), (1, 0.6))),
    "B": (((0, 0), (0.7, 0), (1, 0.24), (1, 0.38), (0.78, 0.5), (1, 0.62),
           (1, 0.76), (0.7, 1), (0, 1), (0, 0)), ((0, 0.5), (0.78, 0.5))),
    "C": (((1, 0.2), (0.76, 0), (_C, 0), (0, _C), (0, 1 - _C), (_C, 1),
           (0.76, 1), (1, 0.8)),),
    "D": (((0, 0), (0.7, 0), (1, 0.3), (1, 0.7), (0.7, 1), (0, 1), (0, 0)),),
    "E": (((1, 0), (0, 0), (0, 1), (1, 1)), ((0, 0.5), (0.76, 0.5))),
    "F": (((1, 0), (0, 0), (0, 1)), ((0, 0.5), (0.76, 0.5))),
    "G": (((1, 0.2), (0.76, 0), (_C, 0), (0, _C), (0, 1 - _C), (_C, 1),
           (0.76, 1), (1, 0.74), (1, 0.52), (0.5, 0.52)),),
    "H": (((0, 0), (0, 1)), ((1, 0), (1, 1)), ((0, 0.5), (1, 0.5))),
    "I": (((0.5, 0), (0.5, 1)),),
    "J": (((1, 0), (1, 0.74), (0.76, 1), (_C, 1), (0, 0.74)),),
    "K": (((0, 0), (0, 1)), ((1, 0), (0, 0.56)), ((0.3, 0.38), (1, 1))),
    "L": (((0, 0), (0, 1), (1, 1)),),
    "M": (((0, 1), (0, 0), (0.5, 0.54), (1, 0), (1, 1)),),
    "N": (((0, 1), (0, 0), (1, 1), (1, 0)),),
    "O": (_OCT,),
    "P": (((0, 1), (0, 0), (0.7, 0), (1, 0.26), (1, 0.4), (0.7, 0.62),
           (0, 0.62)),),
    "Q": (_OCT, ((0.6, 0.68), (1, 1.08))),
    "R": (((0, 1), (0, 0), (0.7, 0), (1, 0.26), (1, 0.4), (0.7, 0.62),
           (0, 0.62)), ((0.48, 0.62), (1, 1))),
    "S": (((1, 0.2), (0.76, 0), (_C, 0), (0, 0.22), (0, 0.34), (_C, 0.5),
           (0.76, 0.5), (1, 0.66), (1, 0.78), (0.76, 1), (_C, 1), (0, 0.8)),),
    "T": (((0, 0), (1, 0)), ((0.5, 0), (0.5, 1))),
    "U": (((0, 0), (0, 1 - _C), (_C, 1), (1 - _C, 1), (1, 1 - _C), (1, 0)),),
    "V": (((0, 0), (0.5, 1), (1, 0)),),
    "W": (((0, 0), (0.22, 1), (0.5, 0.32), (0.78, 1), (1, 0)),),
    "X": (((0, 0), (1, 1)), ((1, 0), (0, 1))),
    # The one letter that gives the whole sleeve away: a 4, not a Y.
    "Y": (((0, 0), (0, 0.52), (1, 0.52)), ((1, 0), (1, 1))),
    "Z": (((0, 0), (1, 0), (0, 1), (1, 1)),),
    "0": (_OCT, ((0.14, 0.84), (0.86, 0.16))),
    "1": (((0.12, 0.22), (0.5, 0), (0.5, 1)),),
    "2": (((0, 0.22), (_C, 0), (0.76, 0), (1, 0.24), (1, 0.4), (0, 1),
           (1, 1)),),
    "3": (((0, 0), (1, 0), (0.42, 0.46), (0.76, 0.46), (1, 0.66), (1, 0.78),
           (0.76, 1), (_C, 1), (0, 0.8)),),
    "4": (((0.72, 1), (0.72, 0), (0, 0.66), (1, 0.66)),),
    "5": (((1, 0), (0.14, 0), (0.06, 0.44), (0.7, 0.44), (1, 0.64), (1, 0.78),
           (0.76, 1), (_C, 1), (0, 0.82)),),
    "6": (((0.9, 0.1), (0.62, 0), (_C, 0), (0, 0.28), (0, 0.74), (_C, 1),
           (0.76, 1), (1, 0.76), (1, 0.62), (0.74, 0.44), (_C, 0.44),
           (0, 0.6)),),
    "7": (((0, 0), (1, 0), (0.34, 1)),),
    "8": (((0.22, 0), (0.78, 0), (1, 0.16), (1, 0.32), (0.78, 0.48),
           (0.22, 0.48), (0, 0.32), (0, 0.16), (0.22, 0)),
          ((0.22, 0.48), (0.78, 0.48), (1, 0.64), (1, 0.84), (0.78, 1),
           (0.22, 1), (0, 0.84), (0, 0.64), (0.22, 0.48))),
    "9": (((0.1, 0.9), (0.38, 1), (0.74, 1), (1, 0.72), (1, 0.26), (0.74, 0),
           (0.24, 0), (0, 0.24), (0, 0.38), (0.26, 0.56), (0.74, 0.56),
           (1, 0.4)),),
    "-": (((0.08, 0.52), (0.92, 0.52)),),
    "_": (((0, 1), (1, 1)),),
    ".": (((0.36, 0.92), (0.64, 0.92)),),
    ",": (((0.56, 0.86), (0.34, 1.08)),),
    ":": (((0.38, 0.3), (0.62, 0.3)), ((0.38, 0.78), (0.62, 0.78))),
    "/": (((0.04, 1), (0.96, 0)),),
    "\\": (((0.04, 0), (0.96, 1)),),
    "+": (((0.5, 0.22), (0.5, 0.82)), ((0.18, 0.52), (0.82, 0.52))),
    "=": (((0.08, 0.38), (0.92, 0.38)), ((0.08, 0.68), (0.92, 0.68))),
    "<": (((0.82, 0.08), (0.18, 0.5), (0.82, 0.92)),),
    ">": (((0.18, 0.08), (0.82, 0.5), (0.18, 0.92)),),
    "(": (((0.72, 0), (0.3, 0.26), (0.3, 0.74), (0.72, 1)),),
    ")": (((0.28, 0), (0.7, 0.26), (0.7, 0.74), (0.28, 1)),),
    "[": (((0.72, 0), (0.3, 0), (0.3, 1), (0.72, 1)),),
    "]": (((0.28, 0), (0.7, 0), (0.7, 1), (0.28, 1)),),
    "!": (((0.5, 0), (0.5, 0.64)), ((0.5, 0.88), (0.5, 1))),
    "?": (((0, 0.22), (_C, 0), (0.76, 0), (1, 0.24), (1, 0.36), (0.5, 0.62),
           (0.5, 0.7)), ((0.5, 0.88), (0.5, 1))),
    "'": (((0.5, 0), (0.5, 0.24)),),
    "*": (((0.5, 0.18), (0.5, 0.82)), ((0.18, 0.34), (0.82, 0.66)),
          ((0.82, 0.34), (0.18, 0.66))),
    "%": (((0.9, 0.08), (0.1, 0.92)), ((0.04, 0.1), (0.34, 0.1)),
          ((0.66, 0.9), (0.96, 0.9))),
    "#": (((0.28, 0.08), (0.18, 0.92)), ((0.72, 0.08), (0.62, 0.92)),
          ((0.06, 0.36), (0.9, 0.36)), ((0.06, 0.66), (0.9, 0.66))),
}

ASPECT = 0.60                  # glyph width as a share of cap height
TRACK = 0.30                   # the sleeve's letterspacing, same units


def type_width(h, text, track=TRACK) -> float:
    """Advance width of `text` in the sleeve lettering at cap height `h`."""
    s = str(text).upper()
    if not s:
        return 0.0
    w = sum((ASPECT * 0.55 if ch == " " else ASPECT) * h for ch in s)
    return w + track * h * (len(s) - 1)


def type_(dl, x, y, h, text, col, thickness=None, track=TRACK, shadow=None):
    """Letter `text` in the sleeve alphabet. Returns the advance width.

    `shadow` is the offset drop the sleeve prints behind its title - the
    second pass that makes plum on yellow read instead of vibrating.
    """
    if shadow is not None:
        off = h * 0.10
        type_(dl, x + off, y + off, h, text, shadow, thickness, track)
    th = thickness if thickness is not None else max(1.0, h * 0.145)
    cx = x
    for ch in str(text).upper():
        w = (ASPECT * 0.55 if ch == " " else ASPECT) * h
        strokes = _G.get(ch)
        if ch != " " and strokes is None:
            # The sleeve's own answer to a character it has no sorts for:
            # a box, like the glyph crates down its margins.
            dl.add_rect(ImVec2(cx + w * 0.1, y + h * 0.14),
                        ImVec2(cx + w * 0.9, y + h * 0.9), col, 0.0, th)
        elif strokes:
            for st in strokes:
                pts = [ImVec2(cx + px * w, y + py * h) for px, py in st]
                if len(pts) == 2:
                    dl.add_line(pts[0], pts[1], col, th)
                else:
                    dl.add_polyline(pts, col, th, 0)
        cx += w + track * h
    return cx - x - track * h


# --- the second label ---------------------------------------------------
#
# Japanese hardware labels a control twice: the word, and the word. These
# are the ones a panel built on this toolkit actually prints. A title with
# no match gets no sub-label rather than an invented one.
SUB = {
    "status": "状態", "state": "状態",
    "output": "出力", "out": "出力",
    "input": "入力", "in": "入力",
    "log": "記録", "logs": "記録",
    "settings": "設定", "options": "設定",
    "control": "制御", "controls": "制御",
    "signal": "信号", "sync": "同期",
    "level": "階調", "levels": "階調",
    "volume": "音量", "gain": "音量",
    "speed": "速度", "rate": "速度",
    "time": "時間", "clock": "時間",
    "system": "系統", "device": "機器",
    "sequence": "配列", "pattern": "配列",
    "wave": "波形", "waveform": "波形",
    "filter": "濾波", "memory": "記憶",
    "network": "通信", "power": "電源",
    "test": "試験", "jobs": "作業", "job": "作業",
    "tasks": "作業", "queue": "作業",
    "events": "事象", "feed": "事象",
    "alarm": "警報", "alerts": "警報",
    "monitor": "監視", "watch": "監視",
    "channel": "回路", "channels": "回路",
    "mixer": "混合", "voice": "声", "voices": "声",
    "tempo": "拍子", "steps": "歩", "step": "歩",
    "data": "資料", "table": "資料",
    "detail": "詳細", "summary": "概要",
    "runner": "走者", "riders": "走者",
}


def _sub(title):
    """The kanji that belongs beside this title, or "" for none."""
    if not title or not fonts.has("cjk"):
        return ""
    for word in str(title).lower().replace("-", " ").replace("/", " ").split():
        hit = SUB.get(word.strip(":.,"))
        if hit:
            return hit
    return ""


# --- painters -----------------------------------------------------------

def plate(dl, x, y, w, h, t, edge, style, shadow):
    """A chassis panel: flat cobalt, one ink hairline, a screened edge."""
    if style == "flat":
        return False
    if shadow and style in ("raised", "plated"):
        # flat offset ink - a printed shadow has no gradient in it
        dl.add_rect_filled(ImVec2(x + 4, y + 4), ImVec2(x + w + 4, y + h + 4),
                           theme_mod.u32(INK, 0.5), 0.0)
    if style != "outlined":
        dl.add_rect_filled(ImVec2(x, y), ImVec2(x + w, y + h),
                           theme_mod.u32(t.surface), 0.0)
        # the offset screen the sleeve is printed with, barely there
        paint.halftone(dl, x + 1, y + 1, w - 2, h - 2,
                       theme_mod.u32(INK, 0.10), 7.0, fade=True)
    dl.add_rect(ImVec2(x, y), ImVec2(x + w, y + h), theme_mod.u32(INK),
                0.0, 1.0)
    # the screened highlight along the lit edges of a bent-metal chassis
    dl.add_line(ImVec2(x + 1, y + 1), ImVec2(x + w - 1, y + 1),
                theme_mod.u32(CREAM, 0.16), 1.0)
    dl.add_line(ImVec2(x + 1, y + 1), ImVec2(x + 1, y + h - 1),
                theme_mod.u32(CREAM, 0.16), 1.0)
    # and the sleeve's band, quoted small, along the foot
    dl.add_rect_filled(ImVec2(x + 1, y + h - 3), ImVec2(x + w - 1, y + h - 1),
                       theme_mod.u32(SLEEVE, 0.85), 0.0)
    if edge is not None:
        # status goes down the left edge, where a patch bay puts it
        dl.add_rect_filled(ImVec2(x + 1, y + 1), ImVec2(x + 4, y + h - 3),
                           theme_mod.u32(edge, 0.95), 0.0)
    return True


def head(dl, x, y, w, t, icon, title, right, right_col, dot):
    """The sleeve's band: yellow, plum lettering, warm offset shadow."""
    bar = 25.0
    bx, by, bw = x + 1, y + 1, w - 2
    dl.add_rect_filled(ImVec2(bx, by), ImVec2(bx + bw, by + bar),
                       theme_mod.u32(SLEEVE), 0.0)
    # the second plate, a hair out of registration
    dl.add_rect_filled(ImVec2(bx, by + bar), ImVec2(bx + bw, by + bar + 1.0),
                       theme_mod.u32(VERMIL, 0.85), 0.0)

    cap = 11.0
    tx = bx + 9.0
    if dot is not None:
        dl.add_rect_filled(ImVec2(bx + 6, by + bar * 0.5 - 3),
                           ImVec2(bx + 12, by + bar * 0.5 + 3),
                           theme_mod.u32(dot), 0.0)
        tx = bx + 18.0
    tw = type_(dl, tx, by + (bar - cap) * 0.5, cap, title or "",
               theme_mod.u32(PLUM), shadow=theme_mod.u32(SIENNA, 0.7))

    sub = _sub(title)
    if sub:
        with fonts.use("cjk"):
            sz = imgui.calc_text_size(sub)
            dl.add_text(ImVec2(tx + tw + 9.0, by + (bar - sz.y) * 0.5),
                        theme_mod.u32(PLUM, 0.62), sub)

    if right:
        with fonts.use("mono"):
            rw = imgui.calc_text_size(right)
            dl.add_text(ImVec2(bx + bw - 9 - rw.x, by + (bar - rw.y) * 0.5),
                        theme_mod.u32(right_col if right_col is not None
                                      else PLUM, 0.95), right)
    return y + bar + 12.0


def frame(dl, x, y, w, h, t, kind):
    """Silkscreened key caps, and wells that are cut into the chassis."""
    if kind == "input":
        dl.add_rect_filled(ImVec2(x, y), ImVec2(x + w, y + h),
                           theme_mod.u32(rgb("#0a1835")), 0.0)
        dl.add_rect(ImVec2(x, y), ImVec2(x + w, y + h), theme_mod.u32(INK),
                    0.0, 1.0)
        # light from below: a cut reads as a cut when its lit edge is low
        dl.add_line(ImVec2(x + 1, y + h - 1), ImVec2(x + w - 1, y + h - 1),
                    theme_mod.u32(CREAM, 0.14), 1.0)
        return True
    if not kind.startswith("button"):
        return False
    primary = kind.endswith("primary")
    fill = SLEEVE if primary else theme_mod.lerp(COBALT, CREAM, 0.07)
    dl.add_rect_filled(ImVec2(x, y), ImVec2(x + w, y + h),
                       theme_mod.u32(fill), 0.0)
    dl.add_rect(ImVec2(x, y), ImVec2(x + w, y + h), theme_mod.u32(INK),
                0.0, 1.0)
    dl.add_line(ImVec2(x + 1, y + 1), ImVec2(x + w - 1, y + 1),
                theme_mod.u32(CREAM, 0.30 if primary else 0.20), 1.0)
    dl.add_line(ImVec2(x + 1, y + h - 1.5), ImVec2(x + w - 1, y + h - 1.5),
                theme_mod.u32(INK, 0.45), 1.0)
    return True


def hover_aura(dl, x0, y0, x1, y1, t, amount, kind):
    """Registration marks, not a glow.

    There are no lights in this picture - it is paper. What a printer does
    to say *this is the thing* is drop crop marks round it, so hover puts
    the four corner registers down in vermilion and a single cream keyline
    a pixel out. Nothing blurs and nothing fades up from behind.
    """
    a = max(0.0, min(1.0, amount))
    m = 7.0 * a
    reg = theme_mod.u32(VERMIL, 0.95 * a)
    for cx, sx in ((x0 - 2, 1.0), (x1 + 2, -1.0)):
        for cy, sy in ((y0 - 2, 1.0), (y1 + 2, -1.0)):
            dl.add_line(ImVec2(cx, cy), ImVec2(cx + sx * m, cy), reg, 1.0)
            dl.add_line(ImVec2(cx, cy), ImVec2(cx, cy + sy * m), reg, 1.0)
    dl.add_rect(ImVec2(x0 - 2, y0 - 2), ImVec2(x1 + 2, y1 + 2),
                theme_mod.u32(CREAM, 0.30 * a), 0.0, 1.0)


def press(dl, x0, y0, x1, y1, t, amount):
    """A key with travel: the cap darkens and the LED under it comes on."""
    a = max(0.0, min(1.0, amount))
    dl.add_rect_filled(ImVec2(x0, y0), ImVec2(x1, y1),
                       theme_mod.u32(INK, 0.28 * a), 0.0)
    dl.add_rect_filled(ImVec2(x0 + 1, y1 - 2.5), ImVec2(x1 - 1, y1 - 0.5),
                       theme_mod.u32(VERMIL, 0.95 * a), 0.0)


def label(dl, x, y, h, text, col, t, kind):
    """Tab captions in the sleeve's lettering. `dl=None` measures."""
    if kind != "tab":
        return None
    if dl is None:
        return type_width(h, text)
    return type_(dl, x, y, h, text, col)


def tabs(dl, x, y, w, h, t, rects, index, hots):
    """A rack selector: blocks in a bay, the live one with its LED on."""
    if not rects:
        return False
    dl.add_rect_filled(ImVec2(x - 8, y - 2), ImVec2(x + w + 8, y + h + 2),
                       theme_mod.u32(INK, 0.55), 0.0)
    for i, (tx, tw) in enumerate(rects):
        on = i == index
        fill = theme_mod.lerp(COBALT_D, COBALT_L, 0.55 if on else 0.14)
        if hots[i] > 0.01 and not on:
            fill = theme_mod.lerp(fill, COBALT_L, 0.35 * hots[i])
        dl.add_rect_filled(ImVec2(tx, y), ImVec2(tx + tw, y + h),
                           theme_mod.u32(fill), 0.0)
        dl.add_rect(ImVec2(tx, y), ImVec2(tx + tw, y + h),
                    theme_mod.u32(INK, 0.9), 0.0, 1.0)
        dl.add_line(ImVec2(tx + 1, y + 1), ImVec2(tx + tw - 1, y + 1),
                    theme_mod.u32(CREAM, 0.22 if on else 0.10), 1.0)
        if on:
            # the band under the live unit, and its indicator
            dl.add_rect_filled(ImVec2(tx, y + h - 3), ImVec2(tx + tw, y + h),
                               theme_mod.u32(SLEEVE), 0.0)
            dl.add_rect_filled(ImVec2(tx + 5, y + 5), ImVec2(tx + 10, y + 9),
                               theme_mod.u32(VERMIL), 0.0)
    dl.add_rect_filled(ImVec2(x - 8, y + h + 2), ImVec2(x + w + 8, y + h + 3),
                       theme_mod.u32(CREAM, 0.16), 0.0)
    return True


WIRES = (CREAM, INK, VERMIL, FAN, COBALT_L, SLEEVE, PLUM, rgb("#d6cfc0"),
         LENS, rgb("#8a1f16"))


def spinner(dl, cx, cy, r, t, phase, spin=1.0):
    """The head of flex leads off the sleeve, turning.

    At rest each lead curls away from the hub. As it comes up to speed the
    curl is pulled out of them - one term, `curl`, scaled by the heat -
    until they stand straight off the hub and the stripped tips smear into
    a ring. That is the form change the brief asks each spinner for, and
    it is the actual physics of the picture rather than a second mode.

    Outside the leads is a scanning block meter in the panel's own gold
    and crimson, so the busy indicator and `graphics.segments` are visibly
    the same instrument.
    """
    heat = max(0.0, min(1.0, (spin - 1.0) / 4.0))
    turn = phase * 3.2
    n = len(WIRES)
    gauge = max(1.6, r * 0.078)
    for i in range(n):
        a = turn + i / n * math.tau
        # the lead's own slow sway, so a still spinner is not a frozen one
        curl = (1.0 - 0.80 * heat) * (0.95 + 0.30 * math.sin(phase * 1.6 + i))
        pts = []
        for k in range(9):
            f = k / 8.0
            ang = a + curl * f * f * 1.7
            rad = r * (0.28 + 0.80 * f)             # out to 1.08r
            pts.append(ImVec2(cx + math.cos(ang) * rad,
                              cy + math.sin(ang) * rad))
        dl.add_polyline(pts, theme_mod.u32(INK, 0.55), gauge + 1.6, 0)
        dl.add_polyline(pts, theme_mod.u32(WIRES[i], 0.97), gauge, 0)
        # the stripped end: a short bright length of bare copper, not a dot
        dl.add_line(pts[-2], pts[-1], theme_mod.u32(FAN, 0.95), gauge * 0.92)
        dl.add_circle_filled(pts[-1], gauge * 0.55,
                             theme_mod.u32(rgb("#ffd9a0"), 0.9), 10)
    if heat > 0.02:
        dl.add_circle(ImVec2(cx, cy), r * 1.08,
                      theme_mod.u32(CREAM, 0.24 * heat), 48, 1.0 + 2.5 * heat)

    # the hub: a yellow octagon on ink, with the plum one inside it
    for rad, col in ((r * 0.34, INK), (r * 0.29, SLEEVE), (r * 0.15, PLUM)):
        dl.add_convex_poly_filled(
            [ImVec2(cx + math.cos(k / 8 * math.tau + 0.3927) * rad,
                    cy + math.sin(k / 8 * math.tau + 0.3927) * rad)
             for k in range(8)], theme_mod.u32(col))

    # the scan: blocks, gold until the last fifth and crimson after it
    seg = 16
    scan = (phase * (2.4 + 7.0 * spin)) % seg
    tick = max(1.6, r * 0.085)
    for i in range(seg):
        lag = (scan - i) % seg
        a = max(0.14, 1.0 - lag / 3.2)       # unlit blocks stay readable,
        ang = i / seg * math.tau - math.tau * 0.25   # so it reads as a ring
        c, s = math.cos(ang), math.sin(ang)
        dl.add_line(ImVec2(cx + c * r * 1.22, cy + s * r * 1.22),
                    ImVec2(cx + c * r * 1.40, cy + s * r * 1.40),
                    theme_mod.u32(VERMIL if i >= seg * 0.78 else SLEEVE,
                                  0.95 * a), tick)
    return True


# the glyph crates down the sleeve's margins: (x share, y share, letter)
# Two sit right on the trimmed edge, where content never reaches, and one
# a little further in so the margin has some depth - that one is often
# behind a panel, which is where it is on the sleeve too.
MARGIN = ((0.011, 0.23, "Y"), (0.034, 0.57, "M"), (0.014, 0.81, "O"),
          (0.989, 0.33, "A"), (0.966, 0.62, "G"), (0.986, 0.86, "I"))


def background(dl, x, y, w, h, t, now):
    """The sleeve. It does not move.

    Every other bundled theme animates its ground - SBR's speed lines,
    Y2K's receding grid, Aero's drifting bubbles. This one is a printed
    object, and print holds still; the whole motion budget goes to the
    controls instead. `now` is deliberately unused.
    """
    dl.add_rect_filled(ImVec2(x, y), ImVec2(x + w, y + h),
                       theme_mod.u32(NAVY), 0.0)
    # the field, a touch deeper at the foot where the ink pools
    paint.grad_rect(dl, x, y, w, h, COBALT_D, rgb("#101f42"), 0.0)
    paint.halftone(dl, x, y, w, h, theme_mod.u32(INK, 0.13), 9.0, fade=False)

    for fx, fy, ch in MARGIN:
        s = 13.0
        bx, by = x + w * fx - s * 0.5, y + h * fy - s * 0.5
        dl.add_rect_filled(ImVec2(bx, by), ImVec2(bx + s, by + s),
                           theme_mod.u32(rgb("#5c2438"), 0.92), 0.0)
        dl.add_rect(ImVec2(bx, by), ImVec2(bx + s, by + s),
                    theme_mod.u32(INK, 0.6), 0.0, 1.0)
        cap = s * 0.52
        cw = type_width(cap, ch)
        type_(dl, bx + (s - cw) * 0.5, by + (s - cap) * 0.5, cap, ch,
              theme_mod.u32(CREAM, 0.78), thickness=1.0)

    # the band, at the foot where it stays out of the chrome's way, with
    # the sleeve's credit line set in its own letters
    band = 16.0
    dl.add_rect_filled(ImVec2(x, y + h - band), ImVec2(x + w, y + h),
                       theme_mod.u32(SLEEVE), 0.0)
    dl.add_rect_filled(ImVec2(x, y + h - band - 1.0),
                       ImVec2(x + w, y + h - band), theme_mod.u32(INK, 0.8))
    cap = 7.5
    type_(dl, x + 14, y + h - band + (band - cap) * 0.5, cap,
          "YELLOW MAGIC ORCHESTRA", theme_mod.u32(PLUM), track=0.52,
          thickness=1.2)
    tail = "A-M 1979"
    tw = type_width(cap, tail, track=0.52)
    type_(dl, x + w - 14 - tw, y + h - band + (band - cap) * 0.5, cap, tail,
          theme_mod.u32(PLUM, 0.72), track=0.52, thickness=1.2)

    # crop marks at the trimmed corners
    for ox, sx in ((x + 10, 1.0), (x + w - 10, -1.0)):
        for oy, sy in ((y + 10, 1.0), (y + h - band - 10, -1.0)):
            dl.add_line(ImVec2(ox, oy), ImVec2(ox + sx * 9, oy),
                        theme_mod.u32(CREAM, 0.22), 1.0)
            dl.add_line(ImVec2(ox, oy), ImVec2(ox, oy + sy * 9),
                        theme_mod.u32(CREAM, 0.22), 1.0)
    return True


SKIN = skins.Skin(
    name="ymo-technodelic",
    plate=plate, head=head, frame=frame, hover_aura=hover_aura, press=press,
    label=label, tabs=tabs, spinner=spinner, background=background,
    corner=lambda t: 0.0,     # nothing here has a radius, including widgets
    press_depth=2.0,
    extras={"sleeve": SLEEVE, "cobalt": COBALT, "plum": PLUM,
            "vermilion": VERMIL, "cream": CREAM, "ink": INK, "fan": FAN,
            "type": type_, "type_width": type_width, "sub": _sub},
)

YMO = profiles.Profile(
    name="ymo-technodelic", theme=TECHNO, layout=layouts.TABBED,
    face_ui="Arial", face_display="Bahnschrift", face_mono="Courier New",
    base_size=16.5, density=0.94,
    card_style="raised", card_shadow=True,
    motion=1.15,              # hardware, not software: it moves once
    sound_set="crisp", volume=0.14,
    skin=SKIN,
    blurb="The 1979 sleeve as a synth front panel - drawn letters, real kanji",
)
