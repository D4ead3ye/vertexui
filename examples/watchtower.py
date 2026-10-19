"""The same modules, rendered as completely different programs.

    python examples/watchtower.py              # reactive: an icon rail
    python examples/watchtower.py --hud        # overlay: a corner panel
    python examples/watchtower.py --profile paper
    python examples/watchtower.py --profile console

Not one module changes between those. They register pages, slots, hooks
and bus topics; the profile picks a layout; the layout decides whether a
page becomes an icon in a rail, a segment in a hairline strip, or the only
thing on screen because this chrome has no navigation at all.

That is the whole argument for keeping layout out of the modules. A
toolkit where a panel knows it lives under a tab strip can only ever make
one shape of program.
"""

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from imgui_bundle import ImVec2, imgui                   # noqa: E402

import vertexui as vui                                   # noqa: E402
from vertexui import (cards, compose, fonts, graphics, logview, profiles,
                      widgets)                           # noqa: E402
from vertexui import theme as theme_mod                  # noqa: E402

JOBS = ["sync:assets", "build:web", "test:unit", "deploy:edge", "scan:deps"]


class Runner(compose.Module):
    """Behaviour only. Emits on the bus; never imports a listener."""

    name = "runner"

    def __init__(self):
        self.rng = np.random.default_rng(5)
        self.jobs = {n: {"state": "idle", "progress": 0.0, "runs": 0}
                     for n in JOBS}
        self.events = []
        self.started = time.time()
        self.throughput = np.zeros(80)
        self._next = 0.0
        self.seed()

    def seed(self, minutes=12.0):
        """Backdate some history.

        An interface with an empty timeline and a 0% ring is not a picture
        of this program, it is a picture of its first second - which is
        the one second nobody runs it for.
        """
        now = time.time()
        for i, (name, j) in enumerate(self.jobs.items()):
            j["runs"] = int(self.rng.integers(3, 20))
            j["state"] = ["ok", "ok", "running", "ok", "error"][i % 5]
            j["progress"] = float(self.rng.uniform(0.2, 0.8))                 if j["state"] == "running" else 1.0
        for _ in range(44):
            t0 = now - self.rng.uniform(0, minutes * 60)
            kind = self.rng.choice(["ok", "ok", "ok", "info", "error"])
            self.events.append((t0, str(kind),
                                str(self.rng.choice(JOBS))))
        self.events.sort()
        self.throughput = np.clip(
            np.cumsum(self.rng.normal(0, 1, 80)) * 0.6 + 6.0, 0.5, None)

    def setup(self, app):
        app.hook("frame_begin", self.tick)

    def tick(self, app):
        now = time.time()
        if now < self._next:
            return
        self._next = now + 0.08
        vui.anim.mark_busy()
        for name, j in self.jobs.items():
            if j["state"] == "running":
                j["progress"] += self.rng.uniform(0.01, 0.06)
                if j["progress"] >= 1.0:
                    ok = self.rng.random() > 0.22
                    j.update(state="ok" if ok else "error", progress=1.0,
                             runs=j["runs"] + 1)
                    self.events.append((now, "ok" if ok else "error", name))
                    self.throughput = np.roll(self.throughput, -1)
                    self.throughput[-1] = max(
                        0.5, self.throughput[-2] + self.rng.normal(0, 0.7))
                    app.bus.emit("job", name, j["state"])
            elif self.rng.random() < 0.012:
                j.update(state="running", progress=0.0)
                self.events.append((now, "info", name))
                app.bus.emit("job", name, "running")
        self.events = self.events[-120:]

    def counts(self):
        c = {"ok": 0, "error": 0, "running": 0, "idle": 0}
        for j in self.jobs.values():
            c[j["state"]] = c.get(j["state"], 0) + 1
        return c


