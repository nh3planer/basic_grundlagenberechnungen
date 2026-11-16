# Kostenabschätzung – Python-Desktop-Anwendung

Python-Version der Kostenabschätzung (PySide6/Qt). Gleiche Logik und Dateiformate wie die
Excel-Liste (Blätter `SUM_Entwurf`, `POS`, `KG_NR`, `drop`) und die JavaScript-Version im
Hauptverzeichnis.

## Installation & Start

Voraussetzung: Python 3.10+ (z. B. von [python.org](https://www.python.org)).

```bash
cd python
pip install -r requirements.txt
python main.py
```

## Funktionen

- **Positionen (POS)**: Berechnungsblatt mit Bedarf / max. Belastung (EP-Basis je Zeile
  wählbar: L = Bedarf, M = max. Belastung), EP spezifisch/manuell, Anzahl, automatischer
  GP (ANZ × EP, gerundet wie in Excel), KG (DIN 276), BT-Gruppe, Bemerkung
- **Varianten**: BASIS + 4 Varianten per ja/nein je Position
- **Übersicht (SUM_Entwurf)**: Gruppen (BT) mit Summen je Variante, „berücksichtigt"-
  Schalter, Gesamtbildung nach wählbarer Variante
- **Variantenvergleich**: alle Varianten je Gruppe mit Differenz zur BASIS
- **Excel-Import/-Export** sowie Projektdateien (.json)
- **PDF-Export**: Übersicht, Positionen oder Variantenvergleich als A4-Querformat-PDF
  mit EP-Bildmarke (`ep-logo.png`, ersetzbar über den Projekt-Tab)
- Automatische lokale Speicherung unter `~/.kostenabschaetzung.json`

## EXE erstellen (optional)

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name Kostenabschaetzung --add-data "ep-logo.png:." main.py
```

Ergebnis liegt unter `dist/`.

## Test

Headless-Smoke-Test (Import, Summen, Export, PDFs):

```bash
python smoke_test.py
```
