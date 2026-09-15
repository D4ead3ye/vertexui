"""Record the looping spotlight GIF in docs/.

    python tools/spotlight.py

GitHub autoplays and loops an animated GIF in a README; an mp4 gets a
player with a play button, which is not the same thing. So this drives the
demo through a scripted timeline, reads each frame back off the
framebuffer, and encodes a GIF with Pillow - no ffmpeg needed.

Recording needs a GL context and PyOpenGL; encoding needs Pillow. They are
separate stages so the two can run under different interpreters when one
environment does not have both:

    python tools/spotlight.py --record frames/     # GL + PyOpenGL
    python tools/spotlight.py --encode frames/     # Pillow

Re-encoding without re-recording is the common case anyway, when the only
thing being tuned is the palette or the frame rate.

The cursor is drawn in afterwards. ImGui does not render the OS pointer
into the framebuffer, and without one the hover animations look like
buttons lighting up on their own rather than like someone using the thing.

Nothing here simulates clicks. State is driven directly and the cursor
travels to the control that would have caused it and arrives before it
fires, which reads the same and cannot desynchronise from what the app
actually did. Travel is eased and its duration scales with distance, so
the pointer moves rather than teleports between controls.
"""

import ctypes
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from imgui_bundle import ImVec2, hello_imgui, imgui       # noqa: E402

import vertexui as vui                                    # noqa: E402
from vertexui import cards                                # noqa: E402
from vertexui.demo import Demo                            # noqa: E402

W, H = 1040, 700
# Frames are captured at whatever rate the app runs - about 60fps - so
# playback rate sets how fast the clip reads. 25fps is a touch over twice
# slow motion, which is what makes the easing legible without the whole
# thing feeling sluggish.
FPS = 25
SCALE = 0.62                       # 645x434 - small enough for a README
COLOURS = 96
DITHER = 8.0                       # static ordered dither, see encode()
OUT = ROOT / "docs" / "spotlight.gif"

# Hit points, read off the captured screenshots. They only position a
# drawn cursor, so a few pixels either way costs nothing.
TAB_Y = 81
TABS_X = {"controls": 60, "cards": 144, "theme": 222, "icons": 300,
          "ambience": 389, "log": 470, "settings": 548}
BTN_Y = 123
BTN_X = [81, 216, 346, 476, 606]           # Start Stop Warn Error Locked
CHECK_Y = 176
CHECK_X = [25, 129, 232]
STYLE_Y = 199
STYLE_X = [76, 206, 336, 466]              # raised plated outlined flat
SCENE_Y = 141                              # the scene row on Ambience
SCENE_X = [68, 183, 298, 413, 528, 643, 758]


TABS = ["controls", "cards", "theme", "icons", "ambience", "log", "settings"]

# Where the cursor starts, and where it has to finish for the loop to land.
HOME = (TABS_X["controls"], TAB_Y)


