"""Whole identities, not colour swaps.

An accent picker cannot stop two tools looking like each other, because
what makes them look the same is everything *except* the accent: the same
tab strip, the same card radius, the same row height, the same two
typefaces, the same easing speed. A profile is all of that, named after
the kind of work it is for:

    INSTRUMENT   telemetry and profiling. Dense layout, square corners,
                 hairline borders, no shadows, tight rows, amber on slate.
                 Reads like something with a serial number.
    CONSOLE      logs and command output. Phosphor on near-black, zero
                 radius, mono everywhere, dense.
    MINIMAL      one job, one number. Stage layout, no navigation at all,
                 very round, borderless, slow and quiet.
    REACTIVE     automation you watch rather than drive. Icon rail, strong
                 status colours, quick motion, plated cards.
    PAPER        light ground, high contrast, split view. For long reading
                 and anything that gets printed or screenshotted into a
                 document.
    OVERLAY      a corner HUD over someone else's application.
    NOIR         the toolkit's original look, kept so nothing regresses.

    app = compose.App(profile=profiles.INSTRUMENT)

Derive rather than copy - a project wants its own identity, not one of
these seven verbatim:

    MINE = profiles.INSTRUMENT.variant(
        name="mine", accent="#7c5cff", layout="rail", motion=1.4)

The rule the whole module exists to serve: form follows the domain. If a
profile does not obviously suit what you are building, write one. There
is nothing here a project cannot replace.
"""

from dataclasses import dataclass, field, replace

from . import anim, cards, fonts, layouts, sound
from . import theme as theme_mod
from .theme import Theme, rgb

# --- palettes ----------------------------------------------------------

SLATE = Theme(
    name="slate-amber",
    bg=rgb("#0b0d10"), panel=rgb("#10141a"), surface=rgb("#151a21"),
    surface_hover=rgb("#1d242e"), border=rgb("#222b36"),
    accent=rgb("#f0a830"), accent_bright=rgb("#ffc45f"), accent_dim=rgb("#5c3f12"),
    text=rgb("#dfe5ec"), text_dim=rgb("#8793a3"), text_mute=rgb("#5a6572"),
    ok=rgb("#4cc38a"), warn=rgb("#e0a63d"), danger=rgb("#e5544b"),
    info=rgb("#6fa8d6"),
    rounding=2.0, rounding_panel=3.0, border_width=1.0,
)

PHOSPHOR = Theme(
    name="phosphor",
    bg=rgb("#05070a"), panel=rgb("#080c10"), surface=rgb("#0b1014"),
    surface_hover=rgb("#121a20"), border=rgb("#16222a"),
    accent=rgb("#39d353"), accent_bright=rgb("#6ef58a"), accent_dim=rgb("#12481f"),
    text=rgb("#cfe6d4"), text_dim=rgb("#6f9079"), text_mute=rgb("#45604d"),
    ok=rgb("#39d353"), warn=rgb("#d8b43a"), danger=rgb("#e05252"),
    info=rgb("#5aa9c9"),
    rounding=0.0, rounding_panel=0.0, border_width=1.0,
)

QUIET = Theme(
    name="quiet-cyan",
    bg=rgb("#0a0a0c"), panel=rgb("#0e0e11"), surface=rgb("#141418"),
    surface_hover=rgb("#1d1d23"), border=rgb("#1c1c22"),
    accent=rgb("#4ec9f5"), accent_bright=rgb("#8ee0ff"), accent_dim=rgb("#124a5e"),
    text=rgb("#f0f2f5"), text_dim=rgb("#8a8f98"), text_mute=rgb("#555961"),
    ok=rgb("#5ad0a0"), warn=rgb("#e5c07b"), danger=rgb("#e06c75"),
    info=rgb("#4ec9f5"),
    rounding=14.0, rounding_panel=18.0, border_width=0.0,
)

PAPER_WHITE = Theme(
    name="paper",
    bg=rgb("#f4f5f8"), panel=rgb("#ffffff"), surface=rgb("#ffffff"),
    surface_hover=rgb("#eceef3"), border=rgb("#d5dae2"),
    accent=rgb("#4f46e5"), accent_bright=rgb("#6d64ff"), accent_dim=rgb("#d9d7fb"),
    text=rgb("#14171c"), text_dim=rgb("#4d5560"), text_mute=rgb("#878e9a"),
    ok=rgb("#137a4a"), warn=rgb("#a9690a"), danger=rgb("#c02a2a"),
    info=rgb("#2f6ea8"),
    rounding=6.0, rounding_panel=8.0, border_width=1.0,
)


# --- the profile -------------------------------------------------------

