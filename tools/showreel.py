"""Record the three-theme showreel in docs/.

    python tools/showreel.py --record frames/     # GL + PyOpenGL
    python tools/showreel.py --encode frames/     # Pillow

Recording drives the real mouse for about half a minute, because that is
the only way ImGui reports a control as hovered - see `Pointer`.
`--no-pointer` leaves the mouse alone, at the cost of every control in
the clip staying cold.

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
TITLE = "vertexui showreel"
FPS = 25
OUT = ROOT / "docs" / "showreel.gif"


_U32 = ctypes.windll.user32 if sys.platform == "win32" else None


class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class Pointer:
    """Drives the real OS cursor over the recording window.

    Injecting `io.mouse_pos` inside the frame is not enough to make a
    control light up. ImGui decides which *window* is hovered during
    NewFrame, from the position the platform backend reported - and the
    backend overwrites anything we set, every frame. So nothing is ever
    hovered, the buttons stay cold, and the clip looks like the pointer
    is passing straight through them.

    Moving the actual cursor fixes it at the source: hover, press and
    every skin's hover_aura then behave exactly as they do for a person.
    The cursor is put back where it was when the recording ends.
    """

    def __init__(self, title):
        self.title = title
        self.hwnd = 0
        self.origin = None
        self.restore = None
        self.ok = False

    def _foreground(self):
        """Make our window the foreground one, and keep it there.

        Windows refuses SetForegroundWindow from a process that is not
        already in front, which is why a recording would sometimes come
        out with every control cold: the position was right, the window
        simply was not hovered. Attaching to the current foreground
        thread's input queue first is the documented way round it, and
        it is re-asserted whenever focus wanders.
        """
        hwnd = ctypes.c_void_p(self.hwnd)
        fg = _U32.GetForegroundWindow()
        if fg == self.hwnd:
            return True
        k32 = ctypes.windll.kernel32
        mine = k32.GetCurrentThreadId()
        other = _U32.GetWindowThreadProcessId(ctypes.c_void_p(fg), None)
        if other and other != mine:
            _U32.AttachThreadInput(other, mine, True)
        _U32.BringWindowToTop(hwnd)
        _U32.SetForegroundWindow(hwnd)
        if other and other != mine:
            _U32.AttachThreadInput(other, mine, False)
        return _U32.GetForegroundWindow() == self.hwnd

    def find(self):
        if _U32 is None:
            return None
        if self.origin is None:
            _U32.FindWindowW.restype = ctypes.c_void_p
            _U32.FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
            _U32.GetForegroundWindow.restype = ctypes.c_void_p
            hwnd = _U32.FindWindowW(None, self.title)
            if not hwnd:
                return None
            self.hwnd = hwnd
            p = _POINT(0, 0)
            _U32.ClientToScreen(ctypes.c_void_p(hwnd), ctypes.byref(p))
            if self.restore is None:
                was = _POINT(0, 0)
                _U32.GetCursorPos(ctypes.byref(was))
                self.restore = (was.x, was.y)
            self.origin = (p.x, p.y)
        self.ok = self._foreground()
        return self.origin

    def move(self, x, y):
        o = self.find()
        if o is None:
            return False
        _U32.SetCursorPos(int(o[0] + x), int(o[1] + y))
        return True

    def release(self):
        if _U32 is not None and self.restore is not None:
            _U32.SetCursorPos(*self.restore)


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
    """(frames, kind, payload). `kind` is move / do, as in spotlight.

    Target coordinates are the measured centres of the real controls at
    this window size, not guesses. They drifted once already - the card
    holding each spinner grew when the spinner did, which pushed every
    control below it down by a dozen pixels and left the cursor hovering
    just above three buttons in a row. `on=True` marks a move that is
    supposed to land on something interactive, and the recorder checks it.
    """
    plan = []
    at = [(W * 0.5, H * 0.5)]

    def move(x, y, on=False):
        d = math.dist(at[0], (x, y))
        n = max(7, min(26, int(d / 20) + 4))
        plan.append((n, "move", (x, y), on))
        at[0] = (x, y)
        return on

    def hold(fn, n, check=False):
        plan.append((n, "do", fn, check))

    def visit(x, y, fn, n):
        """Travel onto a control and act once there, checking it landed."""
        move(x, y, on=True)
        hold(fn, n, check=True)

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

    nothing = lambda: None

    # --- aero: habitat ------------------------------------------------
    hold(show(0), 16)
    visit(268, 146, nothing, 14)            # the Sampling switch
    visit(435, 153, nothing, 12)            # the Reef segment
    visit(470, 217, nothing, 14)            # Log reading
    visit(74, 180, lambda: widgets.spin_boost("sampler"), 34)   # the bubble
    move(150, 380)                          # away, over the gauges
    hold(nothing, 16)

    # --- steel ball run ------------------------------------------------
    hold(show(1), 10)
    visit(727, 169, lambda: widgets.spin_boost("race"), 34)     # the ball
    visit(716, 238, nothing, 14)            # the Live switch
    visit(220, 316, nothing, 14)            # the Devil's Palm segment
    visit(650, 319, nothing, 20)            # Flag stage
    move(400, 520)                          # down the standings
    hold(nothing, 12)

    # --- y2k: cyberdeck -------------------------------------------------
    hold(show(2), 10)
    visit(71, 329, lambda: widgets.spin_boost("cd"), 34)        # the disc
    visit(48, 406, nothing, 14)             # the Spin up switch
    visit(78, 457, nothing, 12)             # the GIBSON segment
    visit(648, 357, nothing, 20)            # EXECUTE

    # --- and the same application through every theme, live -----------
    hold(show(0), 12)
    move(560, 300)
    for name in ("noir", "steel-ball-run", "y2k-cyber", "frutiger-aero"):
        hold(theme(name), 26)
    hold(nothing, 20)
    return plan, state


def record(dump, pointer=True):
    apps = build()
    for a in apps:
        a.setup()
    plan, state = timeline(apps)
    total = sum(n for n, _, _, _ in plan)
    st = {"i": 0, "f": 0, "cursor": (W * 0.5, H * 0.5),
          "from": (W * 0.5, H * 0.5), "n": 0, "misses": [], "checks": 0,
          "landed": False}
    pen = Pointer(TITLE) if pointer else None
    dump.mkdir(parents=True, exist_ok=True)

    def gui():
        if st["i"] >= len(plan):
            hello_imgui.get_runner_params().app_shall_exit = True
            return
        n, kind, payload, check = plan[st["i"]]
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
        if check and st["f"] >= n - 4:
            # Over the last few frames of the block, not just the final
            # one: the OS delivers a cursor move asynchronously, so a
            # single frame can still be reading the previous position.
            if imgui.is_any_item_hovered():
                st["landed"] = True
            if st["f"] == n - 1:
                st["checks"] += 1
                if not st["landed"]:
                    mp = imgui.get_io().mouse_pos
                    st["misses"].append(
                        (state["active"], tuple(round(v) for v in st["cursor"]),
                         (round(mp.x), round(mp.y)),
                         imgui.is_window_hovered()))
                st["landed"] = False

    def pre_frame():
        if pen is not None:
            pen.move(*st["cursor"])

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
    params.app_window_params.window_title = TITLE
    params.app_window_params.window_geometry.size = (W, H)
    params.imgui_window_params.default_imgui_window_type = (
        hello_imgui.DefaultImGuiWindowType.provide_full_screen_window)
    params.callbacks.show_gui = gui
    params.callbacks.pre_new_frame = pre_frame
    params.callbacks.before_swap = grab
    # start on the first app's identity; the rest are swapped in live
    vui.install(params, theme_=apps[0].profile.build_theme(),
                faces=apps[0].profile.build_faces())
    hello_imgui.run(params)
    if pen is None:
        print("note: --no-pointer, so hover states only light up where the "
              "real mouse happens to be - controls will mostly look cold")
    else:
        pen.release()
        if not pen.ok:
            print("note: could not drive the real cursor - hover states "
                  "will not light up in this recording")
    print(f"captured {st['n']} of {total} frames into {dump}")
    print(f"cursor landed on a control for {st['checks'] - len(st['misses'])}"
          f" of {st['checks']} targets")
    if st["misses"]:
        for app_i, pos, seen, win in st["misses"]:
            print(f"  MISS  app {app_i} aimed {pos}  imgui saw {seen}  "
                  f"window_hovered={win}")
        return 1
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
    sys.exit(record(Path(d), pointer="--no-pointer" not in sys.argv))
