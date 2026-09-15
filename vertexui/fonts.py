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

Roles, not filenames. Seven of them, and the spread between them is the
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
    "Match interface": (None, 1.0),
}

MONO_FACES = {
    "Cascadia Mono": ("CascadiaMono.ttf", "consola.ttf"),
    "Consolas": ("consola.ttf",),
    "Lucida Console": ("lucon.ttf", "consola.ttf"),
    "Courier New": ("cour.ttf",),
}


def build_faces(ui="Segoe UI Variable", display="Bahnschrift",
                mono="Cascadia Mono", base=17.5):
    """Build the seven roles from three face choices.

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


def available() -> bool:
    return bool(_loaded)


def roles():
    """Which roles actually loaded - what a diagnostics panel reports."""
    return sorted(_loaded)


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
