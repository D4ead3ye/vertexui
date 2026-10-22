"""ENA World: a survey station for a place that does not hold still.

    python examples/outworld.py
    python examples/outworld.py --profile noir     # the same app, stock

The domain picked for this theme is a *survey*, because the one thing
the environment it comes from is about is being measured by someone who
cannot quite trust the measurement. So every reading here has a
confidence that decays, the region you are looking at drifts on its own,
and the log is mostly the instrument complaining.

That shapes the program: a tab strip over three fixed views, no scrolling
document, high density, and status colour doing real work - a region
whose stability falls below the floor is the only thing on the screen
that is allowed to shout.

`--profile noir` is the identical code as a flat dark panel. The cut
corners, the chess floor, the 12fps monolith, the 1-bit hover and the
magenta corruption all come from the profile and its skin.
"""

import math
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from imgui_bundle import ImVec2, imgui                      # noqa: E402

import vertexui as vui                                      # noqa: E402
from vertexui import (cards, compose, fonts, graphics, inputs, logview,
                      notices, profiles, skins, table, widgets)  # noqa: E402
from vertexui import theme as theme_mod                     # noqa: E402

# Canon where there is canon, and the reference sheet's own names where
# there is not. Nothing here is invented to fill a column.
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


def _pal(key, fallback):
    """The skin's colour if it has one, the palette's if not - so this
    file renders honestly under `--profile noir` too."""
    return skins.extra(key, fallback)


