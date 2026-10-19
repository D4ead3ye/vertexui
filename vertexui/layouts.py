"""Where the slots go - the part that decides what an application *is*.

A layout receives an `App` and draws its pages and slots. Nothing about a
module changes when you swap one for another, which is the whole claim:
the same modules come out as a tabbed panel, an icon-rail tool, a dense
instrument, a single-purpose stage or a corner overlay.

    TABBED   title, tab strip, page below. Familiar, and the right answer
             for a handful of equal-weight views.
    RAIL     icons down the left edge, no tab strip. For a tool with many
             views where the content, not the navigation, is the subject.
    DENSE    one hairline strip of chrome and nothing else. Everything is
             content. For profiling, telemetry, log analysis.
    STAGE    one centred column, no navigation at all. For a tool that
             does one thing - a tuner, a meter, a single readout.
    HUD      a small corner panel over nothing. For an automation watching
             something else, where the interface must not be the subject.
    SPLIT    page and aside side by side, for a browser/inspector shape.

Pick one in a profile, not in a module. A layout with no `aside` simply
does not draw that slot, and a module that fills one is none the wiser.
"""

from imgui_bundle import ImVec2, imgui

from . import anim, fonts, icons, widgets
from . import theme as theme_mod


class Layout:
    """Base. `draw(app)` is the whole interface."""

    name = "layout"
    #: slots this layout has somewhere to put
    accepts = ("chrome", "nav", "body", "aside", "status", "overlay")

    def draw(self, app):
        raise NotImplementedError

    # -- shared pieces ---------------------------------------------------
    def page_body(self, app):
        """Draw the current page, then anything in the body slot."""
        p = app.current_page()
        if p is not None and p.draw is not None:
            p.draw(app)
        app.slots.draw("body", app)

    def title(self, app, mark=True, size="title"):
        t = theme_mod.current()
        if mark:
            dl = imgui.get_window_draw_list()
            o = imgui.get_cursor_screen_pos()
            dl.add_rect_filled(ImVec2(o.x, o.y + 4), ImVec2(o.x + 3.5, o.y + 26),
                               imgui.get_color_u32(t.accent), 2.0)
            imgui.dummy(ImVec2(10, 22))
            imgui.same_line()
        with fonts.use(size):
            imgui.text_colored(t.text, app.title)

    def rule(self, width=0.0, alpha=0.6):
        t = theme_mod.current()
        dl = imgui.get_window_draw_list()
        o = imgui.get_cursor_screen_pos()
        w = width or imgui.get_content_region_avail().x
        dl.add_rect_filled(ImVec2(o.x, o.y), ImVec2(o.x + w, o.y + 1.0),
                           imgui.get_color_u32(
                               theme_mod.with_alpha(t.border, alpha)))
        imgui.dummy(ImVec2(w, 1.0))


class Tabbed(Layout):
    """Title row, tab strip, page below."""

    name = "tabbed"

    def draw(self, app):
        app.slots.draw("chrome", app)
        if not app.slots.has("chrome"):
            self.title(app)
            imgui.same_line(0, 16)
            app.slots.draw("status", app)
        if app.pages:
            labels = [p.label for p in app.pages]
            i = widgets.tabs("nav", labels, app.page_index)
            if i != app.page_index:
                app.go(i)
        app.slots.draw("nav", app)
        self.page_body(app)
        app.slots.draw("overlay", app)


class Rail(Layout):
    """An icon rail down the left edge. No tab strip, no title bar."""

    name = "rail"

    def __init__(self, width=62.0, labels=False):
        self.width = width
        self.labels = labels

    def draw(self, app):
        t = theme_mod.current()
        dl = imgui.get_window_draw_list()
        o = imgui.get_cursor_screen_pos()
        avail = imgui.get_content_region_avail()
        w = self.width + (26 if self.labels else 0)

        # the rail is a different ground, which is most of why this reads
        # as a different application rather than as tabs turned sideways
        dl.add_rect_filled(ImVec2(o.x - 8, o.y - 8),
                           ImVec2(o.x + w, o.y + avail.y + 8),
                           imgui.get_color_u32(theme_mod.sink(t.panel, 0.45, t)))
        dl.add_line(ImVec2(o.x + w, o.y - 8), ImVec2(o.x + w, o.y + avail.y + 8),
                    imgui.get_color_u32(t.border), 1.0)

        imgui.begin_child("##rail", ImVec2(w, 0))
        imgui.dummy(ImVec2(0, 4))
        for i, p in enumerate(app.pages):
            on = p.key == app.page_key
            hot = anim.to(f"rail:{p.key}", 1.0 if on else 0.0, 16.0)
            pos = imgui.get_cursor_screen_pos()
            if on or hot > 0.01:
                dl.add_rect_filled(
                    ImVec2(pos.x - 6, pos.y), ImVec2(pos.x - 3, pos.y + 38),
                    imgui.get_color_u32(theme_mod.with_alpha(t.accent, hot)), 2.0)
            if widgets.icon_button(p.icon or "dot", 38.0,
                                   tooltip=None if self.labels else p.label,
                                   key=f"rail:{p.key}"):
                app.go(p.key)
            if self.labels:
                imgui.same_line()
                imgui.text_colored(t.text if on else t.text_mute, p.label)
            if p.badge:
                imgui.same_line(0, 4)
                imgui.text_colored(t.accent, p.badge)
        imgui.end_child()
        imgui.same_line(0, 18)

        imgui.begin_child("##body")
        if app.slots.has("chrome"):
            app.slots.draw("chrome", app)
        else:
            p = app.current_page()
            self.title(app, mark=False)
            if p is not None:
                imgui.same_line(0, 10)
                imgui.text_colored(t.text_mute, p.label.lower())
            if app.slots.has("status"):
                imgui.same_line(0, 16)
                app.slots.draw("status", app)
        app.slots.draw("nav", app)
        self.page_body(app)
        imgui.end_child()
        app.slots.draw("overlay", app)


