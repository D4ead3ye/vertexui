"""Record the three-theme showreel in docs/.

    python tools/showreel.py --record frames/     # GL + PyOpenGL
    python tools/showreel.py --encode frames/     # Pillow

Three themed applications in one continuous take, then one of them
flipping through every theme live - which is possible at all because
`fonts.reload` can swap the typefaces at runtime. Before that, a theme
switch could change colour and shape but not type, so a reel like this
had to be three recordings stitched together.

Shares the encoder with `spotlight.py`, including the static ordered
dither: error diffusion triples a GIF of this length because its noise
differs every frame.
"""

import ctypes
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "examples"))

from imgui_bundle import ImVec2, hello_imgui, imgui       # noqa: E402

import vertexui as vui                                    # noqa: E402
from vertexui import compose, fonts, profiles, widgets    # noqa: E402

import spotlight                                          # noqa: E402

W, H = 1120, 740
FPS = 25
OUT = ROOT / "docs" / "showreel.gif"


def build():
    """One app per theme, each on the example written for it."""
    from cyberdeck import Deck
    from habitat import Habitat
    from steelball import Race

    made = []
    for name, mod, title, app_id in (
            ("frutiger-aero", Habitat, "habitat", "vertexui-aero"),
            ("steel-ball-run", Race, "Steel Ball Run", "vertexui-sbr"),
            ("y2k-cyber", Deck, "cyberdeck", "vertexui-y2k")):
        app = compose.App(profile=profiles.get(name), title=title,
                          app_id=app_id, size=(W, H))
        app.use(mod())
        made.append(app)
    return made


def timeline(apps):
    """(frames, kind, payload). `kind` is move / do, as in spotlight."""
    plan = []
    at = [(W * 0.5, H * 0.5)]

    def move(x, y):
        d = math.dist(at[0], (x, y))
        n = max(7, min(26, int(d / 20) + 4))
        plan.append((n, "move", (x, y)))
        at[0] = (x, y)

    def hold(fn, n):
        plan.append((n, "do", fn))

    def show(i):
        def go():
            apps[i].profile.apply(apps[i].app_id)
            state["active"] = i
        return go

    state = {"active": 0}

    def theme(name):
        def go():
            a = apps[state["active"]]
            a.profile = profiles.get(name)
            a.profile.apply(a.app_id)
        return go

    # --- aero ---------------------------------------------------------
    hold(show(0), 16)
    move(250, 150)                      # the sampling switch
    hold(lambda: None, 12)
    move(430, 160)                      # the tank segmented control
    hold(lambda: None, 10)
    move(470, 225)                      # log reading
    hold(lambda: None, 10)
    move(118, 150)                      # onto the bubble
    hold(lambda: widgets.spin_boost("sampler"), 30)
    move(150, 400)                      # down over the gauges
    hold(lambda: None, 18)

    # --- steel ball run ----------------------------------------------
    hold(show(1), 10)
    move(740, 175)                      # onto the steel ball
    hold(lambda: widgets.spin_boost("race"), 32)
    move(722, 214)                      # the live switch
    hold(lambda: None, 12)
    move(222, 292)                      # the stage segmented control
    hold(lambda: None, 12)
    move(652, 296)                      # flag stage
    hold(lambda: None, 20)
    move(400, 500)                      # across the standings
    hold(lambda: None, 14)

    # --- y2k ----------------------------------------------------------
    hold(show(2), 10)
    move(64, 352)                       # onto the disc
    hold(lambda: widgets.spin_boost("cd"), 32)
    move(60, 395)                       # the spin-up switch
    hold(lambda: None, 12)
    move(240, 430)                      # the node segmented control
    hold(lambda: None, 12)
    move(650, 360)                      # execute
    hold(lambda: None, 20)

    # --- and the same application through every theme, live -----------
    hold(show(0), 12)
    move(560, 300)
    for name in ("noir", "steel-ball-run", "y2k-cyber", "frutiger-aero"):
        hold(theme(name), 26)
    hold(lambda: None, 20)
    return plan, state


