"""Colour, shape and spacing tokens - the part you swap per project.

Everything visual is a value on a Theme, never a literal inside a widget.
That is the whole point of the split: a different project changes one
object and every button, tab, checkbox and toast follows, instead of
hunting hardcoded reds through the drawing code.

    from vertexui import theme
    theme.use(theme.NOIR_RED)          # or your own Theme(...)

A Theme carries semantic names (`accent`, `surface`, `danger`), not
descriptive ones (`red`, `dark_grey`). A palette named after what colours
ARE stops making sense the moment you swap it; named after what they DO,
it survives.
"""

from dataclasses import dataclass, field, replace

from imgui_bundle import ImVec2, ImVec4, imgui


def rgb(hex_str: str, alpha: float = 1.0) -> ImVec4:
    """`rgb("#e0243b")` - hex is how palettes are written down everywhere
    else, so accept it directly rather than making callers convert."""
    h = hex_str.lstrip("#")
    return ImVec4(int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0,
                  int(h[4:6], 16) / 255.0, alpha)


def with_alpha(c: ImVec4, a: float) -> ImVec4:
    return ImVec4(c.x, c.y, c.z, a)


def lerp(a: ImVec4, b: ImVec4, t: float) -> ImVec4:
    return ImVec4(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t,
                  a.z + (b.z - a.z) * t, a.w + (b.w - a.w) * t)


@dataclass
class Theme:
    """One project's look. Copy a preset and override what differs:

        MINE = replace(theme.NOIR_RED, accent=theme.rgb("#3b82f6"))
    """

    name: str = "custom"

    # surfaces, back to front
    bg: ImVec4 = field(default_factory=lambda: rgb("#08080a"))
    panel: ImVec4 = field(default_factory=lambda: rgb("#0e0e11"))
    surface: ImVec4 = field(default_factory=lambda: rgb("#16161a"))
    surface_hover: ImVec4 = field(default_factory=lambda: rgb("#212127"))
    border: ImVec4 = field(default_factory=lambda: rgb("#23232a"))

    # the one colour that carries meaning
    accent: ImVec4 = field(default_factory=lambda: rgb("#da2538"))
    accent_bright: ImVec4 = field(default_factory=lambda: rgb("#ff4355"))
    accent_dim: ImVec4 = field(default_factory=lambda: rgb("#661019"))

    text: ImVec4 = field(default_factory=lambda: rgb("#eaeaef"))
    text_dim: ImVec4 = field(default_factory=lambda: rgb("#828290"))
    text_mute: ImVec4 = field(default_factory=lambda: rgb("#53535f"))

    # status, used by toasts and anything reporting an outcome
    ok: ImVec4 = field(default_factory=lambda: rgb("#53c971"))
    warn: ImVec4 = field(default_factory=lambda: rgb("#e5aa45"))
    danger: ImVec4 = field(default_factory=lambda: rgb("#e54355"))
    info: ImVec4 = field(default_factory=lambda: rgb("#9aa3b3"))

    # scale - applied on top of everything, so one value adjusts density
    text_scale: float = 1.0
    row_scale: float = 1.0

    # shape
    rounding: float = 7.0
    rounding_panel: float = 9.0
    border_width: float = 1.0

    # spacing
    padding: ImVec2 = field(default_factory=lambda: ImVec2(16, 14))
    frame_padding: ImVec2 = field(default_factory=lambda: ImVec2(14, 8))
    item_spacing: ImVec2 = field(default_factory=lambda: ImVec2(10, 10))

    # -- derived ---------------------------------------------------------
    def with_accent(self, colour: ImVec4) -> "Theme":
        """A copy using `colour` as the accent, with the bright and dim
        variants derived from it.

        A colour picker gives one value; asking a user to pick three that
        relate correctly is asking them to do the designer's job.
        """
        return replace(self, name=self.name + "*", accent=colour,
                       accent_bright=_shift(colour, 1.30),
                       accent_dim=_shift(colour, 0.42))

    def scaled(self, text: float = None, rows: float = None) -> "Theme":
        t = replace(self,
                    text_scale=self.text_scale if text is None else text,
                    row_scale=self.row_scale if rows is None else rows)
        r = t.row_scale
        return replace(t,
                       padding=ImVec2(16 * r, 14 * r),
                       frame_padding=ImVec2(14 * r, 8 * r),
                       item_spacing=ImVec2(10 * r, 10 * r))

    # -- serialisation ---------------------------------------------------
    def to_dict(self) -> dict:
        out = {"name": self.name}
        for k, v in self.__dict__.items():
            if k == "name":
                continue
            if isinstance(v, ImVec4):
                out[k] = to_hex(v)
            elif isinstance(v, ImVec2):
                out[k] = [v.x, v.y]
            else:
                out[k] = v
        return out

    @staticmethod
    def from_dict(data: dict) -> "Theme":
        base = Theme()
        kwargs = {}
        for k, v in (data or {}).items():
            if not hasattr(base, k):
                continue          # unknown keys are ignored, not fatal
            cur = getattr(base, k)
            if isinstance(cur, ImVec4) and isinstance(v, str):
                kwargs[k] = rgb(v)
            elif isinstance(cur, ImVec2) and isinstance(v, (list, tuple)):
                kwargs[k] = ImVec2(float(v[0]), float(v[1]))
            elif isinstance(cur, (int, float, str)) and isinstance(v, (int, float, str)):
                kwargs[k] = type(cur)(v)
        return replace(base, **kwargs)

    def status(self, kind: str) -> ImVec4:
        """Colour for "ok" / "warn" / "error" / "info"."""
        return {"ok": self.ok, "warn": self.warn,
                "error": self.danger, "info": self.info}.get(kind, self.info)