def timeline(app):
    """Blocks of (frames, kind, payload), in order.

    Two kinds, and keeping them separate is the whole point:

        ("move", (x, y))   travel there, eased, touching nothing
        ("do", fn)         fire once on arrival, cursor held still

    A block that both jumped the cursor and changed the state made the
    click land before the pointer got there, which is what made the first
    cut look like the cursor was teleporting between controls.
    """
    def move(x, y, n):
        return (n, "move", (x, y))

    def do(fn, n):
        return (n, "do", fn)

    def tab(name):
        def go():
            app.tab = TABS.index(name)
        return go

    def style(i):
        def go():
            app.st.card_style = cards.STYLES[i]
            cards.set_style(cards.STYLES[i], True)
        return go

    def scene(name):
        return lambda: app.bg.set(name)

    def check(i, value):
        label = list(app.checks)[i]
        return lambda: app.checks.__setitem__(label, value)

    plan = []
    at = [HOME]                      # where the cursor will be, as we build

    def travel(x, y):
        """Frames for a move, from how far it has to go.

        A fixed count per move means a long hop covers ground far faster
        than a short one, and smoothstep peaks at 1.5x its average - which
        on the widest hops put 53 pixels between consecutive frames and
        read as a skip rather than as a movement.
        """
        dist = math.dist(at[0], (x, y))
        return max(7, min(24, int(dist / 18) + 3))

    def visit(x, y, fn, hold):
        plan.append(move(x, y, travel(x, y)))
        plan.append(do(fn, hold))
        at[0] = (x, y)

    # --- the interface, and what moves in it --------------------------
    # a sweep along the button row first, so hover eases in and out
    for i, x in enumerate(BTN_X[:4]):
        visit(x, BTN_Y, lambda: None, 3 if i else 4)
    visit(CHECK_X[2], CHECK_Y, check(2, True), 4)
    visit(CHECK_X[0], CHECK_Y, check(0, False), 3)
    plan.append(do(check(0, True), 5))          # same spot, no travel
    # --- cards --------------------------------------------------------
    visit(TABS_X["cards"], TAB_Y, tab("cards"), 6)
    for i in range(4):
        visit(STYLE_X[i], STYLE_Y, style(i), 6)
    # --- the shader backdrop ------------------------------------------
    # Left to right along the row rather than hopping about it: the same
    # three scenes for two thirds of the travel.
    visit(TABS_X["ambience"], TAB_Y, tab("ambience"), 6)
    for name, i in (("flow", 3), ("nebula", 4), ("grid", 5)):
        visit(SCENE_X[i], SCENE_Y, scene(name), 10)
    # --- and the log glide, over the top ------------------------------
    visit(TABS_X["log"], TAB_Y, tab("log"), 18)
    # --- back to where it started, so the loop lands ------------------
    # The hold has to outlast everything still easing, which is longer
    # than the screen wipe alone: the tab indicator is still travelling
    # back from Log after the fade has gone, and a tail that ends
    # mid-ease makes the loop pop every time it comes round.
    visit(HOME[0], HOME[1],
          lambda: (app.bg.set("none"), tab("controls")())[-1], 40)
    return plan


def draw_cursor(img, x, y):
    """A pointer, drawn in after the fact."""
    x, y = int(x), int(y)
    arrow = np.array([[x, y], [x, y + 17], [x + 5, y + 12], [x + 9, y + 20],
                      [x + 12, y + 18], [x + 8, y + 11], [x + 14, y + 11]],
                     np.int32)
    cv2.fillPoly(img, [arrow], (18, 18, 20), cv2.LINE_AA)
    cv2.polylines(img, [arrow], True, (236, 236, 240), 1, cv2.LINE_AA)
    return img


def encode_dir(folder):
    """Encode the PNGs in `folder`, in name order."""
    files = sorted(Path(folder).glob("f*.png"))
    if not files:
        print(f"no frames in {folder}")
        return None
    return encode([cv2.imread(str(f)) for f in files])


