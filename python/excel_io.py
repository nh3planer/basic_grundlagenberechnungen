"""Import/Export der Excel-Kostenliste (POS, SUM_Entwurf, KG_NR, drop)."""
from __future__ import annotations

import re
from pathlib import Path

from openpyxl import Workbook, load_workbook

from model import Group, Project, Position, VARIANT_KEYS


def _num(v):
    if v is None or v == "" or v == "-":
        return None
    try:
        f = float(v)
        return f
    except (TypeError, ValueError):
        return None


def _str(v) -> str:
    return "" if v is None else str(v).strip()


def _ja(v) -> bool:
    return _str(v).lower() == "ja"


def import_excel(pfad: str | Path) -> dict:
    """Liest die bestehende Excel-Liste ein und gibt Projekt-Ersatzdaten zurück."""
    pfad = Path(pfad)
    wb_werte = load_workbook(pfad, data_only=True)
    wb_formeln = load_workbook(pfad, data_only=False)
    ergebnis: dict = {}

    # --- POS ---------------------------------------------------------------
    if "POS" in wb_werte:
        ws = wb_werte["POS"]
        wf = wb_formeln["POS"]
        positionen: list[Position] = []
        for r in range(9, ws.max_row + 1):
            nr_zelle = ws.cell(row=r, column=4).value
            if isinstance(nr_zelle, str) and nr_zelle.strip():
                continue  # SUMME / Nebenrechnung / Textzeilen
            nr = _num(nr_zelle)
            benennung = _str(ws.cell(row=r, column=7).value)
            bedarf = _num(ws.cell(row=r, column=12).value)
            belastung = _num(ws.cell(row=r, column=13).value)
            spez = _num(ws.cell(row=r, column=15).value)
            manuell = _num(ws.cell(row=r, column=16).value)
            anz = _num(ws.cell(row=r, column=18).value)
            if nr is None and not benennung:
                continue
            if benennung == "" and bedarf is None and belastung is None and spez is None \
                    and manuell is None and anz is None:
                continue
            pos = Position(
                benennung=benennung,
                nr=int(nr) if nr is not None else 1,
                ebene=int(_num(ws.cell(row=r, column=5).value) or 1),
                unternr=int(_num(ws.cell(row=r, column=6).value) or 0),
                t1=_str(ws.cell(row=r, column=9).value),
                t2=_str(ws.cell(row=r, column=11).value),
                bedarf=bedarf,
                max_belastung=belastung,
                ep_basis="belastung",
                einheit=_str(ws.cell(row=r, column=14).value),
                ep_spezifisch=spez,
                ep_manuell=manuell,
                anz=anz,
                kg=int(_num(ws.cell(row=r, column=20).value) or 0) or None,
                bt=_str(ws.cell(row=r, column=22).value),
                bemerkung=_str(ws.cell(row=r, column=23).value),
                flags={
                    "basis": _ja(ws.cell(row=r, column=24).value),
                    "var1": _ja(ws.cell(row=r, column=25).value),
                    "var2": _ja(ws.cell(row=r, column=26).value),
                    "var3": _ja(ws.cell(row=r, column=27).value),
                    "var4": _ja(ws.cell(row=r, column=28).value),
                },
            )
            q_formel = wf.cell(row=r, column=17).value  # Spalte Q = EP
            if isinstance(q_formel, str) and re.search(r"L\d+\s*\*\s*O\d+", q_formel):
                pos.ep_basis = "bedarf"
            elif not isinstance(q_formel, str):
                q_wert = _num(ws.cell(row=r, column=17).value)
                if q_wert is not None:
                    pos.ep_manuell = q_wert
            positionen.append(pos)
        ergebnis["positionen"] = positionen

    # --- SUM_Entwurf ---------------------------------------------------------
    if "SUM_Entwurf" in wb_werte:
        ws = wb_werte["SUM_Entwurf"]
        gruppen: list[Group] = []
        for r in range(8, ws.max_row + 1):
            bt = _str(ws.cell(row=r, column=3).value)
            beschreibung = _str(ws.cell(row=r, column=4).value)
            if not beschreibung or (bt == "-" and beschreibung == "GESAMT"):
                continue
            gruppen.append(
                Group(
                    bt=bt,
                    beschreibung=beschreibung,
                    entwurf=_str(ws.cell(row=r, column=5).value),
                    beruecksichtigt=_ja(ws.cell(row=r, column=15).value),
                )
            )
        ergebnis["gruppen"] = gruppen
        projekt = _str(ws.cell(row=1, column=15).value)
        if projekt:
            ergebnis["projekt"] = projekt
        bearbeiter_stand = _str(ws.cell(row=2, column=17).value)
        if "/" in bearbeiter_stand:
            b, s = bearbeiter_stand.split("/", 1)
            ergebnis["bearbeiter"] = b.strip()
            ergebnis["stand"] = s.strip()

    # --- KG_NR ---------------------------------------------------------------
    if "KG_NR" in wb_werte:
        ws = wb_werte["KG_NR"]
        kg: list[dict] = []
        gesehen: set[int] = set()
        for r in range(1, ws.max_row + 1):
            nr = _num(ws.cell(row=r, column=2).value)
            name = _str(ws.cell(row=r, column=3).value)
            if nr is None or not name or int(nr) in gesehen:
                continue
            gesehen.add(int(nr))
            kg.append({"nr": int(nr), "name": name})
        ergebnis["kostengruppen"] = kg

    # --- drop ---------------------------------------------------------------
    if "drop" in wb_werte:
        ws = wb_werte["drop"]
        einheiten = [
            _str(ws.cell(row=r, column=1).value)
            for r in range(4, ws.max_row + 1)
            if _str(ws.cell(row=r, column=1).value)
        ]
        if einheiten:
            ergebnis["einheiten"] = einheiten

    return ergebnis


