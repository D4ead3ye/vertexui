"""VertexUI - a dark-UI toolkit for Dear ImGui (imgui-bundle).

Each piece is usable on its own:

    theme     colour/shape tokens, user presets, accent derivation
    anim      frame-rate-independent easing for immediate-mode UI
    sound     synthesised interface cues, no audio files to ship
    fonts     real system typefaces, seven roles, in pairs that read
    icons     vector icons drawn from primitives - no font, no atlas
    widgets   buttons, tabs, sliders, colour picker, badges - all animated
    cards     the panels an interface is built out of, in four styles
    graphics  sparklines, dials, meters, heatmaps - drawn, theme-coloured
    inputs    text fields, switches, segmented controls, chips, steppers
    table     sortable, selectable, clipped rows of data
    dialogs   modals, a scrim, and a registry so anything can open one
    notices   note, banner, empty state, and an in-window message tray
    fmt       durations, sizes, counts, and text that fits its box
    i18n      strings in more than one language, with a sane fallback
    paint     gradients, textures and shapes for skins and widgets
    skins     painter slots, for a theme that needs more than a palette
    themes    bundled themes - a profile plus its own drawing
    compose   slots, modules, pages, hooks and a connector bus
    layouts   six chrome shapes: tabbed, rail, dense, stage, hud, split
    profiles  whole identities - palette, shape, type, density, motion
    logview   a log pane that glides instead of yanking to the bottom
    settings  a ready-made settings panel, and the object behind it
    toasts    click-through notifications drawn over another application
    effects   ambient particles behind - and over - the interface
    backdrop  a themed shader backdrop under the whole window

Minimal app:

    from imgui_bundle import hello_imgui
    import vertexui as vui

    def gui():
        if vui.widgets.button("Go", primary=True):
            print("clicked")
        vui.end_frame()

    params = hello_imgui.RunnerParams()
    params.callbacks.show_gui = gui
    vui.install(params, theme_=vui.theme.NOIR_RED)
    hello_imgui.run(params)

`install` wires the theme, the fonts, the sound set and the idling rule in
one call - the last of which is easy to miss and makes every animation look
broken at 9fps if you do.

`toasts`, `effects`, `backdrop` and `graphics` are imported on first use
rather than up front, so a project that wants none of them pays for none of
them - numpy and PyOpenGL are only touched if you touch those modules.
"""

import importlib

from . import (anim, cards, compose, dialogs, fmt, fonts, i18n, icons,
               inputs, layouts, logview, notices, paint, profiles, settings,
               skins, sound, table, theme, themes, widgets)

__all__ = ["anim", "backdrop", "cards", "compose", "dialogs", "effects",
           "fmt", "fonts", "graphics", "i18n", "icons", "inputs", "layouts",
           "logview", "notices", "paint", "profiles", "settings", "skins",
           "sound",
           "table", "theme", "themes", "toasts", "widgets", "install",
           "end_frame",
           "App", "Module"]

__version__ = "1.9.2"

_LAZY = ("toasts", "effects", "backdrop", "graphics")

#: The two names a composed application actually needs.
App = compose.App
Module = compose.Module


def __getattr__(name):
    """Import the heavy optional modules on first touch.

    Without this, `vui.toasts` after a bare `import vertexui` is an
    AttributeError - which is a confusing way to find out that a module is
    not eagerly imported.
    """
    if name in _LAZY:
        mod = importlib.import_module("." + name, __name__)
        globals()[name] = mod
        return mod
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | set(_LAZY))


def install(params, theme_=None, faces=None, sounds=None, idle_fps=9.0,
            active_after_input=1.2):
    """Wire the toolkit into a hello_imgui RunnerParams.

    `active_after_input` is the one that matters: a panel that idles to
    save power renders every ease at the idle rate, which looks broken.
    Staying at full rate briefly after any input keeps motion smooth while
    still costing nothing when untouched.

    `faces` takes a role mapping from `fonts.build_faces(...)`, or a
    `Settings.build_faces()` when the user picks their own.
    """
    if theme_ is not None:
        theme.use(theme_)
    if sounds is not None:
        sound.use(sounds)

    params.callbacks.load_additional_fonts = fonts.loader(faces)
    params.callbacks.setup_imgui_style = lambda: theme.apply_style(theme.current())

    params.fps_idling.enable_idling = True
    params.fps_idling.fps_idle = idle_fps
    params.fps_idling.time_active_after_last_event = active_after_input
    return params


def end_frame(params=None):
    """Call once at the end of your gui() to let the app idle again only
    when nothing is mid-transition."""
    from imgui_bundle import hello_imgui
    try:
        p = params or hello_imgui.get_runner_params()
        p.fps_idling.enable_idling = anim.settled()
    except Exception:
        pass
