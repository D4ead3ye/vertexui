"""Controls that animate, drawn rather than styled.

ImGui's own widgets take their geometry and colour from the global style,
which is tuned for one shape of control. Restyling them gets you a themed
panel that still snaps between states; these draw themselves, so hover,
press and selection can each ease independently.

Every widget reads the active theme and plays from the active sound set,
so a project sets those once and never passes them again:

    theme.use(theme.NOIR_BLUE)
    if widgets.button("Start", primary=True):
        ...
"""

from imgui_bundle import ImVec2, ImVec4, imgui

from . import anim, fonts, icons, sound
from . import theme as theme_mod

_hover_was = {}


def hover_tick(key: str, hovered: bool):
    """Play the hover cue on the frame the cursor arrives, and not again
    until it leaves. Without the edge check it fires every frame."""
    was = _hover_was.get(key, False)
    if hovered and not was:
        sound.play("hover")
    _hover_was[key] = bool(hovered)


def button(label, width=0.0, height=36.0, primary=False, enabled=True,
           tooltip=None, key=None, icon=None) -> bool:
    """A button whose fill eases, that sinks when pressed, and that wipes an
    accent underline in from the left on hover.

    `icon` is a name from vertexui.icons - drawn, so it needs no font and
    cannot render as a tofu box.
    """
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    key = key or label
    icon_w = 0.0 if not icon else height * 0.5
    if width <= 0:
        width = imgui.calc_text_size(label).x + 34 + icon_w
    pos = imgui.get_cursor_screen_pos()

    if not enabled:
        imgui.begin_disabled()
    imgui.invisible_button(f"##{key}", ImVec2(width, height))
    clicked = imgui.is_item_clicked() if enabled else False
    hovered = imgui.is_item_hovered() and enabled
    held = imgui.is_item_active() and enabled
    if not enabled:
        imgui.end_disabled()

    hover_tick(f"btn:{key}", hovered)
    hot = anim.to(f"btn:{key}", 1.0 if hovered else 0.0, 16.0)
    press = anim.to(f"btnp:{key}", 1.0 if held else 0.0, 26.0)

    base = t.accent_dim if primary else t.surface
    top = t.accent if primary else t.surface_hover
    fill = anim.lerp_col(base, top, hot)
    if not enabled:
        fill = ImVec4(fill.x * 0.5, fill.y * 0.5, fill.z * 0.5, 0.6)

    inset = 1.0 * press           # sinks rather than jumping to a third colour
    p0 = ImVec2(pos.x, pos.y + inset)
    p1 = ImVec2(pos.x + width, pos.y + height - inset)

    dl.add_rect_filled(p0, p1, imgui.get_color_u32(fill), t.rounding)
    if hot > 0.01:
        dl.add_rect(p0, p1, imgui.get_color_u32(
            theme_mod.with_alpha(t.accent, 0.55 * hot)), t.rounding, 1.0)
        uw = (width - 16) * hot
        dl.add_rect_filled(ImVec2(pos.x + 8, p1.y - 2.5),
                           ImVec2(pos.x + 8 + uw, p1.y - 1.0),
                           imgui.get_color_u32(t.accent_bright), 1.0)

    ts = imgui.calc_text_size(label)
    col = anim.lerp_col(t.text if enabled else t.text_mute, t.text, hot)
    block = ts.x + (icon_w + 6 if icon else 0)
    tx = pos.x + (width - block) * 0.5
    if icon:
        icons.draw(icon, dl, tx + icon_w * 0.5, pos.y + height * 0.5 + inset,
                   height * 0.24, imgui.get_color_u32(col))
        tx += icon_w + 6
    with fonts.use("semi"):
        dl.add_text(ImVec2(tx, pos.y + (height - ts.y) * 0.5 + inset),
                    imgui.get_color_u32(col), label)

    if tooltip and hovered:
        imgui.set_tooltip(tooltip)
    if clicked:
        sound.play("click")
    return clicked


