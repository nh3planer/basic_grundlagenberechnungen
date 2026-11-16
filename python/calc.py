"""Berechnungslogik – identisch zur Excel-Liste."""
from __future__ import annotations

from model import Project, Position, VARIANT_KEYS


def runden(wert: float, stellen: int) -> float:
    factor = 10 ** stellen
    return round(wert * factor) / factor


def ep(pos: Position) -> float:
    if pos.ep_manuell is not None and pos.ep_manuell > 0:
        return pos.ep_manuell
    primaer = pos.bedarf if pos.ep_basis == "bedarf" else pos.max_belastung
    fallback = pos.max_belastung if pos.ep_basis == "bedarf" else pos.bedarf
    menge = primaer if primaer is not None else fallback
    if menge is None:
        return 0.0
    return menge * (pos.ep_spezifisch or 0.0)


def ist_kalkulationszeile(pos: Position) -> bool:
    return pos.unternr > 0


def gp(pos: Position) -> float:
    if not ist_kalkulationszeile(pos):
        return 0.0
    return runden((pos.anz or 0) * ep(pos), -2)


def gp_variante(pos: Position, variante: str) -> float:
    if not pos.flags.get(variante):
        return 0.0
    return gp(pos)


def summe_variante(positionen: list[Position], variante: str, bt: str | None = None) -> float:
    return sum(
        gp_variante(p, variante) for p in positionen if bt is None or p.bt == bt
    )


def gruppen_summen(project: Project) -> list[dict]:
    result = []
    for g in project.gruppen:
        result.append(
            {
                "gruppe": g,
                "summen": {v: summe_variante(project.positionen, v, g.bt) for v in VARIANT_KEYS},
            }
        )
    return result


def total_summen(project: Project, nur_beruecksichtigt: bool = False) -> dict[str, float]:
    relevante = project.positionen
    if nur_beruecksichtigt and project.gruppen:
        aktive = {g.bt for g in project.gruppen if g.beruecksichtigt}
        bekannte = {g.bt for g in project.gruppen}
        relevante = [p for p in project.positionen if p.bt in aktive or p.bt not in bekannte]
    return {v: summe_variante(relevante, v) for v in VARIANT_KEYS}


def kg_summen(project: Project, variante: str) -> list[dict]:
    map_: dict[int, float] = {}
    for p in project.positionen:
        if p.kg is None:
            continue
        map_[p.kg] = map_.get(p.kg, 0.0) + gp_variante(p, variante)
    namen = {k["nr"]: k["name"] for k in project.kostengruppen}
    eintraege = [{"kg": kg, "name": namen.get(kg, ""), "summe": s} for kg, s in map_.items()]
    return sorted(eintraege, key=lambda e: -e["summe"])


def fmt(wert: float) -> str:
    return f"{wert:,.0f}".replace(",", ".")


def fmt_eur(wert: float) -> str:
    return fmt(wert) + " €"
