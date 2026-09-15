"""Cards - the panels an interface is actually built out of.

`widgets.section` draws a label and a rule floating in the gaps *between*
things, which reads as captions around boxes. A card reads as an instrument
with a name on it, and that difference is most of what separates a laid-out
panel from a stack of default widgets.

Four genuinely different grounds, not four names for one:

    raised    gradient fill, border, a hairline of light inside the top
              edge, and a soft drop shadow
    plated    flat fill, border, an accent rule along the top
    outlined  border only - whatever is behind shows straight through
    flat      fill only, no edges at all

The choice changes whether a card has a fill at all, which is what decides
how much of a `backdrop` or `effects` pass comes through the interface.

    from vertexui import cards
    cards.set_style("raised", shadow=True)

    with cards.card("temperature", icon="bolt", right="ok", width=300):
        imgui.text("210 degrees")

The context manager sizes itself to its content by splitting the draw list,
so nothing has to know its own height in advance. When you do know it - or
when you are drawing into a rect you already reserved - the primitives
underneath (`plate`, `card_head`, `meter`, `grad_fill`) take explicit
coordinates and are just as public.
"""

from imgui_bundle import ImVec2, imgui

from . import fonts, icons
from . import theme as theme_mod
from .widgets import caps, caps_width

STYLES = ("raised", "plated", "outlined", "flat")

_style = "raised"
_shadow = True

HEAD_H = 27.0


def set_style(name, shadow=True):
    """Set the look for every card drawn from here on.

    Global on purpose: a card style is a property of the interface, the
    same way the theme is, and threading it through every call site is how
    half an app ends up on the old one. Pass `style=` to a single call to
    override it.
    """
    global _style, _shadow
    _style = name if name in STYLES else "raised"
    _shadow = bool(shadow)


def style() -> str:
    return _style


def shadow() -> bool:
    return _shadow


def grad_fill(dl, x, y, w, h, t=None, top=None, bottom=None, rounding=None):
    """A rounded rect with a vertical gradient.

    ImGui's own multi-colour rect is square-cornered, which is why this
    looks impossible at first. The way through is to draw the rounded fill
    normally and then re-colour the vertices it just emitted:
    ShadeVertsLinearColorGradientKeepAlpha lerps their RGB along an axis
    and leaves alpha alone, so the anti-aliased corner fringe keeps its
    coverage and picks up the gradient with everything else.
    """
    t = t or theme_mod.current()
    top = top if top is not None else theme_mod.lerp(t.surface, t.text, 0.055)
    bottom = bottom if bottom is not None else theme_mod.lerp(t.surface, t.bg, 0.35)
    r = t.rounding if rounding is None else rounding
    i0 = dl.vtx_buffer.size()
    dl.add_rect_filled(ImVec2(x, y), ImVec2(x + w, y + h),
                       imgui.get_color_u32(top), r)
    i1 = dl.vtx_buffer.size()
    if i1 > i0:
        imgui.internal.shade_verts_linear_color_gradient_keep_alpha(
            dl, i0, i1, ImVec2(x, y), ImVec2(x, y + h),
            imgui.get_color_u32(top), imgui.get_color_u32(bottom))


def plate(dl, x, y, w, h, t=None, edge=None, style=None, shadow=None):
    """A card's background, in whichever style is selected.

    `edge` colours the accent rule along the top - pass the status colour
    and the card says what it is doing from the corner of your eye.
    """
    t = t or theme_mod.current()
    st = style if style in STYLES else _style
    sh = _shadow if shadow is None else bool(shadow)
    r = t.rounding
    p0, p1 = ImVec2(x, y), ImVec2(x + w, y + h)

    if sh and st in ("raised", "plated"):
        # Three stacked rounded rects, each fainter and larger. Cheaper
        # than a blur and, at this size, indistinguishable from one.
        for i, a_ in ((3.0, 0.16), (6.0, 0.09), (10.0, 0.05)):
            dl.add_rect_filled(
                ImVec2(x + 1.0, y + i * 0.5), ImVec2(x + w - 1.0, y + h + i),
                imgui.get_color_u32(theme_mod.with_alpha(t.bg, a_)), r + i)

    if st == "raised":
        grad_fill(dl, x, y, w, h, t)
    elif st != "outlined":
        dl.add_rect_filled(p0, p1, imgui.get_color_u32(t.surface), r)

    if st in ("raised", "plated", "outlined"):
        # Note the argument order: this binding is
        # (col, rounding, thickness, flags), not the C++ one.
        dl.add_rect(p0, p1,
                    imgui.get_color_u32(theme_mod.with_alpha(t.border, 0.9)),
                    r, max(0.5, t.border_width))

    if st == "raised":
        dl.add_line(ImVec2(x + r, y + 1.0), ImVec2(x + w - r, y + 1.0),
                    imgui.get_color_u32(theme_mod.with_alpha(t.text, 0.07)), 1.0)

    if edge is not None and st in ("plated", "raised"):
        thick = 2.0 if st == "plated" else 1.5
        dl.add_rect_filled(
            ImVec2(x + r + 1, y), ImVec2(x + w - r - 1, y + thick),
            imgui.get_color_u32(theme_mod.with_alpha(edge, 0.9)), 1.0)