def _shift(c: ImVec4, factor: float) -> ImVec4:
    """Brighten or darken while keeping the hue, so a derived variant still
    reads as the same colour rather than drifting toward grey."""
    return ImVec4(max(0.0, min(1.0, c.x * factor)),
                  max(0.0, min(1.0, c.y * factor)),
                  max(0.0, min(1.0, c.z * factor)), c.w)


def to_hex(c: ImVec4) -> str:
    return "#%02x%02x%02x" % (int(round(c.x * 255)), int(round(c.y * 255)),
                              int(round(c.z * 255)))


NOIR_RED = Theme(name="noir-red")

# Two more so the mechanism is obviously usable, not just theoretically so.
NOIR_BLUE = replace(
    NOIR_RED, name="noir-blue",
    accent=rgb("#2f7fe8"), accent_bright=rgb("#5a9dff"), accent_dim=rgb("#123258"))

SLATE_LIME = replace(
    NOIR_RED, name="slate-lime",
    bg=rgb("#0d1013"), panel=rgb("#141920"), surface=rgb("#1c232c"),
    surface_hover=rgb("#26303b"), border=rgb("#2b3641"),
    accent=rgb("#8ed11f"), accent_bright=rgb("#a7e93c"), accent_dim=rgb("#3a5610"))

_active = NOIR_RED


def use(theme: Theme):
    """Make `theme` the one widgets read from."""
    global _active
    _active = theme
    return _active


def current() -> Theme:
    return _active


