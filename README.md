# VertexUI

A small dark-UI toolkit for [Dear ImGui](https://github.com/pthom/imgui_bundle)
(imgui-bundle), for desktop tools that need to look deliberate rather than
default — and to keep looking that way while they run unattended for hours.

MIT licensed. No assets, no icon font, no audio files — everything is
generated or drawn, so vendoring the folder is the whole install.

![VertexUI](docs/spotlight.gif)

*The demo, running. `python -m vertexui.demo`*

| module | what it is |
|---|---|
| `theme` | colour/shape tokens, user presets on disk, accent derivation |
| `anim` | frame-rate-independent easing for immediate-mode UI |
| `sound` | synthesised interface cues — no audio files to ship |
| `fonts` | real system typefaces, seven roles, in pairs that read |
| `icons` | 16 vector icons drawn from primitives — no font, no atlas |
| `widgets` | buttons, tabs, sliders, colour picker, badges — all animated |
| `cards` | the panels an interface is built out of, in four styles |
| `graphics` | sparklines, dials, meters, heatmaps — drawn, theme-coloured |
| `inputs` | text fields, switches, segmented controls, chips, steppers |
| `table` | sortable, selectable, clipped rows of data |
| `dialogs` | modals, a scrim, and a registry so anything can open one |
| `notices` | note, banner, empty state, and an in-window message tray |
| `fmt` | durations, sizes, counts, and text that fits its box |
| `i18n` | strings in more than one language, with a sane fallback |
| `compose` | slots, modules, pages, hooks and a connector bus |
| `layouts` | six chrome shapes: tabbed, rail, dense, stage, hud, split |
| `profiles` | whole identities — palette, shape, type, density, motion |
| `skins` | painter slots, for a theme that needs more than a palette |
| `themes` | bundled themes — a profile plus its own drawing |
| `logview` | a log pane that glides instead of yanking to the bottom |
| `settings` | a ready-made settings panel, and the object behind it |
| `toasts` | click-through notifications drawn *over another application* |
| `effects` | ambient particles behind — and over — the interface |
| `backdrop` | a themed shader backdrop under the whole window |

Try it — every widget, the icon sheet, the card styles, live theming, the
shader scenes and the log glide:

```bash
pip install "vertexui[all] @ git+https://github.com/D4ead3ye/vertexui"
python -m vertexui.demo
```

## Profiles

An accent picker cannot stop two tools looking like each other, because
what makes them look the same is everything *except* the accent: the same
tab strip, the same card radius, the same row height, the same two
typefaces, the same easing speed.

A profile is all of that at once, named after the kind of work it is for.

![Seven profiles](docs/profiles.png)

**That image is one application.** Same four modules, same data, nine
profiles — and it is in the repo as `tools/matrix.py` precisely so the
claim can be checked rather than believed.

| profile | layout | for |
|---|---|---|
| `NOIR` | tabbed | the toolkit's original look, kept so nothing regresses |
| `SBR` | tabbed | Araki western — parchment, brass, notched corners, golden ratio |
| `Y2K` | tabbed | Win98 chrome, neon on pitch black, a CD-ROM spinner |
| `INSTRUMENT` | dense | telemetry and profiling — amber on slate, square corners, 0.82 density |
| `CONSOLE` | dense | logs and command output — phosphor, mono throughout, zero radius |
| `MINIMAL` | stage | one job, one number — no navigation, 14px corners, slow and quiet |
| `REACTIVE` | rail | automation you watch — icon rail, strong status, quick motion |
| `PAPER` | split | light ground, high contrast, for reading and screenshots |
| `OVERLAY` | hud | a corner panel over someone else's application |

```python
app = compose.App(profile=profiles.INSTRUMENT)
```

Derive rather than copy — a project wants its own identity, not one of
these seven verbatim:

```python
MINE = profiles.INSTRUMENT.variant(name="mine", accent="#7c5cff",
                                   layout="rail", motion=1.4, density=0.9)
```

A profile carries palette, shape (radius, border width), the three
typeface choices, text scale, row density, card style, **motion rate**,
cue set and optional ambience. Tempo is a real part of character: the same
panel at `motion=0.6` feels considered and at `1.8` feels eager, and
neither is a colour.

`PAPER` is light, and widgets handle that now — `theme.ink`, `theme.lift`,
`theme.sink` and `theme.is_light` replace the assumption that foreground
means "add white". A checkbox tick contrasts with the box it is in, a
primary button's label contrasts with its own fill rather than with the
panel behind it, and a card's shadow is cast light rather than a tint
toward the background.

## Composition

Modules say *what* they contribute. A layout — picked by the profile, not
by the module — decides what becomes of it.

```python
class Rates(compose.Module):
    name = "rates"

    def setup(self, app):
        app.page("rates", "Rates", icon="bolt", draw=self.body)
        app.slot("status", self.status)
        app.bus.on("tick", self.on_tick)

app = compose.App(profile=profiles.REACTIVE, title="rates")
app.use(Rates(), Alerts())
app.run()
```

Three composition points, and none of them is subclassing:

* **slots** — `chrome`, `nav`, `body`, `aside`, `status`, `overlay`. A
  layout draws the ones it has room for and ignores the rest, which is how
  one module set survives a layout with no sidebar.
* **hooks** — `setup`, `frame_begin`, `frame_end`, `teardown`, for work
  that is not drawing.
* **bus** — publish/subscribe by topic. A module emits `"job.done"`
  without knowing whether anything listens; a notifier listens without
  importing what emits. A subscriber that raises is reported and skipped,
  never allowed to take the frame.

The test for whether this is working: can the application become a
genuinely different program by changing its profile and nothing else? If a
module has to change, that module knows something it should not.

## Layouts

```python
profiles.INSTRUMENT.variant(layout="rail")      # or an instance
```

| | |
|---|---|
| `TABBED` | title, tab strip, page below. For a handful of equal-weight views |
| `RAIL` | icons down the left edge, no tab strip. Many views, content is the subject |
| `DENSE` | one hairline strip of chrome. Everything else is content |
| `STAGE` | one centred column, no navigation at all |
| `HUD` | a small corner panel over nothing |
| `SPLIT` | page and aside side by side |

A layout declares what it `accepts`, so a module filling `aside` on a
layout that has none is not an error — it simply does not get drawn.

## Graphics

![Graphics](docs/graphics.png)

The quickest way to make two tools built on one toolkit look like two
different tools is to let each show its data in the shape that data
actually has. All drawn on the draw list from the theme's own colours — no
plotting library, no texture, nothing to ship.

```python
graphics.sparkline(history, 200, 34)
graphics.gauge(temp, 0, 300, label="NOZZLE", unit="C")
graphics.plot({"cpu": cpu, "mem": mem}, fill=True)
graphics.levels([left, right], peaks=[l_pk, r_pk])
```

`sparkline` `plot` `bars` `histogram` `levels` `gauge` `ring` `heatmap`
`scatter` `waveform` `timeline` `pips`. Pass `width=0` to fill the
available width; everything advances the cursor, so these sit in a column
with ordinary widgets and inside cards.

Two that are worth the pixels over a number: a sparkline's **head dot**,
because without one the eye has to find the right-hand end before it can
read "now"; and `levels` going hot near the top, because a meter that
stays one colour makes you read the number to find out whether it is
clipping.

## Forms and records

![Forms](docs/forms.png)

The toolkit had everything you need to *trigger* something and nothing you
need to *enter* something. These came back from the applications built on
it — the duplication counts are from a scan of ten of them.

```python
changed, name = inputs.text_input("name", name, label="Supplier")
only_open     = inputs.switch("Open orders only", only_open)
view          = inputs.segmented("view", ["Day", "Week", "Month"], view)
qty           = inputs.stepper("qty", qty, lo=1, hi=99)
on            = inputs.chip("late", "error", on=on)
inputs.delta(-1.1, good_up=False)      # down is the win for latency
```

`switch` is not a reskinned checkbox: a checkbox says *this item is
selected*, a switch says *this setting is on*, and five checkboxes read as
a multi-select where five switches read as five independent settings.

### Table

A tool that holds records cannot do without one, and one project wrote
about 150 lines of its own — including a header row drawn by hand, because
ImGui's built-in one cannot hold a tri-state checkbox or sort on a click of
the label, which is where everyone clicks.

```python
cols = [table.Col("ref", "Ref", 110),
        table.Col("supplier", "Supplier"),
        table.Col("total", "Total", 130, align="r")]
st = table.State(sort="due")

rows = st.sort_rows(rows)
with table.table("orders", cols, height=380) as open_:
    if open_:
        table.header(cols, st, ids=[r["id"] for r in rows])
        for i, r in table.rows(rows, st):
            hovered, clicked = table.row_begin(r["id"], r["id"] in st.selected)
            table.cell(r["ref"], role="mono", column=0)
            table.cell(r["supplier"], column=1)
            table.cell(f"{r['total']:,.2f}", align="r", column=2)
```

`table.rows` runs a clipper, so four thousand rows cost a screenful.
Sorting, selection and the tri-state header box live on `State`, which is a
plain dataclass you can persist. `None` sorts last in both directions,
because *missing* is not smaller than everything.

### Dialogs

The hard part was never the box — it is that a dialog is opened from
somewhere it is not drawn: a table row, a toolbar, a shortcut. ImGui wants
`open_popup` in the same ID stack the popup is drawn in, which is why every
project ended up with a registry. This is that registry.

```python
dialogs.register("delete", draw_delete)     # once
dialogs.open("delete", ids=selected)        # from anywhere, even a row
dialogs.draw()                              # once, end of frame
```

`dialogs.confirm(...)` is the yes/no case in a single call and registers
itself. Escape closes anything closable, which hand-rolled modals
reliably forget.

### Notices

```python
notices.note("Fragile crates route to the inspection bay.", icon="warning")
notices.banner("Saving failed.", "error", action=("Retry", retry))
notices.empty_state("search", "Nothing matches", body, actions=[...])
tray = notices.Tray(); tray.push("ok", "Saved"); tray.draw()
```

Four surfaces in rising order of interruption. `note` is here because
**six separate projects wrote it** before this module existed, and two were
byte-for-byte identical — same signature, same `rule, pad = 3.0, 9.0`, same
wrap arithmetic. That is the clearest signal a toolkit can get.

`Tray` is the in-window sibling of `toasts`: same four kinds, same
collapse-repeats, drawn on the window's own list — for anything that does
not want a layered OS window, or is not on Windows.

## Formatting and language

```python
fmt.duration(4512)   # 1h 15m        fmt.bytes(1536000)  # 1.5 MB
fmt.count(28400)     # 28.4k         fmt.ago(then)       # 4m ago
fmt.clock(3725)      # 1:02:05       fmt.ellipsis(s, 180)
```

`ellipsis` measures rather than counting characters — a proportional face
makes `WWWW` twice the width of `iiii`, and a character budget truncates
one far too early and the other not at all.

```python
i18n.load("pt", {"save": "Salvar"})
i18n.use("pt")
i18n.t("save")            # Salvar
i18n.t("nope")            # "nope" - never an exception, never a blank
```

Deliberately small. A missing key returns the key, because a panel reading
`orders.due` is a bug you can see and an empty label is one you find from a
screenshot three weeks later. `i18n.missing()` lists everything asked for
and not found, so the translation to-do list writes itself.

## Themes

A profile is configuration — colours, shape, type, density, which layout.
Some identities need *drawing*: a card that is parchment in an engraved
brass frame with notched corners and a cross-hatched ink shadow is not a
palette, and no amount of tokens gets you there.

So `skins` is a small set of optional painters a profile can carry:

```python
Skin(plate=..., head=..., frame=..., hover_aura=..., press=...,
     spinner=..., background=..., press_depth=2.4, press_snap=False)
```

Where a painter is set the widget calls it; where it is not, nothing
changes and the widget draws as it always did. Every painter may return
`False` to mean *not mine, draw it normally* — which is what lets a skin
restyle only the `raised` card and leave the other three stock. No
subclassing, and a theme that only wants a palette never touches it.

### Steel Ball Run

![Steel Ball Run](docs/sbr.png)

Araki western: desert parchment ground, panels held in engraved brass
frames with notched corners and ornate bracket flourishes, headers that
are struck brass nameplates rather than a label and a rule, and serif
throughout.

The manga vocabulary is load-bearing rather than decorative, and it is
what separates this from a western palette:

* **halftone screentone** where a flat theme would use a tint — ben-day
  dots on a 45° lattice, growing toward the foot of each panel, because
  that is how a page gets a grey without a grey ink
* **cross-hatched ink** where a flat theme would use a blurred shadow
* **focus lines and rising menacing marks** on hover where a flat theme
  would use a glow. A glow is a lighting effect and this interface has no
  lights in it; the page's own way of saying *look here* is to point every
  line at the thing. The ゴ marks are drawn from three strokes rather than
  typed, since the glyph needs a Japanese range in the font atlas — a
  megabyte of texture for one decorative character
* **variable-weight borders** — heavy ink with a lighter brass companion
  inside it, which is how a panel border is actually inked. One even line
  was the single thing that made the first cut look flat

![The same code on two profiles](docs/sbr_contrast.png)

**Same application, same code.** Everything on the left comes from the
profile and its skin — which is the claim the whole `skins` module exists
to make good on.

φ is load-bearing rather than decorative: the notch size, the frame inset,
the card header, the aura radii, the motion rate and the background spiral
are all steps of it.

```python
from vertexui import themes
app = compose.App(profile=themes.SBR)
```

![Riders](docs/sbr_riders.png)

The spinner is Gyro's steel ball, and **Gyro's are green** — a green metal
that desaturates toward white at the highlight, which is what stops it
reading as painted plastic. It turns about a vertical axis, so each etched
groove is a meridian whose half-width is the cosine of how far round it
has come; that sells the rotation with no 3D involved, and the poles stay
put, which is where the brass caps go.

One more thing a sphere needs: **bounce light along its shaded edge**.
Without it the thing reads as a flat disc with a dot on it however good
the ramp is, because the dark side of a polished object is never the
darkest part of the picture.

Two things worth knowing if you write one of these:

* **a golden spiral grows by φ every quarter turn**, so over three turns
  that is φ¹², and the only sane way to draw one to a given size is from
  the outside inward. The first attempt overflowed a float.
* **alphas tuned on a dark ground read heavy on a pale one.** Area fills
  drop from 0.16 to 0.10 when `theme.is_light` — the same value that looks
  like a tint on black looks like a wash on parchment.

### Y2K Cyber

![Y2K Cyber](docs/y2k.png)

Pitch black, liquid chrome, hot pink and electric cyan over deep purple.
Zero radius anywhere, chamfered corners, hard offset shadows with no blur
at all, and the inset/outset bevels every operating system drew between
1995 and 2001.

Cards are **floating windows** — a gradient title bar carrying the module
name in monospace with minimise and close squares at its right, a dot-grid
ground, a chrome frame. That needed a new painter: `head`, because the
stock card header is a label and a rule and no amount of configuration
turns one into a title bar.

![Network page](docs/y2k_network.png)

Buttons are metal blocks that drop **the instant** you touch them —
`press_snap=True`, a new skin flag, because this look is *about* not being
smooth and an eased press makes it read as a modern button in costume.
Hover is a CRT glitch: chromatic pink/cyan edge separation and a torn
scanline sliding down the control, driven by the clock rather than by the
hover amount, since a glitch that pulses smoothly is not a glitch.

![The same code on two profiles](docs/y2k_contrast.png)

The spinner is a CD-ROM. The holographic sheen is the part worth getting
right: `|cos(angle - spin)|` is **already** two lobes 180° apart, which is
what a disc shows. Adding a second term looked like more holograph and was
really four wide lobes — a colour wheel. One term at a high exponent gives
two narrow arcs sweeping a dark silver disc, which is what a CD does.

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

## Typography

Two faces, not one. One face doing every job is most of what makes an
interface look like a default — a body face set at 35px is just big body
text, where a display face set at 35px reads as an instrument.

Seven roles are wired, and a settings panel drives them from three choices:

| role | what it is for |
|---|---|
| `ui` | body text, and the default |
| `semi` | headings and emphasis — the bold of the interface face |
| `title` | the display face at heading size |
| `mono` | logs and tables, where things have to line up |
| `label` | the tracked micro-labels on cards |
| `big` / `huge` | a readout meant to be seen from across the room |

```python
faces = fonts.build_faces(ui="Segoe UI Variable",
                          display="Bahnschrift",     # DIN-derived, technical
                          mono="Cascadia Mono")
vui.install(params, faces=faces)
...
with fonts.use("huge"):
    imgui.text("210")
```

`DISPLAY_FACES` carries a **per-face size scale**, because faces disagree
about how much of the em the x-height takes: Bahnschrift at a matched em
size renders noticeably larger than the body face, so it is scaled to 0.88
and card layouts built around it stay intact.

ImGui has no letter-spacing, so tracked capitals are drawn a glyph at a
time — three to seven characters each, and the tracking is most of what
separates a laid-out panel from a stack of default text:

```python
widgets.caps(dl, x, y, "NOZZLE", colour, track=1.5)
widgets.caps_width("NOZZLE")        # to right-align one
```

## Animation

```python
hot = vui.anim.to(f"btn:{label}", 1.0 if hovered else 0.0, speed=16)
```

The chase is exponential on the frame delta, so it takes the same
wall-clock time at 30fps and 144fps. `anim.settled()` reports whether
anything is mid-transition, which is what `end_frame()` uses to decide
when idling is safe.

Also: `ease_out`, `ease_in_out`, `pulse()` for "this is alive" indicators.

Two pieces of motion that are worth having ready-made:

```python
widgets.progress_hairline(0.62)      # full width, along the very top edge
```

The one number worth seeing from the other side of the room, and up against
the edge it costs no layout at all. The bloom on the leading edge is what
makes the eye find it moving rather than having to read it.

```python
wipe = widgets.Transition()
...
wipe.to(self.screen)     # anywhere before drawing
... draw the screen ...
wipe.draw()              # last thing in the frame
```

Swapping the whole window from one screen to another reads as a glitch
without a beat in between; a short fade over the top reads as navigation.

## Widgets

![Widgets](docs/controls.png)

Drawn rather than styled. ImGui's own widgets take their geometry and
colour from the global style, which is tuned for one shape of control;
restyling them gets you a themed panel that still snaps between states.
These draw themselves, so hover, press and selection each ease
independently, and every one reads the active theme and plays from the
active sound set.

| | |
|---|---|
| `button` | with an optional icon, a primary variant, and a disabled state |
| `checkbox` | the tick draws itself, so it eases in rather than appearing |
| `tabs` | the indicator spans the label, not the cell |
| `slider` / `combo` | themed, and keyed so two can share a label |
| `color_button` | opens ImGui's picker in a popup |
| `badge` | a status pill; the icon comes from the kind |
| `icon_button` | square, with a tooltip |
| `status_pill` | the IDLE/RUNNING lozenge, with a pulsing dot |
| `activity_rule` | a rule that sweeps while something is running |
| `section` | accent tick, label, hairline out to the edge |
| `underline` / `label_underlined` | a rule matched to the word's own width |

Every widget takes a `key=` when the label is not unique. Widget identity
in ImGui comes from the label, and two controls sharing one in the same
window is a hard error rather than a cosmetic one.

## Cards

![Cards](docs/cards.png)

`widgets.section` draws a label and a rule floating in the gaps *between*
things, which reads as captions around boxes. A card reads as an instrument
with a name on it.

| style | |
|---|---|
| `raised` | gradient fill, border, a hairline of light inside the top edge, drop shadow |
| `plated` | flat fill, border, accent rule along the top |
| `outlined` | border only — whatever is behind shows straight through |
| `flat` | fill only, no edges |

Four genuinely different grounds rather than four names for one: the choice
decides whether a card has a fill at all, and so how much of a `backdrop`
or `effects` pass comes through the interface.

```python
cards.set_style("raised", shadow=True)

with cards.card("connection", icon="bolt", right="online",
                right_col=t.ok, edge=t.ok) as c:
    imgui.text("10.0.0.4:8080")
    cards.meter(dl, x, x + c.width, y, 0.72, t.ok)
```

The card sizes itself to its content. A background cannot be drawn until
the height is known, and in immediate mode that is not until the content
has been drawn — so the draw list is **split in two**: content goes on the
front channel, the plate is drawn on the back one afterwards, and merging
puts them in the right order. No measuring pass, no height passed in, and
no drift when a label changes length.

`edge` colours the accent rule along the top, so a panel says what it is
doing from the corner of your eye.

**Rounded gradients.** ImGui's own multi-colour rect is square-cornered, so
the first attempt at this concluded it was impossible. It is not: draw the
rounded fill normally, then re-colour the vertices it just emitted with
`ShadeVertsLinearColorGradientKeepAlpha`. `KeepAlpha` is the part that
matters — it lerps RGB along an axis and leaves each vertex's alpha alone,
so the anti-aliased corner fringe keeps its coverage and picks up the
gradient with everything else.

**Shadows** are three stacked rounded rects, each fainter and larger —
cheaper than a blur and, at this size, indistinguishable from one.

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

## Backdrop

![Scenes](docs/scenes.png)

![A scene under an interface](docs/hero.png)

A fragment shader over a fullscreen triangle, rendered to its own
framebuffer and blitted beneath the entire interface. This is the one thing
the draw list cannot do: a particle costs a draw call each, so that tops out
at a few hundred dots, while anything continuous — a gradient that moves,
cloud, a horizon, light that pools — is per-pixel work.

Six scenes, all tinted from your accent colour: `aurora`, `plasma`, `flow`,
`nebula`, `grid`, `warp`.

```python
bd = backdrop.Backdrop("flow", intensity=0.6)
def gui():
    bd.draw()            # first thing in the frame
    ...
```

- **One program, not six.** Scenes branch on a uniform, so switching is not
  a recompile and a settings panel can flick between them live.
- **Half resolution on each axis** — a quarter of the pixels. Every scene
  is soft by construction and nothing in them survives close inspection.
- **Vignetted, always.** The panels sit in the middle and the backdrop has
  no business competing with them for contrast there.
- **Opaque.** It composites the theme background itself rather than
  blending over the window fill, which keeps one guess out of the colour
  maths — so it must be drawn *before* any content.
- **Fails once, then stops.** A backdrop is decoration; it does not get to
  throw from the frame loop sixty times a second. `Backdrop.error` says
  what went wrong, and `active` goes False.
- **Puts the context back.** Framebuffer, viewport, program and the depth
  and blend enables are all restored. Leaving the viewport at half
  resolution is invisible here — ImGui's backend sets its own before it
  draws — and breaks the next renderer to share the context, which is
  exactly the kind of bug that gets blamed on that renderer.

Needs PyOpenGL: `pip install vertexui[backdrop]`. Without it, `active` is
False and `draw()` is a no-op.

## Particle effects

![Effects](docs/effects.png)

Ten of them: `fireflies`, `starfield`, `constellation`, `rain`, `sakura`,
`sparkles`, `bubbles`, `embers`, `orbits`, `dust`.

- `embers` rise, wander and flicker, dimming as they climb.
- `dust` runs three depths at different speeds — parallax is the whole
  trick, and identical motes at one speed read as noise.
- `orbits` has no integration at all: position is a closed form of the
  clock, so it cannot drift out of shape however long it runs.

**Paint it twice from one simulation** — once behind the content and once
over it at a fraction of the alpha. Behind only, the effect shows in the
gaps between panels and nowhere else, which on a dense screen is a thin
border of weather around an interface that does not participate in it.
Painted again over the top, it drifts across the cards and reads as one
atmosphere.

```python
moving = fx.step(now, dt)
if moving:
    fx.paint(dl, 0, 0, w, h, now, 1.0)      # behind
... draw your panels ...
if moving:
    fx.paint(dl, 0, 0, w, h, now, 0.42)     # and over the top
```

`step()` and `paint()` are separate precisely so that painting twice does
not advance the motion twice. The over-pass goes on the window's own list
after the content, so it sits above everything drawn that frame but still
below popups — a modal has to stay readable.

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

Four named sets, and `SETS` is a plain dict you can add to:

| set | |
|---|---|
| `soft taps` | low tonal knocks — the default |
| `breeze` | filtered noise, no attack to flinch at |
| `crisp` | brighter and shorter |
| `custom .wav` | your own files, per cue |

```python
sound.install("breeze", volume=0.16)
```

**`breeze` is noise, not tone.** A band of filtered noise steered by
overlap-add FFT under a long raised-cosine envelope reads as breath rather
than as a knock — right for something open beside you for nine hours, where
a tonal cue is a small tap on the shoulder every time. Identity comes from
where the band sits and which way it sweeps, plus a quiet sine underneath
so each cue has a pitch you can name.

**`custom .wav`** reads `<cue>.wav` from `%APPDATA%/<app>/sounds`, **per
cue** rather than all-or-nothing — replacing just the click and leaving the
rest synthesised is the common case, and a set that stayed silent until all
seven files existed would be useless for it. `export()` writes the
synthesised cues out as real files to replace, because hearing the shape
you are replacing is most of knowing what to record. A file that is not
really a WAV is reported on the set's `bad` dict, not raised — it must not
take the interface silent.

Seven cues: `hover`, `click`, `ok`, `warn`, `error`, `toast_in`,
`toast_out`.

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

`on_event("in"|"out", kind, text)` fires when a toast appears and when it
starts sliding away, which is what arrival and departure cues hang off. It
runs on the toast thread and is guarded — a callback that raises would
otherwise stop the overlay repainting and strand the frame it was drawing.

```python
tray = toasts.Toasts(on_event=lambda phase, kind, text:
                     sound.play("toast_in" if phase == "in" else "toast_out"))
```

A third trap, also silent: **clearing a layered window by blitting a
transparent surface is not reliable.** On some compositors
`UpdateLayeredWindow` with an all-zero bitmap leaves the previous frame
painted, which strands a toast on the desktop until the process dies. The
window is hidden outright when the list empties instead, which nothing
ignores.

`exclude_from_capture=True` (the default) hides the window from screen
capture, so an app that reads the screen never photographs its own
notifications. On a few graphics configurations that flag stops the window
drawing entirely — hence the switch, and `on_status` to report which.

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

## Where this came from

Most of 1.4 is not new invention. Ten applications built on this toolkit
were scanned for what they had to write themselves, and the duplication
decided the priorities:

| built independently by | |
|---|---|
| 6 projects | `notices.note` |
| 3 projects | sparkline, ring, line chart, own icon pack, duration formatting, a `u32` colour helper |
| 2 projects | modal/dialog, scrim, progress meter |
| 1 project, ~1,600 lines | table, inputs, switch, segmented, empty state, in-window toasts, UI zoom |

The icon set went from 16 to 46 for the same reason — three packs
overlapped on `trash`, `download`, `cube`, `upload`, `plus`/`minus`, `eye`,
`pencil`, `sort_up`/`sort_down`, `gauge` and `terminal`. `icons.register()`
is there so the next project extends the set instead of forking it.

## Install

```bash
pip install git+https://github.com/D4ead3ye/vertexui
```

Or drop the `vertexui/` folder into your project and import it — there is
nothing to build and no data files to find at runtime, which is also what
makes it survive PyInstaller without a `--add-data` line.

## Requirements

`imgui-bundle` and `numpy`. `opencv-python` for `toasts`, `PyOpenGL` for
`backdrop` — `pip install vertexui[all]` for both.

`toasts` and `sound` are Windows-only (layered windows and `winsound`);
`theme`, `anim`, `fonts`, `icons`, `widgets`, `cards`, `effects`,
`backdrop` and `logview` are cross-platform.

`toasts`, `effects`, `backdrop` and `graphics` are imported on first touch
rather than up front, so a project that wants none of them pays for none of
them.

Every module degrades rather than raising: a missing font role renders in
the default face, an unknown icon draws nothing, and a machine with no
audio device disables sounds after reporting why.

## Contributing

Issues and pull requests welcome. [`CLAUDE.md`](CLAUDE.md) is the working
brief this repo is built to — four rules, of which the load-bearing one is
that **layout belongs to the profile, never to a module**. A panel that
knows it lives under a tab strip has made every other layout impossible.

Conventions worth knowing before you open a PR:

* **colour names are semantic.** `accent`, `surface`, `danger` — never
  `red` or `dark_grey`. A palette named after what the colours *are* stops
  making sense the moment somebody swaps them.
* **nothing raises from a draw call.** A frame that throws takes the whole
  window down, so unknown icons, missing fonts and absent audio devices all
  degrade quietly instead.
* **never assume a dark ground.** Use `theme.ink`, `theme.lift`,
  `theme.sink` and `theme.is_light`. `profiles.PAPER` is light and has to
  keep working.
* **this binding's draw-list argument order is not the C++ order:**
  `add_rect(p_min, p_max, col, rounding, thickness, flags)`,
  `add_polyline(points, col, thickness, flags)` with no defaults, and
  `path_stroke(col, thickness, flags)`. Both of the bugs this repo has
  shipped and fixed were this.

Every feature ships with **two contrasting examples**, because one shows
that a thing runs and two opposed ones show that it is actually modular:

| | |
|---|---|
| `examples/profiler.py` | dense, data-rich — sparklines, heatmap, histogram, shared plot |
| `examples/tuner.py` | the opposite — one number, no navigation, nothing else |
| `examples/watchtower.py` | **identical modules under every profile** — `--profile paper`, `--hud` |
| `examples/ledger.py` | 4,000-row table, search, chips, dialogs, banner, split aside |
| `examples/intake.py` | the opposite — one form, one screen, zoomed up |
| `examples/steelball.py` | a themed race board; `--profile noir` strips it back to stock |
| `examples/cyberdeck.py` | a Y2K system monitor built out of floating windows |

![Ledger and intake](docs/ledger.png)

The same six modules, on the same day: a light records tool and a zoomed
single-purpose form.

![Intake](docs/intake.png)
| `examples/minimal.py` | twelve lines |
| `examples/ambience.py` | backdrop, particles and cards together |
| `examples/notifications.py` | the toast overlay on its own |

`python tools/smoke.py` draws every screen in every state — each tab, each
card style, each effect, with the cursor swept over a grid — and fails if
any frame raises. It exists because a wrong argument order sits silent until
the one frame that hits it: `add_rect` in this binding takes
`(rounding, thickness, flags)` rather than the C++ order, and the resulting
`TypeError` only ever fired on a frame where a widget was hovered.
`python tools/matrix.py tile` regenerates `docs/profiles.png` — the
falsifiable version of the profile claim. If those seven tiles ever start
looking like one program in seven colours, the README is wrong and the
code needs fixing.

`python tools/shots.py` regenerates every still in `docs/`, and
`python tools/spotlight.py` re-records the looping clip at the top — it
records and encodes as separate stages, so re-encoding to tune the palette
does not mean driving the demo again.

## Licence

MIT — see [LICENSE](LICENSE).
