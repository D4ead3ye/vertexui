"""A shader backdrop for the whole window.

The particle effects in `effects` are drawn on ImGui's draw list, one call
per particle, which puts a hard ceiling on what they can be: a few hundred
dots and lines. Anything continuous - a gradient that moves, cloud, a
horizon, light that pools - is per-pixel work, and per-pixel work at
1300x880 on the CPU is not a background, it is the whole frame budget.

So this is a fragment shader over a fullscreen triangle, rendered into its
own target and blitted underneath everything else. It costs one draw call,
it takes its colours from the theme, and it renders at half resolution
because every scene here is soft by construction and nothing in them
survives being looked at closely anyway.

    from vertexui import backdrop
    bd = backdrop.Backdrop()
    bd.set("aurora")
    ...
    def gui():
        bd.draw()            # first thing in the frame
        ...

Scenes live in one program behind a branch rather than one program each:
switching is then a uniform, not a recompile, and a settings panel can
flick between them while you watch.

Needs PyOpenGL (`pip install vertexui[backdrop]`) and a GL backend. Without
either, `active` is False and `draw()` is a no-op - the interface renders
exactly as it would have, minus the decoration.
"""

from __future__ import annotations

try:
    from OpenGL import GL
    HAVE_GL = True
except Exception:                                    # pragma: no cover
    GL = None
    HAVE_GL = False


# Order is the order a settings panel shows them in.
SCENES = ("none", "aurora", "plasma", "flow", "nebula", "grid", "warp")
_SCENE_ID = {n: i for i, n in enumerate(SCENES)}

# What each one looks like, for a panel that wants to say so.
BLURBS = {
    "none": "no backdrop",
    "aurora": "four layered curtains, wave-modulated",
    "plasma": "interfering sinusoids, radial term included",
    "flow": "domain-warped noise, three lookups a pixel",
    "nebula": "layered cloud with a sparse star field",
    "grid": "perspective grid receding to a glowing horizon",
    "warp": "radial noise streaks from the centre out",
}

# Half of each axis, so a quarter of the pixels. These scenes have no
# detail finer than the blur that gets us, and it is the difference between
# a backdrop that is free and one that is not.
SUPERSAMPLE = 0.5

VERT = """#version 330 core
out vec2 v_uv;
void main() {
    // One oversized triangle rather than two triangles of a quad: no
    // vertex buffer, no seam down the diagonal.
    vec2 p = vec2(float((gl_VertexID << 1) & 2), float(gl_VertexID & 2));
    v_uv = p;
    gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0);
}
"""

FRAG = """#version 330 core
in vec2 v_uv;
out vec4 frag;

uniform vec2  u_res;
uniform float u_time;
uniform int   u_scene;
uniform vec3  u_accent;
uniform vec3  u_accent2;
uniform vec3  u_bg;
uniform float u_intensity;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
}

float noise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x),
               mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

float fbm(vec2 p) {
    float v = 0.0, a = 0.5;
    for (int i = 0; i < 5; i++) { v += a * noise(p); p *= 2.02; a *= 0.5; }
    return v;
}

void main() {
    vec2 uv = v_uv;
    float t = u_time;
    float aspect = u_res.x / max(u_res.y, 1.0);
    vec3 col = vec3(0.0);

    if (u_scene == 1) {                                   // aurora
        float glow = 0.0;
        for (int i = 0; i < 4; i++) {
            float fi = float(i);
            float w = sin(uv.x * (2.0 + fi * 0.8) + t * (0.25 + fi * 0.11)) * 0.10
                    + sin(uv.x * (5.3 - fi * 0.6) - t * (0.17 + fi * 0.07)) * 0.05;
            float cy = 0.52 + w + fi * 0.06;
            glow += smoothstep(0.26, 0.0, abs(uv.y - cy)) * (0.55 / (1.0 + fi * 0.8));
        }
        glow *= 0.55 + 0.45 * fbm(vec2(uv.x * 3.0, t * 0.2));
        col = mix(u_accent, u_accent2, clamp(uv.y, 0.0, 1.0)) * glow;

    } else if (u_scene == 2) {                            // plasma
        float v = sin(uv.x * 6.0 + t * 0.6)
                + sin(uv.y * 5.0 - t * 0.5)
                + sin((uv.x + uv.y) * 4.0 + t * 0.35)
                + sin(length((uv - 0.5) * vec2(aspect, 1.0)) * 11.0 - t * 0.7);
        v = v * 0.125 + 0.5;
        col = mix(u_accent, u_accent2, v) * (0.12 + 0.55 * v * v);

    } else if (u_scene == 3) {                            // flow
        vec2 p = uv * vec2(aspect, 1.0) * 2.0;
        vec2 q = vec2(fbm(p + t * 0.05), fbm(p + vec2(5.2, 1.3) - t * 0.04));
        float f = fbm(p + 2.5 * q + t * 0.03);
        col = mix(u_accent * 0.55, u_accent2, f) * f * 1.25;

    } else if (u_scene == 4) {                            // nebula
        vec2 p = uv * vec2(aspect, 1.0);
        float f = fbm(p * 3.0 + vec2(t * 0.03, -t * 0.02));
        float g = fbm(p * 6.0 - vec2(t * 0.05, t * 0.01));
        float m = smoothstep(0.32, 0.95, f * 0.7 + g * 0.5);
        col = mix(u_accent * 0.45, u_accent2, g) * m;
        // a sparse field of stars, on the pixel grid so they do not crawl
        float s = hash(floor(v_uv * u_res / 2.6));
        col += vec3(smoothstep(0.9993, 1.0, s)) * (0.5 + 0.5 * sin(t * 2.0 + s * 40.0));

    } else if (u_scene == 5) {                            // grid
        vec2 p = uv - vec2(0.5, 0.60);
        p.x *= aspect;
        if (p.y < -0.002) {
            float z = 0.35 / (-p.y);
            vec2 g = vec2(p.x * z * 1.6, z + t * 0.45);
            vec2 gg = abs(fract(g) - 0.5);
            float line = min(gg.x, gg.y);
            float w = fwidth(line) * 1.6 + 0.004;
            float m = 1.0 - smoothstep(0.0, w, line);
            col = mix(u_accent2, u_accent, clamp(z * 0.06, 0.0, 1.0))
                * m * exp(-z * 0.09);
        }
        col += u_accent2 * smoothstep(0.05, 0.0, abs(p.y)) * 0.30;

    } else if (u_scene == 6) {                            // warp
        vec2 p = (uv - 0.5) * vec2(aspect, 1.0);
        float ang = atan(p.y, p.x), rad = length(p);
        float streak = 0.0;
        for (int i = 0; i < 3; i++) {
            float fi = float(i);
            float n = noise(vec2(ang * (13.0 + fi * 8.0), t * 0.35 + fi * 17.0));
            streak += smoothstep(0.72, 1.0, n);
        }
        col = mix(u_accent, u_accent2, clamp(rad * 1.6, 0.0, 1.0))
            * streak * smoothstep(0.02, 0.55, rad) * 0.55;
    }

    // A vignette on every scene. The content sits in the middle, and the
    // backdrop has no business competing with it for contrast there.
    vec2 d = (uv - 0.5) * vec2(aspect, 1.0);
    col *= 0.35 + 0.65 * smoothstep(0.08, 0.62, length(d));

    frag = vec4(u_bg + col * u_intensity, 1.0);
}
"""


