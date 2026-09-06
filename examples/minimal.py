"""The smallest thing that shows the toolkit working.

    python examples/minimal.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from imgui_bundle import hello_imgui, imgui  # noqa: E402

import vertexui as vui  # noqa: E402

state = {"tab": 0, "on": True, "running": False}


def gui():
    vui.widgets.status_pill(on=state["running"])
    state["tab"] = vui.widgets.tabs("main", ["Home", "About"], state["tab"])

    if state["tab"] == 0:
        if vui.widgets.button("Start", 130, primary=True, icon="play",
                              enabled=not state["running"]):
            state["running"] = True
        imgui.same_line()
        state["on"] = vui.widgets.checkbox("Enabled", state["on"])
        imgui.same_line()
        vui.widgets.badge("healthy" if state["on"] else "paused",
                          "ok" if state["on"] else "info")
    else:
        vui.widgets.section("about")
        vui.widgets.label_underlined("VertexUI")

    # Lets the app drop back to idling once nothing is mid-transition.
    vui.end_frame()


params = hello_imgui.RunnerParams()
params.app_window_params.window_title = "VertexUI minimal"
params.app_window_params.window_geometry.size = (620, 380)
params.imgui_window_params.default_imgui_window_type = (
    hello_imgui.DefaultImGuiWindowType.provide_full_screen_window)
params.callbacks.show_gui = gui
vui.install(params, theme_=vui.theme.NOIR_RED)
hello_imgui.run(params)