class Dense(Layout):
    """One hairline strip of chrome. Everything else is content."""

    name = "dense"
    accepts = ("chrome", "nav", "body", "status", "overlay")

    def draw(self, app):
        t = theme_mod.current()
        with fonts.use("label"):
            imgui.text_colored(t.text_mute, app.title.upper())
        imgui.same_line(0, 18)
        # pages as a tight segmented strip, not tabs with air around them
        for i, p in enumerate(app.pages):
            on = p.key == app.page_key
            if i:
                imgui.same_line(0, 2)
            if widgets.button(p.label, 0, height=22.0, primary=on,
                              key=f"seg:{p.key}"):
                app.go(p.key)
        if app.slots.has("status"):
            imgui.same_line(0, 18)
            app.slots.draw("status", app)
        app.slots.draw("chrome", app)
        self.rule(alpha=0.9)
        imgui.dummy(ImVec2(0, 2))
        app.slots.draw("nav", app)
        self.page_body(app)
        app.slots.draw("overlay", app)


class Stage(Layout):
    """One centred column. No navigation - this tool does one thing."""

    name = "stage"
    accepts = ("chrome", "body", "status", "overlay")

    def __init__(self, width=560.0, top=0.16):
        self.width = width
        self.top = top

    def draw(self, app):
        avail = imgui.get_content_region_avail()
        imgui.dummy(ImVec2(0, max(8.0, avail.y * self.top)))
        w = min(self.width, avail.x * 0.92)
        imgui.dummy(ImVec2(max(0.0, (avail.x - w) * 0.5), 0))
        imgui.same_line()
        # Scrollable: a stage is a column, and a column of content taller
        # than the window is simply unreachable without this - which a
        # form of any length hits on the first screen.
        imgui.begin_child("##stage", ImVec2(w, 0))
        imgui.push_item_width(w)
        app.slots.draw("chrome", app)
        self.page_body(app)
        imgui.pop_item_width()
        imgui.end_child()
        if app.slots.has("status"):
            imgui.dummy(ImVec2(0, 10))
            imgui.dummy(ImVec2(max(0.0, (avail.x - w) * 0.5), 0))
            imgui.same_line()
            app.slots.draw("status", app)
        app.slots.draw("overlay", app)


class Hud(Layout):
    """A compact corner panel. The interface is not the subject here."""

    name = "hud"
    accepts = ("body", "status", "overlay")

    def __init__(self, corner="tl", width=330.0, margin=14.0):
        self.corner = corner
        self.width = width
        self.margin = margin

    def draw(self, app):
        from . import cards
        avail = imgui.get_content_region_avail()
        x = self.margin if "l" in self.corner else \
            max(self.margin, avail.x - self.width - self.margin)
        imgui.dummy(ImVec2(0, self.margin if "t" in self.corner
                           else max(self.margin, avail.y * 0.55)))
        imgui.dummy(ImVec2(x, 0))
        imgui.same_line()
        imgui.begin_group()
        p = app.current_page()
        with cards.card(app.title, width=self.width,
                        right=(p.label if p else ""), style="plated"):
            self.page_body(app)
            if app.slots.has("status"):
                imgui.dummy(ImVec2(0, 4))
                app.slots.draw("status", app)
        imgui.end_group()
        app.slots.draw("overlay", app)


class Split(Layout):
    """Page and aside side by side."""

    name = "split"

    def __init__(self, aside=320.0, aside_right=True):
        self.aside = aside
        self.aside_right = aside_right

    def draw(self, app):
        app.slots.draw("chrome", app)
        if not app.slots.has("chrome"):
            self.title(app)
            imgui.same_line(0, 16)
            app.slots.draw("status", app)
        if app.pages:
            i = widgets.tabs("nav", [p.label for p in app.pages], app.page_index)
            if i != app.page_index:
                app.go(i)
        app.slots.draw("nav", app)

        avail = imgui.get_content_region_avail()
        side = min(self.aside, avail.x * 0.45)
        main = max(120.0, avail.x - side - 18)
        order = [("##main", main), ("##aside", side)]
        if not self.aside_right:
            order.reverse()
        for n, (tag, w) in enumerate(order):
            if n:
                imgui.same_line(0, 18)
            imgui.begin_child(tag, ImVec2(w, 0))
            if tag == "##main":
                self.page_body(app)
            else:
                app.slots.draw("aside", app)
            imgui.end_child()
        app.slots.draw("overlay", app)


#: Ready-made instances, for a profile to name.
TABBED = Tabbed()
RAIL = Rail()
DENSE = Dense()
STAGE = Stage()
HUD = Hud()
SPLIT = Split()

ALL = {l.name: l for l in (TABBED, RAIL, DENSE, STAGE, HUD, SPLIT)}


def get(name):
    """By name, falling back to the familiar one."""
    return ALL.get(name, TABBED)
