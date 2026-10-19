"""Composition: slots, modules, pages, hooks and a connector bus.

The toolkit's first version shipped one shape of application - a title, a
tab strip, sections down a page - and every project built on it came out
looking like the same program wearing a different accent colour. The
colours were never the problem. One layout idiom was.

So nothing here draws anything. A module says *what* it contributes:

    class Rates(compose.Module):
        name = "rates"

        def setup(self, app):
            app.page("rates", "Rates", icon="bolt", draw=self.body)
            app.slot("status", self.status)
            app.bus.on("tick", self.on_tick)

        def body(self, app): ...
        def status(self, app): ...

and a `Layout` - picked by the profile, not by the module - decides
whether that page becomes a tab, an icon in a rail, a line in a command
palette, or nothing at all because this layout has no navigation. Swap the
profile and the same modules come out as a different program.

    app = compose.App(profile=profiles.INSTRUMENT)
    app.use(Rates(), Alerts())
    app.run()

Three ways modules reconfigure without knowing about each other:

    slots    named regions - "chrome", "nav", "body", "aside", "status",
             "overlay". A layout draws the ones it has room for and
             ignores the rest, which is how one module set survives a
             layout with no sidebar.
    hooks    "setup", "frame_begin", "frame_end", "teardown" - for work
             that is not drawing.
    bus      publish/subscribe by name. A module emits "job.done" without
             knowing whether anything is listening, and a notifier listens
             without importing the thing that emits.
"""

from dataclasses import dataclass, field

SLOTS = ("chrome", "nav", "body", "aside", "status", "overlay")


class Bus:
    """Dynamic connector. Topics are strings; nothing imports anything."""

    def __init__(self):
        self._subs = {}

    def on(self, topic, fn):
        self._subs.setdefault(topic, []).append(fn)
        return fn

    def off(self, topic, fn=None):
        if fn is None:
            self._subs.pop(topic, None)
        elif topic in self._subs and fn in self._subs[topic]:
            self._subs[topic].remove(fn)

    def emit(self, topic, *args, **kw):
        """Deliver to every subscriber. Returns how many ran.

        A subscriber that raises is reported and skipped rather than
        allowed to take the frame - one module's bad afternoon is not the
        rest of the application's.
        """
        n = 0
        for fn in list(self._subs.get(topic, ())):
            try:
                fn(*args, **kw)
                n += 1
            except Exception as exc:
                print(f"[vertexui] subscriber for {topic!r} raised: {exc!r}")
        return n

    def topics(self):
        return sorted(k for k, v in self._subs.items() if v)


@dataclass
class Page:
    """One view. What a layout *does* with it is the layout's business."""
    key: str
    label: str = ""
    icon: str = ""
    draw: object = None
    badge: str = ""              # a count or state a nav may choose to show
    order: int = 0

    def __post_init__(self):
        self.label = self.label or self.key.replace("_", " ").title()


class Module:
    """A unit of interface and behaviour.

    Subclass and override `setup` to register pages, slots, hooks and bus
    subscriptions. Everything else is optional.
    """

    name = ""

    def setup(self, app):
        """Register what this module contributes."""

    def frame(self, app):
        """Per-frame work that is not drawing - polling, decay, timers."""

    def teardown(self, app):
        """Release anything held. Called in reverse order of `use`."""


class _Slots:
    def __init__(self):
        self._by_name = {}

    def add(self, name, fn, order=0):
        self._by_name.setdefault(name, []).append((order, fn))
        self._by_name[name].sort(key=lambda p: p[0])

    def has(self, name):
        return bool(self._by_name.get(name))

    def draw(self, name, app):
        """Draw everything in a slot. Returns True if anything ran."""
        entries = self._by_name.get(name)
        if not entries:
            return False
        for _, fn in entries:
            fn(app)
        return True

    def names(self):
        return sorted(k for k, v in self._by_name.items() if v)


class App:
    """The shell. Owns the profile, the modules, and the frame."""

    def __init__(self, profile=None, title="VertexUI", app_id="vertexui",
                 size=(1040, 700)):
        from . import profiles as profiles_mod
        self.profile = profile or profiles_mod.get("noir")
        self.title = title
        self.app_id = app_id
        self.size = size
        self.bus = Bus()
        self.slots = _Slots()
        self.modules = []
        self.pages = []
        self.page_key = None
        self.state = {}             # scratch space shared across modules
        self.hooks = {k: [] for k in
                      ("setup", "frame_begin", "frame_end", "teardown")}
        self._started = False

    # -- registration ----------------------------------------------------
    def use(self, *modules):
        """Add modules. Safe before or after setup."""
        for m in modules:
            self.modules.append(m)
            if self._started:
                m.setup(self)
        return self

    def slot(self, name, fn, order=0):
        self.slots.add(name, fn, order)
        return self

    def page(self, key, label="", icon="", draw=None, badge="", order=0):
        p = Page(key, label, icon, draw, badge, order)
        self.pages.append(p)
        self.pages.sort(key=lambda q: q.order)
        if self.page_key is None:
            self.page_key = p.key
        return p

    def hook(self, when, fn):
        self.hooks[when].append(fn)
        return fn

    # -- navigation ------------------------------------------------------
    @property
    def page_index(self):
        for i, p in enumerate(self.pages):
            if p.key == self.page_key:
                return i
        return 0

    def go(self, key):
        """Switch page by key or index. Emits "page" on the bus."""
        if isinstance(key, int):
            if not self.pages:
                return
            key = self.pages[max(0, min(len(self.pages) - 1, key))].key
        if key != self.page_key:
            self.page_key = key
            self.bus.emit("page", key)

    def current_page(self):
        for p in self.pages:
            if p.key == self.page_key:
                return p
        return self.pages[0] if self.pages else None

    # -- lifecycle -------------------------------------------------------
    def setup(self):
        if self._started:
            return self
        self.profile.apply(self.app_id)
        for m in self.modules:
            m.setup(self)
        for fn in self.hooks["setup"]:
            fn(self)
        self._started = True
        return self

    def frame(self):
        """One frame. Call from your gui() if you are driving the loop."""
        from . import end_frame
        for fn in self.hooks["frame_begin"]:
            fn(self)
        for m in self.modules:
            m.frame(self)
        self.profile.layout.draw(self)
        for fn in self.hooks["frame_end"]:
            fn(self)
        end_frame()

    def teardown(self):
        for fn in self.hooks["teardown"]:
            fn(self)
        for m in reversed(self.modules):
            m.teardown(self)
        self._started = False

    def run(self, full_screen=True):
        """Open a window and run until closed."""
        from imgui_bundle import hello_imgui

        from . import install
        self.setup()
        params = hello_imgui.RunnerParams()
        params.app_window_params.window_title = self.title
        params.app_window_params.window_geometry.size = self.size
        if full_screen:
            params.imgui_window_params.default_imgui_window_type = (
                hello_imgui.DefaultImGuiWindowType.provide_full_screen_window)
        params.callbacks.show_gui = self.frame
        install(params, theme_=self.profile.build_theme(),
                faces=self.profile.build_faces())
        hello_imgui.run(params)
        self.teardown()


def module(name=None, **slots):
    """Build a Module from loose callables, for a module too small to be a
    class:

        compose.module("clock", status=draw_clock, body=draw_face)
    """
    class _Loose(Module):
        pass

    _Loose.name = name or "module"

    def setup(self, app):
        for where, fn in slots.items():
            if where in SLOTS:
                app.slot(where, fn)
            else:
                app.page(where, draw=fn)

    _Loose.setup = setup
    return _Loose()
