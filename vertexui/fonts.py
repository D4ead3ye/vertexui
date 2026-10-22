"""Real typefaces instead of ImGui's built-in bitmap font.

ImGui ships Proggy: a 13px bitmap face. It is crisp and it is unmistakably
from 2005, and no amount of restyling rescues a panel drawn in it. Loading
system faces costs nothing to ship and survives being frozen into a
one-file exe, which bundled font assets did not.

    from vertexui import fonts
    params.callbacks.load_additional_fonts = fonts.loader()
    ...
    with fonts.use("semi"):
        imgui.text("heading")

Roles, not filenames. Eight of them, and the spread between them is the
point: one face doing every job is most of what makes an interface look
like a default, because a body face set at 35px is just big body text where
a display face set at 35px reads as an instrument.

    ui      body text, the default
    semi    headings and emphasis - the bold of the interface face
    title   the display face at heading size
    mono    logs, tables, anything that has to line up in columns
    label   the tracked micro-labels on cards (see widgets.caps)
    big     a readout you are meant to see from across the room
    huge    the one number a screen is about
    cjk     a face that has the CJK block, for Japanese sub-labels and
            any locale `i18n` grows into - silently absent where the
            system has no such face, so test it with `fonts.has("cjk")`

A project on a machine without Segoe, or one that simply wants a different
pairing, passes its own mapping and every widget follows.
"""

import os
from pathlib import Path

from imgui_bundle import imgui

# (regular candidates, bold candidates), tried in order. Segoe UI Variable
# is the modern Windows face and is noticeably cleaner than plain Segoe UI
# at small sizes; it is a variable font, so the bold role falls to
# Semibold, which pairs with it correctly.
UI_FACES = {
    "Segoe UI Variable": (("SegUIVar.ttf", "segoeui.ttf"),
                          ("seguisb.ttf", "segoeuib.ttf")),
    "Segoe UI": (("segoeui.ttf",), ("seguisb.ttf", "segoeuib.ttf")),
    "Bahnschrift": (("bahnschrift.ttf",), ("bahnschrift.ttf",)),
    "Calibri": (("calibri.ttf",), ("calibrib.ttf",)),
    "Tahoma": (("tahoma.ttf",), ("tahomabd.ttf",)),
    "Verdana": (("verdana.ttf",), ("verdanab.ttf",)),
    "Arial": (("arial.ttf",), ("arialbd.ttf",)),
    # Serifs, for themes where the interface is meant to read as printed
    # matter rather than as software.
    "Georgia": (("georgia.ttf",), ("georgiab.ttf",)),
    "Cambria": (("cambria.ttc", "cambriab.ttf"), ("cambriab.ttf",)),
    "Constantia": (("constan.ttf",), ("constanb.ttf",)),
    "Palatino": (("pala.ttf",), ("palab.ttf",)),
}

# The readouts and micro-labels get their own face: (candidates, scale).
# The scale exists because faces disagree about how much of the em the
# x-height takes, so a matched em size is not a matched apparent size -
# Bahnschrift at the same size renders noticeably larger than the body
# face, and left unscaled it breaks card layouts that fit around it.
DISPLAY_FACES = {
    # DIN-derived, technical, and the reason a panel stops looking stock.
    "Bahnschrift": (("bahnschrift.ttf",), 0.88),
    "Cascadia Mono": (("CascadiaMono.ttf", "consola.ttf"), 0.92),
    "Segoe UI Semibold": (("seguisb.ttf", "segoeuib.ttf"), 1.0),
    "Palatino": (("palab.ttf", "pala.ttf"), 0.96),
    "Georgia": (("georgiab.ttf", "georgia.ttf"), 0.96),
    "Impact": (("impact.ttf",), 0.92),
    "Match interface": (None, 1.0),
}

MONO_FACES = {
    "Cascadia Mono": ("CascadiaMono.ttf", "consola.ttf"),
    "Consolas": ("consola.ttf",),
    "Lucida Console": ("lucon.ttf", "consola.ttf"),
    "Courier New": ("cour.ttf",),
}

# A face that actually has the CJK block, for the `cjk` role. None of the
# interface faces do, and ImGui draws nothing at all for a codepoint the
# face is missing - so a Japanese sub-label without this is an empty gap.
#
# This used to be unaffordable: the atlas was built once at startup and a
# Japanese range meant rasterising thousands of glyphs into a megabyte of
# texture for the four characters a panel actually prints. imgui-bundle
# 1.92 rasterises on demand, so registering the face costs a file handle
# and each glyph is baked the first time it is drawn. Which is why this
# role is always loaded and not an opt-in: it is free until used.
CJK_FACES = ("msgothic.ttc", "YuGothR.ttc", "YuGothM.ttc", "meiryo.ttc",
             "simsun.ttc", "malgun.ttf")


