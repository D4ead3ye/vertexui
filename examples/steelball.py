"""Steel Ball Run: a cross-country race board.

    python examples/steelball.py
    python examples/steelball.py --profile noir     # the same app, stock

A theme is only worth anything applied to something, so this is a real
little tool rather than a swatch page: stage standings, a leg timer, a
rider card per competitor, and the steel ball turning while the stage is
live.

The point of the `--profile` switch is the honest one - every pixel of
character here comes from the profile and its skin. Run it on `noir` and
the same code is a flat dark dashboard.
"""

import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from imgui_bundle import ImVec2, imgui                   # noqa: E402

import vertexui as vui                                   # noqa: E402
from vertexui import (cards, compose, fmt, fonts, graphics, inputs, notices,
                      profiles, table, themes, widgets)   # noqa: E402
from vertexui import theme as theme_mod                  # noqa: E402

RIDERS = [
    ("Gyro Zeppeli", "Valkyrie", "#c2185b"),
    ("Johnny Joestar", "Slow Dancer", "#17888c"),
    ("Diego Brando", "Silver Bullet", "#8d6e2f"),
    ("Sandman", "-", "#a3202b"),
    ("Pocoloco", "Hey Ya", "#1f7a5e"),
]
STAGES = ["Dry Bones", "Devil's Palm", "Rocky Mountain", "Philadelphia"]


def _walk(seed, n=40):
    """A bounded random walk - a stage profile, not a sine wave."""
    rnd = __import__("random").Random(seed * 17 + 3)
    v, out = 0.5, []
    for _ in range(n):
        v = max(0.08, min(0.98, v + rnd.uniform(-0.09, 0.09)))
        out.append(v)
    return out


class Race(compose.Module):
    name = "race"

    def __init__(self):
        self.t0 = time.time()
        self.stage = 1
        self.live = True
        self.tray = notices.Tray(corner="tr", width=290)
        self.tbl = table.State(sort="gap")
        self.riders = [
            {"name": n, "horse": h, "tint": c,
             "gap": i * 42.0 + (i * 7 % 13),
             "dist": 1.0 - i * 0.07,
             "trail": _walk(i)}
            for i, (n, h, c) in enumerate(RIDERS)]

    def setup(self, app):
        app.page("standings", "Standings", icon="list", draw=self.standings)
        app.page("riders", "Riders", icon="user", draw=self.riders_page)
        app.slot("status", self.status)
        app.hook("frame_begin", self.tick)

    def tick(self, app):
        if not self.live:
            return
        vui.anim.mark_busy()
        for i, r in enumerate(self.riders):
            r["gap"] = max(0.0, r["gap"] + math.sin(time.time() * 0.6 + i) * 0.06)
            r["trail"] = r["trail"][1:] + [
                max(0.05, min(1.0, r["trail"][-1]
                              + math.sin(time.time() * 2.1 + i * 2.0) * 0.012))]

    def status(self, app):
        t = theme_mod.current()
        widgets.status_pill(label_on="STAGE LIVE", label_off="HELD",
                            on=self.live)
        imgui.same_line(0, 12)
        with fonts.use("label"):
            imgui.text_colored(t.text_dim,
                               fmt.clock(time.time() - self.t0).upper())

    # -- pages ---------------------------------------------------------
    def standings(self, app):
        t = theme_mod.current()
        avail = imgui.get_content_region_avail().x

        with cards.card(STAGES[self.stage], icon="bolt",
                        right="LEG " + str(self.stage + 1),
                        right_col=t.accent, edge=t.accent) as c:
            left = c.width * 0.618                   # the golden division
            imgui.begin_group()
            second = sorted(self.riders, key=lambda r: r["gap"])[1]["gap"]
            with fonts.use("huge"):
                imgui.text_colored(t.text, f"{second:.0f}")
            imgui.same_line(0, 6)
            imgui.text_colored(t.text_mute, "m lead")
            graphics.sparkline(self.riders[0]["trail"], left, 40,
                               colour=t.accent, tooltip=True)
            imgui.end_group()
            imgui.same_line(0, 18)
            imgui.begin_group()
            if self.live:
                widgets.spinner(69, label="stage running", key="race")
            else:
                imgui.text_colored(t.text_mute, "stage held")
            imgui.dummy(ImVec2(0, 6))
            self.live = inputs.switch("Live", self.live)
            imgui.end_group()

        imgui.dummy(ImVec2(0, 10))
        self.stage = inputs.segmented("stage", STAGES, self.stage)
        imgui.same_line(0, 14)
        if widgets.button("Flag stage", 150, primary=True, icon="check",
                          key="flag"):
            self.tray.push("ok", f"{STAGES[self.stage]} flagged")

        imgui.dummy(ImVec2(0, 10))
        with cards.card("stage standings", icon="list",
                        right=f"{len(self.riders)} RIDERS") as _c:
            self._standings_table(t)
        self.tray.draw()

    def _standings_table(self, t):
        cols = [table.Col("name", "Rider"),
                table.Col("horse", "Horse", 170),
                table.Col("gap", "Gap", 120, align="r"),
                table.Col("dist", "Stage", 150, align="r")]
        rows = self.tbl.sort_rows(self.riders)
        with table.table("standings", cols, height=300) as open_:
            if open_:
                table.header(cols, self.tbl)
                for i, r in table.rows(rows, self.tbl):
                    sel = r["name"] in self.tbl.selected
                    _, clicked = table.row_begin(r["name"], sel)
                    if clicked:
                        self.tbl.toggle(r["name"])
                    table.cell(r["name"], column=0)
                    table.cell(r["horse"], column=1, colour=t.text_dim)
                    table.cell("leader" if r["gap"] < 1 else f"+{r['gap']:.0f} m",
                               align="r", column=2,
                               colour=t.accent if i == 0 else t.text)
                    table.cell(fmt.ratio(r["dist"], 1.0), align="r", column=3,
                               role="mono")

    def riders_page(self, app):
        t = theme_mod.current()
        avail = imgui.get_content_region_avail().x
        w = (avail - 18) * 0.5
        for i, r in enumerate(self.riders):
            if i % 2:
                imgui.same_line()
            tint = theme_mod.rgb(r["tint"])
            with cards.card(r["name"], icon="user", right=r["horse"],
                            right_col=tint, edge=tint, width=w) as c:
                graphics.ring(r["dist"], radius=30, thickness=6, colour=tint,
                              centre=f"{r['dist'] * 100:.0f}%")
                imgui.same_line(0, 16)
                imgui.begin_group()
                with fonts.use("big"):
                    imgui.text_colored(t.text, f"{r['gap']:+.0f}")
                imgui.same_line(0, 5)
                imgui.text_colored(t.text_mute, "metres")
                graphics.sparkline(r["trail"], c.width - 92, 26, colour=tint)
                imgui.end_group()
        imgui.new_line()
        imgui.dummy(ImVec2(0, 8))
        notices.note("Gaps are to the stage leader and update while the "
                     "stage is live. Flagging a stage freezes them.",
                     icon="info")
        self.tray.draw()


def main(argv):
    name = "steel-ball-run"
    if "--profile" in argv:
        name = argv[argv.index("--profile") + 1]
    profile = profiles.get(name)
    print(f"profile {profile.name}: {profile.blurb}")
    app = compose.App(profile=profile, title="Steel Ball Run",
                      app_id="vertexui-sbr", size=(1120, 740))
    app.use(Race())
    if "--page" in argv:
        app.setup()
        app.go(argv[argv.index("--page") + 1])
    app.run()


if __name__ == "__main__":
    main(sys.argv[1:])
