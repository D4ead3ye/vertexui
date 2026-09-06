"""A log pane that follows new output without yanking the page.

Auto-scroll normally means "jump to the bottom every frame", which makes a
busy log unreadable - lines appear already gone. This glides instead, at a
speed you choose, so the eye can follow a line down and off.

    log = logview.LogView(speed="calm")
    log.add("Connected", kind="ok", tag="net")
    log.draw()

Speeds are in pixels per second, which is the honest unit - lines per
second depends on the font size:

    calm     140 px/s   ~7 lines a second   (default)
    steady   260 px/s   ~13 lines a second
    quick    520 px/s   ~26 lines a second
    snap     straight to the bottom, no glide

Scrolling up by hand stops the follow; scrolling back to the bottom
resumes it. Nothing is more irritating than a pane that drags you away
from the line you were reading.
"""

import time

from imgui_bundle import ImVec2, imgui

from . import fonts
from . import theme as theme_mod

SPEEDS = {"calm": 140.0, "steady": 260.0, "quick": 520.0, "snap": None}
SPEED_ORDER = ["calm", "steady", "quick", "snap"]


class LogView:
    def __init__(self, speed="calm", max_lines=2000, monospaced=True,
                 timestamps=True, tags=True, row_spacing=1.0):
        self.entries = []
        self.max_lines = int(max_lines)
        self.speed = speed if speed in SPEEDS else "calm"
        self.monospaced = monospaced
        self.timestamps = timestamps
        self.tags = tags
        self.row_spacing = float(row_spacing)
        self.follow = True
        self.filter = ""
        # A rule that maps an entry to a colour; replaceable per project.
        self.colour_for = default_colour
        self._scroll = 0.0
        self._last_set = -1.0
        self._pending = False

    # -- content --------------------------------------------------------
    def add(self, text, kind=None, tag=None, ts=None):
        self.entries.append({"text": str(text), "kind": kind, "tag": tag,
                             "ts": ts or time.strftime("%H:%M:%S")})
        if len(self.entries) > self.max_lines:
            del self.entries[: len(self.entries) - self.max_lines]
        self._pending = True

    def extend(self, texts, **kw):
        for t in texts:
            self.add(t, **kw)

    def clear(self):
        self.entries.clear()
        self._scroll = 0.0

    def visible(self):
        needle = self.filter.lower()
        if not needle:
            return self.entries
        return [e for e in self.entries
                if needle in e["text"].lower() or needle in (e["tag"] or "").lower()]

    # -- drawing --------------------------------------------------------
    def draw(self, size=None, border=True):
        t = theme_mod.current()
        flags = imgui.ChildFlags_.borders if border else 0
        if not imgui.begin_child("##logview", size or ImVec2(0, 0), flags):
            imgui.end_child()
            return

        font = fonts.use("mono") if self.monospaced else fonts.use("ui")
        font.__enter__()
        if self.row_spacing != 1.0:
            imgui.push_style_var(imgui.StyleVar_.item_spacing,
                                 ImVec2(imgui.get_style().item_spacing.x,
                                        4.0 * self.row_spacing))
        rows = self.visible()
        # Only the visible slice is emitted: ImGui rebuilds every line every
        # frame, and a few thousand of them is a measurable cost for text
        # nobody can see.
        clipper = imgui.ListClipper()
        clipper.begin(len(rows))
        while clipper.step():
            for i in range(clipper.display_start, clipper.display_end):
                self._row(rows[i], t)
        if self.row_spacing != 1.0:
            imgui.pop_style_var()
        font.__exit__()

        self._autoscroll()
        imgui.end_child()

    def _row(self, e, t):
        if self.timestamps:
            imgui.text_colored(t.text_mute, e["ts"])
            imgui.same_line()
        if self.tags and e.get("tag"):
            imgui.text_colored(t.status(e["kind"]) if e["kind"] else t.text_dim,
                               f"{e['tag']:<10}")
            imgui.same_line()
        colour = self.colour_for(e, t)
        if colour is None:
            imgui.text_unformatted(e["text"])
        else:
            imgui.text_colored(colour, e["text"])

    def _autoscroll(self):
        """Glide toward the bottom, and get out of the way if the reader
        takes over."""
        maxy = imgui.get_scroll_max_y()
        now = imgui.get_scroll_y()

        # A scroll position we did not set means the wheel was used. Treat
        # moving away from the bottom as "stop following", and coming back
        # to it as "resume".
        if self._last_set >= 0.0 and abs(now - self._last_set) > 1.0:
            self.follow = now >= maxy - 4.0
            self._scroll = now

        if not self.follow:
            self._last_set = -1.0
            return

        speed = SPEEDS.get(self.speed)
        if speed is None:                     # snap
            self._scroll = maxy
        else:
            dt = min(0.05, max(0.0001, imgui.get_io().delta_time))
            gap = maxy - self._scroll
            if gap > 0.5:
                self._scroll = min(maxy, self._scroll + speed * dt)
            else:
                self._scroll = maxy
        imgui.set_scroll_y(self._scroll)
        self._last_set = self._scroll

    # -- helpers --------------------------------------------------------
    def lines_per_second(self, line_height=None):
        """What the current speed works out to, for showing in a UI."""
        speed = SPEEDS.get(self.speed)
        if speed is None:
            return None
        lh = line_height or max(1.0, imgui.get_text_line_height_with_spacing())
        return speed / lh


def default_colour(entry, t):
    """Colour by kind if given, otherwise leave it alone. Projects with
    their own conventions replace `LogView.colour_for`."""
    kind = entry.get("kind")
    if kind:
        return t.status(kind)
    return None