@dataclass
class Profile:
    """One identity: palette, shape, type, density, motion, chrome."""

    name: str = "custom"
    theme: Theme = field(default_factory=lambda: theme_mod.NOIR_RED)
    layout: object = field(default_factory=lambda: layouts.TABBED)

    # type
    face_ui: str = "Segoe UI Variable"
    face_display: str = "Bahnschrift"
    face_mono: str = "Cascadia Mono"
    text_scale: float = 1.0
    base_size: float = 17.5

    # density and shape
    density: float = 1.0            # row scale
    card_style: str = "raised"
    card_shadow: bool = True

    # feel
    motion: float = 1.0             # global easing rate
    sound_set: str = "soft taps"    # None leaves whatever is installed
    volume: float = 0.16

    # ambience, for the profiles that want it
    backdrop: str = "none"
    backdrop_intensity: float = 1.0
    effect: str = "none"
    effect_intensity: float = 1.0

    blurb: str = ""

    # -- derive --------------------------------------------------------
    def variant(self, name=None, accent=None, layout=None, theme=None, **kw):
        """A copy with changes. `accent` takes a hex string and derives the
        bright and dim variants; `layout` takes a name or an instance."""
        t = theme if theme is not None else self.theme
        if accent:
            t = t.with_accent(rgb(accent) if isinstance(accent, str) else accent)
        lay = self.layout
        if layout is not None:
            lay = layouts.get(layout) if isinstance(layout, str) else layout
        return replace(self, name=name or (self.name + "*"), theme=t,
                       layout=lay, **kw)

    # -- build ---------------------------------------------------------
    def build_theme(self) -> Theme:
        return self.theme.scaled(text=self.text_scale, rows=self.density)

    def build_faces(self) -> dict:
        return fonts.build_faces(self.face_ui, self.face_display,
                                 self.face_mono, base=self.base_size)

    def apply(self, app_id="vertexui"):
        """Make this the active identity. Safe before an ImGui context."""
        t = self.build_theme()
        theme_mod.use(t)
        try:
            theme_mod.apply_style(t)
        except Exception:
            pass                       # no context yet - install() styles it
        cards.set_style(self.card_style, self.card_shadow)
        anim.set_rate(self.motion)
        if self.sound_set:
            # Same courtesy as Settings.apply: never over a set the
            # application built and installed itself.
            active = sound.active_set()
            named = getattr(active, "set_name", None) if active else None
            if active is None or (named is not None and named != self.sound_set):
                sound.install(self.sound_set, volume=self.volume, app=app_id)
            else:
                active.volume = self.volume
        return t


# --- the seven ---------------------------------------------------------

NOIR = Profile(
    name="noir", theme=theme_mod.NOIR_RED, layout=layouts.TABBED,
    blurb="the toolkit's original look - tabs, raised cards, red on black",
)

INSTRUMENT = Profile(
    name="instrument", theme=SLATE, layout=layouts.DENSE,
    face_display="Bahnschrift", base_size=16.0, density=0.82,
    card_style="outlined", card_shadow=False, motion=1.6,
    blurb="telemetry and profiling - everything is content, nothing is chrome",
)

CONSOLE = Profile(
    name="console", theme=PHOSPHOR, layout=layouts.DENSE,
    face_ui="Consolas", face_display="Cascadia Mono", base_size=15.5,
    density=0.78, card_style="flat", card_shadow=False, motion=2.2,
    sound_set="crisp",
    blurb="logs and command output - mono throughout, zero radius",
)

MINIMAL = Profile(
    name="minimal", theme=QUIET, layout=layouts.STAGE,
    face_display="Bahnschrift", base_size=19.0, text_scale=1.1, density=1.3,
    card_style="flat", card_shadow=False, motion=0.65,
    sound_set="breeze", volume=0.10,
    blurb="one job, one number - no navigation, slow and quiet",
)

REACTIVE = Profile(
    name="reactive", theme=theme_mod.NOIR_RED, layout=layouts.RAIL,
    card_style="plated", card_shadow=True, motion=1.5,
    effect="fireflies", effect_intensity=0.8,
    blurb="automation you watch - icon rail, strong status, quick motion",
)

PAPER = Profile(
    name="paper", theme=PAPER_WHITE, layout=layouts.SPLIT,
    face_display="Segoe UI Semibold", density=1.1,
    card_style="outlined", card_shadow=False, motion=1.0,
    blurb="light ground and high contrast, for reading and for screenshots",
)

OVERLAY = Profile(
    name="overlay", theme=theme_mod.NOIR_RED, layout=layouts.HUD,
    base_size=16.0, density=0.85, card_style="plated", card_shadow=True,
    motion=1.8, sound_set=None,
    blurb="a corner panel over someone else's application",
)

ALL = {p.name: p for p in
       (NOIR, INSTRUMENT, CONSOLE, MINIMAL, REACTIVE, PAPER, OVERLAY)}
ORDER = ["noir", "instrument", "console", "minimal", "reactive", "paper",
         "overlay"]


def get(name):
    """By name, falling back to the original look."""
    return ALL.get(name, NOIR)


def names():
    return list(ORDER)
