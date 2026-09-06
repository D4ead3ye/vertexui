"""A ready-made settings panel, and the object behind it.

Every project ends up writing the same panel: pick a theme, pick an accent,
set the text size, turn the sounds off. This is that panel, plus a Settings
object that knows how to persist itself and how to apply itself to the rest
of the toolkit.

    st = settings.Settings.load()
    st.apply()
    ...
    settings.panel(st, extra=my_diagnostics_section)

Nothing here is mandatory. A project that wants its own layout can use the
Settings object alone, or ignore it and drive theme/sound directly.
"""

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

from imgui_bundle import ImVec2, imgui

from . import fonts, logview, sound, widgets
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

    monospaced_log: bool = True
    timestamps: bool = True
    tag_column: bool = True
    log_speed: str = "calm"

    sounds: bool = True
    volume: float = 0.16

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
            if hasattr(base, k) and isinstance(v, type(getattr(base, k))):
                setattr(base, k, v)
        return base

    # -- application ----------------------------------------------------
    def build_theme(self) -> "theme_mod.Theme":
        t = theme_mod.load_preset(self.theme_name, self.app) or theme_mod.NOIR_RED
        if self.accent:
            t = t.with_accent(theme_mod.rgb(self.accent))
        return t.scaled(text=self.text_scale,
                        rows=ROW_SPACING.get(self.row_spacing, 1.0))

    def apply(self, log: "logview.LogView" = None):
        t = self.build_theme()
        theme_mod.use(t)
        try:
            theme_mod.apply_style(t)
        except Exception:
            pass      # no ImGui context yet - install() will style it later
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
        return t


def panel(st: Settings, log: "logview.LogView" = None, extra=None,
          on_change=None, width=0.0):
    """Draw the panel. Returns True if anything changed.

    `extra` is called at the end for project-specific rows, inside the same
    section styling.
    """
    t = theme_mod.current()
    changed = False

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

    new_scale = widgets.slider("text size", st.text_scale, 0.8, 1.6, 180.0,
                               "%.2fx", key="textscale")
    if abs(new_scale - st.text_scale) > 0.001:
        st.text_scale = round(new_scale, 2)
        changed = True

    ridx = ROW_ORDER.index(st.row_spacing) if st.row_spacing in ROW_ORDER else 1
    nr = widgets.combo("row spacing", ROW_ORDER, ridx, 140.0, key="rowspace")
    if nr != ridx:
        st.row_spacing = ROW_ORDER[nr]
        changed = True

    for label, attr in (("monospaced log", "monospaced_log"),
                        ("timestamps", "timestamps"),
                        ("tag column", "tag_column")):
        v = widgets.checkbox(label, getattr(st, attr))
        if v != getattr(st, attr):
            setattr(st, attr, v)
            changed = True
        imgui.same_line()
    imgui.new_line()

    widgets.section("log", width)
    sidx = logview.SPEED_ORDER.index(st.log_speed) if st.log_speed in logview.SPEED_ORDER else 0
    ns = widgets.combo("scroll", logview.SPEED_ORDER, sidx, 140.0, key="logspeed")
    if ns != sidx:
        st.log_speed = logview.SPEED_ORDER[ns]
        changed = True
    imgui.same_line()
    px = logview.SPEEDS[st.log_speed]
    imgui.text_colored(t.text_mute,
                       "straight to the bottom" if px is None
                       else f"{px:.0f} px/s")

    widgets.section("sound", width)
    v = widgets.checkbox("interface sounds", st.sounds)
    if v != st.sounds:
        st.sounds = v
        changed = True
    imgui.same_line()
    nv = widgets.slider("volume", st.volume, 0.0, 0.6, 160.0, "%.2f", key="vol")
    if abs(nv - st.volume) > 0.001:
        st.volume = round(nv, 2)
        changed = True
    imgui.same_line()
    if widgets.button("test", 80, height=26.0):
        sound.current()._last = 0.0
        sound.play("ok")

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
        st.apply(log)
        if on_change is not None:
            on_change(st)
    return changed
