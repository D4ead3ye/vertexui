"""Data-rich: a records tool, on the PAPER profile.

    python examples/ledger.py
    python examples/ledger.py --profile instrument

Exercises the parts a tool that holds records needs and a dashboard does
not: a sortable, selectable, clipped table over 4,000 rows; a search
field; chips as filters; a confirm dialog that is opened from inside a
table row and drawn somewhere else entirely; a banner; an empty state
when a filter matches nothing; and an in-window message tray.

Contrast with `intake.py`, which is the same modules asked to do one
thing on one screen.
"""

import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from imgui_bundle import ImVec2, imgui                   # noqa: E402

import vertexui as vui                                   # noqa: E402
from vertexui import (compose, dialogs, fmt, fonts, graphics, i18n, inputs,
                      notices, profiles, table, widgets)  # noqa: E402
from vertexui import theme as theme_mod                  # noqa: E402

SUPPLIERS = ["Northwind", "Açaí do Vale", "Beira Têxtil", "Köhler GmbH",
             "Sun Fabrics", "Oliveira & Filhos", "Tri-State Paper"]
STATES = ["open", "paid", "late", "draft"]
TONE = {"open": "info", "paid": "ok", "late": "error", "draft": "warn"}

i18n.load("en", {
    "orders": "Orders", "search": "Search suppliers", "total": "Total",
    "due": "Due", "state": "State", "supplier": "Supplier", "ref": "Ref",
    "selected": "{n} selected", "delete": "Delete", "none.title": "Nothing matches",
    "none.body": "No order matches the filters you have set. Clear them to "
                 "see the whole ledger again.", "clear": "Clear filters",
})
i18n.load("pt", {
    "orders": "Pedidos", "search": "Buscar fornecedores", "total": "Total",
    "due": "Vencimento", "state": "Situação", "supplier": "Fornecedor",
    "ref": "Ref", "selected": "{n} selecionados", "delete": "Excluir",
    "none.title": "Nada encontrado",
    "none.body": "Nenhum pedido corresponde aos filtros. Limpe-os para ver "
                 "o livro inteiro novamente.", "clear": "Limpar filtros",
})


def make_rows(n=4000):
    rng = random.Random(7)
    now = time.time()
    return [{"id": i, "ref": f"PO-{4000 + i}",
             "supplier": rng.choice(SUPPLIERS),
             "state": rng.choice(STATES),
             "due": now + rng.uniform(-20, 40) * 86400,
             "total": round(rng.uniform(40, 9000), 2)} for i in range(n)]


