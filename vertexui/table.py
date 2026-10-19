"""Rows of data you can sort, select and scroll.

The one thing a tool that holds records cannot do without, and the one
thing the toolkit had nothing for - so the project that needed it wrote
about a hundred and fifty lines of its own, including a header row drawn
by hand because ImGui's built-in one cannot hold a tri-state checkbox or
sort on a click of the label.

Low-level, so a project keeps control of its own cells:

    cols = [table.Col("name", "Supplier"),
            table.Col("due", "Due", 110, align="r"),
            table.Col("total", "Total", 120, align="r")]
    st = table.State(sort="due")

    rows = st.sort_rows(rows, key=lambda r, k: r[k])
    with table.table("orders", cols, height=380) as open_:
        if open_:
            table.header(cols, st)
            for i, r in table.rows(rows, st):
                table.cell(r["name"])
                table.cell(fmt.clock(r["due"]), align="r")
                table.cell(fmt.count(r["total"]), align="r", colour=tone(r))

`table.rows` runs a clipper, so a hundred thousand rows cost the same as a
screenful. Selection, sorting and the tri-state header box live on
`State`, which is a plain dataclass a project can persist.
"""

from contextlib import contextmanager
from dataclasses import dataclass, field

from imgui_bundle import ImVec2, imgui

from . import anim, fonts, icons
from . import theme as theme_mod

__all__ = ["Col", "State", "table", "header", "rows", "row_begin", "cell",
           "row_height"]

ROW_H = 38.0


@dataclass
class Col:
    """One column.

    `width` is a fixed pixel width, or 0 to share what is left. `align`
    is l / r / c - right for numbers, always, because a column of
    right-aligned figures can be compared by eye and a left-aligned one
    cannot.
    """
    key: str
    label: str = ""
    width: float = 0.0
    align: str = "l"
    sortable: bool = True

    def __post_init__(self):
        self.label = self.label or self.key.replace("_", " ").title()


@dataclass
class State:
    """Sort and selection, kept outside the draw call so it survives."""
    sort: str = ""
    desc: bool = False
    selected: set = field(default_factory=set)
    row_h: float = ROW_H

    def click_sort(self, key):
        """Clicking the active column flips it; a new one starts ascending."""
        if self.sort == key:
            self.desc = not self.desc
        else:
            self.sort, self.desc = key, False

    def sort_rows(self, data, key=None):
        """Return `data` ordered by the current sort.

        `key(row, column_key)` pulls the value. Defaults to item access
        with attribute access as a fallback, so dicts and objects both
        work without a wrapper.
        """
        if not self.sort:
            return list(data)

        def get(r):
            if key is not None:
                return key(r, self.sort)
            try:
                return r[self.sort]
            except Exception:
                return getattr(r, self.sort, None)

        def safe(r):
            v = get(r)
            # None sorts last whichever way the column points, because
            # "missing" is not smaller than everything.
            return (v is None, v if v is not None else 0)

        try:
            return sorted(data, key=safe, reverse=self.desc)
        except TypeError:
            return sorted(data, key=lambda r: str(get(r)), reverse=self.desc)

    # -- selection -----------------------------------------------------
    def toggle(self, row_id):
        self.selected.symmetric_difference_update({row_id})

    def select_all(self, ids):
        self.selected = set(ids)

    def clear(self):
        self.selected.clear()

    def tri_state(self, ids):
        """0 none, 1 some, 2 all - what the header box should show."""
        ids = set(ids)
        if not ids or not self.selected:
            return 0
        hit = len(self.selected & ids)
        return 2 if hit == len(ids) else (1 if hit else 0)


def row_height(t=None):
    t = t or theme_mod.current()
    return theme_mod.px(ROW_H, t) * t.row_scale


