"""A ready-made settings panel, and the object behind it.

Every project ends up writing the same panel: pick a theme, pick an accent,
set the text size, turn the sounds off. This is that panel, plus a Settings
object that knows how to persist itself and how to apply itself to the rest
of the toolkit.

    st = settings.Settings.load(app="myapp")
    st.apply(log, backdrop=bd, effects=fx)
    ...
    settings.panel(st, log, backdrop=bd, effects=fx, extra=my_own_rows)

Nothing here is mandatory. A project that wants its own layout can use the
Settings object alone, or ignore it and drive theme/sound/backdrop directly.
"""

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

from imgui_bundle import ImVec2, imgui

from . import cards, fonts, logview, sound, widgets
from . import theme as theme_mod

ROW_SPACING = {"compact": 0.85, "normal": 1.0, "roomy": 1.25}
ROW_ORDER = ["compact", "normal", "roomy"]


def config_dir(app="vertexui") -> Path:
    base = Path(os.environ.get("APPDATA") or Path.home())
    d = base / app
    d.mkdir(parents=True, exist_ok=True)
    return d


@dataclass
class Settings:
    app: str = "vertexui"

    theme_name: str = "noir-red"
    accent: str = ""            # hex override; empty means the theme's own
    text_scale: float = 1.0
    row_spacing: str = "normal"

    # shape - the three numbers that change how built a panel looks
    rounding: float = 7.0
    rounding_panel: float = 9.0
    border_width: float = 1.0

    # type. Changing a face needs the atlas rebuilt, which happens at
    # startup, so these apply on the next run.
    face_ui: str = "Segoe UI Variable"
    face_display: str = "Bahnschrift"
    face_mono: str = "Cascadia Mono"

    # cards
    card_style: str = "raised"
    card_shadow: bool = True

    # backdrop (needs PyOpenGL; ignored without it)
    backdrop: str = "none"
    backdrop_intensity: float = 1.0
    backdrop_speed: float = 1.0

    # particles
    effect: str = "none"
    effect_intensity: float = 1.0
    effect_over: float = 0.42

    monospaced_log: bool = True
    timestamps: bool = True
    tag_column: bool = True
    log_speed: str = "calm"

    sounds: bool = True
    volume: float = 0.16
    sound_set: str = "soft taps"

    extras: dict = field(default_factory=dict)   # room for project settings

    # -- persistence ----------------------------------------------------
    def path(self) -> Path:
        return config_dir(self.app) / "settings.json"

    def save(self):
        self.path().write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        return self.path()

    @classmethod
    def load(cls, app="vertexui"):
        """Load, falling back to defaults. A settings file that has gone bad
        should cost you your preferences, not your program."""
        p = config_dir(app) / "settings.json"
        base = cls(app=app)
        if not p.exists():
            return base
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return base
        for k, v in (data or {}).items():
            if not hasattr(base, k):
                continue          # a key from a later version, or a typo
            cur = getattr(base, k)
            # JSON has one number type, so a float that happens to be whole
            # comes back as int and a strict isinstance check would silently
            # drop it - which looks exactly like the setting not saving.
            if isinstance(cur, float) and isinstance(v, (int, float)) \
                    and not isinstance(v, bool):
                setattr(base, k, float(v))
            elif isinstance(v, type(cur)):
                setattr(base, k, v)
        return base

    # -- application ----------------------------------------------------
    def build_theme(self) -> "theme_mod.Theme":
        from dataclasses import replace
        t = theme_mod.load_preset(self.theme_name, self.app) or theme_mod.NOIR_RED
        if self.accent:
            t = t.with_accent(theme_mod.rgb(self.accent))
        t = replace(t, rounding=self.rounding,
                    rounding_panel=self.rounding_panel,
                    border_width=self.border_width)
        return t.scaled(text=self.text_scale,
                        rows=ROW_SPACING.get(self.row_spacing, 1.0))

    def build_faces(self) -> dict:
        """Font roles for `install(faces=...)`, honouring the saved choices."""
        return fonts.build_faces(self.face_ui, self.face_display, self.face_mono)

    def apply(self, log: "logview.LogView" = None, backdrop=None, effects=None):
        t = self.build_theme()
        theme_mod.use(t)
        try:
            theme_mod.apply_style(t)
        except Exception:
            pass      # no ImGui context yet - install() will style it later

        cards.set_style(self.card_style, self.card_shadow)

        # Install the configured set - but never over one the application
        # built and installed itself with sound.use(). A project with its
        # own cues calls install() before apply(), and having its choice
        # silently swapped for the toolkit default on the next settings
        # touch would be a maddening bug to chase.
        active = sound.active_set()
        chosen = getattr(active, "set_name", None) if active else None
        if active is None or (chosen is not None and chosen != self.sound_set):
            sound.install(self.sound_set, volume=self.volume,
                          enabled=self.sounds, app=self.app)
        s = sound.current()
        s.enabled = self.sounds
        s.volume = self.volume
        s._cache.clear()          # volume is baked into the rendered wave

        if log is not None:
            log.monospaced = self.monospaced_log
            log.timestamps = self.timestamps
            log.tags = self.tag_column
            log.speed = self.log_speed
            log.row_spacing = ROW_SPACING.get(self.row_spacing, 1.0)
        if backdrop is not None:
            backdrop.set(self.backdrop)
            backdrop.intensity = self.backdrop_intensity
            backdrop.speed = self.backdrop_speed
        if effects is not None:
            effects.set(self.effect)
            effects.intensity = self.effect_intensity
        return t


