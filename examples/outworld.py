"""ENA World: a reference CD-ROM for a place that will not hold still.

    python examples/outworld.py
    python examples/outworld.py --profile noir     # the same app, stock

The shape of a 2001 multimedia title, because that is what the theme is:
a file menu across the top, dense asymmetric panels under it, a framed
viewport with a model turning in it, pixelated progress bars, a settings
dialog full of chunky form controls, and a status strip along the foot
that is never empty.

The domain is a survey, and the joke the whole program is built on is
that the subject declines to be surveyed: every reading has a confidence
that decays, the region you are looking at drifts *because* you are
looking at it, and the log is mostly the instrument complaining.

That shapes it as a program rather than as a skin. Panels are deliberately
unequal - a wide index against a narrow viewport, a tall log against a
short meter stack - because a grid of equal cards is a 2015 dashboard and
this is not one. `--profile noir` is the identical code as a flat dark
panel.
"""

import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from imgui_bundle import ImVec2, imgui                      # noqa: E402

import vertexui as vui                                      # noqa: E402
from vertexui import (cards, compose, dialogs, fonts, graphics, inputs,
                      logview, notices, profiles, skins, table,
                      widgets)                              # noqa: E402
from vertexui import theme as theme_mod                     # noqa: E402

# Canon where there is canon, the reference sheet's own names where there
# is not. Nothing here is invented to fill a column.
REGIONS = [
    ("RED_OUTWORLD", "赤の外界", 0.72),
    ("THE_HUB", "中枢", 0.91),
    ("LONELY_DOOR", "孤独の扉", 0.64),
    ("UNCANNY_STREETS", "街", 0.38),
    ("LOST_VILLAGE", "失われた村", 0.21),
    ("THE_CORE", "核", 0.47),
    ("TEMPTATION_STAIRWAY", "誘惑の階段", 0.33),
    ("TURQUOISE_HILL", "青の丘", 0.80),
    ("HOURGLASS_MEADOW", "砂時計の野", 0.55),
    ("THE_GREAT_RUNAWAY", "大逃亡", 0.12),
]
CHATTER = [
    ("info", "survey", "geometry resolved :: 4 exits"),
    ("info", "survey", "floor sampled, grid intact"),
    ("warn", "drift", "horizon moved 11 units while observed"),
    ("warn", "drift", "exit count disagrees with previous pass"),
    ("error", "void", "reading lost - region declined to be measured"),
    ("ok", "sync", "re-registered against the hub"),
    ("info", "noise", "static floor 0.04, within tolerance"),
]
MENUS = {
    "File": ["Open Volume...", "Close Volume", "-", "Export Readings",
             "-", "Exit"],
    "Edit": ["Copy Reading", "Clear Log"],
    "View": ["Index", "Readings", "Archive", "-", "Status Bar"],
    "Options": ["Preferences...", "-", "Recalibrate"],
}


def _pal(key, fallback):
    """The skin's colour where it has one, the palette's where it has
    not - so this file renders honestly under `--profile noir` too."""
    return skins.extra(key, fallback)