def _compile(src, kind):
    s = GL.glCreateShader(kind)
    GL.glShaderSource(s, src)
    GL.glCompileShader(s)
    if not GL.glGetShaderiv(s, GL.GL_COMPILE_STATUS):
        raise RuntimeError(GL.glGetShaderInfoLog(s).decode())
    return s


class Backdrop:
    """Owns its program and its render target.

    Every method must be called on the render thread - that is the thread
    your gui() callback runs on, so calling `draw()` from there is correct
    and calling it from a worker is not.
    """

    def __init__(self, kind="none", intensity=1.0, speed=1.0):
        self.kind = kind if kind in SCENES else "none"
        self.intensity = float(intensity)
        self.speed = float(speed)
        self.error = ""
        self._prog = None
        self._vao = None
        self._uni = {}
        self._fbo = self._tex = None
        self._w = self._h = 0
        self._dead = False          # one failure and we stop trying

    def set(self, kind):
        self.kind = kind if kind in SCENES else "none"

    @property
    def active(self) -> bool:
        return HAVE_GL and not self._dead and self.kind != "none"

    # -- lifecycle --------------------------------------------------------

    def _ensure_program(self):
        if self._prog is not None:
            return
        prog = GL.glCreateProgram()
        GL.glAttachShader(prog, _compile(VERT, GL.GL_VERTEX_SHADER))
        GL.glAttachShader(prog, _compile(FRAG, GL.GL_FRAGMENT_SHADER))
        GL.glLinkProgram(prog)
        if not GL.glGetProgramiv(prog, GL.GL_LINK_STATUS):
            raise RuntimeError(GL.glGetProgramInfoLog(prog).decode())
        self._prog = prog
        for n in ("u_res", "u_time", "u_scene", "u_accent", "u_accent2",
                  "u_bg", "u_intensity"):
            self._uni[n] = GL.glGetUniformLocation(prog, n)
        # Core profile draws nothing without a bound VAO, even when the
        # vertex shader reads no attributes at all.
        self._vao = GL.glGenVertexArrays(1)

    def _ensure_target(self, w, h):
        if self._fbo is not None and (w, h) == (self._w, self._h):
            return
        self.release()
        self._fbo = GL.glGenFramebuffers(1)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self._fbo)
        self._tex = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._tex)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA8, w, h, 0,
                        GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, None)
        for p in (GL.GL_TEXTURE_MIN_FILTER, GL.GL_TEXTURE_MAG_FILTER):
            GL.glTexParameteri(GL.GL_TEXTURE_2D, p, GL.GL_LINEAR)
        for p in (GL.GL_TEXTURE_WRAP_S, GL.GL_TEXTURE_WRAP_T):
            GL.glTexParameteri(GL.GL_TEXTURE_2D, p, GL.GL_CLAMP_TO_EDGE)
        GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0,
                                  GL.GL_TEXTURE_2D, self._tex, 0)
        ok = GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
        if ok != GL.GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError(f"backdrop framebuffer incomplete ({ok})")
        self._w, self._h = w, h

    def release(self):
        """Drop the GL objects. Safe to call when there are none."""
        if self._tex is not None:
            GL.glDeleteTextures(int(self._tex))
            self._tex = None
        if self._fbo is not None:
            GL.glDeleteFramebuffers(1, [self._fbo])
            self._fbo = None
        self._w = self._h = 0

    # -- drawing ----------------------------------------------------------

    def render(self, w, h, now, accent, accent2, bg):
        """Draw one frame into the target; returns the texture id, or None.

        Colours are (r, g, b) triples in 0..1. Prefer `draw()`, which reads
        them off the theme and blits the result for you.
        """
        if not self.active:
            return None
        prev = None
        try:
            rw = max(8, int(w * SUPERSAMPLE))
            rh = max(8, int(h * SUPERSAMPLE))
            self._ensure_program()
            self._ensure_target(rw, rh)
            # Put back everything we are about to change. Leaving the
            # viewport at half resolution is invisible here - ImGui's
            # backend sets its own before it draws - and breaks the next
            # renderer to share this context, which is exactly the kind of
            # bug that gets blamed on that renderer.
            prev = (GL.glGetIntegerv(GL.GL_FRAMEBUFFER_BINDING),
                    GL.glGetIntegerv(GL.GL_VIEWPORT),
                    GL.glGetIntegerv(GL.GL_CURRENT_PROGRAM),
                    GL.glIsEnabled(GL.GL_DEPTH_TEST),
                    GL.glIsEnabled(GL.GL_BLEND))
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self._fbo)
            GL.glViewport(0, 0, rw, rh)
            GL.glDisable(GL.GL_DEPTH_TEST)
            GL.glDisable(GL.GL_BLEND)
            GL.glUseProgram(self._prog)
            GL.glUniform2f(self._uni["u_res"], float(rw), float(rh))
            GL.glUniform1f(self._uni["u_time"], float(now) * self.speed)
            GL.glUniform1i(self._uni["u_scene"], _SCENE_ID.get(self.kind, 0))
            GL.glUniform3f(self._uni["u_accent"], *accent)
            GL.glUniform3f(self._uni["u_accent2"], *accent2)
            GL.glUniform3f(self._uni["u_bg"], *bg)
            GL.glUniform1f(self._uni["u_intensity"], float(self.intensity))
            GL.glBindVertexArray(self._vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, 3)
            GL.glBindVertexArray(0)
            self._restore(prev)
            return self._tex
        except Exception as exc:                        # pragma: no cover
            # A backdrop is decoration. It does not get to take the app
            # down, and it does not get a second chance either - a shader
            # that fails once will fail every frame, and reporting that
            # sixty times a second helps nobody.
            self.error = str(exc)
            self._dead = True
            try:
                self._restore(prev)
            except Exception:
                pass
            return None

    @staticmethod
    def _restore(prev):
        """Put the context back the way we found it."""
        if prev is None:
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
            return
        fbo, vp, prog, depth, blend = prev
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, int(fbo))
        GL.glViewport(int(vp[0]), int(vp[1]), int(vp[2]), int(vp[3]))
        GL.glUseProgram(int(prog))
        (GL.glEnable if depth else GL.glDisable)(GL.GL_DEPTH_TEST)
        (GL.glEnable if blend else GL.glDisable)(GL.GL_BLEND)

    def draw(self, dl=None, size=None, accent=None, bg=None):
        """Render and blit under the frame. Returns True if it drew.

        Call it first in your gui(), before any content: it paints over the
        window's own fill, and it is opaque by construction - it composites
        the theme background itself rather than blending over it, which
        keeps one guess out of the colour maths.
        """
        if not self.active:
            return False
        from imgui_bundle import ImVec2, imgui

        from . import anim
        from . import theme as theme_mod

        t = theme_mod.current()
        one = accent or t.accent
        two = t.accent_bright
        back = bg or t.bg
        io = imgui.get_io()
        w, h = size or (io.display_size.x, io.display_size.y)
        tex = self.render(int(w), int(h), imgui.get_time(),
                          (one.x, one.y, one.z), (two.x, two.y, two.z),
                          (back.x, back.y, back.z))
        if tex is None:
            return False
        dl = dl if dl is not None else imgui.get_window_draw_list()
        # V flipped: GL's origin is bottom-left and ImGui's is top-left.
        dl.add_image(imgui.ImTextureRef(int(tex)), ImVec2(0, 0), ImVec2(w, h),
                     ImVec2(0, 1), ImVec2(1, 0))
        anim.mark_busy()
        return True
