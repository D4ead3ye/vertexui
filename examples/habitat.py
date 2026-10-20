"""Frutiger Aero: a habitat monitor.

    python examples/habitat.py
    python examples/habitat.py --profile noir     # the same app, stock

Clean water, clean air, a sunny afternoon and a readout telling you
everything is fine - which is the exact thing this aesthetic was built to
sell in 2007, so it is the honest subject for it.

Glass plates over a sky-and-grass scene, pill buttons, pebble badges, and
the water bubble turning while a sample is running.
"""

import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from imgui_bundle import ImVec2, imgui                   # noqa: E402

import vertexui as vui                                   # noqa: E402
from vertexui import (cards, compose, fmt, fonts, graphics, inputs, notices,
                      profiles, themes, widgets)         # noqa: E402
from vertexui import theme as theme_mod                  # noqa: E402

TANKS = ["Reef", "Nursery", "Quarantine"]


class Habitat(compose.Module):
    name = "habitat"

    def __init__(self):
        self.t0 = time.time()
        self.tank = 0
        self.sampling = True
        self.aeration = True
        self.readings = {
            "temperature": {"v": 24.4, "unit": "C", "lo": 18.0, "hi": 30.0,
                            "kind": "ok", "hist": []},
            "oxygen": {"v": 7.8, "unit": "mg/L", "lo": 0.0, "hi": 12.0,
                       "kind": "info", "hist": []},
            "salinity": {"v": 34.1, "unit": "ppt", "lo": 28.0, "hi": 38.0,
                         "kind": "ok", "hist": []},
            "turbidity": {"v": 1.9, "unit": "NTU", "lo": 0.0, "hi": 8.0,
                          "kind": "warn", "hist": []},
        }
        for r in self.readings.values():
            r["hist"] = [r["v"]] * 48
        self.tray = notices.Tray(corner="tr", width=290)
        self._next = 0.0

    def setup(self, app):
        app.page("tanks", "Tanks", icon="cloud", draw=self.tanks)
        app.slot("status", self.status)
        app.hook("frame_begin", self.tick)

    def tick(self, app):
        now = time.time()
        if now < self._next or not self.sampling:
            return
        self._next = now + 0.08
        vui.anim.mark_busy()
        for i, r in enumerate(self.readings.values()):
            span = r["hi"] - r["lo"]
            r["v"] = max(r["lo"], min(r["hi"], r["v"] + math.sin(
                now * (0.5 + i * 0.3)) * span * 0.004))
            r["hist"] = r["hist"][1:] + [r["v"]]

    def status(self, app):
        widgets.badge("ONLINE" if self.sampling else "PAUSED",
                      "ok" if self.sampling else "warn")
        imgui.same_line()
        widgets.badge(f"{fmt.clock(time.time() - self.t0)} UPTIME", "info")

    def tanks(self, app):
        t = theme_mod.current()
        avail = imgui.get_content_region_avail().x

        with cards.card("sample run", icon="cloud",
                        right=TANKS[self.tank].upper(), right_col=t.accent,
                        edge=t.accent) as c:
            if self.sampling:
                widgets.spinner(64, label="drawing sample")
            else:
                imgui.text_colored(t.text_mute, "sampler idle")
            imgui.same_line(0, 26)
            imgui.begin_group()
            self.sampling = inputs.switch("Sampling", self.sampling)
            imgui.dummy(ImVec2(0, 6))
            self.aeration = inputs.switch("Aeration", self.aeration)
            imgui.end_group()
            imgui.same_line(0, 30)
            imgui.begin_group()
            self.tank = inputs.segmented("tank", TANKS, self.tank, height=32)
            imgui.dummy(ImVec2(0, 8))
            if widgets.button("Log reading", 180, primary=True, icon="check",
                              key="log"):
                self.tray.push("ok", f"{TANKS[self.tank]} logged")
            imgui.same_line()
            if widgets.button("Flush", 130, icon="refresh", key="flush"):
                self.tray.push("info", "flush cycle queued")
            imgui.end_group()

        imgui.dummy(ImVec2(0, 10))
        half = (avail - 18) * 0.5
        for i, (name, r) in enumerate(self.readings.items()):
            if i % 2:
                imgui.same_line()
            col = t.status(r["kind"])
            with cards.card(name, right=f"{r['v']:.1f} {r['unit']}",
                            right_col=col, edge=col, width=half) as c:
                graphics.gauge(r["v"], r["lo"], r["hi"], radius=38,
                               unit=r["unit"], colour=col,
                               value_fmt=lambda v: f"{v:.1f}")
                imgui.same_line(0, 18)
                imgui.begin_group()
                imgui.text_colored(t.text_mute,
                                   f"range {r['lo']:g} - {r['hi']:g}")
                graphics.sparkline(r["hist"], c.width - 110, 40, colour=col,
                                   tooltip=True,
                                   value_fmt=lambda v, u=r["unit"]: f"{v:.2f} {u}")
                imgui.end_group()
        imgui.new_line()

        imgui.dummy(ImVec2(0, 8))
        notices.note("Readings are smoothed over the last four minutes. "
                     "Pause sampling before moving a probe between tanks.",
                     icon="info")
        self.tray.draw()


def main(argv):
    name = "frutiger-aero"
    if "--profile" in argv:
        name = argv[argv.index("--profile") + 1]
    profile = profiles.get(name)
    print(f"profile {profile.name}: {profile.blurb}")
    app = compose.App(profile=profile, title="habitat",
                      app_id="vertexui-aero", size=(1100, 780))
    app.use(Habitat())
    app.run()


if __name__ == "__main__":
    main(sys.argv[1:])