def checkbox(label, value: bool, box=18.0, key=None) -> bool:
    """Three things ease independently: the hover lift, the fill as it turns
    on, and the tick drawing itself in rather than appearing whole."""
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    key = key or label
    pos = imgui.get_cursor_screen_pos()
    with fonts.use("ui"):
        tw = imgui.calc_text_size(label).x
    gap = 9.0
    line_h = max(box, imgui.get_text_line_height())

    imgui.invisible_button(f"##chk{key}", ImVec2(box + gap + tw, line_h))
    if imgui.is_item_clicked():
        value = not value
        sound.play("click")

    hovered = imgui.is_item_hovered()
    hover_tick(f"chk:{key}", hovered)
    hot = anim.to(f"chk:{key}", 1.0 if hovered else 0.0, 15.0)
    on = anim.to(f"chkon:{key}", 1.0 if value else 0.0, 16.0)

    y0 = pos.y + (line_h - box) * 0.5
    p0, p1 = ImVec2(pos.x, y0), ImVec2(pos.x + box, y0 + box)
    rest = anim.lerp_col(t.surface, t.surface_hover, hot)
    # Checked matches the primary button - deep at rest, brighter under the
    # cursor. Full accent at rest makes a minor control shout.
    fill = anim.lerp_col(rest, anim.lerp_col(t.accent_dim, t.accent, hot), on)
    dl.add_rect_filled(p0, p1, imgui.get_color_u32(fill), 5.0)
    edge = anim.lerp_col(anim.lerp_col(t.border, t.text_mute, hot),
                         anim.lerp_col(t.accent, t.accent_bright, hot), on)
    dl.add_rect(p0, p1, imgui.get_color_u32(edge), 5.0, 1.0)

    if on > 0.02:
        cx, cy = pos.x + box * 0.5, y0 + box * 0.5
        a = ImVec2(cx - box * 0.22, cy + box * 0.02)
        b = ImVec2(cx - box * 0.06, cy + box * 0.18)
        c = ImVec2(cx + box * 0.24, cy - box * 0.18)
        ink = imgui.get_color_u32(ImVec4(1, 1, 1, min(1.0, on * 1.4)))
        t1 = min(1.0, on / 0.45)
        dl.add_line(a, ImVec2(a.x + (b.x - a.x) * t1, a.y + (b.y - a.y) * t1), ink, 2.2)
        if on > 0.45:
            t2 = (on - 0.45) / 0.55
            dl.add_line(b, ImVec2(b.x + (c.x - b.x) * t2, b.y + (c.y - b.y) * t2), ink, 2.2)

    col = anim.lerp_col(anim.lerp_col(t.text_dim, t.text, hot), t.text, on)
    ts = imgui.calc_text_size(label)
    dl.add_text(ImVec2(pos.x + box + gap, pos.y + (line_h - ts.y) * 0.5),
                imgui.get_color_u32(col), label)
    return value


