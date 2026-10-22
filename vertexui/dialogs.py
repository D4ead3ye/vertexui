"""Modals, and the scrim behind them.

Two projects wrote a dialog system and two wrote a scrim, which between
them is four implementations of "dim everything and put one thing in
front". The hard part is not the box - ImGui has popups - it is that a
dialog is usually opened from somewhere that is not where it is drawn: a
row's context menu, a toolbar, a keyboard shortcut. Opening a popup in
ImGui has to happen in the same ID stack it will be drawn in, which is why
every project ended up with a little registry.

    dialogs.register("confirm-delete", draw_delete)   # once, at setup
    ...
    if widgets.button("Delete"):
        dialogs.open("confirm-delete", item=row)      # from anywhere
    ...
    dialogs.draw()                                    # once, end of frame

`dialogs.confirm` is the common case in one call, and takes the callback:

    dialogs.confirm("Delete 4 orders?", on_yes=do_delete, kind="error")
"""

import time

from imgui_bundle import ImVec2, ImVec4, imgui

from . import anim, fonts, icons
from . import theme as theme_mod

__all__ = ["register", "open", "close", "is_open", "payload", "draw",
           "modal", "buttons", "confirm", "scrim"]

_dialogs = {}
_queue = []
_active = None
_payload = {}
_opened_at = 0.0


def register(name, fn):
    """Register a drawing function. Called as `fn(payload)` while open."""
    _dialogs[name] = fn
    return fn


def open(name, **payload):                 # noqa: A001 - reads correctly here
    """Request a dialog. Safe from any point in the frame, including from
    inside a table row or a popup that is about to close."""
    _queue.append((name, payload))


def close():
    global _active, _payload
    _active, _payload = None, {}


def is_open(name=None):
    return _active is not None if name is None else _active == name


def payload():
    return _payload


def scrim(amount=1.0, rounding=0.0):
    """Dim the whole window. Drawn on the foreground list, so it covers
    content without needing to be drawn after it - and covers every popup
    and modal too, which is why `modal` does not use it (see `_modal_dim`)."""
    if amount <= 0.001:
        return
    t = theme_mod.current()
    io = imgui.get_io()
    imgui.get_foreground_draw_list().add_rect_filled(
        ImVec2(0, 0), ImVec2(io.display_size.x, io.display_size.y),
        theme_mod.u32(theme_mod.sink(t.bg, 0.6, t), 0.62 * amount), rounding)


def _modal_dim(t):
    """The dim behind a modal, as ImGui's own modal background.

    ImGui draws that just beneath the modal window, and fades it in by
    itself. The foreground-list `scrim` this replaced sat above the box as
    well, so every dialog came out greyed by its own veil: the fields and
    buttons at ~40% contrast, worst on the light themes.
    """
    c = theme_mod.sink(t.bg, 0.6, t)
    try:
        imgui.get_style().set_color_(int(imgui.Col_.modal_window_dim_bg.value),
                                     ImVec4(c.x, c.y, c.z, 0.62))
    except Exception:
        pass


def draw():
    """Pump the queue and draw whatever is open. Call once per frame."""
    global _active, _payload, _opened_at
    if _queue:
        name, data = _queue.pop(0)
        if name in _dialogs:
            _active, _payload = name, data
            _opened_at = time.time()
            imgui.open_popup(f"##dlg{name}")
        else:
            print(f"[vertexui] no dialog registered as {name!r}")
    if _active is None:
        return
    fn = _dialogs.get(_active)
    if fn is None:
        close()
        return
    anim.mark_busy()
    fn(_payload)


