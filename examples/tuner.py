"""Minimal: an instrument tuner, on the MINIMAL profile.

    python examples/tuner.py

The sparse end of the range, and the same toolkit as `profiler.py`. No
navigation, no cards with headers, no borders, 14px corners, type a third
larger, motion at 0.65 so nothing snaps. One centred column, and the only
thing on it is the answer.

What makes this hard is not drawing less. It is that a toolkit which
assumes a tab strip and a title bar cannot *get* here - which is why
layout is a profile's business and not a widget's.
"""

import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from imgui_bundle import ImVec2, imgui                   # noqa: E402

import vertexui as vui                                   # noqa: E402
from vertexui import compose, fonts, graphics, profiles  # noqa: E402
from vertexui import theme as theme_mod                  # noqa: E402

NOTES = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]


class Tuner(compose.Module):
    name = "tuner"

    def __init__(self):
        self.rng = np.random.default_rng(11)
        self.cents = 0.0
        self.note = "A"
        self.hz = 440.0
        self.wave = np.zeros(900)
        self.level = np.zeros(2)
        self._t = 0.0

    def setup(self, app):
        app.page("tune", draw=self.draw)
        app.slot("status", self.status)
        app.hook("frame_begin", self.tick)

    def tick(self, app):
        dt = min(0.05, imgui.get_io().delta_time)
        self._t += dt
        # drift toward in-tune, then wander off again
        target = 14.0 * math.sin(self._t * 0.35) + self.rng.normal(0, 1.1)
        self.cents += (target - self.cents) * min(1.0, dt * 3.0)
        self.note = NOTES[int(self._t * 0.22) % len(NOTES)]
        self.hz = 440.0 * (2 ** (self.cents / 1200.0))
        n = self.wave.size
        phase = np.linspace(0, 42 * math.pi, n) + self._t * 7.0
        env = 0.55 + 0.45 * math.sin(self._t * 1.3)
        self.wave = (np.sin(phase) + 0.35 * np.sin(phase * 2.01)) * env
        self.level = np.clip(np.array([env, env * 0.82]) +
                             self.rng.normal(0, 0.03, 2), 0, 1)
        vui.anim.mark_busy()

    def status(self, app):
        t = theme_mod.current()
        with fonts.use("label"):
            imgui.text_colored(t.text_mute, "LISTENING")

    def draw(self, app):
        t = theme_mod.current()
        w = imgui.get_content_region_avail().x
        near = abs(self.cents) < 4.0
        col = t.ok if near else (t.warn if abs(self.cents) < 18 else t.danger)

        # the note, enormous, and nothing competing with it
        with fonts.use("huge"):
            size = imgui.calc_text_size(self.note)
            imgui.dummy(ImVec2(max(0.0, (w - size.x) * 0.5), 0))
            imgui.same_line()
            imgui.text_colored(t.text, self.note)

        # how far off, as a position rather than as a number
        dl = imgui.get_window_draw_list()
        o = imgui.get_cursor_screen_pos()
        mid = o.x + w * 0.5
        dl.add_rect_filled(ImVec2(o.x, o.y + 16), ImVec2(o.x + w, o.y + 17),
                           imgui.get_color_u32(
                               theme_mod.with_alpha(t.border, 0.8)))
        for k in (-1, -0.5, 0, 0.5, 1):
            x = mid + k * w * 0.46
            h = 9 if k == 0 else 5
            dl.add_rect_filled(ImVec2(x - 1, o.y + 16 - h),
                               ImVec2(x + 1, o.y + 17 + h),
                               imgui.get_color_u32(
                                   theme_mod.with_alpha(t.text_mute,
                                                        1.0 if k == 0 else 0.5)))
        x = mid + max(-1.0, min(1.0, self.cents / 50.0)) * w * 0.46
        eased = vui.anim.to("tuner:needle", x, 9.0)
        dl.add_circle_filled(ImVec2(eased, o.y + 16.5), 13.0,
                             imgui.get_color_u32(
                                 theme_mod.with_alpha(col, 0.18)))
        dl.add_circle_filled(ImVec2(eased, o.y + 16.5), 6.0,
                             imgui.get_color_u32(col))
        imgui.dummy(ImVec2(w, 38))

        with fonts.use("big"):
            txt = f"{self.cents:+.1f}"
            size = imgui.calc_text_size(txt)
            imgui.dummy(ImVec2(max(0.0, (w - size.x) * 0.5), 0))
            imgui.same_line()
            imgui.text_colored(col, txt)
        with fonts.use("label"):
            txt = f"{self.hz:.1f} HZ      CENTS"
            size = imgui.calc_text_size(txt)
            imgui.dummy(ImVec2(max(0.0, (w - size.x) * 0.5), 0))
            imgui.same_line()
            imgui.text_colored(t.text_mute, txt)

        imgui.dummy(ImVec2(0, 22))
        graphics.waveform(self.wave, w, 64,
                          colour=theme_mod.lerp(col, t.text, 0.25))
        imgui.dummy(ImVec2(0, 10))
        imgui.dummy(ImVec2(max(0.0, w * 0.5 - 30), 0))
        imgui.same_line()
        graphics.levels(self.level, 58, 40)


def main():
    app = compose.App(profile=profiles.MINIMAL, title="tuner",
                      app_id="vertexui-tuner", size=(760, 620))
    app.use(Tuner())
    app.run()


if __name__ == "__main__":
    main()
