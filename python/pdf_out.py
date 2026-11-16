"""PDF-Ausdruck mit EP-Bildmarke (A4 quer)."""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from model import Project, VARIANT_KEYS

STANDARD_LOGO = Path(__file__).with_name("ep-logo.png")

KOPFZEILE = colors.HexColor("#10233f")
AKZENT = colors.HexColor("#1a5fb4")


def _logo_pfad(project: Project) -> Path | None:
    if project.logo and Path(project.logo).exists():
        return Path(project.logo)
    if STANDARD_LOGO.exists():
        return STANDARD_LOGO
    return None


def _kopf(project: Project, titel: str, styles) -> list:
    story: list = []
    logo = _logo_pfad(project)
    daten = [
        [Paragraph(f"<b>{project.firma}</b>", styles["Small"]),
         Paragraph(f"<b>{titel}</b>", styles["SmallHead"]),
         Paragraph(f"<b>{project.projekt}</b>", styles["SmallRight"])],
        [Paragraph(project.adresse, styles["Small"]),
         Paragraph("", styles["Small"]),
         Paragraph(f"{project.bearbeiter} / {project.stand}", styles["SmallRight"])],
    ]
    breiten = [70 * mm, 60 * mm, 151 * mm]
    if logo:
        tabelle = Table(
            [[Image(str(logo), width=28 * mm, height=18 * mm, kind="proportional"), daten]],
            colWidths=[32 * mm, 281 * mm],
        )
        tabelle.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(tabelle)
    else:
        story.append(Table(daten, colWidths=breiten))
    story.append(Spacer(1, 4 * mm))
    story.append(_linie())
    story.append(Spacer(1, 4 * mm))
    return story


def _linie() -> Table:
    t = Table([[""]], colWidths=[313 * mm], rowHeights=[1.2])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), KOPFZEILE)]))
    return t


def _styles() -> dict:
    basis = getSampleStyleSheet()
    return {
        "Small": ParagraphStyle("Small", parent=basis["Normal"], fontSize=8, leading=10),
        "SmallHead": ParagraphStyle(
            "SmallHead", parent=basis["Normal"], fontSize=11, leading=13, textColor=KOPFZEILE
        ),
        "SmallRight": ParagraphStyle(
            "SmallRight", parent=basis["Normal"], fontSize=8, leading=10, alignment=2
        ),
        "Zelle": ParagraphStyle("Zelle", parent=basis["Normal"], fontSize=7, leading=8.5),
    }


def _tabelle(kopf: list[str], zeilen: list[list], breiten: list[float], styles) -> Table:
    daten = [kopf] + zeilen
    t = Table(daten, colWidths=breiten, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 0), (-1, 0), KOPFZEILE),
                ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f4f8")]),
                ("LINEBELOW", (0, 0), (-1, 0), 0.6, KOPFZEILE),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dde3ec")),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return t


def pdf_uebersicht(project: Project, pfad: str | Path) -> None:
    from calc import fmt_eur, gruppen_summen, total_summen

    styles = _styles()
    story = _kopf(project, "Kostenberechnung – Entwurf", styles)
    quelle = project.gesamt_quelle
    kopf = ["BT", "Beschreibung"] + [v.upper() for v in VARIANT_KEYS] + ["GESAMT"]
    zeilen = []
    for eintrag in gruppen_summen(project):
        g = eintrag["gruppe"]
        summen = eintrag["summen"]
        gesamt = fmt_eur(summen[quelle]) if g.beruecksichtigt else "–"
        zeilen.append(
            [g.bt, Paragraph(g.beschreibung, styles["Zelle"])]
            + [fmt_eur(summen[v]) if summen[v] else "–" for v in VARIANT_KEYS]
            + [gesamt]
        )
    totals = total_summen(project)
    totals_b = total_summen(project, nur_beruecksichtigt=True)
    zeilen.append(
        ["-", "GESAMT"]
        + [fmt_eur(totals[v]) for v in VARIANT_KEYS]
        + [fmt_eur(totals_b[quelle])]
    )
    breiten = [12 * mm, 75 * mm] + [26 * mm] * 5 + [28 * mm]
    t = _tabelle(kopf, zeilen, breiten, styles)
    t.setStyle(TableStyle([("FONTNAME", (0, len(zeilen)), (-1, len(zeilen)), "Helvetica-Bold")]))
    story.append(t)
    SimpleDocTemplate(
        str(pfad), pagesize=landscape(A4),
        leftMargin=12 * mm, rightMargin=12 * mm, topMargin=12 * mm, bottomMargin=12 * mm,
        title=f"Kostenberechnung {project.projekt}",
    ).build(story)


