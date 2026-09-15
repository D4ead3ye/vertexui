"""A runnable tour of the toolkit.

    python -m vertexui.demo

Every widget, the icon set, the card styles, live theming with a colour
picker, the shader backdrop, the particle effects, the settings panel and
the log glide - so the package can be checked in isolation before being
wired into anything.
"""

import random
import time

from imgui_bundle import ImVec2, ImVec4, hello_imgui, imgui

import vertexui as vui
from vertexui import (backdrop as bgmod, cards, effects, fonts, icons,
                      logview, settings, sound, theme, widgets)

SAMPLES = [
    ("ok", "net", "Connected to 10.0.0.4:8080"),
    ("info", "scan", "Sweeping ports 1000-2000"),
    ("info", "scan", "No response on 1042"),
    ("warn", "net", "Retrying after timeout"),
    ("error", "disk", "Write failed: device busy"),
    (None, "core", "Cache warm, 1284 entries"),
    (None, "core", "Tick 4821 - queue depth 3"),
]

TABS = ["Controls", "Cards", "Theme", "Icons", "Ambience", "Log", "Settings"]


class Demo:
    def __init__(self):
        self.tab = 0
        self.running = False
        self.checks = {"Auto-scroll": True, "Timestamps": True, "Disabled": False}
        self.tray = None
        self.st = settings.Settings.load(app="vertexui-demo")
        self.log = logview.LogView(speed=self.st.log_speed)
        self.fx = effects.Effects()
        self.bg = bgmod.Backdrop()
        self.wipe = widgets.Transition()
        self.st.apply(self.log, backdrop=self.bg, effects=self.fx)
        self._next = 0.0
        self._progress = 0.0
        for _ in range(30):
            self._emit()

    def _emit(self):
        kind, tag, text = random.choice(SAMPLES)
        self.log.add(text, kind=kind, tag=tag)

    # -- sections -------------------------------------------------------
    def header(self):
        """Laid out with ordinary items and same_line rather than manual
        cursor maths - hand-computed offsets drift the moment a font or a
        label changes."""
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

    def card_tab(self):
        t = theme.current()
        imgui.text_colored(t.text_dim,
                           "Cards size themselves to their content - the draw "
                           "list is split so the plate can be drawn behind "
                           "afterwards, with no height passed in.")
        imgui.dummy(ImVec2(0, 8))

        widgets.section("style")
        for name in cards.STYLES:
            if widgets.button(name, 120, primary=(self.st.card_style == name)):
                self.st.card_style = name
                self.st.apply(self.log)
            imgui.same_line()
        shadow = widgets.checkbox("drop shadow", self.st.card_shadow)
        if shadow != self.st.card_shadow:
            self.st.card_shadow = shadow
            self.st.apply(self.log)

        imgui.dummy(ImVec2(0, 10))
        col = (imgui.get_content_region_avail().x - 20) * 0.5

        with cards.card("connection", icon="bolt", right="online",
                        right_col=t.ok, dot=t.ok, width=col, edge=t.ok) as c:
            imgui.text_colored(t.text_dim, "10.0.0.4:8080")
            imgui.dummy(ImVec2(0, 4))
            dl = imgui.get_window_draw_list()
            o = imgui.get_cursor_screen_pos()
            cards.meter(dl, o.x, o.x + c.width, o.y, 0.72, t.ok)
            imgui.dummy(ImVec2(c.width, 10))
            imgui.text_colored(t.text_mute, "72% of the window used")
        imgui.same_line()
        with cards.card("readout", icon="gear", right="live", width=col) as c:
            with fonts.use("huge"):
                imgui.text_colored(t.text, "210")
            imgui.same_line()
            imgui.text_colored(t.text_mute, "degrees")
            imgui.text_colored(t.text_dim,
                               "A display face at size reads as an "
                               "instrument; a body face at size is just "
                               "big body text.")

        imgui.dummy(ImVec2(0, 10))
        with cards.card("no header card", width=0) as c:
            imgui.text_colored(t.text_dim,
                               "A card with no title is just a plate - useful "
                               "when the contents name themselves.")
            imgui.dummy(ImVec2(0, 4))
            for kind, text in (("ok", "healthy"), ("warn", "3 retries")):
                widgets.badge(text, kind)
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
                self.st.apply(self.log, backdrop=self.bg, effects=self.fx)
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

        imgui.dummy(ImVec2(0, 8))
        widgets.section("tracked micro-labels")
        imgui.text_colored(t.text_dim,
                           "ImGui has no letter-spacing, so widgets.caps "
                           "draws these a glyph at a time:")
        dl = imgui.get_window_draw_list()
        o = imgui.get_cursor_screen_pos()
        with fonts.use("label"):
            x = widgets.caps(dl, o.x, o.y + 6, "NOZZLE",
                             imgui.get_color_u32(t.text_dim), 1.5)
            widgets.caps(dl, x + 24, o.y + 6, "BED",
                         imgui.get_color_u32(t.text_mute), 1.5)
        imgui.dummy(ImVec2(0, 26))

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

    def ambience(self):
        t = theme.current()
        widgets.section("backdrop")
        if not bgmod.HAVE_GL:
            imgui.text_colored(t.warn,
                               "PyOpenGL is not installed, so the shader "
                               "backdrop is unavailable here: "
                               "pip install vertexui[backdrop]")
        else:
            for name in bgmod.SCENES:
                if widgets.button(name, 105, primary=(self.bg.kind == name)):
                    self.bg.set(name)
                    self.st.backdrop = name
                imgui.same_line()
            imgui.new_line()
            imgui.text_colored(t.text_mute, bgmod.BLURBS.get(self.bg.kind, ""))
            if self.bg.kind != "none":
                self.bg.intensity = widgets.slider(
                    "brightness", self.bg.intensity, 0.1, 2.0, 200.0,
                    "%.2f", key="demo_bdint")
                imgui.same_line()
                self.bg.speed = widgets.slider(
                    "speed", self.bg.speed, 0.1, 3.0, 200.0, "%.2f",
                    key="demo_bdspeed")
            if self.bg.error:
                imgui.text_colored(t.danger, self.bg.error)

        imgui.dummy(ImVec2(0, 10))
        widgets.section("particles")
        per_row = 6
        for i, name in enumerate(effects.NAMES):
            if widgets.button(name, 125, primary=(self.fx.kind == name)):
                self.fx.set(name)
                self.st.effect = name
            if (i + 1) % per_row:
                imgui.same_line()
        imgui.new_line()
        imgui.text_colored(t.text_mute, effects.BLURBS.get(self.fx.kind, ""))
        if self.fx.kind != "none":
            self.fx.intensity = widgets.slider(
                "intensity", self.fx.intensity, 0.1, 2.0, 200.0, "%.2f",
                key="demo_fxint")
            imgui.same_line()
            self.st.effect_over = widgets.slider(
                "over panels", self.st.effect_over, 0.0, 1.0, 200.0, "%.2f",
                key="demo_fxover")
            imgui.text_colored(t.text_dim,
                               "Behind only, an effect shows in the gaps "
                               "between panels and nowhere else. Painted "
                               "again over the top, it reads as one "
                               "atmosphere rather than as wallpaper.")

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
        settings.panel(self.st, self.log, backdrop=self.bg, effects=self.fx,
                       on_change=lambda s: self.notify("info", "Settings applied"))

    # -- plumbing -------------------------------------------------------
    def notify(self, kind, text):
        if self.tray is not None:
            self.tray.notify(kind, text)

    def on_toast(self, phase, kind, text):
        """Arrival and departure cues, hung off the toast overlay's own
        callback - it runs on the toast thread, so this only queues."""
        sound.play("toast_in" if phase == "in" else "toast_out")

    def gui(self):
        io = imgui.get_io()
        now = imgui.get_time()
        w, h = io.display_size.x, io.display_size.y

        # First: the backdrop paints over the window's own fill, so it has
        # to land before any content.
        self.bg.draw()

        # a trickle of log output, so the glide has something to follow
        if self.running and time.time() > self._next:
            self._next = time.time() + 0.12
            self._emit()
            vui.anim.mark_busy()
            self._progress = (self._progress + 0.004) % 1.0

        widgets.progress_hairline(self._progress if self.running else 0.0)

        moving = self.fx.step(now, io.delta_time)
        if moving:
            self.fx.paint(imgui.get_window_draw_list(), 0, 0, w, h, now, 1.0)

        self.header()
        self.tab = widgets.tabs("demo", TABS, self.tab)
        self.wipe.to(self.tab)
        (self.controls, self.card_tab, self.theming, self.icon_sheet,
         self.ambience, self.log_tab, self.settings_tab)[self.tab]()

        # Second pass, same particles, over the top - on the window's own
        # list after the content, so it sits above everything drawn this
        # frame but still below popups. A modal has to stay readable.
        if moving and self.st.effect_over > 0.004:
            self.fx.paint(imgui.get_window_draw_list(), 0, 0, w, h, now,
                          self.st.effect_over)

        self.wipe.draw()
        vui.end_frame()

    def run(self):
        from vertexui import toasts
        self.tray = toasts.Toasts(seconds=3.5, on_status=print,
                                  on_event=self.on_toast)
        self.tray.start()

        params = hello_imgui.RunnerParams()
        params.app_window_params.window_title = "VertexUI demo"
        params.app_window_params.window_geometry.size = (1040, 700)
        params.imgui_window_params.default_imgui_window_type = (
            hello_imgui.DefaultImGuiWindowType.provide_full_screen_window)
        params.callbacks.show_gui = self.gui
        vui.install(params, theme_=self.st.build_theme(),
                    faces=self.st.build_faces())
        hello_imgui.run(params)
        self.tray.stop()


if __name__ == "__main__":
    Demo().run()