def export_excel(project: Project, pfad: str | Path) -> None:
    from calc import ep, gp, runden

    wb = Workbook()
    sum_ws = wb.active
    sum_ws.title = "SUM_Entwurf"
    sum_ws["A1"] = project.firma
    sum_ws["A2"] = project.adresse
    sum_ws["A4"] = "Projekt"
    sum_ws["B4"] = project.projekt
    sum_ws["A5"] = "Bearbeiter / Stand"
    sum_ws["B5"] = f"{project.bearbeiter} / {project.stand}"
    kopf = ["BT", "Beschreibung"] + [v.upper() for v in VARIANT_KEYS] + ["berücksichtigt"]
    sum_ws.append([])
    sum_ws.append(kopf)
    from calc import gruppen_summen, total_summen

    for eintrag in gruppen_summen(project):
        g = eintrag["gruppe"]
        sum_ws.append(
            [g.bt, g.beschreibung]
            + [round(eintrag["summen"][v]) for v in VARIANT_KEYS]
            + ["ja" if g.beruecksichtigt else "nein"]
        )
    totals = total_summen(project)
    sum_ws.append(["-", "GESAMT"] + [round(totals[v]) for v in VARIANT_KEYS] + [""])
    for breite, spalte in zip([6, 42, 14, 14, 14, 14, 14, 14], "ABCDEFGH"):
        sum_ws.column_dimensions[spalte].width = breite

    pos_ws = wb.create_sheet("POS")
    pos_ws.append(
        ["Nr", "Ebene", "Unternr", "Benennung", "T1", "T2", "Bedarf", "max. Belastung",
         "Basis", "Einheit", "EP spezifisch", "EP manuell", "EP", "Anzahl", "GP",
         "KG", "BT", "Bemerkung"] + [v.upper() for v in VARIANT_KEYS]
    )
    for p in sorted(project.positionen, key=lambda x: (x.nr, x.ebene, x.unternr)):
        pos_ws.append(
            [p.nr, p.ebene, p.unternr, p.benennung, p.t1, p.t2, p.bedarf, p.max_belastung,
             "L" if p.ep_basis == "bedarf" else "M", p.einheit, p.ep_spezifisch, p.ep_manuell,
             runden(ep(p), 0) or None, p.anz, gp(p) or None, p.kg, p.bt, p.bemerkung]
            + ["ja" if p.flags.get(v) else "nein" for v in VARIANT_KEYS]
        )
    for spalte, breite in zip(
        "ABCDEFGHIJKLMNOPQRSTUV",
        [5, 6, 7, 42, 10, 8, 10, 12, 6, 9, 12, 12, 12, 8, 12, 7, 6, 30, 8, 8, 8, 8],
    ):
        pos_ws.column_dimensions[spalte].width = breite

    if project.kostengruppen:
        kg_ws = wb.create_sheet("KG_NR")
        kg_ws.append(["KG Nr.", "Kostengruppe lt. DIN 276 - 2018"])
        for k in project.kostengruppen:
            kg_ws.append([k["nr"], k["name"]])

    drop_ws = wb.create_sheet("drop")
    drop_ws.append(["Einheit"])
    for e in project.einheiten:
        drop_ws.append([e])

    wb.save(pfad)
