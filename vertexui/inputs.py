"""Controls for entering and choosing things.

The toolkit had buttons, checkboxes and tabs - everything you need to
*trigger* something and nothing you need to *enter* something. Every
project that had a form wrote this layer itself.

    changed, name = inputs.text_input("name", name, hint="Supplier")
    only_open = inputs.switch("Open orders only", only_open)
    view = inputs.segmented("view", ["Day", "Week", "Month"], view)

Returns follow ImGui's shape for the ones that wrap it - `(changed,
value)` - and plain values for the ones drawn here. Every control takes a
`key` because widget identity in ImGui comes from the label, and two
fields labelled "Name" in one window is a hard error rather than a
cosmetic one.
"""

from imgui_bundle import ImVec2, imgui

from . import anim, fonts, icons
from . import theme as theme_mod

__all__ = ["field_label", "text_input", "search_input", "switch",
           "segmented", "chip", "delta", "stepper"]


def _focus_ring(t, active):
    """An accent outline on the control that was just drawn."""
    key = f"ring:{imgui.get_item_rect_min().x:.0f}:{imgui.get_item_rect_min().y:.0f}"
    hot = anim.to(key, 1.0 if active else 0.0, 18.0)
    if hot <= 0.01:
        return
    dl = imgui.get_window_draw_list()
    a, b = imgui.get_item_rect_min(), imgui.get_item_rect_max()
    dl.add_rect(ImVec2(a.x - 1, a.y - 1), ImVec2(b.x + 1, b.y + 1),
                theme_mod.u32(t.accent, 0.75 * hot), t.rounding,
                max(1.0, t.border_width + 0.4))


def field_label(text, hint=None):
    """A label above a field, with an optional quieter hint beside it."""
    t = theme_mod.current()
    with fonts.use("label"):
        imgui.text_colored(t.text_dim, text)
        if hint:
            imgui.same_line(0, 8)
            imgui.text_colored(t.text_mute, hint)


def text_input(key, value, hint="", width=0.0, height=0.0, password=False,
               enabled=True, label=None, flags=0):
    """A themed text field. Returns `(changed, value)`.

    `hint` is placeholder text shown while empty - which is the right
    place for an example, and the wrong place for the field's name. Pass
    `label` for the name; it goes above, where it stays readable once
    something has been typed.
    """
    t = theme_mod.current()
    if label:
        field_label(label)
    w = theme_mod.px(width, t) if width > 0 else \
        max(60.0, imgui.get_content_region_avail().x)
    imgui.push_id(key)
    imgui.push_item_width(w)
    imgui.push_style_var(imgui.StyleVar_.frame_rounding, t.rounding)
    imgui.push_style_color(imgui.Col_.frame_bg,
                           theme_mod.u32(theme_mod.sink(t.surface, 0.45, t)))
    imgui.push_style_color(imgui.Col_.frame_bg_hovered,
                           theme_mod.u32(t.surface_hover))
    imgui.push_style_color(imgui.Col_.frame_bg_active,
                           theme_mod.u32(t.surface_hover))
    if not enabled:
        flags |= imgui.InputTextFlags_.read_only
    if password:
        flags |= imgui.InputTextFlags_.password
    if height > 0:
        changed, value = imgui.input_text_multiline(
            "##f", value, ImVec2(w, theme_mod.px(height, t)), flags)
    elif hint:
        changed, value = imgui.input_text_with_hint("##f", hint, value, flags)
    else:
        changed, value = imgui.input_text("##f", value, flags)
    active = imgui.is_item_active()
    imgui.pop_style_color(3)
    imgui.pop_style_var()
    imgui.pop_item_width()
    _focus_ring(t, active)
    imgui.pop_id()
    return changed, value


def search_input(key, value, hint="Search", width=260.0, on_clear=None):
    """A field with a magnifier and, once there is something in it, a way
    to empty it. Returns `(changed, value)`."""
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    o = imgui.get_cursor_screen_pos()
    w = theme_mod.px(width, t)
    icons.draw("search", dl, o.x + theme_mod.px(15, t),
               o.y + imgui.get_frame_height() * 0.5, theme_mod.px(7, t),
               theme_mod.u32(t.text_mute))
    imgui.dummy(ImVec2(theme_mod.px(26, t), 0))
    imgui.same_line(0, 0)
    changed, value = text_input(key, value, hint=hint,
                                width=(w - theme_mod.px(26, t)) / t.ui_scale)
    if value:
        imgui.same_line(0, 6)
        from . import widgets
        if widgets.icon_button("cross", 24.0, tooltip="Clear",
                               key=f"{key}:clear"):
            value, changed = "", True
            if on_clear:
                on_clear()
    return changed, value