class Survey(compose.Module):
    name = "survey"

    def __init__(self):
        self.rng = random.Random(27)
        self.region = 3
        self.scanning = True
        self.depth = 4
        self.transfer = 0.0
        self.stability = [s for _n, _k, s in REGIONS]
        self.turbulence = [0.2] * 70
        self.noise = [0.05] * 70
        self.note = ""
        self.quality = 1
        self.opts = {"grid": True, "noise": False, "halt": True}
        self.cols = [table.Col("id", "REF", 62),
                     table.Col("place", "REGION"),
                     table.Col("exits", "EXITS", 72, align="r"),
                     table.Col("stab", "STABILITY", 100, align="r")]
        self.state = table.State(sort="")
        self.log = logview.LogView(speed="quick")
        self.msgs = notices.Tray(corner="tr", width=290)
        self._next = 0.0
        for _ in range(9):
            self._emit()

    def _emit(self):
        k, tag, text = self.rng.choice(CHATTER)
        self.log.add(text, kind=k, tag=tag)

    def setup(self, app):
        app.page("index", "INDEX", icon="list", draw=self.page_index)
        app.page("readings", "READINGS", icon="gauge", draw=self.page_readings)
        app.page("archive", "ARCHIVE", icon="cube", draw=self.page_archive)
        app.slot("chrome", self.chrome)
        app.slot("status", self.status)
        app.hook("frame_begin", self.tick)
        dialogs.register("prefs", self.prefs)

    def tick(self, app):
        now = time.time()
        if now < self._next:
            return
        self._next = now + 0.07
        vui.anim.mark_busy()
        for series, drift, lo in ((self.turbulence, 0.09, 0.02),
                                  (self.noise, 0.04, 0.0)):
            series.pop(0)
            series.append(max(lo, min(0.99, series[-1]
                                      + self.rng.uniform(-drift, drift))))
        if not self.scanning:
            return
        self.transfer = (self.transfer + 0.012) % 1.0
        i = self.region
        self.stability[i] = max(0.02, min(0.99, self.stability[i]
                                          + self.rng.uniform(-0.035, 0.03)))
        if self.rng.random() < 0.07:
            self._emit()

    # -- chrome --------------------------------------------------------
    def chrome(self, app):
        hit = widgets.menubar("mb", MENUS)
        if hit[1] == "Preferences...":
            dialogs.open("prefs")
        elif hit[1] == "Clear Log":
            self.log.rows.clear() if hasattr(self.log, "rows") else None
            self.msgs.push("info", "log cleared")
        elif hit[1] == "Recalibrate":
            self.stability = [s for _n, _k, s in REGIONS]
            self.msgs.push("ok", "readings reset to survey baseline")
        elif hit[1] == "Exit":
            app.running = False

    def status(self, app):
        t = theme_mod.current()
        s = self.stability[self.region]
        widgets.badge("SURVEYING" if self.scanning else "HELD",
                      "ok" if self.scanning else "warn")
        imgui.same_line(0, 10)
        with fonts.use("mono"):
            imgui.text_colored(t.text_dim,
                               f"{REGIONS[self.region][0]}  DEPTH {self.depth}")
        imgui.same_line(0, 12)
        graphics.segments(self.transfer, count=14, block=5.0, height=9.0,
                          hot=1.1, colour=_pal("olive", t.ok))
        if s < 0.25:
            imgui.same_line(0, 10)
            widgets.badge("UNSTABLE", "error")

    # -- the settings dialog -------------------------------------------
    def prefs(self, data):
        t = theme_mod.current()
        with dialogs.modal("prefs", "Preferences", width=430) as open_:
            if not open_:
                return
            inputs.field_label("Render quality", "affects the viewport only")
            self.quality = inputs.radio(
                "q", ["Wireframe only", "Flat shaded", "Flat + wireframe"],
                self.quality)
            imgui.dummy(ImVec2(0, 6))
            inputs.field_label("Overlays")
            self.opts["grid"] = inputs.check("CAD gridlines",
                                             self.opts["grid"])
            self.opts["noise"] = inputs.check("Granite noise",
                                              self.opts["noise"])
            self.opts["halt"] = inputs.check("Halt survey on instability",
                                             self.opts["halt"])
            imgui.dummy(ImVec2(0, 4))
            inputs.field_label("Operator")
            _, self.note = inputs.text_input("op", self.note,
                                             hint="initials for the log")
            ok, _no = dialogs.buttons("Apply", "Cancel")
            if ok:
                self.msgs.push("ok", "preferences applied")

    # -- pages ---------------------------------------------------------
    def page_index(self, app):
        t = theme_mod.current()
        avail = imgui.get_content_region_avail().x
        name, kana, _ = REGIONS[self.region]
        s = self.stability[self.region]
        # deliberately unequal: a wide index against a narrow viewport
        side = 260.0

        with cards.card("Region", right=f"{self.depth} DEEP",
                        edge=t.status("error" if s < 0.25 else "ok"),
                        width=avail - side - 16) as c:
            with fonts.use("big"):
                imgui.text_colored(t.text, name.replace("_", " ").title())
            if fonts.has("cjk"):
                imgui.same_line(0, 10)
                with fonts.use("cjk"):
                    imgui.text_colored(t.text_mute, kana)
            imgui.dummy(ImVec2(0, 6))
            inputs.field_label("Stability", "drifts while observed")
            graphics.segments(s, count=26, block=7.0, hot=1.1,
                              colour=t.status("error" if s < 0.25 else "ok"))
            imgui.dummy(ImVec2(0, 6))
            inputs.field_label("Transfer", "reading the volume")
            graphics.segments(self.transfer, count=26, block=7.0, hot=1.1,
                              colour=_pal("rust", t.warn))
            imgui.dummy(ImVec2(0, 8))
            self.region = inputs.segmented(
                "reg", [r[0].split("_")[-1][:6] for r in REGIONS[:5]],
                min(self.region, 4), height=26)
            imgui.dummy(ImVec2(0, 8))
            if widgets.button("HOLD" if self.scanning else "SURVEY", 140,
                              primary=not self.scanning, key="go"):
                self.scanning = not self.scanning
            imgui.same_line()
            if widgets.button("DESCEND", 130, key="down"):
                self.depth += 1
                self.log.add(f"descended to depth {self.depth}",
                             kind="warn", tag="core")
            imgui.same_line()
            if widgets.button("OPTIONS", 130, key="opt"):
                dialogs.open("prefs")
        imgui.same_line()
        with cards.card("Viewport", right="3D", width=side) as c:
            draw = skins.extra("viewport")
            if draw is not None:
                dl = imgui.get_window_draw_list()
                o = imgui.get_cursor_screen_pos()
                half = min(c.width, 190.0) * 0.5 - 6
                draw(dl, o.x + c.width * 0.5, o.y + half + 4, half,
                     imgui.get_time(), 1.0)
                imgui.dummy(ImVec2(c.width, half * 2 + 10))
            elif self.scanning:
                widgets.spinner(84, key="mono", label="RESOLVING")
            else:
                imgui.dummy(ImVec2(0, 92))
            imgui.dummy(ImVec2(0, 4))
            with fonts.use("mono"):
                imgui.text_colored(t.text_dim, f"POLY  {8 + self.depth * 2}")
                imgui.text_colored(t.text_dim, f"EXITS {self.depth % 5 + 1}")

        # a second, unequal row - a narrow exit list against a wide log,
        # because a page of two equal halves is a 2015 dashboard
        imgui.dummy(ImVec2(0, 8))
        narrow = 300.0
        avail2 = imgui.get_content_region_avail().x
        with cards.card("Exits", right=f"{self.depth % 5 + 1}",
                        width=narrow) as c:
            for i in range(self.depth % 5 + 1):
                nm = REGIONS[(self.region + i + 1) % len(REGIONS)][0]
                with fonts.use("mono"):
                    imgui.text_colored(t.text_dim,
                                       f"{i + 1:02d}  {nm[:18]}")
        imgui.same_line()
        with cards.card("Log", right="LIVE", width=avail2 - narrow - 16,
                        edge=t.info) as c:
            self.log.draw(ImVec2(0, 118))
        self._statusbar(t)
        self.msgs.draw()
        dialogs.draw()

    def _statusbar(self, t):
        """The strip along the foot of a 2001 application: never empty,
        never interactive, and the first place anyone looks when
        something has gone quiet."""
        dl = imgui.get_window_draw_list()
        pos = imgui.get_window_pos()
        size = imgui.get_window_size()
        h = 22.0
        y0 = pos.y + size.y - h
        bev = skins.extra("bevel")
        if bev is not None:
            bev(dl, pos.x, y0, size.x, h, False, t.surface)
        else:
            dl.add_rect_filled(ImVec2(pos.x, y0), ImVec2(pos.x + size.x,
                                                         pos.y + size.y),
                               theme_mod.u32(theme_mod.sink(t.surface, 0.3, t)))
        cells = (f"{REGIONS[self.region][0]}", f"DEPTH {self.depth}",
                 "SURVEYING" if self.scanning else "HELD",
                 f"NOISE {self.noise[-1]:.2f}")
        x = pos.x + 8
        with fonts.use("mono"):
            for i, text in enumerate(cells):
                w = (200.0 if i == 0 else 120.0)
                if bev is not None:
                    bev(dl, x, y0 + 3, w, h - 6, False, None)
                dl.add_text(ImVec2(x + 6, y0 + 4), theme_mod.u32(t.text_dim),
                            text)
                x += w + 4

    def page_readings(self, app):
        t = theme_mod.current()
        with cards.card("Turbulence", right="LIVE",
                        edge=t.status("warn")) as c:
            graphics.plot({"turbulence": self.turbulence,
                           "noise": self.noise}, c.width, 150,
                          lo=0.0, hi=1.0, fill=True, tooltip=True)
        imgui.dummy(ImVec2(0, 8))
        wide = (imgui.get_content_region_avail().x - 16) * 0.62
        with cards.card("Readings", width=wide) as c:
            for i, (nm, _k, _s) in enumerate(REGIONS[:6]):
                imgui.text_colored(t.text_dim, nm.replace("_", " ").title()[:20])
                imgui.same_line(0, 8)
                graphics.segments(self.stability[i], count=16, block=5.0,
                                  height=10.0, hot=1.1,
                                  colour=t.status("error"
                                                  if self.stability[i] < 0.25
                                                  else "ok"))
        imgui.same_line()
        with cards.card("Noise", right=f"{self.noise[-1]:.2f}") as c:
            graphics.segments(self.noise[-1], count=20, vertical=True,
                              height=96, width=13, hot=1.1,
                              colour=_pal("rust", t.warn))
            imgui.same_line(0, 12)
            graphics.segments(self.turbulence[-1], count=20, vertical=True,
                              height=96, width=13, hot=1.1,
                              colour=_pal("crimson", t.danger))
            imgui.dummy(ImVec2(0, 6))
            if widgets.button("COMMIT", 120, primary=True, key="commit"):
                self.log.add(self.note or "(no observation)", kind="info",
                             tag="note")
        self._statusbar(t)
        self.msgs.draw()
        dialogs.draw()

    def page_archive(self, app):
        t = theme_mod.current()
        # full width: a table tints its rows out to the window edge
        with cards.card("Archive", right=f"{len(REGIONS)} VOLUMES") as c:
            rows = [{"id": f"{i:02d}", "place": n.replace("_", " ").title(),
                     "exits": (i * 3) % 5 + 1,
                     "stab": f"{self.stability[i]:.2f}"}
                    for i, (n, _k, _s) in enumerate(REGIONS)]
            with table.table("regions", self.cols, height=244) as open_:
                if open_:
                    table.header(self.cols, self.state)
                    for i, r in table.rows(rows, self.state):
                        _h, clicked = table.row_begin(r["id"],
                                                      i == self.region)
                        table.cell(r["id"], role="mono", column=0)
                        table.cell(r["place"], column=1)
                        table.cell(str(r["exits"]), align="r", role="mono",
                                   column=2)
                        table.cell(r["stab"], align="r", role="mono", column=3,
                                   colour=t.status("error")
                                   if self.stability[i] < 0.25 else None)
                        if clicked:
                            self.region = i
                            self.log.add(f"opened {REGIONS[i][0]}", kind="ok",
                                         tag="survey")
        imgui.dummy(ImVec2(0, 8))
        with cards.card("Log", right="LIVE", edge=t.info) as c:
            self.log.draw(ImVec2(0, 160))
        self._statusbar(t)
        self.msgs.draw()
        dialogs.draw()


def main(argv):
    name = "ena-world"
    if "--profile" in argv:
        name = argv[argv.index("--profile") + 1]
    profile = profiles.get(name)
    print(f"profile {profile.name}: {profile.blurb}")
    app = compose.App(profile=profile, title="outworld",
                      app_id="vertexui-ena", size=(1120, 740))
    app.use(Survey())
    if "--page" in argv:
        app.setup()
        app.go(argv[argv.index("--page") + 1])
    app.run()


if __name__ == "__main__":
    main(sys.argv[1:])
