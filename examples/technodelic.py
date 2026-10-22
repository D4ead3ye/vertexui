"""YMO Technodelic: a step sequencer, as a piece of 1979 hardware.

    python examples/technodelic.py
    python examples/technodelic.py --profile noir     # the same app, stock

A sequencer is the right domain for this theme because the theme is a
front panel and a sequencer is the one instrument that is almost entirely
front panel: a grid of keys you press, a row of lamps that walks across
them, and meters. There is no document, nothing to scroll and nothing to
read - so the layout is a tab strip over fixed panels, the density is
high, and every value is a block meter rather than a number, because on
hardware you read the shape and not the digits.

The transport is the only thing that moves on its own. Under this profile
the background is printed and still, which is the point: the lamps are
the only lights in the room.

`--profile noir` is the identical code as a flat dark panel. Everything
that makes it an instrument - the lettered captions, the yellow band, the
kanji sub-labels, the wire spinner, the registration marks on hover -
comes from the profile and its skin.
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

STEPS = 16
TRACKS = [("BASS", "ベース"), ("SNARE", "スネア"),
          ("RIM", "リム"), ("CYMBAL", "シンバル")]
PATTERNS = ["TONG POO", "RYDEEN", "FIRECRACKER", "TECHNOPOLIS",
            "COSMIC SURFIN", "SIMOON", "BEHIND THE MASK", "CASTALIA"]


def _pal(key, fallback):
    """A theme colour where the skin has one, the palette's where it has
    not - so this file renders under `--profile noir` as well."""
    return skins.extra(key, fallback)


class Sequencer(compose.Module):
    name = "sequencer"

    def __init__(self):
        self.rng = random.Random(1978)
        self.grid = [[self.rng.random() < 0.3 for _ in range(STEPS)]
                     for _ in TRACKS]
        self.grid[0][0] = self.grid[0][8] = True
        self.running = True
        self.step = 0
        self.tempo = 116
        self.pattern = 1
        self.swing = 0.18
        self.levels = [0.62, 0.48, 0.3, 0.74]
        self.peaks = list(self.levels)
        self.history = [[0.0] * 48 for _ in TRACKS]
        self.cols = [table.Col("bank", "BANK", 70),
                     table.Col("name", "NAME"),
                     table.Col("steps", "STEPS", 80, align="r")]
        self.state = table.State(sort="")
        self.log = logview.LogView(speed="quick")
        self.msgs = notices.Tray(corner="tr", width=290)
        self._next = 0.0
        self.log.add("clock source internal", kind="info", tag="sync")

    # -- the running clock ---------------------------------------------
    def setup(self, app):
        app.page("sequence", "SEQUENCE", icon="grid", draw=self.sequence)
        app.page("voices", "VOICES", icon="sliders", draw=self.voices)
        app.page("memory", "MEMORY", icon="cube", draw=self.memory)
        app.slot("status", self.status)
        app.hook("frame_begin", self.tick)

    def tick(self, app):
        now = time.time()
        beat = 60.0 / max(40, self.tempo) / 4.0
        if not self.running or now < self._next:
            for i in range(len(self.peaks)):
                self.peaks[i] = max(self.levels[i], self.peaks[i] - 0.004)
            return
        self._next = now + beat
        vui.anim.mark_busy()
        self.step = (self.step + 1) % STEPS
        for i, on in enumerate(row[self.step] for row in self.grid):
            if on:
                self.levels[i] = min(1.0, 0.55 + self.rng.random() * 0.45)
                self.peaks[i] = max(self.peaks[i], self.levels[i])
                app.bus.emit("hit", track=i, step=self.step)
            else:
                self.levels[i] *= 0.62
        for i, h in enumerate(self.history):
            h.pop(0)
            h.append(self.levels[i])
        if self.step == 0:
            self.log.add(f"bar complete  {PATTERNS[self.pattern]}",
                         kind="ok", tag="seq")

    def status(self, app):
        t = theme_mod.current()
        widgets.badge("RUN" if self.running else "STOP",
                      "ok" if self.running else "warn")
        imgui.same_line(0, 12)
        with fonts.use("mono"):
            imgui.text_colored(t.text_dim,
                               f"{self.tempo} BPM  /  STEP {self.step + 1:02d}")

    # -- the grid ------------------------------------------------------
    def _steps(self, app, width):
        """The key matrix. Drawn here rather than in the toolkit: a step
        grid is this instrument's one idea, and a widget general enough
        for every sequencer would be a worse grid for this one."""
        t = theme_mod.current()
        dl = imgui.get_window_draw_list()
        lit = _pal("sleeve", t.accent)
        hot = _pal("vermilion", t.danger)
        ink = _pal("ink", theme_mod.sink(t.bg, 0.5, t))
        gap = 4.0
        legend = 86.0
        # a key is a key: it does not grow to fill the card, because a
        # 60px step button is a tile and you stop reading it as a matrix
        cell = max(16.0, min(38.0, (width - legend - gap * (STEPS - 1))
                             / STEPS))
        o = imgui.get_cursor_screen_pos()
        with fonts.use("label"):
            for c in range(STEPS):
                mark = c % 4 == 0
                imgui.set_cursor_screen_pos(
                    ImVec2(o.x + legend + c * (cell + gap) + 3, o.y))
                imgui.text_colored(t.text_dim if mark else t.text_mute,
                                   f"{c + 1:02d}" if mark else "·")
        imgui.set_cursor_screen_pos(ImVec2(o.x, o.y + 18))
        for r, (name, kana) in enumerate(TRACKS):
            o = imgui.get_cursor_screen_pos()
            with fonts.use("label"):
                imgui.text_colored(t.text_dim, name)
            if fonts.has("cjk"):
                imgui.same_line(0, 6)
                with fonts.use("cjk"):
                    imgui.text_colored(t.text_mute, kana)
            imgui.set_cursor_screen_pos(ImVec2(o.x + legend, o.y))
            for c in range(STEPS):
                x = o.x + legend + c * (cell + gap)
                imgui.set_cursor_screen_pos(ImVec2(x, o.y))
                imgui.invisible_button(f"##k{r}{c}", ImVec2(cell, cell))
                if imgui.is_item_clicked():
                    self.grid[r][c] = not self.grid[r][c]
                    vui.sound.play("click")
                hov = imgui.is_item_hovered()
                widgets.hover_tick(f"k{r}{c}", hov)
                on = self.grid[r][c]
                here = self.running and c == self.step
                # every fourth key is a downbeat and sits a shade lighter,
                # which is how you find your place without counting
                ground = theme_mod.lerp(t.surface, t.text,
                                        0.10 if c % 4 == 0 else 0.03)
                col = hot if (on and here) else (lit if on else ground)
                a = 1.0 if on else (0.55 if hov else 0.4)
                dl.add_rect_filled(ImVec2(x, o.y), ImVec2(x + cell, o.y + cell),
                                   theme_mod.u32(col, a),
                                   skins.corner(t.rounding, t))
                dl.add_rect(ImVec2(x, o.y), ImVec2(x + cell, o.y + cell),
                            theme_mod.u32(ink, 0.8),
                            skins.corner(t.rounding, t), 1.0)
                if here:
                    dl.add_rect(ImVec2(x - 2, o.y - 2),
                                ImVec2(x + cell + 2, o.y + cell + 2),
                                theme_mod.u32(hot, 0.9),
                                skins.corner(t.rounding, t), 1.0)
            # the accent level for this track, where a drum machine puts it
            imgui.set_cursor_screen_pos(
                ImVec2(o.x + legend + STEPS * (cell + gap) + 14,
                       o.y + (cell - 12) * 0.5))
            graphics.segments(self.levels[r], count=12, block=5.0, gap=2.0,
                              height=12.0, hot=0.8, peak=self.peaks[r])
            imgui.set_cursor_screen_pos(ImVec2(o.x, o.y + cell + gap))
        imgui.dummy(ImVec2(width, 2))

    # -- pages ---------------------------------------------------------
    def sequence(self, app):
        t = theme_mod.current()
        avail = imgui.get_content_region_avail().x
        with cards.card("Pattern", right=PATTERNS[self.pattern],
                        dot=t.ok if self.running else t.warn) as c:
            self._steps(app, c.width)
        imgui.dummy(ImVec2(0, 8))

        side = 320.0
        with cards.card("Transport", width=avail - side - 18) as c:
            if widgets.button("RUN" if not self.running else "STOP", 130,
                              primary=not self.running, key="run"):
                self.running = not self.running
                self.msgs.push("ok" if self.running else "warn",
                               "clock running" if self.running
                               else "clock halted")
            imgui.same_line()
            if widgets.button("CLEAR", 120, key="clr"):
                self.grid = [[False] * STEPS for _ in TRACKS]
                self.log.add("matrix cleared", kind="warn", tag="seq")
            imgui.same_line()
            if widgets.button("SEED", 120, key="seed"):
                self.grid = [[self.rng.random() < 0.32 for _ in range(STEPS)]
                             for _ in TRACKS]
                self.log.add("matrix seeded", kind="info", tag="seq")
            imgui.dummy(ImVec2(0, 10))
            inputs.field_label("Tempo", "steps of one")
            self.tempo = inputs.stepper("bpm", self.tempo, lo=40, hi=200,
                                        step=2)
            imgui.dummy(ImVec2(0, 6))
            self.swing = widgets.slider("Swing", self.swing, 0.0, 0.5,
                                        fmt="%.2f")
        imgui.same_line()
        with cards.card("Output", right="48k", width=side) as c:
            if self.running:
                widgets.spinner(82, key="clk", label="CLOCK", speed=1.0
                                + self.tempo / 180.0)
            else:
                imgui.dummy(ImVec2(0, 92))
                imgui.text_colored(t.text_mute, "clock halted")
            imgui.dummy(ImVec2(0, 8))
            for i, (name, _k) in enumerate(TRACKS[:2]):
                graphics.segments(self.levels[i], count=18, hot=0.8,
                                  peak=self.peaks[i], label=name[0])
        self.msgs.draw()

    def voices(self, app):
        t = theme_mod.current()
        avail = imgui.get_content_region_avail().x
        strip = (avail - 18 * (len(TRACKS) - 1)) / len(TRACKS)
        for i, (name, kana) in enumerate(TRACKS):
            with cards.card(name.title(), width=strip,
                            edge=t.status("ok" if self.levels[i] > 0.1
                                          else "info")) as c:
                graphics.segments(self.levels[i], count=20, vertical=True,
                                  height=104, width=14, hot=0.78,
                                  peak=self.peaks[i])
                imgui.same_line(0, 12)
                wave = [math.sin(x * 0.4 + i) * (0.3 + self.levels[i])
                        for x in range(48)]
                graphics.waveform(wave, c.width - 40, 104,
                                  colour=t.text_dim)
                imgui.dummy(ImVec2(0, 8))
                self.levels[i] = widgets.slider(
                    "Level", self.levels[i], 0.0, 1.0, fmt="%.2f",
                    key=f"lv{i}", width=c.width - 92)
            if i < len(TRACKS) - 1:
                imgui.same_line()
        imgui.dummy(ImVec2(0, 8))
        with cards.card("Signal") as c:
            graphics.plot({nm.lower(): self.history[i]
                           for i, (nm, _k) in enumerate(TRACKS)},
                          c.width, 140, lo=0.0, hi=1.0, tooltip=True)
        self.msgs.draw()

    def memory(self, app):
        t = theme_mod.current()
        # full width, not two columns: `table.row_begin` tints a row out to
        # the window edge - there is no content-region accessor in this
        # binding - so a table in a half-width card paints over its neighbour
        with cards.card("Memory", right=f"{len(PATTERNS)} BANKS") as c:
            banks = [{"bank": f"{i + 1:02d}", "name": n,
                      "steps": (sum(sum(r) for r in self.grid)
                                if i == self.pattern else (i * 7) % 24 + 4)}
                     for i, n in enumerate(PATTERNS)]
            with table.table("banks", self.cols, height=236) as open_:
                if open_:
                    table.header(self.cols, self.state)
                    for i, r in table.rows(banks, self.state):
                        _h, clicked = table.row_begin(r["bank"],
                                                      i == self.pattern)
                        table.cell(r["bank"], role="mono", column=0)
                        table.cell(r["name"], column=1)
                        table.cell(str(r["steps"]), align="r", role="mono",
                                   column=2)
                        if clicked and i != self.pattern:
                            self.pattern = i
                            self.log.add(f"recalled {r['name']}", kind="ok",
                                         tag="mem")
        imgui.dummy(ImVec2(0, 8))
        with cards.card("Log", right="LIVE", edge=t.info) as c:
            # sized rather than greedy: this theme prints its credit line
            # along the foot of the window and a card that runs to the
            # floor covers it
            self.log.draw(ImVec2(0, 232))
        self.msgs.draw()


def main(argv):
    name = "ymo-technodelic"
    if "--profile" in argv:
        name = argv[argv.index("--profile") + 1]
    profile = profiles.get(name)
    print(f"profile {profile.name}: {profile.blurb}")
    app = compose.App(profile=profile, title="technodelic",
                      app_id="vertexui-ymo", size=(1120, 740))
    app.use(Sequencer())
    if "--page" in argv:
        app.setup()
        app.go(argv[argv.index("--page") + 1])
    app.run()


if __name__ == "__main__":
    main(sys.argv[1:])