def switch(label, value: bool, key=None, width=42.0, enabled=True) -> bool:
    """A sliding toggle.

    Not a checkbox with a different skin: a checkbox says "this item is
    selected", a switch says "this setting is on", and a list of five
    checkboxes reads as a multi-select where five switches read as five
    independent settings.
    """
    t = theme_mod.current()
    key = key or label
    dl = imgui.get_window_draw_list()
    w = theme_mod.px(width, t)
    h = w * 0.56
    o = imgui.get_cursor_screen_pos()
    pad = max(2.0, h * 0.12)

    imgui.invisible_button(f"##sw{key}", ImVec2(w, max(h, imgui.get_text_line_height())))
    hovered = imgui.is_item_hovered() and enabled
    clicked = imgui.is_item_clicked() and enabled
    if clicked:
        from . import sound
        value = not value
        sound.play("click")
    from . import widgets
    widgets.hover_tick(f"sw:{key}", hovered)

    on = anim.to(f"sw:{key}:on", 1.0 if value else 0.0, 16.0)
    hot = anim.to(f"sw:{key}:hot", 1.0 if hovered else 0.0, 14.0)
    y0 = o.y + (imgui.get_text_line_height() - h) * 0.5
    track = anim.lerp_col(theme_mod.sink(t.surface, 0.35, t),
                          t.accent if enabled else t.text_mute, on)
    dl.add_rect_filled(ImVec2(o.x, y0), ImVec2(o.x + w, y0 + h),
                       theme_mod.u32(track, 1.0 if enabled else 0.5), h * 0.5)
    if hot > 0.01 and not value:
        dl.add_rect(ImVec2(o.x, y0), ImVec2(o.x + w, y0 + h),
                    theme_mod.u32(t.text_mute, 0.5 * hot), h * 0.5, 1.0)
    kx = o.x + pad + (w - h) * on + (h - pad * 2) * 0.5
    dl.add_circle_filled(ImVec2(kx, y0 + h * 0.5), (h - pad * 2) * 0.5,
                         theme_mod.u32(theme_mod.ink(t, track)
                                       if value else t.text_dim))
    if label:
        imgui.same_line(0, 9)
        imgui.text_colored(t.text if enabled else t.text_mute, label)
    return value


def segmented(key, options, index, width=0.0, height=30.0, equal=True):
    """One choice from a few, as a single control.

    Better than a row of buttons when the options are exclusive and few:
    the shared ground says "pick one of these", which a row of separate
    buttons does not.
    """
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    h = theme_mod.px(height, t)
    pad = theme_mod.px(12, t)
    widths = [max(theme_mod.px(44, t), imgui.calc_text_size(o).x + pad * 2)
              for o in options]
    if equal:
        widths = [max(widths)] * len(options)
    total = theme_mod.px(width, t) if width > 0 else sum(widths) + 6
    if width > 0:
        widths = [(total - 6) / len(options)] * len(options)
    o = imgui.get_cursor_screen_pos()

    dl.add_rect_filled(ImVec2(o.x, o.y), ImVec2(o.x + total, o.y + h),
                       theme_mod.u32(theme_mod.sink(t.surface, 0.45, t)),
                       t.rounding)
    # the indicator slides rather than jumping, which is what makes the
    # control read as one thing with a moving selection
    xs = [o.x + 3 + sum(widths[:i]) for i in range(len(options))]
    tx = anim.to(f"seg:{key}:x", xs[max(0, min(index, len(options) - 1))], 18.0)
    tw = anim.to(f"seg:{key}:w", widths[max(0, min(index, len(options) - 1))], 18.0)
    dl.add_rect_filled(ImVec2(tx, o.y + 3), ImVec2(tx + tw, o.y + h - 3),
                       theme_mod.u32(t.accent, 0.92), max(1.0, t.rounding - 2))

    out = index
    for i, label in enumerate(options):
        imgui.set_cursor_screen_pos(ImVec2(xs[i], o.y))
        imgui.invisible_button(f"##seg{key}{i}", ImVec2(widths[i], h))
        hovered = imgui.is_item_hovered()
        from . import widgets
        widgets.hover_tick(f"seg:{key}:{i}", hovered)
        if imgui.is_item_clicked():
            from . import sound
            out = i
            sound.play("click")
        sel = i == index
        col = theme_mod.ink(t, t.accent) if sel else \
            anim.lerp_col(t.text_dim, t.text,
                          anim.to(f"seg:{key}:{i}:h", 1.0 if hovered else 0.0, 14.0))
        ts = imgui.calc_text_size(label)
        with fonts.use("semi" if sel else "ui"):
            dl.add_text(ImVec2(xs[i] + (widths[i] - ts.x) * 0.5,
                               o.y + (h - ts.y) * 0.5), theme_mod.u32(col), label)
    imgui.set_cursor_screen_pos(ImVec2(o.x, o.y))
    imgui.dummy(ImVec2(total, h))
    return out


