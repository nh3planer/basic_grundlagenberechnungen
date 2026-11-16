"""Kostenabschätzung – Desktop-Anwendung (PySide6).

Start:  python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

import calc
import excel_io
import pdf_out
from model import Group, Position, Project, VARIANT_KEYS, laden, speichern

KOPF_FARBE = QColor("#10233f")
HELL = QColor("#e8f0fb")


def ro_item(wert, fett=False):
    it = QTableWidgetItem("" if wert is None else str(wert))
    it.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
    if fett:
        f = it.font()
        f.setBold(True)
        it.setFont(f)
    return it


class PositionsTab(QWidget):
    SPALTEN = [
        "Nr", "Ebene", "Unternr", "Benennung", "T1", "T2", "Bedarf", "max. Bel.",
        "Basis", "EH", "EP spez.", "EP man.", "EP", "ANZ", "GP", "KG", "BT",
        "Bemerkung", "BASIS", "V1", "V2", "V3", "V4",
    ]
    C_NR, C_EBENE, C_UNTERNR, C_BENENNUNG, C_T1, C_T2, C_BEDARF, C_BELASTUNG, \
        C_BASIS, C_EH, C_SPEZ, C_MANUELL, C_EP, C_ANZ, C_GP, C_KG, C_BT, \
        C_BEMERKUNG, C_FLAG0 = range(19)

    def __init__(self, fenster: "MainWindow"):
        super().__init__()
        self.f = fenster
        self.ids: list[str] = []
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        for text, slot in [
            ("+ Position", self.neue_position),
            ("+ Gewerk / Kapitel", self.neues_gewerk),
            ("Duplizieren", self.duplizieren),
            ("Löschen", self.loeschen),
        ]:
            b = QPushButton(text)
            b.clicked.connect(slot)
            toolbar.addWidget(b)
        self.filter_variante = QComboBox()
        self.filter_variante.currentIndexChanged.connect(lambda: self.aktualisiere())
        toolbar.addWidget(QLabel("Filter:"))
        toolbar.addWidget(self.filter_variante)
        self.suche = QLineEdit()
        self.suche.setPlaceholderText("Suchen (Benennung, Bemerkung, BT)…")
        self.suche.textChanged.connect(lambda: self.aktualisiere())
        toolbar.addWidget(self.suche, 1)
        layout.addLayout(toolbar)

        self.tabelle = QTableWidget(0, len(self.SPALTEN))
        self.tabelle.setHorizontalHeaderLabels(self.SPALTEN)
        self.tabelle.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self.tabelle.horizontalHeader().setStretchLastSection(False)
        self.tabelle.setColumnWidth(self.C_BENENNUNG, 260)
        self.tabelle.setColumnWidth(self.C_BEMERKUNG, 180)
        self.tabelle.cellChanged.connect(self.zelle_geaendert)
        layout.addWidget(self.tabelle, 1)

    def _pos(self, zeile: int) -> Position | None:
        if zeile < 0 or zeile >= len(self.ids):
            return None
        for p in self.f.project.positionen:
            if p.id == self.ids[zeile]:
                return p
        return None

    def neue_position(self):
        max_nr = max((p.nr for p in self.f.project.positionen), default=0)
        self.f.project.positionen.append(Position(nr=max_nr, ebene=2, unternr=0))
        self.f.alle_aktualisieren()

    def neues_gewerk(self):
        max_nr = max((p.nr for p in self.f.project.positionen), default=0) + 1
        p = Position(nr=max_nr, ebene=1, unternr=0, benennung="Neues Gewerk")
        self.f.project.positionen.append(p)
        self.f.alle_aktualisieren()

    def duplizieren(self):
        zeile = self.tabelle.currentRow()
        pos = self._pos(zeile)
        if not pos:
            return
        kopie = Position(**{k: v for k, v in vars(pos).items() if k != "id"})
        kopie.unternr = max(
            (p.unternr for p in self.f.project.positionen
             if p.nr == pos.nr and p.ebene == pos.ebene),
            default=0,
        ) + 1
        self.f.project.positionen.append(kopie)
        self.f.alle_aktualisieren()

    def loeschen(self):
        zeile = self.tabelle.currentRow()
        pos = self._pos(zeile)
        if not pos:
            return
        self.f.project.positionen = [
            p for p in self.f.project.positionen if p.id != pos.id
        ]
        self.f.alle_aktualisieren()

    def zelle_geaendert(self, zeile: int, spalte: int):
        pos = self._pos(zeile)
        if pos is None:
            return
        text = self.tabelle.item(zeile, spalte).text().strip()
        try:
            if spalte in (self.C_NR, self.C_EBENE, self.C_UNTERNR, self.C_KG):
                wert = int(text) if text else (None if spalte == self.C_KG else 0)
                if spalte == self.C_NR:
                    pos.nr = wert or 1
                elif spalte == self.C_EBENE:
                    pos.ebene = wert or 1
                elif spalte == self.C_UNTERNR:
                    pos.unternr = wert
                else:
                    pos.kg = wert
            elif spalte in (self.C_BEDARF, self.C_BELASTUNG, self.C_SPEZ, self.C_MANUELL, self.C_ANZ):
                wert = float(text.replace(",", ".")) if text else None
                if spalte == self.C_BEDARF:
                    pos.bedarf = wert
                elif spalte == self.C_BELASTUNG:
                    pos.max_belastung = wert
                elif spalte == self.C_SPEZ:
                    pos.ep_spezifisch = wert
                elif spalte == self.C_MANUELL:
                    pos.ep_manuell = wert
                else:
                    pos.anz = wert
            elif spalte == self.C_BENENNUNG:
                pos.benennung = text
            elif spalte == self.C_T1:
                pos.t1 = text
            elif spalte == self.C_T2:
                pos.t2 = text
            elif spalte == self.C_BASIS:
                pos.ep_basis = "bedarf" if text.upper().startswith("L") else "belastung"
            elif spalte == self.C_EH:
                pos.einheit = text
            elif spalte == self.C_BT:
                pos.bt = text
            elif spalte == self.C_BEMERKUNG:
                pos.bemerkung = text
            elif spalte >= self.C_FLAG0:
                pos.flags[VARIANT_KEYS[spalte - self.C_FLAG0]] = (
                    text.lower() == "ja"
                )
        except ValueError:
            pass
        self.f.alle_aktualisieren()

    def aktualisiere(self):
        projekt = self.f.project
        self.filter_variante.blockSignals(True)
        self.filter_variante.clear()
        self.filter_variante.addItem("Alle Varianten")
        for v in VARIANT_KEYS:
            self.filter_variante.addItem(v.upper())
        self.filter_variante.blockSignals(False)

        filter_v = None if self.filter_variante.currentIndex() <= 0 \
            else VARIANT_KEYS[self.filter_variante.currentIndex() - 1]
        suche = self.suche.text().strip().lower()

        sichtbar = []
        for p in sorted(projekt.positionen, key=lambda x: (x.nr, x.ebene, x.unternr)):
            if filter_v and p.unternr > 0 and not p.flags.get(filter_v):
                continue
            if suche and suche not in (p.benennung + " " + p.bemerkung + " " + p.bt).lower():
                continue
            sichtbar.append(p)

        self.tabelle.blockSignals(True)
        self.tabelle.setRowCount(len(sichtbar))
        self.ids = [p.id for p in sichtbar]
        for i, p in enumerate(sichtbar):
            kapitel = p.unternr == 0
            werte = [
                f"{p.nr}.{p.ebene}" + (f".{p.unternr}" if p.unternr else ""),
                p.ebene, p.unternr, p.benennung, p.t1, p.t2,
                p.bedarf if p.bedarf is not None else "",
                p.max_belastung if p.max_belastung is not None else "",
                "L" if p.ep_basis == "bedarf" else "M",
                p.einheit,
                p.ep_spezifisch if p.ep_spezifisch is not None else "",
                p.ep_manuell if p.ep_manuell is not None else "",
                calc.runden(calc.ep(p), 0) if not kapitel else "",
                p.anz if p.anz is not None else "",
                calc.fmt_eur(calc.gp(p)) if not kapitel else "",
                p.kg or "", p.bt, p.bemerkung,
            ]
            for spalte, wert in enumerate(werte):
                if spalte in (self.C_EP, self.C_GP):
                    self.tabelle.setItem(i, spalte, ro_item(wert, fett=spalte == self.C_GP))
                else:
                    self.tabelle.setItem(i, spalte, QTableWidgetItem(str(wert)))
            for j, v in enumerate(VARIANT_KEYS):
                it = QTableWidgetItem("ja" if p.flags.get(v) else "nein")
                it.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                self.tabelle.setItem(i, self.C_FLAG0 + j, it)
            if kapitel:
                for spalte in range(len(self.SPALTEN)):
                    it = self.tabelle.item(i, spalte)
                    it.setBackground(HELL)
                    f = it.font()
                    f.setBold(True)
                    it.setFont(f)
        self.tabelle.blockSignals(False)


class UebersichtTab(QWidget):
    def __init__(self, fenster: "MainWindow"):
        super().__init__()
        self.f = fenster
        self.ids: list[str] = []
        layout = QVBoxLayout(self)

        self.kpis = QHBoxLayout()
        layout.addLayout(self.kpis)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Gesamtbildung nach Variante:"))
        self.quelle = QComboBox()
        self.quelle.currentIndexChanged.connect(self._quelle_geaendert)
        toolbar.addWidget(self.quelle)
        b = QPushButton("+ Gruppe")
        b.clicked.connect(self.neue_gruppe)
        toolbar.addWidget(b)
        b = QPushButton("Gruppe löschen")
        b.clicked.connect(self.loesche_gruppe)
        toolbar.addWidget(b)
        toolbar.addStretch(1)
        layout.addLayout(toolbar)

        self.tabelle = QTableWidget(0, 10)
        self.tabelle.setHorizontalHeaderLabels(
            ["BT", "Beschreibung", "Entwurf / Umfang", "BASIS", "VAR 1", "VAR 2",
             "VAR 3", "VAR 4", "GESAMT", "berücksichtigt"]
        )
        self.tabelle.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tabelle.setColumnWidth(2, 320)
        self.tabelle.cellChanged.connect(self.zelle_geaendert)
        layout.addWidget(self.tabelle, 1)

    def _gruppe(self, zeile: int) -> Group | None:
        if zeile < 0 or zeile >= len(self.ids):
            return None
        for g in self.f.project.gruppen:
            if g.id == self.ids[zeile]:
                return g
        return None

    def _quelle_geaendert(self):
        idx = self.quelle.currentIndex()
        if idx >= 0:
            self.f.project.gesamt_quelle = VARIANT_KEYS[idx]
        self.f.alle_aktualisieren()

    def neue_gruppe(self):
        self.f.project.gruppen.append(Group(bt="NEU", beschreibung="Neue Gruppe"))
        self.f.alle_aktualisieren()

    def loesche_gruppe(self):
        zeile = self.tabelle.currentRow()
        g = self._gruppe(zeile)
        if not g:
            return
        self.f.project.gruppen = [x for x in self.f.project.gruppen if x.id != g.id]
        self.f.alle_aktualisieren()

    def zelle_geaendert(self, zeile: int, spalte: int):
        g = self._gruppe(zeile)
        if g is None:
            return
        text = self.tabelle.item(zeile, spalte).text().strip()
        if spalte == 0:
            alt = g.bt
            g.bt = text
            for p in self.f.project.positionen:
                if p.bt == alt and alt:
                    p.bt = text
        elif spalte == 1:
            g.beschreibung = text
        elif spalte == 2:
            g.entwurf = text
        elif spalte == 9:
            g.beruecksichtigt = text.lower() == "ja"
        self.f.alle_aktualisieren()

    def aktualisiere(self):
        projekt = self.f.project
        self.quelle.blockSignals(True)
        self.quelle.clear()
        for v in VARIANT_KEYS:
            self.quelle.addItem(v.upper())
        self.quelle.setCurrentIndex(
            VARIANT_KEYS.index(projekt.gesamt_quelle) if projekt.gesamt_quelle in VARIANT_KEYS else 0
        )
        self.quelle.blockSignals(False)

        while self.kpis.count():
            item = self.kpis.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        totals = calc.total_summen(projekt)
        for v in VARIANT_KEYS:
        # KPI-Kachel
            kachel = QLabel(f"<b style='color:#1a5fb4'>{v.upper()}</b><br>"
                             f"<span style='font-size:16px'>{calc.fmt_eur(totals[v])}</span>")
            kachel.setStyleSheet(
                "background:#fff; border:1px solid #dde3ec; border-radius:8px; padding:10px;"
            )
            self.kpis.addWidget(kachel)

        daten = calc.gruppen_summen(projekt)
        self.tabelle.blockSignals(True)
        self.tabelle.setRowCount(len(daten))
        self.ids = [d["gruppe"].id for d in daten]
        quelle = projekt.gesamt_quelle
        for i, eintrag in enumerate(daten):
            g = eintrag["gruppe"]
            s = eintrag["summen"]
            self.tabelle.setItem(i, 0, QTableWidgetItem(g.bt))
            self.tabelle.setItem(i, 1, QTableWidgetItem(g.beschreibung))
            self.tabelle.setItem(i, 2, QTableWidgetItem(g.entwurf))
            for j, v in enumerate(VARIANT_KEYS):
                self.tabelle.setItem(
                    i, 3 + j, ro_item(calc.fmt_eur(s[v]) if s[v] else "–")
                )
            gesamt = calc.fmt_eur(s[quelle]) if g.beruecksichtigt else "–"
            self.tabelle.setItem(i, 8, ro_item(gesamt, fett=True))
            self.tabelle.setItem(i, 9, QTableWidgetItem("ja" if g.beruecksichtigt else "nein"))
        self.tabelle.blockSignals(False)


class VergleichTab(QWidget):
    def __init__(self, fenster: "MainWindow"):
        super().__init__()
        self.f = fenster
        layout = QVBoxLayout(self)
        self.kpis = QHBoxLayout()
        layout.addLayout(self.kpis)
        self.tabelle = QTableWidget(0, 8)
        self.tabelle.setHorizontalHeaderLabels(
            ["BT", "Beschreibung", "BASIS", "VAR 1", "VAR 2", "VAR 3", "VAR 4", "Δ zur BASIS"]
        )
        self.tabelle.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tabelle.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.tabelle, 1)
        hinweis = QLabel(
            "Δ zur BASIS: vergleicht VAR 1 mit der Basisvariante. "
            "Die Kacheln oben zeigen die Differenz jeder Variante zur BASIS."
        )
        hinweis.setStyleSheet("color:#66748c;")
        layout.addWidget(hinweis)

    def aktualisiere(self):
        projekt = self.f.project
        while self.kpis.count():
            item = self.kpis.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        totals = calc.total_summen(projekt)
        for v in VARIANT_KEYS:
            delta = totals[v] - totals["basis"]
            zeichen = "Δ " + calc.fmt_eur(delta) if v != "basis" else "Referenz"
            farbe = "#c01c28" if delta > 0 else "#1a7f37"
            kachel = QLabel(
                f"<b style='color:#1a5fb4'>{v.upper()}</b><br>"
                f"<span style='font-size:16px'>{calc.fmt_eur(totals[v])}</span><br>"
                f"<span style='color:{farbe};font-size:11px'>{zeichen}</span>"
            )
            kachel.setStyleSheet(
                "background:#fff; border:1px solid #dde3ec; border-radius:8px; padding:10px;"
            )
            self.kpis.addWidget(kachel)

        daten = calc.gruppen_summen(projekt)
        self.tabelle.setRowCount(len(daten) + 1)
        for i, eintrag in enumerate(daten):
            g = eintrag["gruppe"]
            s = eintrag["summen"]
            self.tabelle.setItem(i, 0, ro_item(g.bt))
            self.tabelle.setItem(i, 1, ro_item(g.beschreibung))
            for j, v in enumerate(VARIANT_KEYS):
                self.tabelle.setItem(i, 2 + j, ro_item(calc.fmt_eur(s[v]) if s[v] else "–"))
            delta = s["var1"] - s["basis"]
            self.tabelle.setItem(
                i, 7, ro_item(calc.fmt_eur(delta) if s["basis"] else "–")
            )
        zeile = len(daten)
        self.tabelle.setItem(zeile, 0, ro_item("-", fett=True))
        self.tabelle.setItem(zeile, 1, ro_item("GESAMT", fett=True))
        for j, v in enumerate(VARIANT_KEYS):
            self.tabelle.setItem(zeile, 2 + j, ro_item(calc.fmt_eur(totals[v]), fett=True))
        self.tabelle.setItem(
            zeile, 7, ro_item(calc.fmt_eur(totals["var1"] - totals["basis"]), fett=True)
        )


class ProjektTab(QWidget):
    def __init__(self, fenster: "MainWindow"):
        super().__init__()
        self.f = fenster
        layout = QVBoxLayout(self)
        grid = QGridLayout()
        felder = [
            ("Firma", "firma"), ("Adresse", "adresse"), ("Projekt", "projekt"),
            ("Bearbeiter", "bearbeiter"), ("Stand", "stand"),
        ]
        self.editoren: dict[str, QLineEdit] = {}
        for i, (label, attr) in enumerate(felder):
            grid.addWidget(QLabel(label), i, 0)
            edit = QLineEdit()
            edit.editingFinished.connect(lambda a=attr, e=edit: self._set(a, e.text()))
            self.editoren[attr] = edit
            grid.addWidget(edit, i, 1)
        layout.addLayout(grid)

        box = QWidget()
        box.setStyleSheet(
            "background:#fff; border:1px solid #dde3ec; border-radius:8px; padding:10px;"
        )
        innen = QVBoxLayout(box)
        innen.addWidget(QLabel("<b>Firmenlogo</b>"))
        self.logo_label = QLabel()
        self.logo_label.setFixedHeight(60)
        innen.addWidget(self.logo_label)
        reihe = QHBoxLayout()
        b = QPushButton("Logo-Bild wählen…")
        b.clicked.connect(self.logo_waehlen)
        reihe.addWidget(b)
        b = QPushButton("Standard-Logo (EP-Bildmarke)")
        b.clicked.connect(self.logo_standard)
        reihe.addWidget(b)
        reihe.addStretch(1)
        innen.addLayout(reihe)
        layout.addWidget(box)
        layout.addStretch(1)

    def _set(self, attr, wert):
        setattr(self.f.project, attr, wert)
        self.f.alle_aktualisieren()

    def logo_waehlen(self):
        pfad, _ = QFileDialog.getOpenFileName(
            self, "Logo wählen", "", "Bilder (*.png *.jpg *.jpeg *.svg *.webp)"
        )
        if pfad:
            self.f.project.logo = pfad
            self.f.alle_aktualisieren()

    def logo_standard(self):
        self.f.project.logo = ""
        self.f.alle_aktualisieren()

    def aktualisiere(self):
        for attr, edit in self.editoren.items():
            edit.setText(getattr(self.f.project, attr))
        pfad = self.f.project.logo or str(pdf_out.STANDARD_LOGO)
        if Path(pfad).exists():
            from PySide6.QtGui import QPixmap
            pm = QPixmap(pfad)
            if not pm.isNull():
                self.logo_label.setPixmap(
                    pm.scaledToHeight(56, Qt.SmoothTransformation)
                )
                self.logo_label.setText("")
                return
        self.logo_label.setText("Kein Logo gefunden")


class DatenTab(QWidget):
    def __init__(self, fenster: "MainWindow"):
        super().__init__()
        self.f = fenster
        layout = QVBoxLayout(self)

        def karte(titel: str, buttons: list[tuple[str, object]], hinweis: str) -> None:
            box = QWidget()
            box.setStyleSheet(
                "background:#fff; border:1px solid #dde3ec; border-radius:8px; padding:12px;"
            )
            innen = QVBoxLayout(box)
            innen.addWidget(QLabel(f"<b>{titel}</b>"))
            reihe = QHBoxLayout()
            for text, slot in buttons:
                b = QPushButton(text)
                b.clicked.connect(slot)
                reihe.addWidget(b)
            reihe.addStretch(1)
            innen.addLayout(reihe)
            l = QLabel(hinweis)
            l.setStyleSheet("color:#66748c;")
            l.setWordWrap(True)
            innen.addWidget(l)
            layout.addWidget(box)

        karte(
            "Excel-Import",
            [("Excel-Liste importieren…", self.f.import_excel)],
            "Liest die Blätter POS, SUM_Entwurf, KG_NR und drop der bestehenden "
            "Kostenliste ein. Bestehende Daten werden dabei ersetzt.",
        )
        karte(
            "Export",
            [("Als Excel-Liste speichern…", self.f.export_excel),
             ("Projektdatei speichern…", self.f.projekt_speichern),
             ("Projektdatei laden…", self.f.projekt_laden)],
            "Excel-Export erzeugt dieselbe Blattstruktur. Die Projektdatei (.json) "
            "enthält das komplette Projekt zum Wiederöffnen.",
        )
        karte(
            "PDF",
            [("PDF: Übersicht", lambda: self.f.pdf_drucken("uebersicht")),
             ("PDF: Positionen", lambda: self.f.pdf_drucken("positionen")),
             ("PDF: Variantenvergleich", lambda: self.f.pdf_drucken("vergleich"))],
            "Erzeugt ein A4-Querformat-PDF mit EP-Bildmarke, Firmen- und Projektdaten.",
        )
        karte(
            "Projekt",
            [("Neues Projekt (alles löschen)", self.f.reset)],
            "Achtung: alle Positionen, Gruppen und Projektdaten werden entfernt.",
        )
        layout.addStretch(1)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kostenabschätzung")
        self.resize(1500, 950)
        self.project: Project = laden()

        self.tabs = QTabWidget()
        self.tabs.addTab(UebersichtTab(self), "Übersicht (SUM_Entwurf)")
        self.tabs.addTab(PositionsTab(self), "Positionen (POS)")
        self.tabs.addTab(VergleichTab(self), "Variantenvergleich")
        self.tabs.addTab(ProjektTab(self), "Projekt")
        self.tabs.addTab(DatenTab(self), "Import / Export / PDF")
        self.setCentralWidget(self.tabs)

        menue = self.menuBar().addMenu("&Datei")
        aktion = QAction("Excel-Liste &importieren…", self)
        aktion.triggered.connect(self.import_excel)
        menue.addAction(aktion)
        aktion = QAction("Als Excel-Liste &exportieren…", self)
        aktion.triggered.connect(self.export_excel)
        menue.addAction(aktion)
        aktion = QAction("&PDF erstellen…", self)
        aktion.triggered.connect(lambda: self.pdf_drucken("uebersicht"))
        menue.addAction(aktion)
        menue.addSeparator()
        aktion = QAction("&Beenden", self)
        aktion.triggered.connect(self.close)
        menue.addAction(aktion)

        self.statusBar().showMessage(
            "Daten werden automatisch lokal gespeichert (" + str(__import__("model").SPEICHERORT) + ")"
        )
        self.alle_aktualisieren()

    # --- Aktionen -----------------------------------------------------------
    def import_excel(self):
        pfad, _ = QFileDialog.getOpenFileName(
            self, "Excel-Liste wählen", "", "Excel (*.xlsx *.xlsm)"
        )
        if not pfad:
            return
        try:
            daten = excel_io.import_excel(pfad)
        except Exception as e:
            QMessageBox.critical(self, "Import fehlgeschlagen", str(e))
            return
        if not daten.get("positionen"):
            QMessageBox.warning(self, "Import", "Keine Positionen im Blatt POS gefunden.")
            return
        self.project.positionen = daten["positionen"]
        if daten.get("gruppen"):
            self.project.gruppen = daten["gruppen"]
        if daten.get("kostengruppen"):
            self.project.kostengruppen = daten["kostengruppen"]
        if daten.get("einheiten"):
            self.project.einheiten = daten["einheiten"]
        for attr in ("projekt", "bearbeiter", "stand"):
            if daten.get(attr):
                setattr(self.project, attr, daten[attr])
        self.alle_aktualisieren()
        QMessageBox.information(
            self, "Import erfolgreich",
            f"{len(self.project.positionen)} Position(en), {len(self.project.gruppen)} "
            f"Gruppe(n) und {len(self.project.kostengruppen)} Kostengruppen importiert.",
        )

    def export_excel(self):
        vorschlag = f"Kostenabschaetzung_{self.project.projekt or 'Projekt'}.xlsx"
        pfad, _ = QFileDialog.getSaveFileName(self, "Excel-Export", vorschlag, "Excel (*.xlsx)")
        if not pfad:
            return
        try:
            excel_io.export_excel(self.project, pfad)
        except Exception as e:
            QMessageBox.critical(self, "Export fehlgeschlagen", str(e))
            return
        QMessageBox.information(self, "Export erfolgreich", f"Gespeichert:\n{pfad}")

    def projekt_speichern(self):
        vorschlag = f"{self.project.projekt or 'Projekt'}.kproj.json"
        pfad, _ = QFileDialog.getSaveFileName(self, "Projekt speichern", vorschlag, "Projekt (*.json)")
        if not pfad:
            return
        Path(pfad).write_text(self.project.to_json(), encoding="utf-8")
        QMessageBox.information(self, "Gespeichert", f"Projekt gespeichert:\n{pfad}")

    def projekt_laden(self):
        pfad, _ = QFileDialog.getOpenFileName(self, "Projekt öffnen", "", "Projekt (*.json)")
        if not pfad:
            return
        self.project = Project.from_json(Path(pfad).read_text(encoding="utf-8"))
        self.alle_aktualisieren()

    def pdf_drucken(self, art: str):
        vorschlag = f"Kostenabschaetzung_{self.project.projekt or 'Projekt'}.pdf"
        pfad, _ = QFileDialog.getSaveFileName(self, "PDF speichern", vorschlag, "PDF (*.pdf)")
        if not pfad:
            return
        try:
            if art == "positionen":
                pdf_out.pdf_positionen(self.project, pfad)
            elif art == "vergleich":
                pdf_out.pdf_vergleich(self.project, pfad)
            else:
                pdf_out.pdf_uebersicht(self.project, pfad)
        except Exception as e:
            QMessageBox.critical(self, "PDF fehlgeschlagen", str(e))
            return
        QMessageBox.information(self, "PDF erstellt", f"PDF gespeichert:\n{pfad}")

    def reset(self):
        antwort = QMessageBox.question(
            self, "Neues Projekt", "Alle Daten löschen und neu beginnen?"
        )
        if antwort != QMessageBox.Yes:
            return
        self.project = Project()
        self.alle_aktualisieren()

    # --- Aktualisierung ------------------------------------------------------
    def alle_aktualisieren(self):
        speichern(self.project)
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if hasattr(widget, "aktualisiere"):
                widget.aktualisiere()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    fenster = MainWindow()
    fenster.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
