"""Y2K Cyber: a system monitor built out of floating windows.

    python examples/cyberdeck.py
    python examples/cyberdeck.py --profile noir    # the same app, stock

Cards become Win98 windows here - gradient title bar, module name in
monospace, minimise and close squares - so a screen of panels reads as a
desktop rather than as a dashboard. The CD-ROM spinner runs while the
scan is live, and the command field is a hard inset well with monospace
text in it.

Every bit of that comes from the profile. `--profile noir` is the same
code as a flat dark panel, which is the only honest way to show what a
theme is actually doing.
"""

import math
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from imgui_bundle import ImVec2, imgui                   # noqa: E402

import vertexui as vui                                   # noqa: E402
from vertexui import (cards, compose, fmt, fonts, graphics, inputs, logview,
                      notices, profiles, themes, widgets)  # noqa: E402
from vertexui import theme as theme_mod                  # noqa: E402

NODES = ["GIBSON", "ACID-BURN", "ZERO-COOL", "THE-PLAGUE"]
CHATTER = [
    ("ok", "net", "handshake complete :: 10.0.0.4"),
    ("info", "sys", "paging file resized to 512M"),
    ("info", "cd", "reading track 04 ... ok"),
    ("warn", "net", "packet loss 2.4% on eth0"),
    ("error", "disk", "sector 0x7fe2 unreadable"),
    ("info", "sys", "defrag pass 3 of 7"),
]


class Deck(compose.Module):
    name = "deck"

    def __init__(self):
        self.rng = random.Random(9)
        self.cpu = [0.4] * 60
        self.mem = [0.55] * 60
        self.net = [0.2] * 60
        self.scanning = True
        self.cmd = ""
        self.node = 0
        self.log = logview.LogView(speed="quick")
        self.tray = notices.Tray(corner="tr", width=300)
        self._next = 0.0
        for _ in range(14):
            self._emit()

    def _emit(self):
        k, tag, text = self.rng.choice(CHATTER)
        self.log.add(text, kind=k, tag=tag)

    def setup(self, app):
        app.page("system", "System", icon="terminal", draw=self.system)
        app.page("network", "Network", icon="cloud", draw=self.network)
        app.slot("status", self.status)
        app.hook("frame_begin", self.tick)

    def tick(self, app):
        now = time.time()
        if now < self._next:
            return
        self._next = now + 0.06
        vui.anim.mark_busy()
        for series, drift in ((self.cpu, 0.07), (self.mem, 0.02),
                              (self.net, 0.10)):
            nxt = max(0.03, min(0.99, series[-1] + self.rng.uniform(-drift, drift)))
            series.pop(0)
            series.append(nxt)
        if self.scanning and self.rng.random() < 0.09:
            self._emit()

    def status(self, app):
        t = theme_mod.current()
        with fonts.use("mono"):
            imgui.text_colored(t.info, f"[{NODES[self.node]}]")
        imgui.same_line(0, 10)
        widgets.badge("ONLINE" if self.scanning else "HALTED",
                      "ok" if self.scanning else "warn")

    # -- pages ---------------------------------------------------------
    def system(self, app):
        t = theme_mod.current()
        avail = imgui.get_content_region_avail().x
        third = (avail - 24) / 3.0

        for title, series, unit, kind in (
                ("cpu load", self.cpu, "%", "info"),
                ("memory", self.mem, "%", "ok"),
                ("disk io", self.net, "MB/s", "warn")):
            with cards.card(title, right=f"{series[-1] * 100:.0f}{unit}",
                            right_col=t.status(kind), edge=t.status(kind),
                            width=third) as c:
                graphics.sparkline(series, c.width, 46, lo=0.0, hi=1.0,
                                   colour=t.status(kind), tooltip=True,
                                   value_fmt=lambda v: f"{v * 100:.0f}{unit}")
                imgui.dummy(ImVec2(0, 4))
                graphics.pips(10, int(series[-1] * 10), size=7.0)
            imgui.same_line()
        imgui.new_line()

        imgui.dummy(ImVec2(0, 8))
        half = (avail - 18) * 0.5
        with cards.card("optical drive", right="CD-ROM", width=half) as c:
            if self.scanning:
                widgets.spinner(58, label="READING DISC")
            else:
                imgui.text_colored(t.text_mute, "tray open")
            imgui.dummy(ImVec2(0, 6))
            self.scanning = inputs.switch("Spin up", self.scanning)
            imgui.dummy(ImVec2(0, 4))
            self.node = inputs.segmented("node", NODES, self.node, height=26)
        imgui.same_line()
        with cards.card("console", right="TTY0", width=half) as c:
            _, self.cmd = inputs.text_input("cmd", self.cmd,
                                            hint="type a command",
                                            width=c.width / t.ui_scale)
            imgui.dummy(ImVec2(0, 6))
            if widgets.button("EXECUTE", 150, primary=True, icon="bolt",
                              key="run"):
                self.log.add(f"> {self.cmd or 'noop'}", kind="ok", tag="cmd")
                self.tray.push("ok", f"ran: {self.cmd or 'noop'}")
                self.cmd = ""
            imgui.same_line()
            if widgets.button("ABORT", 120, icon="cross", key="abort"):
                self.tray.push("error", "aborted by operator")
        self.tray.draw()

    def network(self, app):
        t = theme_mod.current()
        with cards.card("traffic", right="eth0", edge=t.info) as c:
            graphics.plot({"in": self.net, "out": self.cpu}, c.width, 150,
                          lo=0.0, hi=1.0, fill=True, tooltip=True,
                          value_fmt=lambda v: f"{v * 94:.1f} MB/s")
        imgui.dummy(ImVec2(0, 8))
        with cards.card("transfer log", right=f"{len(self.log.rows)} LINES"
                        if hasattr(self.log, "rows") else "LIVE") as c:
            self.log.draw()
        self.tray.draw()


def main(argv):
    name = "y2k-cyber"
    if "--profile" in argv:
        name = argv[argv.index("--profile") + 1]
    profile = profiles.get(name)
    print(f"profile {profile.name}: {profile.blurb}")
    app = compose.App(profile=profile, title="cyberdeck",
                      app_id="vertexui-y2k", size=(1120, 740))
    app.use(Deck())
    if "--page" in argv:
        app.setup()
        app.go(argv[argv.index("--page") + 1])
    app.run()


if __name__ == "__main__":
    main(sys.argv[1:])