def tabs(key: str, labels, current: int) -> int:
    """Tab strip whose indicator slides between tabs.

    Built from invisible buttons rather than ImGui's tab bar because the
    indicator has to interpolate between positions, which the built-in bar
    has no concept of - it can only be on one tab or another.
    """
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    origin = imgui.get_cursor_screen_pos()
    h, pad = 34.0, 18.0

    widths, xs, x = [], [], origin.x
    with fonts.use("semi"):
        for lbl in labels:
            w = imgui.calc_text_size(lbl).x + pad * 2
            widths.append(w)
            xs.append(x)
            x += w + 4

    selected = current
    for i, lbl in enumerate(labels):
        imgui.set_cursor_screen_pos(ImVec2(xs[i], origin.y))
        imgui.invisible_button(f"##tab{key}{i}", ImVec2(widths[i], h))
        if imgui.is_item_clicked():
            selected = i
            sound.play("click")
        hovered = imgui.is_item_hovered()
        hover_tick(f"tab:{key}:{i}", hovered)
        hot = anim.to(f"tab:{key}:{i}", 1.0 if hovered else 0.0, 16.0)
        on = i == current
        if hot > 0.01 and not on:
            dl.add_rect_filled(ImVec2(xs[i], origin.y),
                               ImVec2(xs[i] + widths[i], origin.y + h),
                               imgui.get_color_u32(ImVec4(1, 1, 1, 0.045 * hot)),
                               t.rounding)
        ts = imgui.calc_text_size(lbl)
        col = anim.lerp_col(t.text_dim, t.text, max(hot, 1.0 if on else 0.0))
        with fonts.use("semi"):
            dl.add_text(ImVec2(xs[i] + (widths[i] - ts.x) * 0.5,
                               origin.y + (h - ts.y) * 0.5),
                        imgui.get_color_u32(col), lbl)

    # The indicator chases both x and width, so switching reads as one
    # object moving rather than two appearing. It spans the LABEL, not the
    # padded tab box - a rule that runs wider than the word it underlines
    # reads as a box someone forgot to finish.
    with fonts.use("semi"):
        label_w = imgui.calc_text_size(labels[current]).x
    ix = anim.to(f"tabx:{key}", xs[current] + (widths[current] - label_w) * 0.5, 18.0)
    iw = anim.to(f"tabw:{key}", label_w, 18.0)
    dl.add_rect_filled(ImVec2(ix, origin.y + h - 3),
                       ImVec2(ix + iw, origin.y + h - 0.5),
                       imgui.get_color_u32(t.accent), 1.5)

    imgui.set_cursor_screen_pos(ImVec2(origin.x, origin.y + h + 8))
    return selected


def status_pill(label_off="IDLE", label_on="RUNNING", on=False, key="status"):
    """A pill that breathes while active, and crossfades between its two
    words instead of swapping them in one frame. Returns its width."""
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    pos = imgui.get_cursor_screen_pos()
    cy = pos.y + 11.0

    run = anim.to(f"pill:{key}", 1.0 if on else 0.0, 9.0)
    beat = anim.pulse() if on else 0.0

    with fonts.use("semi"):
        w_off = imgui.calc_text_size(label_off).x
        w_on = imgui.calc_text_size(label_on).x
    width = (w_off + (w_on - w_off) * run) + 34

    live = anim.lerp_col(t.ok, theme_mod.with_alpha(t.ok, 0.35), beat)
    dot = anim.lerp_col(t.text_mute, live, run)

    dl.add_rect_filled(ImVec2(pos.x, cy - 11), ImVec2(pos.x + width, cy + 11),
                       imgui.get_color_u32(anim.lerp_col(
                           t.surface, theme_mod.with_alpha(t.ok, 0.12), run)), 11.0)
    dl.add_circle_filled(ImVec2(pos.x + 13, cy), 4.0, imgui.get_color_u32(dot))
    if run > 0.01:
        dl.add_circle(ImVec2(pos.x + 13, cy), 4.0 + 4.0 * beat,
                      imgui.get_color_u32(theme_mod.with_alpha(
                          t.ok, 0.5 * (1.0 - beat) * run)), 0, 1.5)

    label = label_on if run > 0.5 else label_off
    fade = abs(run - 0.5) * 2.0
    with fonts.use("semi"):
        dl.add_text(ImVec2(pos.x + 24, cy - imgui.get_font_size() * 0.5),
                    imgui.get_color_u32(theme_mod.with_alpha(dot, max(0.15, fade))),
                    label)
    imgui.dummy(ImVec2(width, 22))
    return width


def activity_rule(width: float, active: bool, key="rule", thickness=1.6):
    """A hairline that sweeps an accent segment across as something starts,
    and retracts when it stops. Readable from the corner of the eye."""
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    pos = imgui.get_cursor_screen_pos()
    run = anim.to(f"rule:{key}", 1.0 if active else 0.0, 9.0)
    dl.add_rect_filled(ImVec2(pos.x, pos.y), ImVec2(pos.x + width, pos.y + 1),
                       imgui.get_color_u32(t.border))
    if run > 0.005:
        dl.add_rect_filled(ImVec2(pos.x, pos.y),
                           ImVec2(pos.x + width * run, pos.y + thickness),
                           imgui.get_color_u32(theme_mod.with_alpha(t.accent, 0.85)))
    imgui.dummy(ImVec2(width, thickness + 2))


