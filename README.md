# VertexUI

A small dark-UI toolkit for [Dear ImGui](https://github.com/pthom/imgui_bundle)
(imgui-bundle), for desktop tools that need to look deliberate rather than
default — and to keep looking that way while they run unattended for hours.

MIT licensed. No assets, no icon font, no audio files — everything is
generated or drawn, so vendoring the folder is the whole install.

![Controls](docs/controls.png)

| module | what it is |
|---|---|
| `theme` | colour/shape tokens, user presets on disk, accent derivation |
| `anim` | frame-rate-independent easing for immediate-mode UI |
| `sound` | synthesised interface cues — no audio files to ship |
| `fonts` | real system typefaces instead of ImGui's bitmap default |
| `icons` | 16 vector icons drawn from primitives — no font, no atlas |
| `widgets` | buttons, tabs, sliders, colour picker, badges — all animated |
| `logview` | a log pane that glides instead of yanking to the bottom |
| `settings` | a ready-made settings panel, and the object behind it |
| `toasts` | click-through notifications drawn *over another application* |

Try it — every widget, the icon sheet, live theming and the log glide:

```bash
pip install imgui-bundle numpy opencv-python
python -m vertexui.demo
```

## Minimal app

```python
from imgui_bundle import hello_imgui
import vertexui as vui

state = {"on": False, "tab": 0}

def gui():
    state["tab"] = vui.widgets.tabs("main", ["Home", "Settings"], state["tab"])
    if vui.widgets.button("Start", primary=True):
        state["on"] = True
    state["on"] = vui.widgets.checkbox("Enabled", state["on"])
    vui.end_frame()          # lets the app idle once motion has settled

params = hello_imgui.RunnerParams()
params.callbacks.show_gui = gui
vui.install(params, theme_=vui.theme.NOIR_RED)
hello_imgui.run(params)
```

![Minimal app](docs/minimal.png)

`install()` wires the theme, fonts, sounds and the idling rule in one call.
That last one is easy to miss: an app that idles to save power renders
every ease at the idle frame rate, and every animation looks broken.

## Theming

Tokens are semantic (`accent`, `surface`, `danger`), never descriptive
(`red`, `dark_grey`) — a palette named after what colours *are* stops
making sense the moment you swap it.

```python
from dataclasses import replace
MINE = replace(vui.theme.NOIR_RED, accent=vui.theme.rgb("#7c3aed"))
vui.theme.use(MINE)
```

Presets: `NOIR_RED`, `NOIR_BLUE`, `SLATE_LIME`, plus any the user saves.
`theme.apply_style()` also pushes the palette into ImGui's own style, so
stock widgets (inputs, tables, scrollbars) match the drawn ones.

Pick one accent and the variants derive from it — asking a user to choose
three colours that relate correctly is asking them to do the designer's
job:

```python
t = theme.NOIR_RED.with_accent(theme.rgb("#852ebd"))
theme.save_preset(t, "my-purple")            # -> %APPDATA%/vertexui/themes
theme.list_presets()                          # built-ins, then the user's
```

`Theme.scaled(text=1.2, rows=1.25)` adjusts type size and density without
touching colour.

## Animation

```python
hot = vui.anim.to(f"btn:{label}", 1.0 if hovered else 0.0, speed=16)
```

The chase is exponential on the frame delta, so it takes the same
wall-clock time at 30fps and 144fps. `anim.settled()` reports whether
anything is mid-transition, which is what `end_frame()` uses to decide
when idling is safe.

Also: `ease_out`, `ease_in_out`, `pulse()` for "this is alive" indicators.

## Sound

Cues are generated as WAV bytes on first use — nothing to ship, nothing to
lose track of in a frozen exe.

```python
vui.sound.use(vui.sound.SoundSet(volume=0.16))
vui.sound.play("ok")
```

The default set is deliberately dull and low. Three things learned the
hard way while tuning it:

* **pitch, not volume, is what makes a cue feel sharp.** Quiet high beeps
  still cut through; the whole set sits low and is low-passed at 900 Hz.
* **a falling pitch reads as a physical knock.** The same tone held flat
  reads as an alert.
* **fade both ends.** A waveform starting or stopping at non-zero
  amplitude clicks, and that click is most of what "harsh" means.

Swap the set with `SoundSet(specs=sound.CRISP_SPECS)` or your own dict.

## Toasts

![Toasts](docs/toasts.png)

A separate always-on-top window that never takes focus and never receives
a click, so it can report over a fullscreen application.

```python
tray = vui.toasts.Toasts(anchor_titles=["My App"], on_status=print)
tray.start()
tray.notify("ok", "Connected")
```

Kinds: `ok`, `warn`, `error`, `info`. Repeats within a couple of seconds
collapse into one with a counter. It has no ImGui dependency and runs
happily in a process with no GUI at all.

Two traps worth knowing, both of which fail *silently*:

* the window **must** pump its message queue. One that doesn't is a hung
  window as far as Windows is concerned — and `GetWindowText` sends
  `WM_GETTEXT` to windows in the same process, so the owning app can
  deadlock enumerating windows against its own overlay.
* `UpdateLayeredWindow` wants **premultiplied alpha**, or the boxes wash
  out pale instead of reading as translucent.

`exclude_from_capture=True` (the default) hides the window from screen
capture, so an app that reads the screen never photographs its own
notifications. On a few graphics configurations that flag stops the window
drawing entirely — hence the switch, and `on_status` to report which.

## Icons

![Icon sheet](docs/icons.png)

Sixteen drawn from primitives: `play stop pause check cross warning info
gear folder refresh search dot chevron bolt sound_on sound_off`. They take
the theme's colour, stay crisp at any DPI, and cannot render as a tofu box
because there is no font involved.

```python
widgets.button("Start", icon="play", primary=True)
widgets.icon_button("gear", tooltip="Settings")
widgets.badge("3 retries", "warn")           # icon picked from the kind
icons.draw("bolt", dl, x, y, 12, colour)     # or draw one yourself
```

Add your own by putting a function in `icons.ICONS` with the signature
`(dl, cx, cy, r, col)`.

## Log view

![Log view](docs/log.png)

Auto-scroll usually means "jump to the bottom every frame", which makes a
busy log unreadable — lines are gone before you can read them. This glides:

| speed | px/s | roughly |
|---|---|---|
| `calm` (default) | 140 | 7 lines a second |
| `steady` | 260 | 13 lines a second |
| `quick` | 520 | 26 lines a second |
| `snap` | — | straight to the bottom, no glide |

```python
log = logview.LogView(speed="calm")
log.add("Connected", kind="ok", tag="net")
log.draw()
```

Scrolling up by hand stops the follow; scrolling back to the bottom
resumes it. Optional timestamp and tag columns, a filter, and a
replaceable `colour_for` rule. Rows are emitted through `ListClipper`, so a
2000-line buffer costs the same as a screenful.

## Settings panel

![Settings panel](docs/settings.png)

```python
st = settings.Settings.load(app="myapp")
st.apply(log)
...
settings.panel(st, log, extra=my_own_rows)
```

Theme picker, accent colour picker, text size, row density, log speed,
sound toggle and volume, and save/load/delete of user presets. Settings
live in `%APPDATA%/<app>/settings.json`, presets in
`%APPDATA%/<app>/themes/*.json` — per-user, because a program directory is
often read-only and a preset is user data.

A corrupt settings file costs you your preferences, not your program: both
loaders fall back to defaults rather than raising.

## Install

```bash
pip install git+https://github.com/D4ead3ye/vertexui
```

Or drop the `vertexui/` folder into your project and import it — there is
nothing to build and no data files to find at runtime, which is also what
makes it survive PyInstaller without a `--add-data` line.

## Requirements

`imgui-bundle` and `numpy`. `opencv-python` for `toasts` only. `toasts`
and `sound` are Windows-only (layered windows and `winsound`); `theme`,
`anim`, `fonts`, `icons`, `widgets` and `logview` are cross-platform.

Every module degrades rather than raising: a missing font role renders in
the default face, an unknown icon draws nothing, and a machine with no
audio device disables sounds after reporting why.

## Contributing

Issues and pull requests welcome. Two conventions worth knowing before you
open one:

* **colour names are semantic.** `accent`, `surface`, `danger` — never
  `red` or `dark_grey`. A palette named after what the colours *are* stops
  making sense the moment somebody swaps them.
* **nothing raises from a draw call.** A frame that throws takes the whole
  window down, so unknown icons, missing fonts and absent audio devices all
  degrade quietly instead. `examples/` is the fastest way to check a change
  in isolation.

## Licence

MIT — see [LICENSE](LICENSE).
