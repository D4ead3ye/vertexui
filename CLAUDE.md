# Working rules for VertexUI

These are binding on anything built with this toolkit, and on the toolkit
itself. They exist because the first version of VertexUI was good at making
one program and every project built on it came out looking like that
program wearing a different accent colour.

## 1. Zero generic boilerplate

Do not reach for a standard template. There is no default application
shape here, and `profiles.NOIR` is not one - it is the original look, kept
so that existing projects do not regress.

Before writing an interface, answer: what is this tool *for*, and what does
that imply about density, chrome, motion and type? Build from that answer.
A tool gets a tab strip because its views are equal-weight and few, not
because tab strips are what the toolkit has.

If none of the seven profiles suits the domain, write one. A profile is
about twenty lines.

## 2. Visual and functional identity follows the domain

Form follows function, and "function" means the actual job:

| domain | what it implies |
|---|---|
| profiling, telemetry | high density, square corners, hairlines, small type, everything is content |
| logs, command output | mono throughout, zero radius, fast motion |
| audio, single-purpose | one centred column, no navigation, large type, slow motion, quiet |
| automation, monitoring | strong status colour, icon rail, quick feedback, toasts |
| reading, reporting | light ground, high contrast, generous measure |
| overlays | compact, cornered, never the subject |

Control layout and event flow follow the same rule. An automation monitor
pushes events at you; a profiler lets you go and look. Those are different
programs and should not share a navigation model.

## 3. Compose, do not extend

Never subclass a widget to get a variant, and never add a flag to a widget
for one project's special case. Use the composition points:

* **slots** - `chrome`, `nav`, `body`, `aside`, `status`, `overlay`. A
  module fills the ones it has something for. A layout draws the ones it
  has room for and silently ignores the rest.
* **pages** - a module registers a page; the *layout* decides whether that
  becomes a tab, an icon in a rail, a segment in a strip, or nothing.
* **hooks** - `setup`, `frame_begin`, `frame_end`, `teardown`.
* **bus** - modules talk by topic name and never import each other.

The test: can this application be reconfigured into a genuinely different
program by changing its profile and nothing else? If a module has to
change, the module knows something it should not.

Layout belongs to the profile. A panel that knows it lives under a tab
strip has made every future layout impossible.

## 4. Two contrasting use cases, always

Every new feature ships with at least two examples that pull in opposite
directions - typically one ultra-compact or headless and one data-rich.
One example demonstrates that a thing runs. Two contrasting ones
demonstrate that it is actually modular, and they catch the assumptions
that a single example hides.

Current pairs:

* `examples/profiler.py` (dense, data-rich) against `examples/tuner.py`
  (one number, no navigation)
* `examples/watchtower.py` - identical modules under every profile, via
  `--profile`, including a headless corner HUD under `--hud`
* `examples/minimal.py` against `examples/ambience.py`

`docs/profiles.png` is the falsifiable version of the claim: seven
captures of one application under seven profiles. If they ever start
looking like one program in seven colours, this document is wrong and the
code needs fixing, not the README.

## House conventions

* Colour names are semantic - `accent`, `surface`, `danger`. Never `red`.
* Nothing raises from a draw call. Unknown icons draw nothing, missing
  fonts fall back, absent audio devices disable themselves after saying so.
* Never assume a dark ground. Use `theme.ink`, `theme.lift`, `theme.sink`
  and `theme.is_light` - `profiles.PAPER` is light and must keep working.
* This binding's draw-list argument order is not the C++ order:
  `add_rect(p_min, p_max, col, rounding, thickness, flags)`,
  `add_polyline(points, col, thickness, flags)` (no defaults),
  `path_stroke(col, thickness, flags)`.
* Widget identity comes from the label. Two widgets sharing one in the
  same window is a hard ImGui error - pass `key=`.
* A card owns its own `ImDrawListSplitter`, which is what makes nesting
  legal. Do not go back to `draw_list.channels_split`.

## Checks

```bash
python tools/smoke.py          # every screen, every state, every layout
python tools/matrix.py tile    # regenerate docs/profiles.png
python tools/shots.py          # regenerate the stills
python tools/spotlight.py      # re-record the looping clip
```