class modal:
    """The box itself. Use inside a registered dialog function.

        def draw_delete(data):
            with dialogs.modal("confirm-delete", "Delete order?") as open_:
                if open_:
                    ui.text(...)
                    yes, no = dialogs.buttons("Delete", kind="danger")
    """

    def __init__(self, name, title=None, width=460.0, icon=None, kind=None,
                 closable=True):
        self.name = name
        self.title = title
        self.width = width
        self.icon = icon
        self.kind = kind
        self.closable = closable
        self.open = False

    def __enter__(self):
        t = theme_mod.current()
        self._t = t
        _modal_dim(t)
        io = imgui.get_io()
        w = theme_mod.px(self.width, t)
        imgui.set_next_window_size(ImVec2(w, 0))
        imgui.set_next_window_pos(
            ImVec2(io.display_size.x * 0.5, io.display_size.y * 0.5),
            imgui.Cond_.always, ImVec2(0.5, 0.5))
        imgui.push_style_var(imgui.StyleVar_.window_rounding, t.rounding_panel)
        imgui.push_style_color(imgui.Col_.popup_bg,
                               theme_mod.u32(theme_mod.lerp(t.surface, t.bg, 0.2)))
        imgui.push_style_color(imgui.Col_.border, theme_mod.u32(t.border, 0.9))
        flags = (imgui.WindowFlags_.no_resize | imgui.WindowFlags_.no_move
                 | imgui.WindowFlags_.no_saved_settings
                 | imgui.WindowFlags_.always_auto_resize
                 | imgui.WindowFlags_.no_title_bar)
        self.open, _ = imgui.begin_popup_modal(f"##dlg{self.name}", None, flags)
        if self.open and self.title:
            dl = imgui.get_window_draw_list()
            o = imgui.get_cursor_screen_pos()
            col = t.status(self.kind) if self.kind in ("ok", "warn", "error",
                                                       "info") else t.accent
            if self.icon or self.kind:
                icons.draw(self.icon or icons.STATUS_ICONS.get(self.kind, "info"),
                           dl, o.x + theme_mod.px(9, t),
                           o.y + theme_mod.px(10, t), theme_mod.px(8, t),
                           theme_mod.u32(col))
                imgui.dummy(ImVec2(theme_mod.px(24, t), 0))
                imgui.same_line()
            with fonts.use("semi"):
                imgui.text_colored(t.text, self.title)
            imgui.dummy(ImVec2(0, theme_mod.px(4, t)))
            avail = imgui.get_content_region_avail().x
            o = imgui.get_cursor_screen_pos()
            dl.add_rect_filled(ImVec2(o.x, o.y), ImVec2(o.x + avail, o.y + 1),
                               theme_mod.u32(t.border, 0.7))
            imgui.dummy(ImVec2(avail, theme_mod.px(6, t)))
        return self.open

    def __exit__(self, *exc):
        if self.open:
            # Escape closes anything closable, which users expect and
            # which a hand-rolled modal almost never remembers.
            if self.closable and imgui.is_key_pressed(imgui.Key.escape):
                imgui.close_current_popup()
                close()
            imgui.end_popup()
        imgui.pop_style_color(2)
        imgui.pop_style_var()
        return False


def buttons(confirm_text="Save", cancel_text="Cancel", kind="primary",
            width=120.0, extra=None):
    """A right-aligned button row. Returns `(confirmed, cancelled)`.

    Confirm on the right, because that is where it is on this platform,
    and a dialog that puts it elsewhere costs its user a beat every time.
    """
    from . import widgets
    t = theme_mod.current()
    imgui.dummy(ImVec2(0, theme_mod.px(6, t)))
    w = theme_mod.px(width, t)
    gap = theme_mod.px(8, t)
    n = 2 + (1 if extra else 0)
    total = w * n + gap * (n - 1)
    avail = imgui.get_content_region_avail().x
    imgui.dummy(ImVec2(max(0.0, avail - total), 0))
    imgui.same_line()

    did_extra = False
    if extra:
        did_extra = widgets.button(extra, width, height=32.0, key="dlg:extra")
        imgui.same_line(0, gap)
    cancelled = widgets.button(cancel_text, width, height=32.0, key="dlg:cancel")
    imgui.same_line(0, gap)
    confirmed = widgets.button(confirm_text, width, height=32.0,
                               primary=(kind in ("primary", "danger")),
                               key="dlg:ok")
    if cancelled:
        imgui.close_current_popup()
        close()
    if confirmed:
        imgui.close_current_popup()
        close()
    return (confirmed, cancelled, did_extra) if extra else (confirmed, cancelled)


def confirm(question, on_yes=None, body="", kind="warn", yes="Confirm",
            no="Cancel", name="vui-confirm"):
    """The whole yes/no dance in one call.

    Registers itself the first time it is used, so there is nothing to set
    up and nothing to remember to draw - just call it and then call
    `dialogs.draw()` as usual.
    """
    if name not in _dialogs:
        def _draw(data):
            t = theme_mod.current()
            with modal(name, data.get("question"), kind=data.get("kind")) as open_:
                if not open_:
                    return
                if data.get("body"):
                    imgui.push_text_wrap_pos(
                        imgui.get_cursor_pos().x
                        + imgui.get_content_region_avail().x)
                    imgui.text_colored(t.text_dim, data["body"])
                    imgui.pop_text_wrap_pos()
                ok, _no = buttons(data.get("yes", "Confirm"),
                                  data.get("no", "Cancel"),
                                  kind="danger" if data.get("kind") == "error"
                                  else "primary")
                if ok and data.get("on_yes"):
                    data["on_yes"]()
        register(name, _draw)
    open(name, question=question, body=body, kind=kind, yes=yes, no=no,
         on_yes=on_yes)