class Survey(compose.Module):
    name = "survey"

    def __init__(self):
        self.rng = random.Random(27)
        self.region = 3
        self.scanning = True
        self.depth = 4
        self.stability = [s for _n, _k, s in REGIONS]
        self.turbulence = [0.2] * 70
        self.noise = [0.05] * 70
        self.note = ""
        self.cols = [table.Col("id", "REF", 70),
                     table.Col("place", "REGION"),
                     table.Col("exits", "EXITS", 80, align="r"),
                     table.Col("stab", "STABILITY", 110, align="r")]
        self.state = table.State(sort="")
        self.log = logview.LogView(speed="quick")
        self.msgs = notices.Tray(corner="tr", width=300)
        self._next = 0.0
        for _ in range(10):
            self._emit()

    def _emit(self):
        k, tag, text = self.rng.choice(CHATTER)
        self.log.add(text, kind=k, tag=tag)

    def setup(self, app):
        app.page("region", "REGION", icon="grid", draw=self.page_region)
        app.page("signal", "SIGNAL", icon="bolt", draw=self.page_signal)
        app.page("archive", "ARCHIVE", icon="cube", draw=self.page_archive)
        app.slot("status", self.status)
        app.hook("frame_begin", self.tick)

    def tick(self, app):
        now = time.time()
        if now < self._next:
            return
        self._next = now + 0.07
        vui.anim.mark_busy()
        for series, drift, lo in ((self.turbulence, 0.09, 0.02),
                                  (self.noise, 0.04, 0.0)):
            nxt = max(lo, min(0.99,
                              series[-1] + self.rng.uniform(-drift, drift)))
            series.pop(0)
            series.append(nxt)
        if not self.scanning:
            return
        # a measured place drifts *because* it is being measured
        i = self.region
        self.stability[i] = max(0.02, min(0.99, self.stability[i]
                                          + self.rng.uniform(-0.035, 0.03)))
        if self.rng.random() < 0.07:
            self._emit()

    def status(self, app):
        t = theme_mod.current()
        s = self.stability[self.region]
        widgets.badge("SURVEYING" if self.scanning else "HELD",
                      "ok" if self.scanning else "warn")
        imgui.same_line(0, 12)
        with fonts.use("mono"):
            imgui.text_colored(t.text_dim,
                               f"{REGIONS[self.region][0]}  /  DEPTH {self.depth}")
        if s < 0.25:
            imgui.same_line(0, 12)
            widgets.badge("UNSTABLE", "error")

    # -- pages ---------------------------------------------------------
    def page_region(self, app):
        t = theme_mod.current()
        avail = imgui.get_content_region_avail().x
        side = 330.0
        name, kana, _ = REGIONS[self.region]
        s = self.stability[self.region]

        with cards.card("Region", right=f"{self.depth} DEEP",
                        edge=t.status("error" if s < 0.25 else "ok"),
                        width=avail - side - 18) as c:
            with fonts.use("big"):
                imgui.text_colored(t.text, name.replace("_", " "))
            if fonts.has("cjk"):
                imgui.same_line(0, 12)
                with fonts.use("cjk"):
                    imgui.text_colored(_pal("mint", t.info), kana)
            imgui.dummy(ImVec2(0, 8))
            inputs.field_label("Stability", "drifts while observed")
            graphics.segments(s, count=24, hot=0.0, block=7.0,
                              colour=t.status("error" if s < 0.25 else "ok"),
                              hot_colour=t.status("error" if s < 0.25
                                                  else "ok"))
            imgui.dummy(ImVec2(0, 8))
            self.region = inputs.segmented(
                "reg", [r[0].split("_")[-1][:6] for r in REGIONS[:5]],
                min(self.region, 4), height=28)
            imgui.dummy(ImVec2(0, 8))
            if widgets.button("HOLD" if self.scanning else "SURVEY", 150,
                              primary=not self.scanning, key="go"):
                self.scanning = not self.scanning
                self.msgs.push("ok" if self.scanning else "warn",
                               "survey resumed" if self.scanning
                               else "survey held")
            imgui.same_line()
            if widgets.button("DESCEND", 140, key="down"):
                self.depth += 1
                self.log.add(f"descended to depth {self.depth}",
                             kind="warn", tag="core")
        imgui.same_line()
        with cards.card("Void", right="—", width=side) as c:
            if self.scanning:
                widgets.spinner(86, key="mono", label="RESOLVING")
            else:
                imgui.dummy(ImVec2(0, 96))
                imgui.text_colored(t.text_mute, "instrument idle")
            imgui.dummy(ImVec2(0, 8))
            cy_ = _pal("mint", t.info)
            graphics.segments(self.noise[-1], count=16, hot=0.75, label="N",
                              colour=cy_)
            graphics.segments(self.turbulence[-1], count=16, hot=0.75,
                              label="T", colour=cy_)
        self.msgs.draw()

    def page_signal(self, app):
        t = theme_mod.current()
        with cards.card("Turbulence", right="LIVE",
                        edge=t.status("warn")) as c:
            graphics.plot({"turbulence": self.turbulence,
                           "noise": self.noise}, c.width, 170,
                          lo=0.0, hi=1.0, fill=True, tooltip=True)
        imgui.dummy(ImVec2(0, 8))
        half = (imgui.get_content_region_avail().x - 18) * 0.5
        with cards.card("Readings", width=half) as c:
            for i, (nm, _k, _s) in enumerate(REGIONS[:5]):
                imgui.text_colored(t.text_dim, nm.replace("_", " ")[:18])
                imgui.same_line(0, 8)
                graphics.segments(self.stability[i], count=14, hot=0.0,
                                  block=5.0, height=10.0,
                                  colour=t.status("error"
                                                  if self.stability[i] < 0.25
                                                  else "ok"),
                                  hot_colour=t.status("ok"))
        imgui.same_line()
        with cards.card("Noise", right=f"{self.noise[-1]:.2f}",
                        width=half) as c:
            graphics.waveform([math.sin(x * 0.5) * self.noise[-1] * 4
                               for x in range(64)], c.width, 92,
                              colour=_pal("rose", t.accent))
            imgui.dummy(ImVec2(0, 6))
            _, self.note = inputs.text_input("note", self.note,
                                             hint="log an observation",
                                             width=c.width / t.ui_scale)
            if widgets.button("COMMIT", 140, primary=True, key="commit"):
                self.log.add(self.note or "(no observation)", kind="info",
                             tag="note")
                self.note = ""
        self.msgs.draw()

    def page_archive(self, app):
        t = theme_mod.current()
        # full width: a table tints its rows to the window edge
        with cards.card("Archive", right=f"{len(REGIONS)} REGIONS") as c:
            rows = [{"id": f"{i:02d}", "place": n.replace("_", " "),
                     "exits": (i * 3) % 5 + 1,
                     "stab": f"{self.stability[i]:.2f}"}
                    for i, (n, _k, _s) in enumerate(REGIONS)]
            with table.table("regions", self.cols, height=252) as open_:
                if open_:
                    table.header(self.cols, self.state)
                    for i, r in table.rows(rows, self.state):
                        _h, clicked = table.row_begin(r["id"],
                                                      i == self.region)
                        table.cell(r["id"], role="mono", column=0)
                        table.cell(r["place"], column=1)
                        table.cell(str(r["exits"]), align="r", role="mono",
                                   column=2)
                        table.cell(r["stab"], align="r", role="mono",
                                   column=3,
                                   colour=t.status("error")
                                   if self.stability[i] < 0.25 else None)
                        if clicked:
                            self.region = i
                            self.log.add(f"focus {REGIONS[i][0]}", kind="ok",
                                         tag="survey")
        imgui.dummy(ImVec2(0, 8))
        with cards.card("Log", right="LIVE", edge=t.info) as c:
            self.log.draw(ImVec2(0, 220))
        self.msgs.draw()


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