def caps(dl, x, y, text, col, track=1.3):
    """A micro-label in tracked capitals, drawn a glyph at a time.

    ImGui has no letter-spacing, and these labels are three to seven
    characters each - the tracking is most of what separates a laid-out
    panel from a stack of default text, so it is worth the loop. Returns
    the x it finished at.
    """
    for ch in text:
        dl.add_text(ImVec2(x, y), col, ch)
        x += imgui.calc_text_size(ch).x + track
    return x


def caps_width(text, track=1.3):
    """What `caps` will occupy - for right-aligning one."""
    if not text:
        return 0.0
    return sum(imgui.calc_text_size(c).x + track for c in text) - track


def progress_hairline(value, height=3.0, colour=None, key="hairline"):
    """A progress rule along the very top edge of the window, full width.

    For the one number worth seeing from the other side of the room. Up
    against the edge it costs no layout at all, and the bloom on the
    leading edge is what makes the eye find it moving rather than having
    to read it.
    """
    t = theme_mod.current()
    io = imgui.get_io()
    w = io.display_size.x
    dl = imgui.get_window_draw_list()
    eased = anim.to(key, max(0.0, min(1.0, float(value))), 5.0)
    x1 = w * eased
    dl.add_rect_filled(ImVec2(0, 0), ImVec2(w, height),
                       imgui.get_color_u32(theme_mod.with_alpha(t.border, 0.55)))
    if eased <= 0.0005:
        return
    dl.add_rect_filled(ImVec2(0, 0), ImVec2(x1, height),
                       imgui.get_color_u32(colour or t.accent))
    dl.add_circle_filled(
        ImVec2(x1, height * 0.5), height * 2.3,
        imgui.get_color_u32(theme_mod.with_alpha(t.accent_bright, 0.30)))


class Transition:
    """A wipe across a screen change.

        self.wipe = widgets.Transition()
        ...
        self.wipe.to(self.screen)     # anywhere before drawing
        ... draw the screen ...
        self.wipe.draw()              # last thing in the frame

    Swapping the whole window between one screen and another reads as a
    glitch without a beat in between; a short fade over the top reads as
    navigation. Nothing else about the screens has to change.
    """

    def __init__(self, speed=4.5, strength=0.85):
        self.speed = float(speed)
        self.strength = float(strength)
        self._was = None
        self._v = 0.0

    def to(self, screen):
        """Tell it which screen is being drawn. Fires on a change."""
        if self._was is None:
            self._was = screen
        elif screen != self._was:
            self._was = screen
            self._v = 1.0
        return screen

    def draw(self):
        if self._v <= 0.004:
            return False
        t = theme_mod.current()
        io = imgui.get_io()
        self._v = max(0.0, self._v - io.delta_time * self.speed)
        imgui.get_window_draw_list().add_rect_filled(
            ImVec2(0, 0), ImVec2(io.display_size.x, io.display_size.y),
            imgui.get_color_u32(
                theme_mod.with_alpha(t.bg, self._v * self.strength)))
        anim.mark_busy()
        return True


def underline(width: float, colour=None, thickness=1.5, inset=0.0):
    """A rule exactly as wide as what it sits under.

    Sized by the caller from `calc_text_size`, never by the container: a
    line that runs wider than the words above it reads as an unfinished
    box rather than an underline.
    """
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    p = imgui.get_cursor_screen_pos()
    dl.add_rect_filled(ImVec2(p.x + inset, p.y), ImVec2(p.x + inset + width, p.y + thickness),
                       imgui.get_color_u32(colour or t.accent), thickness * 0.5)
    imgui.dummy(ImVec2(width, thickness))


