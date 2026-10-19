"""Minimal: a single-form kiosk, on the MINIMAL profile.

    python examples/intake.py

The same modules as `ledger.py` doing the opposite job. No table, no
navigation, no density: one centred column, large controls, and one
question at a time. The UI zoom is turned up, which is the thing
`text_scale` alone cannot do - the controls grow with the type instead of
the type outgrowing its box.

What this is really demonstrating is that `inputs`, `notices` and
`dialogs` do not assume the shape of the screen they are on.
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from imgui_bundle import ImVec2, imgui                   # noqa: E402

import vertexui as vui                                   # noqa: E402
from vertexui import (compose, dialogs, fmt, fonts, inputs, notices,
                      profiles, widgets)                 # noqa: E402
from vertexui import theme as theme_mod                  # noqa: E402


@dataclass
class Form:
    name: str = ""
    reference: str = ""
    crate: int = 1
    priority: int = 1
    fragile: bool = False
    notes: str = ""
    submitted: list = field(default_factory=list)

    def problems(self):
        out = {}
        if len(self.name.strip()) < 2:
            out["name"] = "Who is this delivery from?"
        if self.reference and not self.reference.upper().startswith("PO-"):
            out["reference"] = "A reference looks like PO-1234."
        return out


class Intake(compose.Module):
    name = "intake"

    def __init__(self):
        self.f = Form()
        self.tray = notices.Tray(corner="tr", width=280)
        self.touched = set()

    def setup(self, app):
        app.page("intake", draw=self.draw)
        app.slot("status", self.status)
        dialogs.register("intake-confirm", self.confirm_dialog)

    def status(self, app):
        t = theme_mod.current()
        with fonts.use("label"):
            imgui.text_colored(
                t.text_mute, f"{len(self.f.submitted)} RECEIVED TODAY")

    def confirm_dialog(self, data):
        t = theme_mod.current()
        f = self.f
        with dialogs.modal("intake-confirm", "Book this in?", icon="check") as ok:
            if not ok:
                return
            for label, value in (("From", f.name),
                                 ("Reference", f.reference or "none"),
                                 ("Crates", str(f.crate)),
                                 ("Priority", ["low", "normal", "urgent"][f.priority]),
                                 ("Fragile", "yes" if f.fragile else "no")):
                imgui.text_colored(t.text_mute, label)
                imgui.same_line(0, 10)
                imgui.text_colored(t.text, value)
            if f.fragile:
                imgui.dummy(ImVec2(0, 6))
                notices.note("Fragile crates are routed to the inspection "
                             "bay before they reach the floor.",
                             tone=t.warn, icon="warning")
            yes, _no = dialogs.buttons("Book in", "Back")
            if yes:
                self.f.submitted.append(f.name)
                self.tray.push("ok", f"{f.name} booked in")
                self.f = Form(submitted=f.submitted)
                self.touched.clear()

    def draw(self, app):
        t = theme_mod.current()
        f = self.f
        bad = f.problems()

        with fonts.use("huge"):
            imgui.text_colored(t.text, "Goods in")
        imgui.text_colored(t.text_mute,
                           "One delivery at a time. Nothing here is saved "
                           "until you book it in.")
        imgui.dummy(ImVec2(0, 14))

        changed, f.name = inputs.text_input("name", f.name, label="From",
                                            hint="Supplier or courier")
        if changed:
            self.touched.add("name")
        if "name" in bad and "name" in self.touched:
            notices.note(bad["name"], tone=t.danger, icon="warning")

        imgui.dummy(ImVec2(0, 8))
        changed, f.reference = inputs.text_input(
            "ref", f.reference, label="Reference", hint="PO-1234 (optional)")
        if changed:
            self.touched.add("reference")
        if "reference" in bad:
            notices.note(bad["reference"], tone=t.warn, icon="info")

        imgui.dummy(ImVec2(0, 12))
        inputs.field_label("Crates")
        f.crate = inputs.stepper("crates", f.crate, lo=1, hi=99, width=170)

        imgui.dummy(ImVec2(0, 12))
        inputs.field_label("Priority")
        f.priority = inputs.segmented("prio", ["Low", "Normal", "Urgent"],
                                      f.priority, height=34)

        imgui.dummy(ImVec2(0, 14))
        f.fragile = inputs.switch("Fragile - handle separately", f.fragile)

        imgui.dummy(ImVec2(0, 10))
        changed, f.notes = inputs.text_input("notes", f.notes, height=64,
                                             label="Notes",
                                             hint="Anything the floor should know")

        imgui.dummy(ImVec2(0, 16))
        ready = not bad
        if widgets.button("Book in", 190, height=40.0, primary=True,
                          icon="check", enabled=ready, key="submit"):
            dialogs.open("intake-confirm")
        imgui.same_line(0, 10)
        if widgets.button("Clear", 130, height=40.0, key="clear"):
            if f.name or f.reference or f.notes:
                dialogs.confirm("Discard this delivery?",
                                on_yes=self.reset,
                                body="Nothing has been booked in yet.",
                                kind="warn", yes="Discard")
            else:
                self.reset()
        if not ready:
            imgui.dummy(ImVec2(0, 8))
            notices.note("Fill in who the delivery is from before booking it in.",
                         icon="info")
        self.tray.draw()

    def reset(self):
        self.f = Form(submitted=self.f.submitted)
        self.touched.clear()


def main():
    # Zoom up: this is a screen read standing up, at arm's length.
    profile = profiles.MINIMAL.variant(name="kiosk", layout="stage")
    app = compose.App(profile=profile, title="goods in",
                      app_id="vertexui-intake", size=(720, 860))
    app.use(Intake())
    app.hook("setup", lambda a: setattr(
        a.profile, "theme", a.profile.theme.scaled(ui=1.15)))
    app.hook("frame_end", lambda a: dialogs.draw())
    app.run()


if __name__ == "__main__":
    main()
