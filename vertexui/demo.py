"""A runnable tour of the toolkit.

    python -m vertexui.demo

Every widget, the icon set, live theming with a colour picker, user
presets, the settings panel and the log glide - so the package can be
checked in isolation before being wired into anything.
"""

import random
import time

from imgui_bundle import ImVec2, ImVec4, hello_imgui, imgui

import vertexui as vui
from vertexui import fonts, icons, logview, settings, sound, theme, widgets

SAMPLES = [
    ("ok", "net", "Connected to 10.0.0.4:8080"),
    ("info", "scan", "Sweeping ports 1000-2000"),
    ("info", "scan", "No response on 1042"),
    ("warn", "net", "Retrying after timeout"),
    ("error", "disk", "Write failed: device busy"),
    (None, "core", "Cache warm, 1284 entries"),
    (None, "core", "Tick 4821 - queue depth 3"),
]


class Demo:
    def __init__(self):
        self.tab = 0
        self.running = False
        self.checks = {"Auto-scroll": True, "Timestamps": True, "Disabled": False}
        self.tray = None
        self.st = settings.Settings.load(app="vertexui-demo")
        self.log = logview.LogView(speed=self.st.log_speed)
        self.st.apply(self.log)
        self._next = 0.0
        for _ in range(30):
            self._emit()

    def _emit(self):
        kind, tag, text = random.choice(SAMPLES)
        self.log.add(text, kind=kind, tag=tag)

    # -- sections -------------------------------------------------------
    def header(self):
        """Laid out with ordinary items and same_line rather than manual
        cursor maths - hand-computed offsets drift the moment a font or a
        label changes, which is exactly how the pill ended up sitting on
        top of the version number."""
        t = theme.current()
        dl = imgui.get_window_draw_list()
        o = imgui.get_cursor_screen_pos()
        avail = imgui.get_content_region_avail().x
        dl.add_rect_filled(ImVec2(o.x, o.y + 4), ImVec2(o.x + 3.5, o.y + 30),
                           imgui.get_color_u32(t.accent), 2.0)
        imgui.dummy(ImVec2(10, 26))
        imgui.same_line()
        with fonts.use("title"):
            imgui.text_colored(t.text, "VERTEXUI")
        imgui.same_line()
        imgui.text_colored(t.text_mute, f"v{vui.__version__}")
        imgui.same_line(0, 16)
        widgets.status_pill(on=self.running)
        widgets.activity_rule(avail, self.running)

    def controls(self):
        if widgets.button("Start", 130, primary=True, icon="play",
                          enabled=not self.running):
            self.running = True
            self.notify("ok", "Started")
        imgui.same_line()
        if widgets.button("Stop", 120, icon="stop", enabled=self.running):
            self.running = False
            self.notify("info", "Stopped")
        imgui.same_line()
        if widgets.button("Warn", 120, icon="warning"):
            self.notify("warn", "Something needs a look")
        imgui.same_line()
        if widgets.button("Error", 120, icon="cross"):
            self.notify("error", "Something went wrong")
        imgui.same_line()
        if widgets.button("Locked", 120, enabled=False):
            pass

        imgui.dummy(ImVec2(0, 6))
        for label in list(self.checks):
            self.checks[label] = widgets.checkbox(label, self.checks[label])
            imgui.same_line()
        imgui.new_line()

        imgui.dummy(ImVec2(0, 6))
        widgets.section("badges")
        for kind, text in (("ok", "healthy"), ("warn", "3 retries"),
                           ("error", "1 failure"), ("info", "idle")):
            widgets.badge(text, kind)
            imgui.same_line()
        imgui.new_line()

        imgui.dummy(ImVec2(0, 6))
        widgets.section("icon buttons")
        for name in ("play", "pause", "stop", "refresh", "search", "gear", "folder"):
            widgets.icon_button(name, tooltip=name)
            imgui.same_line()
        imgui.new_line()

    def theming(self):
        t = theme.current()
        imgui.text_colored(t.text_dim,
                           "Colours are tokens on a Theme. Pick an accent and the "
                           "bright/dim variants derive from it.")
        imgui.dummy(ImVec2(0, 8))
        widgets.section("presets")
        for name in theme.list_presets(self.st.app):
            if widgets.button(name, 0, primary=(name == self.st.theme_name)):
                self.st.theme_name, self.st.accent = name, ""
                self.st.apply(self.log)
                self.notify("info", f"Theme: {name}")
            imgui.same_line()
        imgui.new_line()

        imgui.dummy(ImVec2(0, 8))
        widgets.section("status colours")
        dl = imgui.get_window_draw_list()
        o = imgui.get_cursor_screen_pos()
        for i, kind in enumerate(("ok", "warn", "error", "info")):
            x = o.x + i * 100
            dl.add_rect_filled(ImVec2(x, o.y), ImVec2(x + 92, o.y + 28),
                               imgui.get_color_u32(t.status(kind)), 6.0)
            icons.draw(icons.STATUS_ICONS[kind], dl, x + 16, o.y + 14, 7,
                       imgui.get_color_u32(ImVec4(0.06, 0.06, 0.07, 1)))
            dl.add_text(ImVec2(x + 30, o.y + 6),
                        imgui.get_color_u32(ImVec4(0.06, 0.06, 0.07, 1)), kind)
        imgui.dummy(ImVec2(0, 36))

        widgets.section("underlines")
        imgui.text_colored(t.text_dim, "A rule belongs to the word above it:")
        imgui.dummy(ImVec2(0, 4))
        for word in ("Live", "History", "Diagnostics"):
            widgets.label_underlined(word)
            imgui.same_line(0, 30)
        imgui.new_line()

    def icon_sheet(self):
        t = theme.current()
        imgui.text_colored(t.text_dim,
                           "Drawn from primitives - no icon font to ship, nothing "
                           "to render as a tofu box, crisp at any DPI.")
        imgui.dummy(ImVec2(0, 10))
        dl = imgui.get_window_draw_list()
        o = imgui.get_cursor_screen_pos()
        per_row = 8
        for i, name in enumerate(icons.names()):
            cx = o.x + (i % per_row) * 108 + 30
            cy = o.y + (i // per_row) * 80 + 26
            dl.add_rect_filled(ImVec2(cx - 26, cy - 26), ImVec2(cx + 26, cy + 26),
                               imgui.get_color_u32(t.surface), 8.0)
            icons.draw(name, dl, cx, cy, 13, imgui.get_color_u32(t.accent_bright))
            dl.add_text(ImVec2(cx - 26, cy + 30), imgui.get_color_u32(t.text_mute), name)
        rows = (len(icons.names()) + per_row - 1) // per_row
        imgui.dummy(ImVec2(0, rows * 80))

    def log_tab(self):
        t = theme.current()
        for name in logview.SPEED_ORDER:
            if widgets.button(name, 110, primary=(self.log.speed == name)):
                self.log.speed = self.st.log_speed = name
            imgui.same_line()
        px = logview.SPEEDS[self.log.speed]
        lps = self.log.lines_per_second()
        imgui.text_colored(t.text_mute,
                           "straight to the bottom" if px is None
                           else f"{px:.0f} px/s  ~{lps:.0f} lines a second")
        imgui.dummy(ImVec2(0, 4))
        if widgets.button("burst 40 lines", 180, icon="bolt"):
            for _ in range(40):
                self._emit()
        imgui.same_line()
        if widgets.button("clear", 110, icon="cross"):
            self.log.clear()
        imgui.dummy(ImVec2(0, 6))
        self.log.draw()

    def settings_tab(self):
        settings.panel(self.st, self.log,
                       on_change=lambda s: self.notify("info", "Settings applied"))

    # -- plumbing -------------------------------------------------------
    def notify(self, kind, text):
        if self.tray is not None:
            self.tray.notify(kind, text)

    def gui(self):
        # a trickle of log output, so the glide has something to follow
        if self.running and time.time() > self._next:
            self._next = time.time() + 0.12
            self._emit()
            vui.anim.mark_busy()

        self.header()
        self.tab = widgets.tabs(
            "demo", ["Controls", "Theme", "Icons", "Log", "Settings"], self.tab)
        (self.controls, self.theming, self.icon_sheet,
         self.log_tab, self.settings_tab)[self.tab]()
        vui.end_frame()

    def run(self):
        from vertexui import toasts
        self.tray = toasts.Toasts(seconds=3.5, on_status=print)
        self.tray.start()

        params = hello_imgui.RunnerParams()
        params.app_window_params.window_title = "VertexUI demo"
        params.app_window_params.window_geometry.size = (980, 660)
        params.imgui_window_params.default_imgui_window_type = (
            hello_imgui.DefaultImGuiWindowType.provide_full_screen_window)
        params.callbacks.show_gui = self.gui
        vui.install(params, theme_=self.st.build_theme())
        hello_imgui.run(params)
        self.tray.stop()


if __name__ == "__main__":
    Demo().run()
