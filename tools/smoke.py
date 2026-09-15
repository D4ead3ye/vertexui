"""Draw every screen in every state and fail if any frame raises.

    python tools/smoke.py

An immediate-mode UI has no render until something is on screen, so a
wrong argument order or a bad index sits there silently until the one
frame that hits it. That has happened here: `add_rect` in this binding
takes (rounding, thickness, flags) rather than the C++ order, and the
resulting TypeError only fired on the frame where a widget was hovered.

So this sweeps the cursor over a grid, walks every tab, every card style
and every effect, and treats any exception out of a frame as a failure.
It needs a display - it opens a real window - but it closes itself.
"""

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from imgui_bundle import ImVec2, hello_imgui, imgui      # noqa: E402

from vertexui import cards, effects                      # noqa: E402
from vertexui.demo import TABS, Demo                      # noqa: E402

GRID = [(x, y) for y in range(0, 700, 55) for x in range(0, 1040, 80)]


def main():
    app = Demo()
    app.running = True
    app.tray = None                       # no overlay window in a smoke run
    state = {"i": 0, "fails": 0, "frames": 0}
    total = len(GRID) * len(TABS)

    def gui():
        i = state["i"]
        state["i"] += 1
        if i >= total:
            hello_imgui.get_runner_params().app_shall_exit = True
            return

        app.tab = i // len(GRID)
        pos = GRID[i % len(GRID)]
        imgui.get_io().mouse_pos = ImVec2(float(pos[0]), float(pos[1]))
        # Rotate the things that change how a frame is drawn, so no state
        # goes unvisited: card style, particle effect.
        app.st.card_style = cards.STYLES[i % len(cards.STYLES)]
        cards.set_style(app.st.card_style, (i // 2) % 2 == 0)
        app.fx.set(effects.NAMES[(i // 17) % len(effects.NAMES)])

        try:
            app.gui()
            state["frames"] += 1
        except Exception:
            state["fails"] += 1
            print(f"\nframe {i}  tab={TABS[app.tab]}  mouse={pos}  "
                  f"style={app.st.card_style}  fx={app.fx.kind}")
            traceback.print_exc()
            if state["fails"] > 5:
                hello_imgui.get_runner_params().app_shall_exit = True

    params = hello_imgui.RunnerParams()
    params.app_window_params.window_title = "vertexui smoke"
    params.app_window_params.window_geometry.size = (1040, 700)
    params.imgui_window_params.default_imgui_window_type = (
        hello_imgui.DefaultImGuiWindowType.provide_full_screen_window)
    params.callbacks.show_gui = gui
    import vertexui as vui
    vui.install(params, theme_=app.st.build_theme(),
                faces=app.st.build_faces())
    hello_imgui.run(params)

    print(f"\n{state['frames']} frames over {len(TABS)} tabs, "
          f"{state['fails']} failed")
    return 1 if state["fails"] else 0


if __name__ == "__main__":
    sys.exit(main())