def _combo(st, label, attr, options, width, key):
    """A combo bound straight to a Settings field. Returns True if changed."""
    cur = getattr(st, attr)
    idx = options.index(cur) if cur in options else 0
    new = widgets.combo(label, options, idx, width, key=key)
    if new != idx:
        setattr(st, attr, options[new])
        return True
    return False


def _slider(st, label, attr, lo, hi, width, fmt, key):
    cur = float(getattr(st, attr))
    new = widgets.slider(label, cur, lo, hi, width, fmt, key=key)
    if abs(new - cur) > 0.001:
        setattr(st, attr, round(new, 3))
        return True
    return False


def _check(st, label, attr):
    cur = bool(getattr(st, attr))
    new = widgets.checkbox(label, cur)
    if new != cur:
        setattr(st, attr, new)
        return True
    return False


def panel(st: Settings, log: "logview.LogView" = None, extra=None,
          on_change=None, width=0.0, backdrop=None, effects=None,
          sections=None):
    """Draw the panel. Returns True if anything changed.

    `sections` limits which groups are shown, in case a project wants them
    spread across its own tabs - pass a subset of SECTIONS. `extra` is
    called at the end for project-specific rows.
    """
    t = theme_mod.current()
    changed = False
    show = set(sections or SECTIONS)

    if "appearance" in show:
        widgets.section("appearance", width)
        names = theme_mod.list_presets(st.app)
        idx = names.index(st.theme_name) if st.theme_name in names else 0
        new_idx = widgets.combo("theme", names, idx, 170.0, key="theme")
        if new_idx != idx:
            st.theme_name, st.accent = names[new_idx], ""
            changed = True
        imgui.same_line()

        base = theme_mod.load_preset(st.theme_name, st.app) or theme_mod.NOIR_RED
        cur = theme_mod.rgb(st.accent) if st.accent else base.accent
        picked = widgets.color_button("accent", cur, key="accent")
        if theme_mod.to_hex(picked) != theme_mod.to_hex(cur):
            st.accent = theme_mod.to_hex(picked)
            changed = True
        if st.accent:
            imgui.same_line()
            if widgets.button("reset accent", 130, height=26.0):
                st.accent = ""
                changed = True

        changed |= _slider(st, "text size", "text_scale", 0.8, 1.6, 180.0,
                           "%.2fx", "textscale")
        changed |= _combo(st, "row spacing", "row_spacing", ROW_ORDER, 140.0,
                          "rowspace")

    if "shape" in show:
        widgets.section("shape", width)
        changed |= _slider(st, "corner radius", "rounding", 0.0, 16.0, 170.0,
                           "%.0f", "round")
        imgui.same_line()
        changed |= _slider(st, "panel radius", "rounding_panel", 0.0, 20.0,
                           170.0, "%.0f", "roundp")
        changed |= _slider(st, "border width", "border_width", 0.0, 3.0, 170.0,
                           "%.1f", "borderw")

    if "cards" in show:
        widgets.section("cards", width)
        changed |= _combo(st, "style", "card_style", list(cards.STYLES), 150.0,
                          "cardstyle")
        imgui.same_line()
        changed |= _check(st, "drop shadow", "card_shadow")
        imgui.same_line()
        imgui.text_colored(t.text_mute, {
            "raised": "gradient, border, lit top edge",
            "plated": "flat fill with an accent rule",
            "outlined": "border only - the backdrop shows through",
            "flat": "fill only, no edges",
        }.get(st.card_style, ""))

    if "type" in show:
        widgets.section("type", width)
        changed |= _combo(st, "interface", "face_ui", list(fonts.UI_FACES),
                          190.0, "faceui")
        imgui.same_line()
        changed |= _combo(st, "readouts", "face_display",
                          list(fonts.DISPLAY_FACES), 190.0, "facedisp")
        changed |= _combo(st, "terminal", "face_mono", list(fonts.MONO_FACES),
                          190.0, "facemono")
        imgui.same_line()
        imgui.text_colored(t.warn, "restart to apply")

    if "backdrop" in show:
        from . import backdrop as backdrop_mod
        widgets.section("backdrop", width)
        if not backdrop_mod.HAVE_GL:
            imgui.text_colored(t.text_mute,
                               "PyOpenGL not installed - pip install "
                               "vertexui[backdrop]")
        else:
            changed |= _combo(st, "scene", "backdrop",
                              list(backdrop_mod.SCENES), 150.0, "bdscene")
            imgui.same_line()
            imgui.text_colored(t.text_mute,
                               backdrop_mod.BLURBS.get(st.backdrop, ""))
            if st.backdrop != "none":
                changed |= _slider(st, "brightness", "backdrop_intensity",
                                   0.1, 2.0, 170.0, "%.2f", "bdint")
                imgui.same_line()
                changed |= _slider(st, "speed", "backdrop_speed", 0.1, 3.0,
                                   170.0, "%.2f", "bdspeed")
            if backdrop is not None and backdrop.error:
                imgui.text_colored(t.danger, "backdrop: " + backdrop.error)

    if "effects" in show:
        from . import effects as effects_mod
        widgets.section("particles", width)
        changed |= _combo(st, "effect", "effect", list(effects_mod.NAMES),
                          150.0, "fxkind")
        imgui.same_line()
        imgui.text_colored(t.text_mute, effects_mod.BLURBS.get(st.effect, ""))
        if st.effect != "none":
            changed |= _slider(st, "intensity", "effect_intensity", 0.1, 2.0,
                               170.0, "%.2f", "fxint")
            imgui.same_line()
            changed |= _slider(st, "over panels", "effect_over", 0.0, 1.0,
                               170.0, "%.2f", "fxover")

    if "log" in show:
        widgets.section("log", width)
        changed |= _combo(st, "scroll", "log_speed", list(logview.SPEED_ORDER),
                          140.0, "logspeed")
        imgui.same_line()
        px = logview.SPEEDS[st.log_speed]
        imgui.text_colored(t.text_mute,
                           "straight to the bottom" if px is None
                           else f"{px:.0f} px/s")
        for label, attr in (("monospaced log", "monospaced_log"),
                            ("timestamps", "timestamps"),
                            ("tag column", "tag_column")):
            changed |= _check(st, label, attr)
            imgui.same_line()
        imgui.new_line()

    if "sound" in show:
        widgets.section("sound", width)
        changed |= _check(st, "interface sounds", "sounds")
        imgui.same_line()
        changed |= _slider(st, "volume", "volume", 0.0, sound.VOL_FULL, 160.0,
                           "%.2f", "vol")
        imgui.same_line()
        if widgets.button("test", 80, height=26.0):
            sound.current()._last = 0.0
            sound.play("ok")
        changed |= _combo(st, "cue set", "sound_set", list(sound.SET_ORDER),
                          150.0, "soundset")
        imgui.same_line()
        imgui.text_colored(t.text_mute, {
            "soft taps": "low tonal knocks - the default",
            "breeze": "filtered noise, no attack to flinch at",
            "crisp": "brighter and shorter",
            "custom .wav": "your own files, per cue",
        }.get(st.sound_set, ""))
        cur = sound.current()
        if isinstance(cur, sound.FileSet):
            have = cur.found()
            n = sum(1 for v in have.values() if v)
            imgui.text_colored(t.text_mute if n else t.warn,
                               f"{n} of {len(have)} cues supplied - the rest "
                               f"are synthesised")
            if widgets.button("write starter cues", 200, icon="folder"):
                cur.export()
            imgui.same_line()
            if widgets.button("open folder", 160, icon="folder"):
                cur.reveal()
            for name, why in cur.bad.items():
                imgui.text_colored(t.danger, f"{name}.wav: {why}")

    if "presets" in show:
        widgets.section("presets", width)
        if widgets.button("save as preset", 170, icon="check"):
            name = st.theme_name if st.theme_name not in theme_mod.BUILTIN else \
                st.theme_name + "-custom"
            theme_mod.save_preset(theme_mod.current(), name, st.app)
            st.theme_name, st.accent = name, ""
            changed = True
        imgui.same_line()
        if widgets.button("save settings", 160, icon="folder"):
            st.save()
        if st.theme_name not in theme_mod.BUILTIN:
            imgui.same_line()
            if widgets.button("delete preset", 160, icon="cross"):
                theme_mod.delete_preset(st.theme_name, st.app)
                st.theme_name = "noir-red"
                changed = True

    if extra is not None:
        extra(st)

    if changed:
        st.apply(log, backdrop=backdrop, effects=effects)
        if on_change is not None:
            on_change(st)
    return changed


# The order `panel` draws them in, and the names it accepts in `sections`.
SECTIONS = ["appearance", "shape", "cards", "type", "backdrop", "effects",
            "log", "sound", "presets"]