@contextmanager
def table(key, cols, height=0.0, scroll=True, row_lines=True):
    """Open a table. Yields whether it opened - always check it."""
    t = theme_mod.current()
    flags = (imgui.TableFlags_.pad_outer_x | imgui.TableFlags_.no_saved_settings)
    if scroll:
        flags |= imgui.TableFlags_.scroll_y
    if row_lines:
        flags |= imgui.TableFlags_.borders_inner_h
    imgui.push_style_color(imgui.Col_.table_border_light,
                           theme_mod.u32(t.border, 0.45))
    imgui.push_style_color(imgui.Col_.table_border_strong,
                           theme_mod.u32(t.border, 0.8))
    ok = imgui.begin_table(f"##tbl{key}", len(cols), flags,
                           ImVec2(0, theme_mod.px(height, t)))
    try:
        if ok:
            for c in cols:
                f = (imgui.TableColumnFlags_.width_fixed if c.width > 0
                     else imgui.TableColumnFlags_.width_stretch)
                imgui.table_setup_column(c.label, f | imgui.TableColumnFlags_.no_sort,
                                         theme_mod.px(c.width, t) if c.width > 0
                                         else 1.0)
            imgui.table_setup_scroll_freeze(0, 1)
        yield ok
    finally:
        if ok:
            imgui.end_table()
        imgui.pop_style_color(2)


def header(cols, state, ids=None, height=32.0):
    """Draw the header row. Returns the action taken, or None.

    Drawn rather than using `table_headers_row` because the built-in one
    cannot hold the tri-state select box and cannot sort on a click of the
    label itself, which is where everyone clicks.

    Pass `ids` to get a select-all box in the first column.
    """
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    h = theme_mod.px(height, t)
    action = None
    imgui.table_next_row(0, h)

    for i, c in enumerate(cols):
        imgui.table_set_column_index(i)
        o = imgui.get_cursor_screen_pos()
        w = imgui.get_content_region_avail().x
        active = state.sort == c.key

        # a header cell is a click target across its whole width
        imgui.invisible_button(f"##h{c.key}", ImVec2(max(1.0, w), h))
        hovered = imgui.is_item_hovered() and c.sortable
        if hovered and imgui.is_item_clicked():
            state.click_sort(c.key)
            action = ("sort", c.key)
        hot = anim.to(f"th:{c.key}", 1.0 if hovered else 0.0, 16.0)

        if i == 0 and ids is not None:
            tri = state.tri_state(ids)
            bx = o.x + theme_mod.px(3, t)
            by = o.y + (h - theme_mod.px(15, t)) * 0.5
            s = theme_mod.px(15, t)
            imgui.set_cursor_screen_pos(ImVec2(bx, by))
            imgui.invisible_button("##selall", ImVec2(s, s))
            if imgui.is_item_clicked():
                if tri == 2:
                    state.clear()
                else:
                    state.select_all(ids)
                action = ("select", state.tri_state(ids))
            dl.add_rect(ImVec2(bx, by), ImVec2(bx + s, by + s),
                        theme_mod.u32(t.accent if tri else t.border,
                                      0.9 if tri else 0.8),
                        max(2.0, t.rounding * 0.4), t.border_width)
            if tri == 2:
                icons.draw("check", dl, bx + s * 0.5, by + s * 0.5, s * 0.33,
                           theme_mod.u32(t.accent))
            elif tri == 1:
                dl.add_rect_filled(
                    ImVec2(bx + s * 0.26, by + s * 0.44),
                    ImVec2(bx + s * 0.74, by + s * 0.56),
                    theme_mod.u32(t.accent), 1.0)
            o = ImVec2(o.x + s + theme_mod.px(9, t), o.y)
            w -= s + theme_mod.px(9, t)

        col = anim.lerp_col(t.text_dim if not active else t.text, t.text, hot)
        with fonts.use("label"):
            label = c.label.upper()
            ts = imgui.calc_text_size(label)
            tx = {"l": o.x,
                  "r": o.x + w - ts.x - (theme_mod.px(13, t) if active else 0),
                  "c": o.x + (w - ts.x) * 0.5}[c.align]
            dl.add_text(ImVec2(tx, o.y + (h - ts.y) * 0.5),
                        theme_mod.u32(col), label)
            if active:
                ax = tx + ts.x + theme_mod.px(7, t) if c.align != "r" else \
                    tx + ts.x + theme_mod.px(7, t)
                icons.draw("sort_down" if state.desc else "sort_up", dl,
                           ax, o.y + h * 0.5, theme_mod.px(4.5, t),
                           theme_mod.u32(t.accent))
    # a rule under the header, which is what stops it reading as row zero
    o = imgui.get_cursor_screen_pos()
    dl.add_rect_filled(ImVec2(o.x - 10, o.y - 1),
                       ImVec2(o.x + imgui.get_content_region_avail().x + 10, o.y),
                       theme_mod.u32(t.border, 0.9))
    return action