def build_faces(ui="Segoe UI Variable", display="Bahnschrift",
                mono="Cascadia Mono", base=17.5):
    """Build the eight roles from three face choices.

    This is what a settings panel drives: the user picks an interface face,
    a readouts face and a terminal face, and the sizes and the display
    face's own scale correction fall out of it.

    Unknown names fall back rather than raising, so a settings file naming
    a face that a later version dropped still starts.
    """
    ui_names, bold = UI_FACES.get(ui, UI_FACES["Segoe UI Variable"])
    disp, scale = DISPLAY_FACES.get(display, DISPLAY_FACES["Bahnschrift"])
    if disp is None:                       # "Match interface"
        disp, scale = bold, 1.0
    mono_names = MONO_FACES.get(mono, MONO_FACES["Cascadia Mono"])
    return {
        "ui":    (ui_names, base),
        "semi":  (bold, base),
        "title": (disp, 23.0 * scale),
        "mono":  (mono_names, 14.0),
        "label": (disp, 13.5 * scale),     # the tracked uppercase labels
        "big":   (disp, 27.0 * scale),
        "huge":  (disp, 37.0 * scale),
        # Kanji are full-width, so matched to the em they read a size
        # larger than the Latin beside them; 0.78 lines the two up.
        "cjk":   (CJK_FACES, base * 0.78),
    }


# role -> (candidate filenames in order, size in px)
DEFAULT_FACES = build_faces()

_loaded = {}


def loader(faces=None, fonts_dir=None, default_role="ui"):
    """Return a callback for hello_imgui's `load_additional_fonts`."""
    faces = faces or DEFAULT_FACES
    directory = Path(fonts_dir or (Path(os.environ.get("WINDIR", r"C:\Windows"))
                                   / "Fonts"))

    def load():
        io = imgui.get_io()
        _loaded.clear()
        for role, (names, size) in faces.items():
            for name in names:
                path = directory / name
                if not path.exists():
                    continue
                cfg = imgui.ImFontConfig()
                # Small UI text on a dark ground is where under-sampled
                # glyphs look muddiest.
                cfg.oversample_h = 3
                try:
                    font = io.fonts.add_font_from_file_ttf(str(path), size, cfg)
                except Exception:
                    continue
                # Keep the size: this ImGui wants push_font(font, size) and
                # rejects a bare font handle.
                _loaded[role] = (font, size)
                break
        if default_role in _loaded:
            io.font_default = _loaded[default_role][0]

    return load


_pending = None


def reload(faces=None, default_role="ui"):
    """Swap the typefaces at runtime.

    Needs an ImGui context and must not run while a font is pushed, so
    prefer `request()` unless you know you are at the top of a frame.

    The atlas is cleared first: without that every swap adds another set
    of faces to it, and a user playing with a theme picker would grow the
    texture without limit. Cleared and re-added it stays at exactly the
    number of roles, which is what the font-swap test checks.
    """
    io_ = imgui.get_io()
    io_.fonts.clear_fonts()
    loader(faces, default_role=default_role)()
    return roles()


def request(faces=None, default_role="ui"):
    """Ask for a reload at the start of the next frame. Safe anywhere."""
    global _pending
    _pending = (faces, default_role)


def pump():
    """Apply a requested reload. Call once at the top of a frame.

    `compose.App` does this for you; an application driving its own loop
    should call it before drawing anything.
    """
    global _pending
    if _pending is None:
        return False
    faces, role = _pending
    _pending = None
    try:
        reload(faces, role)
        return True
    except Exception as exc:          # pragma: no cover
        print(f"[vertexui] font reload failed: {exc!r}")
        return False


def available() -> bool:
    return bool(_loaded)


def roles():
    """Which roles actually loaded - what a diagnostics panel reports."""
    return sorted(_loaded)


def has(role: str) -> bool:
    """Whether a role loaded. `use` degrades silently either way; this is
    for the caller that has to *reserve space* for text it may not be able
    to draw - a header that leaves a gap for a Japanese sub-label on a
    machine with no CJK face has made the gap the design."""
    return role in _loaded


def size(role: str, fallback: float = 17.0) -> float:
    """The px size a role loaded at, for laying out around it."""
    entry = _loaded.get(role)
    return entry[1] if entry else fallback


class use:
    """`with fonts.use("semi"):` - silently does nothing if that role never
    loaded, so a machine missing a face still renders."""

    def __init__(self, role: str):
        self.entry = _loaded.get(role)

    def __enter__(self):
        if self.entry is not None:
            imgui.push_font(*self.entry)
        return self

    def __exit__(self, *exc):
        if self.entry is not None:
            imgui.pop_font()
        return False
