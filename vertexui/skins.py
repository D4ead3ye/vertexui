"""Painter slots, for themes that need more than a palette.

A `Profile` can say a card is 2px-radius amber on slate. It cannot say a
card is parchment held in an engraved brass frame with notched corners and
a cross-hatched ink shadow - that is not configuration, it is drawing.

So a `Skin` is a small set of optional painters. Where one is set, the
widget calls it instead of its own; where it is not, nothing changes and
the widget draws as it always did. No subclassing, no flags threaded
through call sites, and a theme that only wants a palette never touches
this module.

    skins.use(Skin(name="mine", plate=my_plate, spinner=my_spinner))
    skins.use(None)                 # back to the stock look

Every painter is optional and every one may return False to mean "I did
not handle this, draw it normally", which is what lets a skin restyle only
the `raised` card style and leave the other three alone.
"""

from dataclasses import dataclass, field

__all__ = ["Skin", "use", "current", "clear", "painter",
           "press_depth", "press_snap", "corner", "extra"]


@dataclass
class Skin:
    """Drawing overrides. Every field is optional.

    plate(dl, x, y, w, h, t, edge, style, shadow) -> bool
        The background of a card. Return True if you drew it.
    head(dl, x, y, w, t, icon, title, right, right_col, dot) -> float | None
        A card's header. Return the y content should start at, or None to
        let the stock header draw. A skin that wants a title *bar* rather
        than a label and a rule needs this - the stock header cannot be
        talked into one by configuration.
    frame(dl, x, y, w, h, t, rect_kind) -> bool
        A generic framed surface - inputs, wells, table grounds.
    hover_aura(dl, x0, y0, x1, y1, t, amount, kind)
        Drawn over a control that is being hovered. `amount` is 0..1.
    press(dl, x0, y0, x1, y1, t, amount)
        Drawn over a control that is being pressed.
    tabs(dl, x, y, w, h, t, rects, index, hots) -> bool
        The navigation strip's ground and its active indicator. `rects` is
        one (x, width) per tab, `hots` one 0..1 hover amount. Labels stay
        with the widget - a skin owns the chrome, not the text. Return
        True if you drew it.
    spinner(dl, cx, cy, r, t, phase)
        The busy indicator. `phase` is seconds, already running.
    background(dl, x, y, w, h, t, now)
        Painted under the whole window, before any content.
    corner(t) -> float
        Override the corner radius a widget would use.
    """

    name: str = "plain"
    plate: object = None
    head: object = None
    frame: object = None
    hover_aura: object = None
    press: object = None
    spinner: object = None
    background: object = None
    tabs: object = None
    #: A radius override for widgets that draw their own rounded shapes
    #: and have no painter of their own. A cheap way to make a theme
    #: squarer or rounder without writing any drawing at all.
    corner: object = None
    press_depth: float = 1.0
    #: Skip the press easing entirely. Some looks are *about* not being
    #: smooth - a 1999 button drops the instant you touch it.
    press_snap: bool = False
    extras: dict = field(default_factory=dict)


_active = None


def use(skin):
    """Install a skin, or `None` to go back to the stock drawing."""
    global _active
    _active = skin
    return _active


def current():
    """The active skin, or None. Callers must handle None - that is the
    normal case and it is what keeps this free for themes that do not
    need it."""
    return _active


def clear():
    return use(None)


def painter(name):
    """The named painter if a skin provides one, else None.

        p = skins.painter("plate")
        if p is None or not p(dl, x, y, w, h, t, edge, style, shadow):
            ... draw it the usual way ...
    """
    s = _active
    return getattr(s, name, None) if s is not None else None


def press_depth():
    s = _active
    return s.press_depth if s is not None else 1.0


def corner(default, t=None):
    """The radius a widget should use, honouring any skin override."""
    s = _active
    fn = getattr(s, "corner", None) if s is not None else None
    if fn is None:
        return default
    try:
        from . import theme as theme_mod
        got = fn(t or theme_mod.current())
        return default if got is None else float(got)
    except Exception:
        return default


def press_snap():
    s = _active
    return bool(s.press_snap) if s is not None else False


def extra(key, default=None):
    """A skin's own setting, for anything too specific to be a field."""
    s = _active
    return s.extras.get(key, default) if s is not None else default