class Ledger(compose.Module):
    name = "ledger"

    def __init__(self):
        self.all = make_rows()
        self.state = table.State(sort="due")
        self.query = ""
        self.filters = {s: True for s in STATES}
        self.tray = notices.Tray(corner="tr")
        self.banner_open = True
        self.lang = 0
        self.cols = None

    def setup(self, app):
        app.page("orders", "Orders", icon="list", draw=self.draw)
        app.slot("status", self.status)
        dialogs.register("ledger-delete", self.delete_dialog)

    # -- data ----------------------------------------------------------
    def visible(self):
        q = self.query.lower().strip()
        rows = [r for r in self.all if self.filters.get(r["state"], True)]
        if q:
            rows = [r for r in rows
                    if q in r["supplier"].lower() or q in r["ref"].lower()]
        return self.state.sort_rows(rows)

    def status(self, app):
        t = theme_mod.current()
        n = len(self.state.selected)
        if n:
            imgui.text_colored(t.accent, i18n.t("selected", n=n))
        else:
            imgui.text_colored(t.text_mute, fmt.plural(len(self.all), "order"))

    # -- dialog, opened from a row and drawn here ----------------------
    def delete_dialog(self, data):
        t = theme_mod.current()
        with dialogs.modal("ledger-delete", i18n.t("delete"), kind="error") as ok:
            if not ok:
                return
            imgui.text_colored(
                t.text_dim, f"{fmt.plural(len(data['ids']), 'order')} "
                            f"will be removed. This cannot be undone.")
            imgui.dummy(ImVec2(0, 6))
            yes, _no = dialogs.buttons(i18n.t("delete"), kind="danger")
            if yes:
                gone = data["ids"]
                self.all = [r for r in self.all if r["id"] not in gone]
                self.state.clear()
                self.tray.push("ok", fmt.plural(len(gone), "order") + " deleted")

    # -- drawing -------------------------------------------------------
    def draw(self, app):
        t = theme_mod.current()
        if self.cols is None or True:
            self.cols = [
                table.Col("ref", i18n.t("ref"), 110),
                table.Col("supplier", i18n.t("supplier")),
                table.Col("state", i18n.t("state"), 110, align="c"),
                table.Col("due", i18n.t("due"), 150, align="r"),
                table.Col("total", i18n.t("total"), 130, align="r"),
            ]
        if self.banner_open:
            def close():
                self.banner_open = False
            notices.banner("This ledger is generated sample data.", "warn",
                           action=("Reload", lambda: self.tray.push(
                               "info", "Sample data regenerated")),
                           on_close=close)

        changed, self.query = inputs.search_input(
            "q", self.query, hint=i18n.t("search"), width=280)
        imgui.same_line(0, 14)
        for s in STATES:
            self.filters[s] = inputs.chip(s, TONE[s], on=self.filters[s],
                                          key=f"f:{s}")
            imgui.same_line(0, 6)
        imgui.same_line(0, 16)
        lang = inputs.segmented("lang", ["EN", "PT"], self.lang, height=26)
        if lang != self.lang:
            self.lang = lang
            i18n.use(["en", "pt"][lang])

        rows = self.visible()
        sel = sorted(self.state.selected)
        if sel:
            imgui.same_line(0, 16)
            if widgets.button(i18n.t("delete"), 120, height=26.0, icon="trash",
                              key="del"):
                dialogs.open("ledger-delete", ids=set(sel))

        imgui.dummy(ImVec2(0, 6))
        if not rows:
            notices.empty_state("search", i18n.t("none.title"),
                                i18n.t("none.body"),
                                actions=[(i18n.t("clear"), self.clear, True)])
            self.tray.draw()
            return

        ids = [r["id"] for r in rows]
        with table.table("orders", self.cols, height=0) as open_:
            if open_:
                table.header(self.cols, self.state, ids=ids)
                for i, r in table.rows(rows, self.state):
                    selected = r["id"] in self.state.selected
                    hovered, clicked = table.row_begin(r["id"], selected)
                    if clicked:
                        self.state.toggle(r["id"])
                    table.cell(r["ref"], role="mono",
                               colour=t.text_mute, column=0)
                    table.cell(r["supplier"], column=1)
                    table.cell(r["state"], align="c", column=2,
                               colour=t.status(TONE[r["state"]]))
                    late = r["due"] < time.time()
                    table.cell(fmt.ago(r["due"]) if late
                               else fmt.duration(r["due"] - time.time(), 1),
                               align="r", column=3,
                               colour=t.danger if late else t.text_dim)
                    table.cell(f"{r['total']:,.2f}", align="r", role="mono",
                               column=4)
        self.tray.draw()

    def clear(self):
        self.query = ""
        self.filters = {s: True for s in STATES}


class Summary(compose.Module):
    """Fills the `aside` slot - which only a layout with room will draw."""

    name = "summary"

    def __init__(self, ledger):
        self.l = ledger

    def setup(self, app):
        app.slot("aside", self.draw)

    def draw(self, app):
        t = theme_mod.current()
        widgets.section("by state")
        counts = [sum(1 for r in self.l.all if r["state"] == s) for s in STATES]
        graphics.bars(counts, 0, 90, labels=STATES, tooltip=True,
                      value_fmt=lambda v: fmt.plural(int(v), "order"))
        for s, n in zip(STATES, counts):
            widgets.badge(f"{s} {n}", TONE[s])
            imgui.same_line()
        imgui.new_line()
        imgui.dummy(ImVec2(0, 8))
        widgets.section("value due, by week")
        now = time.time()
        weeks = [0.0] * 8
        for r in self.l.all:
            k = int((r["due"] - now) / (7 * 86400)) + 2
            if 0 <= k < 8:
                weeks[k] += r["total"]
        graphics.plot({"due": weeks}, 0, 120, fill=True, tooltip=True,
                      value_fmt=lambda v: fmt.count(v),
                      x_labels=[f"week {i - 2:+d}" for i in range(8)])


def main(argv):
    name = "paper"
    if "--profile" in argv:
        name = argv[argv.index("--profile") + 1]
    led = Ledger()
    app = compose.App(profile=profiles.get(name), title="ledger",
                      app_id="vertexui-ledger", size=(1180, 720))
    app.use(led, Summary(led))
    app.hook("frame_end", lambda a: dialogs.draw())
    app.run()


if __name__ == "__main__":
    main(sys.argv[1:])