def apply_style(theme: Theme = None):
    """Push the theme into ImGui's own style.

    Widgets in this toolkit draw themselves, but stock ImGui widgets -
    inputs, tables, scrollbars, popups - read the global style, and a panel
    where half the controls are themed looks worse than one where none are.
    """
    t = theme or _active
    s = imgui.get_style()

    s.window_rounding = t.rounding_panel
    s.child_rounding = t.rounding_panel
    s.frame_rounding = t.rounding
    s.popup_rounding = t.rounding_panel
    s.scrollbar_rounding = t.rounding_panel
    s.grab_rounding = t.rounding
    s.tab_rounding = t.rounding

    s.window_border_size = t.border_width
    s.child_border_size = t.border_width
    s.frame_border_size = 0.0          # borders on every frame read as a grid
    s.popup_border_size = t.border_width
    s.tab_bar_border_size = 0.0

    s.window_padding = t.padding
    s.frame_padding = t.frame_padding
    s.item_spacing = t.item_spacing
    s.item_inner_spacing = ImVec2(8, 6)
    s.cell_padding = ImVec2(10, 7)
    s.scrollbar_size = 11.0
    s.grab_min_size = 11.0

    C = imgui.Col_

    def col(name, value):
        # Enum names drift between ImGui versions; a missing one should not
        # take the whole theme down with it.
        idx = getattr(C, name, None)
        if idx is None:
            return
        try:
            s.set_color_(int(idx.value), value)
        except Exception:
            pass

    clear = ImVec4(0, 0, 0, 0)
    col("text", t.text)
    col("text_disabled", t.text_mute)
    col("window_bg", t.bg)
    col("child_bg", t.panel)
    col("popup_bg", t.panel)
    col("border", t.border)
    col("border_shadow", clear)

    col("frame_bg", t.surface)
    col("frame_bg_hovered", t.surface_hover)
    col("frame_bg_active", t.surface_hover)

    col("title_bg", t.bg)
    col("title_bg_active", t.bg)
    col("title_bg_collapsed", t.bg)
    col("menu_bar_bg", t.panel)

    col("scrollbar_bg", clear)
    col("scrollbar_grab", t.surface_hover)
    col("scrollbar_grab_hovered", lerp(t.surface_hover, t.text_mute, 0.5))
    col("scrollbar_grab_active", t.accent)

    col("check_mark", t.accent_bright)
    col("slider_grab", t.accent)
    col("slider_grab_active", t.accent_bright)

    col("button", t.surface)
    col("button_hovered", t.surface_hover)
    col("button_active", t.accent_dim)

    col("header", with_alpha(t.accent, 0.22))
    col("header_hovered", with_alpha(t.accent, 0.32))
    col("header_active", with_alpha(t.accent, 0.42))

    col("separator", t.border)
    col("separator_hovered", t.accent_dim)
    col("separator_active", t.accent)

    col("tab", clear)
    col("tab_hovered", t.surface)
    col("tab_selected", t.surface)
    col("tab_selected_overline", clear)

    col("table_header_bg", t.surface)
    col("table_border_strong", t.border)
    col("table_border_light", lerp(t.panel, t.border, 0.5))
    col("table_row_bg", clear)
    col("table_row_bg_alt", ImVec4(1, 1, 1, 0.015))

    col("resize_grip", clear)
    col("resize_grip_hovered", with_alpha(t.accent, 0.26))
    col("resize_grip_active", t.accent)
    col("nav_cursor", t.accent_bright)


# --- presets -----------------------------------------------------------
BUILTIN = {t.name: t for t in (NOIR_RED, NOIR_BLUE, SLATE_LIME)}


def presets_dir(app: str = "vertexui") -> "Path":
    """Where user presets live. Per-user, not next to the exe - a program
    directory is often read-only and a preset is user data."""
    from pathlib import Path
    import os
    base = Path(os.environ.get("APPDATA") or Path.home())
    d = base / app / "themes"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_preset(theme: Theme, name: str = None, app: str = "vertexui"):
    """Write a theme to disk as JSON. Returns the path."""
    import json
    name = (name or theme.name).strip().replace("/", "-") or "custom"
    path = presets_dir(app) / f"{name}.json"
    data = theme.to_dict()
    data["name"] = name
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def load_preset(name: str, app: str = "vertexui"):
    """A built-in by name, or a user preset from disk. None if neither."""
    if name in BUILTIN:
        return BUILTIN[name]
    import json
    path = presets_dir(app) / f"{name}.json"
    if not path.exists():
        return None
    try:
        return Theme.from_dict(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return None       # a corrupt preset should not stop the app starting


def delete_preset(name: str, app: str = "vertexui") -> bool:
    path = presets_dir(app) / f"{name}.json"
    if path.exists():
        path.unlink()
        return True
    return False


def list_presets(app: str = "vertexui"):
    """Built-in names first, then the user's own."""
    user = sorted(p.stem for p in presets_dir(app).glob("*.json"))
    return list(BUILTIN) + [u for u in user if u not in BUILTIN]