def pdf_positionen(project: Project, pfad: str | Path) -> None:
    from calc import ep, fmt_eur, gp, runden

    styles = _styles()
    story = _kopf(project, "Berechnungsblatt (POS)", styles)
    kopf = ["Nr", "Benennung", "Bedarf", "max. Bel.", "EH", "EP spez.", "EP man.",
            "EP", "ANZ", "GP", "KG", "BT"] + [v.upper() for v in VARIANT_KEYS]
    zeilen = []
    for p in sorted(project.positionen, key=lambda x: (x.nr, x.ebene, x.unternr)):
        nr = f"{p.nr}.{p.ebene}" + (f".{p.unternr}" if p.unternr else "")
        zeilen.append(
            [nr, Paragraph(p.benennung, styles["Zelle"]),
             p.bedarf if p.bedarf is not None else "",
             p.max_belastung if p.max_belastung is not None else "",
             p.einheit, p.ep_spezifisch if p.ep_spezifisch is not None else "",
             p.ep_manuell if p.ep_manuell is not None else "",
             runden(ep(p), 0), p.anz if p.anz is not None else "",
             fmt_eur(gp(p)) if p.unternr else "",
             p.kg or "", p.bt]
            + ["×" if p.flags.get(v) else "" for v in VARIANT_KEYS]
        )
    summe = sum(gp(p) for p in project.positionen)
    zeilen.append(["", "SUMME"] + [""] * 10 + [fmt_eur(summe)] + ["", ""])
    breiten = [14 * mm, 62 * mm, 12 * mm, 13 * mm, 9 * mm, 12 * mm, 12 * mm,
               12 * mm, 9 * mm, 16 * mm, 8 * mm, 8 * mm] + [10 * mm] * 5
    t = _tabelle(kopf, zeilen, breiten, styles)
    letzte = len(zeilen)
    t.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, letzte), (-1, letzte), "Helvetica-Bold"),
                ("LINEABOVE", (0, letzte), (-1, letzte), 0.8, KOPFZEILE),
                ("BACKGROUND", (0, letzte), (-1, letzte), colors.HexColor("#e8f0fb")),
            ]
        )
    )
    story.append(t)
    SimpleDocTemplate(
        str(pfad), pagesize=landscape(A4),
        leftMargin=12 * mm, rightMargin=12 * mm, topMargin=12 * mm, bottomMargin=12 * mm,
        title=f"Berechnungsblatt {project.projekt}",
    ).build(story)


def pdf_vergleich(project: Project, pfad: str | Path) -> None:
    from calc import fmt_eur, gruppen_summen, total_summen

    styles = _styles()
    story = _kopf(project, "Variantenvergleich", styles)
    kopf = ["BT", "Beschreibung"] + [v.upper() for v in VARIANT_KEYS] + ["Δ zur BASIS"]
    zeilen = []
    for eintrag in gruppen_summen(project):
        g = eintrag["gruppe"]
        s = eintrag["summen"]
        delta = s["var1"] - s["basis"]
        zeilen.append(
            [g.bt, Paragraph(g.beschreibung, styles["Zelle"])]
            + [fmt_eur(s[v]) if s[v] else "–" for v in VARIANT_KEYS]
            + [fmt_eur(delta) if s["basis"] else "–"]
        )
    totals = total_summen(project)
    zeilen.append(
        ["-", "GESAMT"] + [fmt_eur(totals[v]) for v in VARIANT_KEYS]
        + [fmt_eur(totals["var1"] - totals["basis"])]
    )
    breiten = [12 * mm, 85 * mm] + [30 * mm] * 5 + [33 * mm]
    t = _tabelle(kopf, zeilen, breiten, styles)
    t.setStyle(TableStyle([("FONTNAME", (0, len(zeilen)), (-1, len(zeilen)), "Helvetica-Bold")]))
    story.append(t)
    SimpleDocTemplate(
        str(pfad), pagesize=landscape(A4),
        leftMargin=12 * mm, rightMargin=12 * mm, topMargin=12 * mm, bottomMargin=12 * mm,
        title=f"Variantenvergleich {project.projekt}",
    ).build(story)