def chip(text, kind="info", on=None, key=None, icon=None):
    """A small token - a filter, a tag, an applied facet.

    With `on` it is a toggle and returns the new state; without, it is a
    label and returns None. A chip that can be turned off should look
    different from one that cannot, so the toggle form draws a border.
    """
    t = theme_mod.current()
    key = key or text
    dl = imgui.get_window_draw_list()
    col = t.status(kind) if kind in ("ok", "warn", "error", "info") else t.accent
    pad = theme_mod.px(10, t)
    ic = theme_mod.px(13, t) if icon else 0.0
    ts = imgui.calc_text_size(text)
    h = theme_mod.px(23, t)
    w = ts.x + pad * 2 + ic
    o = imgui.get_cursor_screen_pos()

    toggle = on is not None
    imgui.invisible_button(f"##chip{key}", ImVec2(w, h))
    hovered = imgui.is_item_hovered()
    hot = anim.to(f"chip:{key}", 1.0 if hovered and toggle else 0.0, 14.0)
    live = bool(on) if toggle else True
    fill = theme_mod.with_alpha(col, (0.22 if live else 0.08) + 0.08 * hot)
    dl.add_rect_filled(ImVec2(o.x, o.y), ImVec2(o.x + w, o.y + h),
                       theme_mod.u32(fill), h * 0.5)
    if toggle:
        dl.add_rect(ImVec2(o.x, o.y), ImVec2(o.x + w, o.y + h),
                    theme_mod.u32(col, 0.75 if live else 0.3), h * 0.5, 1.0)
    if icon:
        icons.draw(icon, dl, o.x + pad * 0.6 + ic * 0.4, o.y + h * 0.5,
                   theme_mod.px(5.5, t),
                   theme_mod.u32(col, 1.0 if live else 0.5))
    dl.add_text(ImVec2(o.x + pad + ic, o.y + (h - ts.y) * 0.5),
                theme_mod.u32(col, 1.0 if live else 0.55), text)
    if toggle and imgui.is_item_clicked():
        from . import sound
        sound.play("click")
        return not on
    return on


def delta(value, good_up=True, places=1, suffix="%", neutral=0.0005):
    """A change, coloured by whether it is the direction you wanted.

    `good_up=False` for the numbers where down is the win - latency, cost,
    error rate - which is the whole reason this is not just a signed
    number in the accent colour.
    """
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    if value is None:
        imgui.text_colored(t.text_mute, "-")
        return
    flat = abs(value) < neutral
    good = (value > 0) == bool(good_up)
    col = t.text_mute if flat else (t.ok if good else t.danger)
    o = imgui.get_cursor_screen_pos()
    h = imgui.get_text_line_height()
    if not flat:
        icons.draw("sort_up" if value > 0 else "sort_down", dl,
                   o.x + theme_mod.px(6, t), o.y + h * 0.5,
                   theme_mod.px(5, t), theme_mod.u32(col))
    imgui.dummy(ImVec2(theme_mod.px(13, t), h))
    imgui.same_line(0, 2)
    imgui.text_colored(col, f"{abs(value):.{places}f}{suffix}" if not flat
                       else f"0{suffix}")


def stepper(key, value, lo=None, hi=None, step=1, width=118.0, fmt="{:g}"):
    """A number with a minus and a plus. For small integer counts, where
    a slider is imprecise and a text field is four interactions."""
    t = theme_mod.current()
    from . import widgets
    out = value
    if widgets.icon_button("minus", 26.0, key=f"{key}:-"):
        out = value - step
    imgui.same_line(0, 4)
    o = imgui.get_cursor_screen_pos()
    w = theme_mod.px(width, t) - theme_mod.px(60, t)
    h = theme_mod.px(26, t)
    dl = imgui.get_window_draw_list()
    dl.add_rect_filled(ImVec2(o.x, o.y), ImVec2(o.x + w, o.y + h),
                       theme_mod.u32(theme_mod.sink(t.surface, 0.45, t)),
                       t.rounding)
    txt = fmt.format(value)
    ts = imgui.calc_text_size(txt)
    dl.add_text(ImVec2(o.x + (w - ts.x) * 0.5, o.y + (h - ts.y) * 0.5),
                theme_mod.u32(t.text), txt)
    imgui.dummy(ImVec2(w, h))
    imgui.same_line(0, 4)
    if widgets.icon_button("plus", 26.0, key=f"{key}:+"):
        out = value + step
    if lo is not None:
        out = max(lo, out)
    if hi is not None:
        out = min(hi, out)
    return out
