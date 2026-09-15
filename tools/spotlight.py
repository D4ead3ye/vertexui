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

Nothing here simulates clicks. State is driven directly and the cursor is
parked on the control that would have caused it, which reads the same and
cannot desynchronise from what the app actually did.
"""

import ctypes
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


def timeline(app):
    """(frames, action) in order. `action(f, n)` runs every frame of its
    block with the frame index within the block."""
    def at(x, y):
        return lambda f, n: ("cursor", (x, y))

    def glide(x0, y0, x1, y1):
        """Move the cursor across a block, so hovers ease in and out."""
        def go(f, n):
            k = f / max(1, n - 1)
            return ("cursor", (x0 + (x1 - x0) * k, y0 + (y1 - y0) * k))
        return go

    def tab(name):
        def go(f, n):
            app.tab = ["controls", "cards", "theme", "icons", "ambience",
                       "log", "settings"].index(name)
            return ("cursor", (TABS_X[name], TAB_Y))
        return go

    def style(i):
        def go(f, n):
            app.st.card_style = cards.STYLES[i]
            cards.set_style(cards.STYLES[i], True)
            return ("cursor", (STYLE_X[i], STYLE_Y))
        return go

    def scene(name, i):
        def go(f, n):
            app.bg.set(name)
            return ("cursor", (SCENE_X[i], SCENE_Y))
        return go

    def check(i, value):
        label = list(app.checks)[i]

        def go(f, n):
            app.checks[label] = value
            return ("cursor", (CHECK_X[i] + 40, CHECK_Y))
        return go

    return [
        # --- the interface, and what moves in it ----------------------
        (12, tab("controls")),
        (34, glide(BTN_X[0], BTN_Y, BTN_X[4], BTN_Y)),
        (9, check(2, True)),
        (9, check(0, False)),
        (9, check(0, True)),
        # --- cards ----------------------------------------------------
        (12, tab("cards")),
        (14, style(0)),
        (14, style(1)),
        (14, style(2)),
        (14, style(3)),
        # --- the shader backdrop --------------------------------------
        (12, tab("ambience")),
        (18, scene("flow", 3)),
        (18, scene("aurora", 1)),
        (18, scene("nebula", 4)),
        (18, scene("grid", 5)),
        # --- and the log glide, over the top --------------------------
        (12, tab("log")),
        (22, lambda f, n: ("cursor", (470, TAB_Y))),
        # --- back to where it started, so the loop lands --------------
        # Long enough for everything to settle, which is longer than the
        # screen wipe alone: the tab indicator is still easing back from
        # Log after the fade has gone, and a tail that ends mid-ease makes
        # the loop pop every time it comes round.
        (6, lambda f, n: (app.bg.set("none"), ("cursor", (300, 300)))[-1]),
        (40, tab("controls")),
    ]


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
    total = sum(n for n, _ in plan)

    st = {"i": 0, "f": 0, "cursor": (300, 300), "frames": []}

    def gui():
        if st["i"] >= len(plan):
            hello_imgui.get_runner_params().app_shall_exit = True
            return
        n, action = plan[st["i"]]
        got = action(st["f"], n)
        if isinstance(got, tuple) and got and got[0] == "cursor":
            st["cursor"] = got[1]
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
