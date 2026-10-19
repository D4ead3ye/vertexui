"""Data-rich: a profiler, on the INSTRUMENT profile.

    python examples/profiler.py

The dense end of the range. Everything on screen is content - one hairline
strip of chrome, 0.82 row density, square corners, no shadows, and type
small enough that a screenful is worth reading. Compare `tuner.py`, which
is the same toolkit asked to show one number.

Pair it with `watchtower.py` to see the other half of the claim: there,
one module set is rendered by two completely different layouts.
"""

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from imgui_bundle import ImVec2, imgui                   # noqa: E402

import vertexui as vui                                   # noqa: E402
from vertexui import compose, fonts, graphics, profiles, widgets  # noqa: E402
from vertexui import theme as theme_mod                  # noqa: E402

HISTORY = 160
CORES = 8


class Sampler(compose.Module):
    """Pure data. Draws nothing, so the layout cannot constrain it."""

    name = "sampler"

    def __init__(self):
        self.rng = np.random.default_rng(3)
        self.cpu = np.zeros((CORES, HISTORY))
        self.mem = np.full(HISTORY, 40.0)
        self.lat = np.full(HISTORY, 12.0)
        self.frames = np.full(240, 16.6)
        self.calls = {}
        self._next = 0.0

    def setup(self, app):
        app.hook("frame_begin", self.tick)

    def tick(self, app):
        now = time.time()
        if now < self._next:
            return
        self._next = now + 0.05
        drift = self.rng.normal(0, 4, CORES)
        self.cpu = np.roll(self.cpu, -1, axis=1)
        self.cpu[:, -1] = np.clip(self.cpu[:, -2] + drift, 2, 100)
        self.mem = np.roll(self.mem, -1)
        self.mem[-1] = np.clip(self.mem[-2] + self.rng.normal(0, 0.8), 10, 95)
        self.lat = np.roll(self.lat, -1)
        self.lat[-1] = max(0.5, self.lat[-2] + self.rng.normal(0, 1.4))
        self.frames = np.roll(self.frames, -1)
        self.frames[-1] = abs(self.rng.normal(16.6, 3.2))
        vui.anim.mark_busy()
        if self.lat[-1] > 24:
            app.bus.emit("slow", float(self.lat[-1]))


class Overview(compose.Module):
    name = "overview"

    def __init__(self, sampler):
        self.s = sampler
        self.alerts = 0

    def setup(self, app):
        app.page("overview", "Overview", icon="bolt", draw=self.draw, order=0)
        app.slot("status", self.status)
        app.bus.on("slow", self.on_slow)

    def on_slow(self, ms):
        self.alerts += 1

    def status(self, app):
        t = theme_mod.current()
        with fonts.use("label"):
            imgui.text_colored(t.text_mute,
                               f"{CORES} CORES   {self.alerts} STALLS")

    def draw(self, app):
        t = theme_mod.current()
        s = self.s
        avail = imgui.get_content_region_avail().x

        # a row of readouts, each with its own history - the right tool for
        # "is this one climbing", where the shared plot below is the right
        # tool for "how do these compare"
        for label, series, unit, colour in (
                ("CPU", s.cpu.mean(axis=0), "%", t.accent),
                ("MEM", s.mem, "%", t.info),
                ("LATENCY", s.lat, "ms", t.warn),
                ("FRAME", s.frames, "ms", t.ok)):
            imgui.begin_group()
            with fonts.use("label"):
                imgui.text_colored(t.text_dim, label)
            with fonts.use("big"):
                imgui.text_colored(t.text, f"{series[-1]:.1f}")
            imgui.same_line(0, 4)
            imgui.text_colored(t.text_mute, unit)
            graphics.sparkline(series[-90:], avail * 0.22, 26, colour=colour)
            imgui.end_group()
            imgui.same_line(0, 18)
        imgui.new_line()

        imgui.dummy(ImVec2(0, 4))
        widgets.section("per-core utilisation")
        graphics.heatmap(s.cpu[:, -64:], cell=9.0, gap=1.0)
        imgui.same_line(0, 22)
        imgui.begin_group()
        with fonts.use("label"):
            imgui.text_colored(t.text_dim, "FRAME TIME DISTRIBUTION")
        graphics.histogram(s.frames, bins=26, width=avail * 0.42, height=78)
        imgui.end_group()

        imgui.dummy(ImVec2(0, 4))
        widgets.section("tracked series")
        graphics.plot({"cpu": s.cpu.mean(axis=0)[-120:], "mem": s.mem[-120:],
                       "latency": s.lat[-120:]},
                      width=avail, height=130, fill=True)


class Threads(compose.Module):
    name = "threads"

    def __init__(self, sampler):
        self.s = sampler

    def setup(self, app):
        app.page("threads", "Threads", icon="gear", draw=self.draw, order=1)

    def draw(self, app):
        t = theme_mod.current()
        avail = imgui.get_content_region_avail().x
        for i in range(CORES):
            series = self.s.cpu[i]
            imgui.begin_group()
            with fonts.use("mono"):
                imgui.text_colored(t.text_dim, f"core {i}")
            imgui.end_group()
            imgui.same_line(0, 14)
            graphics.sparkline(series[-120:], avail * 0.52, 20,
                               colour=t.accent if series[-1] > 70 else t.info)
            imgui.same_line(0, 14)
            with fonts.use("mono"):
                imgui.text_colored(
                    t.danger if series[-1] > 85 else t.text,
                    f"{series[-1]:5.1f}%")
            imgui.same_line(0, 14)
            graphics.pips(10, int(series[-1] / 10), size=6.0, gap=3.0)


def main():
    sampler = Sampler()
    app = compose.App(profile=profiles.INSTRUMENT, title="profiler",
                      app_id="vertexui-profiler", size=(1080, 660))
    app.use(sampler, Overview(sampler), Threads(sampler))
    app.run()


if __name__ == "__main__":
    main()
