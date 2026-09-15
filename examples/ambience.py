"""Backdrop, particles and cards in one small app.

    python examples/ambience.py

The whole composition in about forty lines: a shader scene under
everything, particles painted twice so they read as one atmosphere, and
cards that size themselves to their contents.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from imgui_bundle import ImVec2, hello_imgui, imgui      # noqa: E402

import vertexui as vui                                   # noqa: E402
from vertexui import backdrop, cards, effects, fonts, theme, widgets  # noqa: E402

bd = backdrop.Backdrop("nebula", intensity=0.8)
fx = effects.Effects("fireflies")
state = {"progress": 0.34}


def gui():
    io = imgui.get_io()
    now, dt = imgui.get_time(), io.delta_time
    w, h = io.display_size.x, io.display_size.y
    t = theme.current()

    bd.draw()                                   # under everything
    widgets.progress_hairline(state["progress"])

    moving = fx.step(now, dt)
    if moving:                                  # behind the panels
        fx.paint(imgui.get_window_draw_list(), 0, 0, w, h, now, 1.0)

    with fonts.use("title"):
        imgui.text_colored(t.text, "AMBIENCE")
    imgui.dummy(ImVec2(0, 6))

    half = (imgui.get_content_region_avail().x - 20) * 0.5
    with cards.card("scene", icon="bolt", right=bd.kind, width=half):
        for name in backdrop.SCENES[:4]:
            if widgets.button(name, 95, primary=(bd.kind == name)):
                bd.set(name)
            imgui.same_line()
        imgui.new_line()
    imgui.same_line()
    with cards.card("particles", icon="gear", right=fx.kind, width=half) as c:
        for name in effects.NAMES[1:5]:
            if widgets.button(name, 110, primary=(fx.kind == name)):
                fx.set(name)
            imgui.same_line()
        imgui.new_line()
        state["progress"] = widgets.slider("progress", state["progress"],
                                           0.0, 1.0, c.width * 0.6, "%.2f")

    if moving:                                  # and over the top, fainter
        fx.paint(imgui.get_window_draw_list(), 0, 0, w, h, now, 0.42)
    vui.end_frame()


params = hello_imgui.RunnerParams()
params.app_window_params.window_title = "VertexUI ambience"
params.app_window_params.window_geometry.size = (760, 460)
params.imgui_window_params.default_imgui_window_type = (
    hello_imgui.DefaultImGuiWindowType.provide_full_screen_window)
params.callbacks.show_gui = gui
vui.install(params, theme_=theme.NOIR_RED, faces=fonts.build_faces())
hello_imgui.run(params)
