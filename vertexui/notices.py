"""Telling the user something, in the window rather than over it.

`toasts` draws on a layered window above every other application, which is
right for a tool you are not looking at and wrong for a dialog box you
are. These are the in-window surfaces, in rising order of how much they
interrupt:

    note        a help line under a control. Quiet, permanent, explains.
    banner      a strip across a screen. Something is wrong or notable.
    empty_state a whole panel saying there is nothing here yet, and what
                to do about it.
    Tray        transient messages stacked in a corner of the window.

`note` is here because six separate projects wrote it before this module
existed, and two of them were byte-for-byte identical - same signature,
same `rule, pad = 3.0, 9.0`, same wrap arithmetic. That is the clearest
signal a toolkit can get that something is missing from it.
"""

import time

from imgui_bundle import ImVec2, imgui

from . import anim, fonts, icons
from . import theme as theme_mod

__all__ = ["note", "banner", "empty_state", "Tray", "KINDS"]

KINDS = ("info", "ok", "warn", "error")


def _kind_colour(t, kind):
    return t.status(kind) if kind in KINDS else t.accent


def note(text, tone=None, icon=None, width=0.0):
    """A help line that belongs to the control above it.

    A recessed ground and an accent rule down the left edge - not a
    border, because a border makes it a separate object and the point is
    that it is part of the thing above.
    """
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    w = theme_mod.px(width, t) if width > 0 else \
        max(theme_mod.px(120, t), imgui.get_content_region_avail().x - 4.0)
    rule = theme_mod.px(3.0, t)
    pad = theme_mod.px(9.0, t)
    ic = theme_mod.px(17, t) if icon else 0.0
    inner = w - rule - pad * 2 - ic
    h = imgui.calc_text_size(text, wrap_width=inner).y + theme_mod.px(12, t)
    p = imgui.get_cursor_screen_pos()

    dl.add_rect_filled(ImVec2(p.x, p.y), ImVec2(p.x + w, p.y + h),
                       theme_mod.u32(t.bg, 0.85), t.rounding)
    dl.add_rect(ImVec2(p.x, p.y), ImVec2(p.x + w, p.y + h),
                theme_mod.u32(t.border, 0.55), t.rounding, t.border_width)
    dl.add_rect_filled(ImVec2(p.x, p.y + 2), ImVec2(p.x + rule, p.y + h - 2),
                       theme_mod.u32(tone or t.accent_bright, 0.85), 1.0)
    if icon:
        icons.draw(icon, dl, p.x + rule + pad + ic * 0.4, p.y + h * 0.5,
                   theme_mod.px(6.5, t), theme_mod.u32(tone or t.text_mute))
    imgui.set_cursor_screen_pos(ImVec2(p.x + rule + pad + ic,
                                       p.y + theme_mod.px(6, t)))
    imgui.push_text_wrap_pos(imgui.get_cursor_pos().x + inner)
    imgui.text_colored(t.text_dim, text)
    imgui.pop_text_wrap_pos()
    imgui.set_cursor_screen_pos(ImVec2(p.x, p.y + h + theme_mod.px(5, t)))
    imgui.dummy(ImVec2(w, 0))