def record(dump):
    apps = build()
    for a in apps:
        a.setup()
    plan, state = timeline(apps)
    total = sum(n for n, _, _ in plan)
    st = {"i": 0, "f": 0, "cursor": (W * 0.5, H * 0.5),
          "from": (W * 0.5, H * 0.5), "n": 0}
    dump.mkdir(parents=True, exist_ok=True)

    def gui():
        if st["i"] >= len(plan):
            hello_imgui.get_runner_params().app_shall_exit = True
            return
        n, kind, payload = plan[st["i"]]
        if st["f"] == 0:
            st["from"] = st["cursor"]
            if kind == "do":
                payload()
        if kind == "move":
            k = st["f"] / max(1, n - 1)
            k = k * k * (3.0 - 2.0 * k)
            x0, y0 = st["from"]
            x1, y1 = payload
            st["cursor"] = (x0 + (x1 - x0) * k, y0 + (y1 - y0) * k)
        imgui.get_io().mouse_pos = ImVec2(float(st["cursor"][0]),
                                          float(st["cursor"][1]))
        apps[state["active"]].frame()

    def grab():
        if st["i"] >= len(plan):
            return
        GL = ctypes.windll.opengl32
        vp = (ctypes.c_int * 4)()
        GL.glGetIntegerv(0x0BA2, vp)
        w, h = int(vp[2]), int(vp[3])
        buf = (ctypes.c_ubyte * (w * h * 4))()
        GL.glReadPixels(0, 0, w, h, 0x1908, 0x1401, buf)
        img = np.flipud(np.frombuffer(buf, np.uint8).reshape(h, w, 4))
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR).copy()
        spotlight.draw_cursor(img, *st["cursor"])
        cv2.imwrite(str(dump / f"f{st['n']:04d}.png"), img)
        st["n"] += 1
        st["f"] += 1
        if st["f"] >= plan[st["i"]][0]:
            st["i"] += 1
            st["f"] = 0

    params = hello_imgui.RunnerParams()
    params.app_window_params.window_title = "vertexui showreel"
    params.app_window_params.window_geometry.size = (W, H)
    params.imgui_window_params.default_imgui_window_type = (
        hello_imgui.DefaultImGuiWindowType.provide_full_screen_window)
    params.callbacks.show_gui = gui
    params.callbacks.before_swap = grab
    # start on the first app's identity; the rest are swapped in live
    vui.install(params, theme_=apps[0].profile.build_theme(),
                faces=apps[0].profile.build_faces())
    hello_imgui.run(params)
    print(f"captured {st['n']} of {total} frames into {dump}")
    return 0 if st["n"] else 1


def encode(folder):
    files = sorted(Path(folder).glob("f*.png"))
    if not files:
        print("no frames")
        return 1
    spotlight.W, spotlight.H = W, H
    spotlight.FPS = FPS
    spotlight.OUT = OUT
    # The single-theme spotlight is fine on 96 colours. Three saturated
    # palettes in one clip are not: median-cut spends its budget on
    # whichever theme has the most frames and the other two come out with
    # a cast - the sky went grey-green and the neon cyan vanished. 256 is
    # the format's ceiling and the only honest answer here.
    spotlight.COLOURS = 256
    size = spotlight.encode([cv2.imread(str(f)) for f in files])
    print(f"{OUT.name}: {size / 1e6:.2f} MB, {len(files)} frames, "
          f"{len(files) / FPS:.1f}s")
    return 0


if __name__ == "__main__":
    if "--encode" in sys.argv:
        sys.exit(encode(sys.argv[sys.argv.index("--encode") + 1]))
    d = sys.argv[sys.argv.index("--record") + 1] if "--record" in sys.argv \
        else str(ROOT / "_reel")
    sys.exit(record(Path(d)))