def card_head(dl, x, y, w, t=None, icon=None, title="", right=None,
              right_col=None, dot=None):
    """A card's own header: icon, tracked title, hairline, optional state.

    Returns the y the content starts at.
    """
    t = t or theme_mod.current()
    cy = y + 13.0
    if icon:
        icons.draw(icon, dl, x + 14, cy, 6.5,
                   imgui.get_color_u32(theme_mod.with_alpha(t.accent, 0.9)))
    with fonts.use("label"):
        caps(dl, x + (27 if icon else 14), y + 7, title,
             imgui.get_color_u32(t.text_dim), 1.5)
        if right:
            rw = caps_width(right, 1.3)
            rx = x + w - 14 - rw
            if dot is not None:
                dl.add_circle_filled(ImVec2(rx - 11, cy), 3.2,
                                     imgui.get_color_u32(dot))
            caps(dl, rx, y + 7, right,
                 imgui.get_color_u32(right_col or t.text_mute), 1.3)
    dl.add_line(ImVec2(x + 12, y + HEAD_H - 1),
                ImVec2(x + w - 12, y + HEAD_H - 1),
                imgui.get_color_u32(theme_mod.with_alpha(t.border, 0.75)), 1.0)
    return y + HEAD_H


def meter(dl, x0, x1, y, frac, col=None, t=None, h=4.0):
    """Track plus fill. For progress, duty cycles, anything 0..1."""
    t = t or theme_mod.current()
    col = col if col is not None else t.accent
    dl.add_rect_filled(ImVec2(x0, y), ImVec2(x1, y + h),
                       imgui.get_color_u32(theme_mod.with_alpha(t.bg, 0.9)),
                       h * 0.5)
    f = max(0.0, min(1.0, frac))
    if f > 0.001:
        dl.add_rect_filled(ImVec2(x0, y), ImVec2(x0 + (x1 - x0) * f, y + h),
                           imgui.get_color_u32(col), h * 0.5)


class card:
    """A card that sizes itself to whatever you draw inside it.

        with cards.card("network", icon="bolt", right="online",
                        right_col=t.ok) as c:
            imgui.text_wrapped("...")
            widgets.button("reconnect", c.width)

    The background cannot be drawn until the content height is known, and
    in immediate mode that is not until the content has been drawn. So the
    draw list is split in two: content goes on the front channel, the plate
    is drawn on the back one afterwards, and merging puts them in the right
    order. No measuring pass, no height passed in, no drift when a label
    changes length.

    `c.width` is the usable width inside the padding - size buttons and
    tables off that rather than off `get_content_region_avail()`, which
    still reports the full column.
    """

    def __init__(self, title=None, icon=None, right=None, right_col=None,
                 dot=None, width=0.0, edge=None, style=None, shadow=None,
                 pad=None):
        self.title = title
        self.icon = icon
        self.right = right
        self.right_col = right_col
        self.dot = dot
        self._width_arg = width
        self.edge = edge
        self.style = style
        self.shadow = shadow
        self._pad = pad
        self.width = 0.0

    def __enter__(self):
        t = theme_mod.current()
        self._t = t
        self.pad = self._pad if self._pad is not None else t.padding
        if isinstance(self.pad, (int, float)):
            self.pad = ImVec2(float(self.pad), float(self.pad))
        self._dl = imgui.get_window_draw_list()
        self._dl.channels_split(2)
        self._dl.channels_set_current(1)

        self._o = imgui.get_cursor_screen_pos()
        self._w = (self._width_arg if self._width_arg > 0
                   else imgui.get_content_region_avail().x)
        self.width = max(1.0, self._w - self.pad.x * 2)

        imgui.begin_group()
        # Reserve the header strip and the top padding as layout, so the
        # content that follows lands below them.
        imgui.dummy(ImVec2(self._w, (HEAD_H if self.title else 0.0)
                           + self.pad.y * 0.5))
        imgui.indent(self.pad.x)
        imgui.push_text_wrap_pos(self._o.x + self._w - self.pad.x)
        return self

    def __exit__(self, *exc):
        imgui.pop_text_wrap_pos()
        imgui.unindent(self.pad.x)
        imgui.dummy(ImVec2(self.width, self.pad.y * 0.5))
        imgui.end_group()
        h = imgui.get_item_rect_size().y

        self._dl.channels_set_current(0)
        plate(self._dl, self._o.x, self._o.y, self._w, h, self._t,
              edge=self.edge, style=self.style, shadow=self.shadow)
        if self.title:
            card_head(self._dl, self._o.x, self._o.y, self._w, self._t,
                      self.icon, self.title, self.right, self.right_col,
                      self.dot)
        self._dl.channels_merge()
        return False
