"""Datenmodell der Kostenabschätzung."""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

VARIANT_KEYS = ["basis", "var1", "var2", "var3", "var4"]

SPEICHERORT = Path.home() / ".kostenabschaetzung.json"

DEFAULT_EINHEITEN = [
    "Stk", "Pa", "lfm", "kg", "kg/h", "kW", "m²", "m² BGF",
    "m³", "m³/h", "m³/min", "MW", "PS",
]


@dataclass
class Position:
    benennung: str = ""
    nr: int = 1
    ebene: int = 1
    unternr: int = 0
    t1: str = ""
    t2: str = ""
    bedarf: float | None = None
    max_belastung: float | None = None
    ep_basis: str = "belastung"  # "bedarf" (L) oder "belastung" (M)
    einheit: str = ""
    ep_spezifisch: float | None = None
    ep_manuell: float | None = None
    anz: float | None = None
    kg: int | None = None
    bt: str = ""
    bemerkung: str = ""
    flags: dict[str, bool] = field(
        default_factory=lambda: {v: (v == "basis") for v in VARIANT_KEYS}
    )
    id: str = field(default_factory=lambda: uuid.uuid4().hex)


@dataclass
class Group:
    bt: str = ""
    beschreibung: str = ""
    entwurf: str = ""
    beruecksichtigt: bool = True
    id: str = field(default_factory=lambda: uuid.uuid4().hex)


@dataclass
class Project:
    firma: str = "Eckert & Partner beratende Ingenieure GmbH"
    adresse: str = "Adamgasse 21, 6120 Innsbruck"
    projekt: str = ""
    bearbeiter: str = ""
    stand: str = ""
    logo: str = ""  # Pfad zur Logo-Datei (leer = eingebautes EP-Logo)
    gesamt_quelle: str = "basis"
    einheiten: list[str] = field(default_factory=lambda: list(DEFAULT_EINHEITEN))
    kostengruppen: list[dict] = field(default_factory=list)
    positionen: list[Position] = field(default_factory=list)
    gruppen: list[Gruppe] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=1)

    @classmethod
    def from_json(cls, text: str) -> "Project":
        data = json.loads(text)
        proj = cls()
        known = {f.name for f in fields(proj)}
        for k, v in data.items():
            if k not in known:
                continue
            if k == "positionen":
                proj.positionen = [Position(**{kk: vv for kk, vv in p.items()}) for p in v]
            elif k == "gruppen":
                proj.gruppen = [Gruppe(**{kk: vv for kk, vv in g.items()}) for g in v]
            else:
                setattr(proj, k, v)
        return proj


def speichern(project: Project) -> None:
    SPEICHERORT.write_text(project.to_json(), encoding="utf-8")


def laden() -> Project:
    if SPEICHERORT.exists():
        try:
            return Project.from_json(SPEICHERORT.read_text(encoding="utf-8"))
        except Exception:
            pass
    return Project()