BAYER8 = np.array([[0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
                   [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
                   [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
                   [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21]],
                  np.float32)


def _ordered(h, w, amp):
    """A fixed Bayer pattern, the same on every frame.

    256 colours cannot hold a smooth gradient, and a shader backdrop is
    nothing but gradient - undithered it quantises into visible contour
    rings. Error-diffusion fixes that and triples the file, because the
    noise it scatters is different in every frame and so every frame
    becomes a full-frame change. An ordered pattern that is *identical*
    every frame breaks the banding just as well and leaves the frame deltas
    alone: here it came out smaller than no dithering at 128 colours.
    """
    m = (BAYER8 + 0.5) / 64.0 - 0.5
    return (np.tile(m, (h // 8 + 1, w // 8 + 1))[:h, :w] * amp)[:, :, None]


def encode(frames):
    """One shared palette for the whole clip.

    Quantising each frame on its own gives every frame a slightly different
    palette, and flat areas then shimmer between them - which on a dark
    interface is the most obvious artefact there is.
    """
    from PIL import Image
    small = [cv2.resize(f, (int(W * SCALE), int(H * SCALE)),
                        interpolation=cv2.INTER_AREA) for f in frames]
    if DITHER:
        noise = _ordered(small[0].shape[0], small[0].shape[1], DITHER)
        small = [np.clip(f.astype(np.float32) + noise, 0, 255).astype(np.uint8)
                 for f in small]
    rgb = [Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) for f in small]
    # sample across the clip so the palette covers every scene
    strip = np.vstack([np.asarray(im) for im in rgb[::max(1, len(rgb) // 24)]])
    pal = Image.fromarray(strip).quantize(colors=COLOURS, method=Image.MEDIANCUT)
    quant = [im.quantize(palette=pal, dither=Image.Dither.NONE)
             for im in rgb]
    quant[0].save(OUT, save_all=True, append_images=quant[1:],
                  duration=int(round(1000 / FPS)), loop=0, optimize=True)
    return OUT.stat().st_size


def main(argv):
    if "--encode" in argv:
        size = encode_dir(argv[argv.index("--encode") + 1])
        if size is None:
            return 1
        print(f"{OUT.name}: {size / 1e6:.2f} MB")
        return 0
    dump = None
    if "--record" in argv:
        dump = Path(argv[argv.index("--record") + 1])
        dump.mkdir(parents=True, exist_ok=True)

    app = Demo()
    app.tray = None
    app.running = True
    app.fx.set("constellation")
    app.fx.intensity = 1.1
    app.bg.set("none")
    app.st.effect_over = 0.5
    plan = timeline(app)
    total = sum(n for n, _, _ in plan)

    st = {"i": 0, "f": 0, "cursor": HOME, "from": HOME, "frames": []}

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
            # Smoothstep, so the pointer accelerates away and settles in
            # rather than sliding at a constant rate - which reads as a
            # dragged object rather than as a hand.
            k = st["f"] / max(1, n - 1)
            k = k * k * (3.0 - 2.0 * k)
            x0, y0 = st["from"]
            x1, y1 = payload
            st["cursor"] = (x0 + (x1 - x0) * k, y0 + (y1 - y0) * k)
        imgui.get_io().mouse_pos = ImVec2(float(st["cursor"][0]),
                                          float(st["cursor"][1]))
        app.gui()

    def grab():
        if st["i"] >= len(plan):
            return
        vp = (ctypes.c_int * 4)()
        GL = ctypes.windll.opengl32
        GL.glGetIntegerv(0x0BA2, vp)
        w, h = int(vp[2]), int(vp[3])
        buf = (ctypes.c_ubyte * (w * h * 4))()
        GL.glReadPixels(0, 0, w, h, 0x1908, 0x1401, buf)
        img = np.flipud(np.frombuffer(buf, np.uint8).reshape(h, w, 4))
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR).copy()
        st["frames"].append(draw_cursor(img, *st["cursor"]))

        st["f"] += 1
        if st["f"] >= plan[st["i"]][0]:
            st["i"] += 1
            st["f"] = 0

    params = hello_imgui.RunnerParams()
    params.app_window_params.window_title = "vertexui spotlight"
    params.app_window_params.window_geometry.size = (W, H)
    params.imgui_window_params.default_imgui_window_type = (
        hello_imgui.DefaultImGuiWindowType.provide_full_screen_window)
    params.callbacks.show_gui = gui
    params.callbacks.before_swap = grab
    vui.install(params, theme_=app.st.build_theme(), faces=app.st.build_faces())
    hello_imgui.run(params)

    got = st["frames"]
    print(f"captured {len(got)} of {total} frames")
    if not got:
        return 1
    if dump is not None:
        for i, f in enumerate(got):
            cv2.imwrite(str(dump / f"f{i:04d}.png"), f)
        print(f"wrote {len(got)} frames to {dump}")
        return 0
    size = encode(got)
    print(f"{OUT.name}: {size / 1e6:.2f} MB, {len(got)} frames, "
          f"{len(got) / FPS:.1f}s at {FPS}fps")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