def label_underlined(text, colour=None, gap=4.0):
    """Text with a rule matched to its own width - the pattern from the
    reference: the line belongs to the word, not to the column.

    Wrapped in a group so the label and its rule count as one item and
    `same_line()` places the next one beside it rather than under the rule.
    """
    t = theme_mod.current()
    imgui.begin_group()
    with fonts.use("semi"):
        w = imgui.calc_text_size(text).x
        imgui.text_colored(t.text, text)
    imgui.dummy(ImVec2(w, gap - 4))
    underline(w, colour)
    imgui.end_group()


def section(label, width=0.0):
    """A section header: short accent tick, the label, then a hairline
    running out to the edge. Cheap structure for a dense panel."""
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    p = imgui.get_cursor_screen_pos()
    avail = width or imgui.get_content_region_avail().x
    with fonts.use("semi"):
        tw = imgui.calc_text_size(label).x
    cy = p.y + 9
    dl.add_rect_filled(ImVec2(p.x, cy - 1), ImVec2(p.x + 10, cy + 1),
                       imgui.get_color_u32(t.accent))
    with fonts.use("semi"):
        dl.add_text(ImVec2(p.x + 16, p.y + 1), imgui.get_color_u32(t.text_dim), label)
    x0 = p.x + 16 + tw + 10
    dl.add_rect_filled(ImVec2(x0, cy), ImVec2(p.x + avail, cy + 1),
                       imgui.get_color_u32(t.border))
    imgui.dummy(ImVec2(avail, 20))


def slider(label, value, lo, hi, width=180.0, fmt="%.2f", key=None):
    """A slider with an animated fill and a grab that grows on hover."""
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    key = key or label
    pos = imgui.get_cursor_screen_pos()
    h = 26.0
    imgui.invisible_button(f"##sl{key}", ImVec2(width, h))
    hovered = imgui.is_item_hovered()
    hover_tick(f"sl:{key}", hovered)
    active = imgui.is_item_active()
    if active:
        rel = (imgui.get_io().mouse_pos.x - pos.x) / max(1.0, width)
        value = lo + (hi - lo) * max(0.0, min(1.0, rel))

    hot = anim.to(f"sl:{key}", 1.0 if (hovered or active) else 0.0, 16.0)
    frac = 0.0 if hi == lo else (value - lo) / (hi - lo)
    y0 = pos.y + (h - 8) * 0.5
    dl.add_rect_filled(ImVec2(pos.x, y0), ImVec2(pos.x + width, y0 + 8),
                       imgui.get_color_u32(t.surface), 4.0)
    dl.add_rect_filled(ImVec2(pos.x, y0), ImVec2(pos.x + width * frac, y0 + 8),
                       imgui.get_color_u32(anim.lerp_col(t.accent_dim, t.accent, hot)), 4.0)
    gx = pos.x + width * frac
    dl.add_circle_filled(ImVec2(gx, y0 + 4), 5.0 + 2.0 * hot,
                         imgui.get_color_u32(anim.lerp_col(t.accent, t.accent_bright, hot)))
    imgui.same_line()
    imgui.text_colored(t.text_dim, (fmt % value) + ("  " + label if label else ""))
    return value


def combo(label, options, index, width=170.0, key=None):
    """Dropdown themed to match the drawn widgets. Uses ImGui's popup for
    the list itself - reimplementing keyboard navigation and clipping to
    save a little styling would be a poor trade."""
    t = theme_mod.current()
    key = key or label
    imgui.set_next_item_width(width)
    imgui.push_style_color(imgui.Col_.frame_bg, t.surface)
    imgui.push_style_color(imgui.Col_.frame_bg_hovered, t.surface_hover)
    imgui.push_style_color(imgui.Col_.popup_bg, t.panel)
    changed, index = imgui.combo(f"##cb{key}", index, list(options))
    imgui.pop_style_color(3)
    if changed:
        sound.play("click")
    if label:
        imgui.same_line()
        imgui.text_colored(t.text_dim, label)
    return index