class Status(compose.Module):
    name = "status"

    def __init__(self, runner):
        self.r = runner

    def setup(self, app):
        app.page("status", "Status", icon="bolt", draw=self.draw, order=0)
        app.slot("status", self.strip)

    def strip(self, app):
        c = self.r.counts()
        widgets.badge(f"{c['ok']} ok", "ok")
        imgui.same_line()
        if c["error"]:
            widgets.badge(f"{c['error']} failed", "error")
            imgui.same_line()
        widgets.badge(f"{c['running']} running", "info")

    def draw(self, app):
        t = theme_mod.current()
        c = self.r.counts()
        done = c["ok"] + c["error"]
        rate = c["ok"] / max(1, done)
        graphics.ring(rate, radius=34, thickness=7,
                      colour=t.ok if rate > 0.7 else t.warn,
                      centre=f"{rate * 100:.0f}%")
        imgui.same_line(0, 18)
        imgui.begin_group()
        with fonts.use("label"):
            imgui.text_colored(t.text_dim, "SUCCESS RATE")
        imgui.text_colored(t.text_mute,
                           f"{done} finished, {c['running']} in flight")
        graphics.pips(len(JOBS), c["ok"], size=8.0)
        imgui.end_group()
        imgui.dummy(ImVec2(0, 10))
        widgets.section("throughput")
        graphics.sparkline(self.r.throughput, 0, 46, colour=t.accent)
        imgui.dummy(ImVec2(0, 8))
        widgets.section("last twelve minutes")
        graphics.timeline(self.r.events[-44:], 0, 42, now=time.time())


class Jobs(compose.Module):
    name = "jobs"

    def __init__(self, runner):
        self.r = runner

    def setup(self, app):
        app.page("jobs", "Jobs", icon="play", draw=self.draw, order=1)
        app.slot("aside", self.aside)

    def draw(self, app):
        t = theme_mod.current()
        for name, j in self.r.jobs.items():
            edge = {"ok": t.ok, "error": t.danger,
                    "running": t.accent}.get(j["state"])
            with cards.card(name, icon="bolt", right=j["state"].upper(),
                            right_col=edge, edge=edge) as c:
                dl = imgui.get_window_draw_list()
                o = imgui.get_cursor_screen_pos()
                cards.meter(dl, o.x, o.x + c.width, o.y,
                            j["progress"] if j["state"] == "running"
                            else (1.0 if j["state"] == "ok" else 0.0),
                            edge or t.text_mute)
                imgui.dummy(ImVec2(c.width, 10))
                imgui.text_colored(t.text_mute, f"{j['runs']} runs")

    def aside(self, app):
        """Only a layout with room for it will ever call this."""
        t = theme_mod.current()
        widgets.section("recent")
        for ts, kind, name in reversed(self.r.events[-14:]):
            imgui.text_colored(t.status(kind), f"{name}")
            imgui.same_line()
            imgui.text_colored(t.text_mute, time.strftime("%H:%M:%S",
                                                          time.localtime(ts)))


class Feed(compose.Module):
    name = "feed"

    def __init__(self):
        self.log = logview.LogView(speed="steady")

    def setup(self, app):
        app.page("feed", "Feed", icon="search", draw=self.draw, order=2)
        app.bus.on("job", self.on_job)
        self.log.add("watchtower started", kind="ok", tag="core")

    def on_job(self, name, state):
        self.log.add(f"{name} -> {state}",
                     kind={"ok": "ok", "error": "error"}.get(state, "info"),
                     tag="job")

    def draw(self, app):
        self.log.draw()


def main(argv):
    name = "reactive"
    if "--hud" in argv:
        name = "overlay"
    if "--profile" in argv:
        name = argv[argv.index("--profile") + 1]
    profile = profiles.get(name)
    print(f"profile {profile.name}: {profile.blurb}")
    print(f"layout  {profile.layout.name}  "
          f"(slots it uses: {', '.join(profile.layout.accepts)})")

    runner = Runner()
    app = compose.App(profile=profile, title="watchtower",
                      app_id="vertexui-watchtower",
                      size=(420, 300) if name == "overlay" else (1000, 640))
    app.use(runner, Status(runner), Jobs(runner), Feed())
    app.run()


if __name__ == "__main__":
    main(sys.argv[1:])