def rows(data, state=None, height=0.0):
    """Iterate visible rows only, via a clipper.

    Yields `(index, item)` and opens each row for you, so the body of the
    loop goes straight to `cell`. A buffer of a hundred thousand costs the
    same as a screenful.
    """
    t = theme_mod.current()
    data = list(data)
    h = theme_mod.px(height, t) if height > 0 else row_height(t)
    clipper = imgui.ListClipper()
    clipper.begin(len(data), h)
    while clipper.step():
        for i in range(clipper.display_start, clipper.display_end):
            if 0 <= i < len(data):
                imgui.table_next_row(0, h)
                imgui.table_set_column_index(0)
                yield i, data[i]


def row_begin(key, selected=False, height=0.0, hover=True):
    """Tint and hit-test the row that is open. Returns `(hovered, clicked)`.

    Call right after the row opens, before any cell.
    """
    t = theme_mod.current()
    dl = imgui.get_window_draw_list()
    h = theme_mod.px(height, t) if height > 0 else row_height(t)
    o = imgui.get_cursor_screen_pos()
    # The row tint has to span every column, and from inside the first
    # cell `get_content_region_avail` only reports that cell. This binding
    # has no window-content-region accessor, so the right edge comes from
    # the window itself, less the scrollbar the table may be showing.
    style = imgui.get_style()
    full = (imgui.get_window_pos().x + imgui.get_window_size().x
            - style.scrollbar_size - style.window_padding.x * 0.5)

    imgui.invisible_button(f"##row{key}", ImVec2(max(1.0, full - o.x), h))
    hovered = imgui.is_item_hovered()
    clicked = imgui.is_item_clicked()
    hot = anim.to(f"row:{key}", 1.0 if (hovered and hover) else 0.0, 20.0)
    if selected or hot > 0.01:
        a = 0.14 if selected else 0.07 * hot
        dl.add_rect_filled(ImVec2(o.x - 8, o.y), ImVec2(full, o.y + h),
                           theme_mod.u32(t.accent if selected else t.text, a))
    if selected:
        dl.add_rect_filled(ImVec2(o.x - 8, o.y),
                           ImVec2(o.x - 8 + theme_mod.px(2.5, t), o.y + h),
                           theme_mod.u32(t.accent, 0.9))
    imgui.set_cursor_screen_pos(o)
    return hovered, clicked


def cell(text, align="l", colour=None, role="ui", column=None, pad=10.0):
    """Draw one cell's text, vertically centred and clipped to the column."""
    t = theme_mod.current()
    if column is not None:
        imgui.table_set_column_index(column)
    dl = imgui.get_window_draw_list()
    o = imgui.get_cursor_screen_pos()
    w = imgui.get_content_region_avail().x
    h = row_height(t)
    p = theme_mod.px(pad, t)
    from . import fmt
    with fonts.use(role):
        label = fmt.ellipsis(str(text), max(8.0, w - p))
        ts = imgui.calc_text_size(label)
        x = {"l": o.x, "r": o.x + w - ts.x - p * 0.3,
             "c": o.x + (w - ts.x) * 0.5}[align]
        dl.add_text(ImVec2(x, o.y + (h - ts.y) * 0.5),
                    theme_mod.u32(colour if colour is not None else t.text),
                    label)