def color_button(label, colour, size=26.0, key=None):
    """A swatch that opens a full picker.

    Returns the (possibly new) colour. The picker is ImGui's own - it
    already has the saturation square, hue bar, RGB/HSV fields and a hex
    box, and reimplementing that is not what a toolkit is for.
    """
    t = theme_mod.current()
    key = key or label
    dl = imgui.get_window_draw_list()
    pos = imgui.get_cursor_screen_pos()
    imgui.invisible_button(f"##col{key}", ImVec2(size, size))
    hovered = imgui.is_item_hovered()
    hover_tick(f"col:{key}", hovered)
    if imgui.is_item_clicked():
        sound.play("click")
        imgui.open_popup(f"picker{key}")
    hot = anim.to(f"col:{key}", 1.0 if hovered else 0.0, 16.0)
    dl.add_rect_filled(ImVec2(pos.x, pos.y), ImVec2(pos.x + size, pos.y + size),
                       imgui.get_color_u32(colour), 5.0)
    dl.add_rect(ImVec2(pos.x, pos.y), ImVec2(pos.x + size, pos.y + size),
                imgui.get_color_u32(anim.lerp_col(t.border, t.text_dim, hot)), 5.0, 1.0)

    if imgui.begin_popup(f"picker{key}"):
        with fonts.use("semi"):
            imgui.text_colored(t.text, label or "colour")
        changed, rgba = imgui.color_picker4(
            f"##pick{key}", [colour.x, colour.y, colour.z, colour.w],
            imgui.ColorEditFlags_.no_side_preview | imgui.ColorEditFlags_.no_alpha
            | imgui.ColorEditFlags_.display_hex)
        if changed:
            colour = ImVec4(rgba[0], rgba[1], rgba[2], 1.0)
        imgui.end_popup()
    if label:
        imgui.same_line()
        imgui.text_colored(t.text_dim, label)
    return colour


def badge(text, kind="info", icon=None):
    """A small status chip: icon, label, tinted ground. For counts, states
    and anything that wants to be seen without being read."""
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    col = t.status(kind)
    icon = icon or icons.STATUS_ICONS.get(kind, "dot")
    pos = imgui.get_cursor_screen_pos()
    tw = imgui.calc_text_size(text).x
    w, h = tw + 40, 22.0
    dl.add_rect_filled(ImVec2(pos.x, pos.y), ImVec2(pos.x + w, pos.y + h),
                       imgui.get_color_u32(theme_mod.with_alpha(col, 0.14)), h * 0.5)
    icons.draw(icon, dl, pos.x + 14, pos.y + h * 0.5, 6.0, imgui.get_color_u32(col))
    dl.add_text(ImVec2(pos.x + 26, pos.y + (h - imgui.get_text_line_height()) * 0.5),
                imgui.get_color_u32(col), text)
    imgui.dummy(ImVec2(w, h))


def icon_button(name, size=30.0, tooltip=None, key=None) -> bool:
    """A square icon-only button, for toolbars and title bars."""
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    key = key or name
    pos = imgui.get_cursor_screen_pos()
    imgui.invisible_button(f"##ic{key}", ImVec2(size, size))
    clicked, hovered = imgui.is_item_clicked(), imgui.is_item_hovered()
    hover_tick(f"ic:{key}", hovered)
    hot = anim.to(f"ic:{key}", 1.0 if hovered else 0.0, 16.0)
    if hot > 0.01:
        dl.add_rect_filled(ImVec2(pos.x, pos.y), ImVec2(pos.x + size, pos.y + size),
                           imgui.get_color_u32(theme_mod.with_alpha(t.accent, 0.7 * hot)),
                           t.rounding)
    icons.draw(name, dl, pos.x + size * 0.5, pos.y + size * 0.5, size * 0.28,
               imgui.get_color_u32(anim.lerp_col(t.text_dim, t.text, hot)))
    if tooltip and hovered:
        imgui.set_tooltip(tooltip)
    if clicked:
        sound.play("click")
    return clicked
