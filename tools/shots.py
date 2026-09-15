"""Regenerate the screenshots in docs/.

    python tools/shots.py

Drives the demo, sets each screen up in turn and reads the framebuffer
back, so every image in the README comes from the code in this repo rather
than from something assembled by hand that can drift away from it.

Doubles as the only test the shader backdrop gets: a scene that fails to
compile leaves `Backdrop.error` set and renders nothing, which this reports
rather than quietly saving a black image.
"""

import ctypes
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from imgui_bundle import hello_imgui, imgui               # noqa: E402

import vertexui as vui                                    # noqa: E402
from vertexui import cards, effects                       # noqa: E402
from vertexui.demo import Demo                            # noqa: E402

DOCS = ROOT / "docs"
GL = ctypes.windll.opengl32
SETTLE = 45          # frames to let animation and easing arrive


def shots(app, bare):
    """(filename, setup) in capture order. Setup runs once, SETTLE frames
    before the grab."""
    def tab(i, **kw):
        def go():
            bare[0] = False
            app.tab = i
            for k, v in kw.items():
                setattr(app, k, v)
        return go

    def hero():
        bare[0] = False
        app.tab = 1
        app.running = True
        app.bg.set("flow")
        app.bg.intensity = 0.55
        app.fx.set("constellation")
        app.fx.intensity = 1.2

    out = [
        ("hero.png", hero),
        ("controls.png", tab(0, running=True)),
        ("cards.png", tab(1)),
        ("icons.png", tab(3)),
        ("log.png", tab(5, running=True)),
        ("settings.png", tab(6)),
    ]
    for scene in SCENE_TILES:
        def go(s=scene):
            bare[0] = True
            app.bg.set(s)
            app.bg.intensity = 1.0
            app.fx.set("none")
        out.append((f"scene_{scene}.png", go))
    for fx in FX_TILES:
        def go(f=fx):
            bare[0] = True
            app.bg.set("none")
            app.fx.set(f)
            app.fx.intensity = 1.6
        out.append((f"fx_{fx}.png", go))
    return out


SCENE_TILES = ("aurora", "flow", "nebula", "grid")
FX_TILES = ("constellation", "embers", "sakura", "starfield")


def montage(names, prefix, out_name, cols=2, band=(180, 520),
            xband=None, scale=0.5):
    """Tile a band out of each shot, labelled.

    These shots are captured with the interface hidden, so any band is
    unobstructed; the middle is where the scenes put their structure - the
    aurora curtains and the grid horizon both sit around the centre line.
    """
    tiles = []
    for n in names:
        im = cv2.imread(str(DOCS / f"{prefix}{n}.png"))
        if im is None:
            return False
        x0, x1 = xband if xband else (0, im.shape[1])
        tile = im[band[0]:band[1], x0:x1].copy()
        cv2.rectangle(tile, (0, 0), (tile.shape[1] - 1, tile.shape[0] - 1),
                      (40, 40, 46), 1)
        cv2.putText(tile, n, (16, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.62,
                    (18, 18, 20), 4, cv2.LINE_AA)
        cv2.putText(tile, n, (16, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.62,
                    (236, 236, 240), 1, cv2.LINE_AA)
        tiles.append(tile)
    rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
    grid = np.vstack(rows)
    if scale != 1.0:
        grid = cv2.resize(grid, (int(grid.shape[1] * scale),
                                 int(grid.shape[0] * scale)),
                          interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(DOCS / out_name), grid)
    return True


def main():
    DOCS.mkdir(exist_ok=True)
    app = Demo()
    app.tray = None
    app.st.card_style = "raised"
    cards.set_style("raised", True)
    bare = [False]
    plan = shots(app, bare)
    st = {"n": 0, "i": 0, "want": None, "saved": []}

    def gui():
        st["n"] += 1
        # one setup, SETTLE frames, one grab, next
        phase = st["n"] - 1
        if phase % SETTLE == 0:
            if st["i"] >= len(plan):
                hello_imgui.get_runner_params().app_shall_exit = True
                return
            name, setup = plan[st["i"]]
            setup()
            st["want"] = name
            st["i"] += 1
        if bare[0]:
            # Backdrop and particles only - these tiles are about the
            # scene, and a screenshot of the scene should not be mostly
            # buttons.
            io_ = imgui.get_io()
            app.bg.draw()
            if app.fx.step(imgui.get_time(), io_.delta_time):
                app.fx.paint(imgui.get_window_draw_list(), 0, 0,
                             io_.display_size.x, io_.display_size.y,
                             imgui.get_time(), 1.0)
            vui.end_frame()
        else:
            app.gui()

    def grab():
        # grab on the last frame of each block, after the content is drawn
        if st["want"] is None or (st["n"] % SETTLE) != SETTLE - 1:
            return
        vp = (ctypes.c_int * 4)()
        GL.glGetIntegerv(0x0BA2, vp)
        w, h = int(vp[2]), int(vp[3])
        buf = (ctypes.c_ubyte * (w * h * 4))()
        GL.glReadPixels(0, 0, w, h, 0x1908, 0x1401, buf)
        img = np.flipud(np.frombuffer(buf, np.uint8).reshape(h, w, 4))
        cv2.imwrite(str(DOCS / st["want"]), cv2.cvtColor(img, cv2.COLOR_RGBA2BGR))
        st["saved"].append(st["want"])
        st["want"] = None

    params = hello_imgui.RunnerParams()
    params.app_window_params.window_title = "vertexui shots"
    params.app_window_params.window_geometry.size = (1040, 700)
    params.imgui_window_params.default_imgui_window_type = (
        hello_imgui.DefaultImGuiWindowType.provide_full_screen_window)
    params.callbacks.show_gui = gui
    params.callbacks.before_swap = grab
    vui.install(params, theme_=app.st.build_theme(), faces=app.st.build_faces())
    hello_imgui.run(params)

    print(f"saved {len(st['saved'])} of {len(plan)}")
    if app.bg.error:
        print("BACKDROP FAILED:", app.bg.error)
        return 1
    # A scene that renders nothing saves a flat image; catch that here
    # rather than noticing it in the README a week later.
    bad = []
    for name in st["saved"]:
        im = cv2.imread(str(DOCS / name))
        if im is None:
            continue
        if name.startswith("scene_"):
            # a scene fills the frame, so flat means it drew nothing
            if float(im.std()) < 4.0:
                bad.append(f"{name} (std {im.std():.1f})")
        elif name.startswith("fx_"):
            # particles are sparse dots on a near-black ground - low
            # variance is correct there, so count lit pixels instead
            lit = int((im.max(axis=2).astype(int) > 26).sum())
            if lit < 400:
                bad.append(f"{name} ({lit} lit pixels)")
    if bad:
        print("FLAT, nothing drawn:", ", ".join(bad))
        return 1

    montage(SCENE_TILES, "scene_", "scenes.png")
    # no downscale for particles: halving the image erases 1px dots
    montage(FX_TILES, "fx_", "effects.png", xband=(260, 780), scale=1.0)
    for n in SCENE_TILES:
        (DOCS / f"scene_{n}.png").unlink(missing_ok=True)
    for n in FX_TILES:
        (DOCS / f"fx_{n}.png").unlink(missing_ok=True)
    print("all scenes rendered; montages written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