def banner(text, kind="info", action=None, on_close=None, width=0.0):
    """A strip across the top of a screen.

    `action` is `(label, callback)`. Returns True if it was dismissed.
    Louder than a note and quieter than a dialog: use it for a condition
    that persists - demo data loaded, saving failed, an update waiting -
    rather than for an event, which is what a toast is for.
    """
    t = theme_mod.current()
    from . import widgets
    dl = imgui.get_window_draw_list()
    col = _kind_colour(t, kind)
    p = imgui.get_cursor_screen_pos()
    w = theme_mod.px(width, t) if width > 0 else imgui.get_content_region_avail().x
    h = theme_mod.px(40, t)
    light = theme_mod.is_light(t)

    dl.add_rect_filled(ImVec2(p.x, p.y), ImVec2(p.x + w, p.y + h),
                       theme_mod.u32(col, 0.13 if light else 0.16), t.rounding)
    dl.add_rect(ImVec2(p.x, p.y), ImVec2(p.x + w, p.y + h),
                theme_mod.u32(col, 0.45), t.rounding, t.border_width)
    icons.draw(icons.STATUS_ICONS.get(kind, "info"), dl,
               p.x + theme_mod.px(21, t), p.y + h * 0.5, theme_mod.px(7.5, t),
               theme_mod.u32(col))

    from . import fmt
    right = theme_mod.px(14, t)
    if on_close:
        right += theme_mod.px(30, t)
    act_w = 0.0
    if action:
        act_w = max(theme_mod.px(110, t),
                    imgui.calc_text_size(action[0]).x + theme_mod.px(34, t))
        right += act_w + theme_mod.px(10, t)
    avail = w - theme_mod.px(40, t) - right
    label = fmt.ellipsis(text, avail)
    ts = imgui.calc_text_size(label)
    dl.add_text(ImVec2(p.x + theme_mod.px(38, t), p.y + (h - ts.y) * 0.5),
                theme_mod.u32(t.text), label)
    imgui.dummy(ImVec2(w, h))

    closed = False
    x = p.x + w - theme_mod.px(14, t)
    if on_close:
        x -= theme_mod.px(26, t)
        imgui.set_cursor_screen_pos(ImVec2(x, p.y + (h - theme_mod.px(26, t)) * 0.5))
        if widgets.icon_button("cross", 26.0, tooltip="Dismiss",
                               key=f"ban:{text[:18]}:x"):
            on_close()
            closed = True
        x -= theme_mod.px(8, t)
    if action:
        bh = theme_mod.px(28, t)
        imgui.set_cursor_screen_pos(ImVec2(x - act_w, p.y + (h - bh) * 0.5))
        if widgets.button(action[0], act_w / t.ui_scale, height=28.0,
                          key=f"ban:{text[:18]}:a"):
            action[1]()
    imgui.set_cursor_screen_pos(ImVec2(p.x, p.y + h))
    imgui.dummy(ImVec2(0, theme_mod.px(6, t)))
    return closed


def empty_state(icon, title, body="", actions=None, height=0.0):
    """A panel that explains why it is blank and what would fill it.

    An empty table that just shows its headers reads as broken. This is
    the difference between "no results" and "you have not added anything
    yet, here is the button".

    `actions` is a sequence of `(label, callback[, primary])`.
    """
    t = theme_mod.current()
    from . import widgets
    dl = imgui.get_window_draw_list()
    avail = imgui.get_content_region_avail()
    h = theme_mod.px(height, t) if height > 0 else max(theme_mod.px(180, t),
                                                       avail.y * 0.6)
    p = imgui.get_cursor_screen_pos()
    cx = p.x + avail.x * 0.5
    cy = p.y + h * 0.42

    dl.add_circle_filled(ImVec2(cx, cy - theme_mod.px(26, t)),
                         theme_mod.px(30, t),
                         theme_mod.u32(theme_mod.sink(t.surface, 0.3, t), 0.9))
    icons.draw(icon, dl, cx, cy - theme_mod.px(26, t), theme_mod.px(14, t),
               theme_mod.u32(t.text_mute))

    with fonts.use("semi"):
        ts = imgui.calc_text_size(title)
        dl.add_text(ImVec2(cx - ts.x * 0.5, cy + theme_mod.px(16, t)),
                    theme_mod.u32(t.text), title)
    if body:
        wrap = min(theme_mod.px(380, t), avail.x * 0.8)
        bs = imgui.calc_text_size(body, wrap_width=wrap)
        imgui.set_cursor_screen_pos(ImVec2(cx - wrap * 0.5,
                                           cy + theme_mod.px(40, t)))
        imgui.push_text_wrap_pos(imgui.get_cursor_pos().x + wrap)
        imgui.text_colored(t.text_mute, body)
        imgui.pop_text_wrap_pos()
        after = cy + theme_mod.px(46, t) + bs.y
    else:
        after = cy + theme_mod.px(46, t)

    if actions:
        widths = [max(theme_mod.px(120, t),
                      imgui.calc_text_size(a[0]).x + theme_mod.px(34, t))
                  for a in actions]
        total = sum(widths) + theme_mod.px(10, t) * (len(actions) - 1)
        imgui.set_cursor_screen_pos(ImVec2(cx - total * 0.5, after))
        for i, a in enumerate(actions):
            if i:
                imgui.same_line(0, theme_mod.px(10, t))
            if widgets.button(a[0], widths[i] / t.ui_scale, height=32.0,
                              primary=(len(a) > 2 and a[2]),
                              key=f"empty:{title[:14]}:{i}"):
                a[1]()
    imgui.set_cursor_screen_pos(ImVec2(p.x, p.y + h))
    imgui.dummy(ImVec2(avail.x, 0))


