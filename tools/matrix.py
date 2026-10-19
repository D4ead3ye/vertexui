"""Capture one application under every profile, and tile the result.

    python tools/matrix.py shoot <profile>     # one frame -> docs/_p_<name>.png
    python tools/matrix.py tile                # -> docs/profiles.png

The point of the image it produces is falsifiable: if the seven tiles look
like one program in seven accent colours, the profile system does not work
and the README should not claim it does.

One process per profile, because the font atlas is built once per
hello_imgui run - and typeface is a large part of an identity, so a sweep
that reused one atlas would be quietly comparing less than it appears to.
"""

import ctypes
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "examples"))

from imgui_bundle import hello_imgui                      # noqa: E402

from vertexui import compose, profiles                    # noqa: E402

DOCS = ROOT / "docs"
SETTLE = 55
W, H = 980, 620


def shoot(name):
    from watchtower import Feed, Jobs, Runner, Status

    profile = profiles.get(name)
    runner = Runner()
    app = compose.App(profile=profile, title="watchtower",
                      app_id="vertexui-matrix", size=(W, H))
    app.use(runner, Status(runner), Jobs(runner), Feed())
    app.setup()

    st = {"n": 0}
    out = DOCS / f"_p_{name}.png"

    def gui():
        st["n"] += 1
        # Park on a page the layout can actually show. STAGE and HUD have
        # no navigation, so they render whichever page is current - make
        # that the one worth looking at.
        if st["n"] == 2:
            app.go("jobs" if profile.layout.name in ("stage", "hud") else "status")
        app.frame()
        if st["n"] > SETTLE:
            hello_imgui.get_runner_params().app_shall_exit = True

    def grab():
        if st["n"] != SETTLE:
            return
        GL = ctypes.windll.opengl32
        vp = (ctypes.c_int * 4)()
        GL.glGetIntegerv(0x0BA2, vp)
        w, h = int(vp[2]), int(vp[3])
        buf = (ctypes.c_ubyte * (w * h * 4))()
        GL.glReadPixels(0, 0, w, h, 0x1908, 0x1401, buf)
        img = np.flipud(np.frombuffer(buf, np.uint8).reshape(h, w, 4))
        cv2.imwrite(str(out), cv2.cvtColor(img, cv2.COLOR_RGBA2BGR))

    from vertexui import install
    params = hello_imgui.RunnerParams()
    params.app_window_params.window_title = f"matrix {name}"
    params.app_window_params.window_geometry.size = (W, H)
    params.imgui_window_params.default_imgui_window_type = (
        hello_imgui.DefaultImGuiWindowType.provide_full_screen_window)
    params.callbacks.show_gui = gui
    params.callbacks.before_swap = grab
    install(params, theme_=profile.build_theme(), faces=profile.build_faces())
    hello_imgui.run(params)
    print(f"{name}: {'saved' if out.exists() else 'FAILED'}")
    return 0 if out.exists() else 1


def tile():
    names = profiles.names()
    tiles = []
    for n in names:
        p = DOCS / f"_p_{n}.png"
        im = cv2.imread(str(p))
        if im is None:
            print(f"missing {p.name}")
            return 1
        im = cv2.resize(im, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
        cv2.rectangle(im, (0, 0), (im.shape[1] - 1, im.shape[0] - 1),
                      (46, 46, 52), 1)
        # a strip along the bottom, so the caption never sits on the
        # application's own title
        h = im.shape[0]
        cv2.rectangle(im, (0, h - 26), (im.shape[1], h), (14, 14, 16), -1)
        cv2.line(im, (0, h - 26), (im.shape[1], h - 26), (46, 46, 52), 1)
        cv2.putText(im, f"{n}", (10, h - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (245, 245, 248), 1, cv2.LINE_AA)
        cv2.putText(im, f"{profiles.get(n).layout.name} layout",
                    (10 + 8 * (len(n) + 3), h - 8), cv2.FONT_HERSHEY_SIMPLEX,
                    0.45, (150, 150, 158), 1, cv2.LINE_AA)
        tiles.append(im)
    while len(tiles) % 3:
        tiles.append(np.full_like(tiles[0], 16))
    rows = [np.hstack(tiles[i:i + 3]) for i in range(0, len(tiles), 3)]
    grid = np.vstack(rows)
    cv2.imwrite(str(DOCS / "profiles.png"), grid)
    for n in names:
        (DOCS / f"_p_{n}.png").unlink(missing_ok=True)
    print(f"profiles.png: {grid.shape[1]}x{grid.shape[0]}")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "tile"
    sys.exit(shoot(sys.argv[2]) if cmd == "shoot" else tile())