class Tray:
    """Transient messages stacked in a corner of the window.

    The sibling of `toasts`, for applications that do not want a layered
    OS window - a tool inside someone else's host, anything that has to
    survive being screen-captured, anything that is not Windows. Same four
    kinds, same collapse-repeats behaviour, drawn on the window's own list.

        tray = notices.Tray()
        ...
        tray.push("ok", "Saved")
        tray.draw()        # last thing in the frame
    """

    def __init__(self, seconds=4.0, corner="tr", width=300.0, max_visible=4,
                 margin=14.0):
        self.seconds = float(seconds)
        self.corner = corner
        self.width = width
        self.max_visible = int(max_visible)
        self.margin = margin
        self.items = []

    def push(self, kind, text):
        """Add one. A repeat within two seconds collapses into a count."""
        now = time.time()
        for it in self.items:
            if it["text"] == text and it["kind"] == kind \
                    and now - it["born"] < 2.0:
                it["born"], it["n"] = now, it["n"] + 1
                return
        self.items.append({"kind": kind, "text": text, "born": now, "n": 1,
                           "y": None})
        if len(self.items) > self.max_visible:
            del self.items[0]

    notify = push

    def clear(self):
        self.items.clear()

    def draw(self):
        """Draw and expire. Call once, after everything else."""
        if not self.items:
            return
        t = theme_mod.current()
        from . import fmt
        dl = imgui.get_window_draw_list()
        io = imgui.get_io()
        now = time.time()
        self.items = [i for i in self.items if now - i["born"] < self.seconds]
        if not self.items:
            return
        anim.mark_busy()

        w = theme_mod.px(self.width, t)
        h = theme_mod.px(34, t)
        gap = theme_mod.px(8, t)
        m = theme_mod.px(self.margin, t)
        right = "r" in self.corner
        x = (io.display_size.x - w - m) if right else m
        base = m if "t" in self.corner else \
            io.display_size.y - m - len(self.items) * (h + gap)

        for i, it in enumerate(self.items):
            age = now - it["born"]
            # in quickly, hold, then out - and the slide comes from the
            # edge it is anchored to, so it never crosses the content
            appear = min(1.0, age / 0.22)
            leave = max(0.0, (age - (self.seconds - 0.3)) / 0.3)
            slide = (1.0 - anim.ease_out(appear)) + leave
            alpha = min(anim.ease_out(appear), 1.0 - leave)
            if alpha <= 0.01:
                continue
            target = base + i * (h + gap)
            it["y"] = target if it["y"] is None else \
                it["y"] + (target - it["y"]) * min(1.0, io.delta_time * 12.0)
            px = x + (w * 0.35 * slide * (1 if right else -1))
            col = _kind_colour(t, it["kind"])

            dl.add_rect_filled(ImVec2(px, it["y"]), ImVec2(px + w, it["y"] + h),
                               theme_mod.u32(theme_mod.lerp(t.surface, t.bg, 0.25),
                                             0.96 * alpha), t.rounding)
            dl.add_rect(ImVec2(px, it["y"]), ImVec2(px + w, it["y"] + h),
                        theme_mod.u32(t.border, 0.7 * alpha), t.rounding,
                        t.border_width)
            dl.add_rect_filled(ImVec2(px, it["y"] + 3),
                               ImVec2(px + theme_mod.px(3, t), it["y"] + h - 3),
                               theme_mod.u32(col, 0.95 * alpha), 1.5)
            icons.draw(icons.STATUS_ICONS.get(it["kind"], "info"), dl,
                       px + theme_mod.px(20, t), it["y"] + h * 0.5,
                       theme_mod.px(6.5, t), theme_mod.u32(col, alpha))
            label = it["text"] if it["n"] == 1 else f"{it['text']}  x{it['n']}"
            label = fmt.ellipsis(label, w - theme_mod.px(44, t))
            ts = imgui.calc_text_size(label)
            dl.add_text(ImVec2(px + theme_mod.px(34, t),
                               it["y"] + (h - ts.y) * 0.5),
                        theme_mod.u32(t.text, alpha), label)
