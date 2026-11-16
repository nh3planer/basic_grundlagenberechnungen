# Kostenabschätzung – Desktop-Anwendung

Moderne Desktop-Software zur Kostenabschätzung (Kälte-/Anlagentechnik) als Ersatz für die
Excel-Liste mit den Blättern `SUM_Entwurf`, `POS`, `KG_NR` und `drop`.

## Funktionen

- **Positionen (POS)**: komplettes Berechnungsblatt – Benennung, Betriebspunkte (T1/T2),
  Bedarf/max. Belastung, Einheit (Dropdown), EP spezifisch/manuell, Anzahl, GP automatisch
  (GP = ANZ × EP, gerundet wie in Excel). EP-Basis pro Zeile wählbar (L = Bedarf, M = max. Belastung).
- **Varianten**: BASIS + 4 Varianten, Zuordnung per Kontrollkästchen (ja/nein) je Position.
- **Übersicht (SUM_Entwurf)**: Gruppen (BT) mit Beschreibung/Entwurfstext, Summen je Variante,
  „berücksichtigt"-Schalter und Gesamtbildung nach wählbarer Variante, inkl. Kostengruppen-Anteile
  (DIN 276) mit Balkendiagramm.
- **Variantenvergleich**: Gegenüberstellung aller Varianten je Gruppe mit Differenz zur Basis.
- **Excel-Import**: liest die bestehende Liste ein (POS, SUM_Entwurf, KG_NR, drop) – Werte und
  Varianten-Flags werden vollständig übernommen.
- **Excel-Export / Projektdatei**: speichern als `.xlsx` bzw. `.kproj.json`.
- **PDF-Export**: druckt das aktuelle Blatt im A4-Querformat über einen Dateidialog.
- Daten werden automatisch lokal gespeichert (localStorage).

## Installation & Start

Voraussetzung: [Node.js](https://nodejs.org) (LTS).

```bash
npm install
npm run app        # baut die Oberfläche und startet die Desktop-Anwendung
```

## Windows-Setup (EXE) erstellen

```bash
npm run dist
```

Erzeugt unter `release/` einen Windows-Installer (NSIS).

## Entwicklung

```bash
npm run dev        # Vite-Dev-Server
npm start          # Electron mit gebautem dist/
```

## Hinweise zur Berechnungslogik

- EP = EP manuell, falls > 0, sonst (EP-Basis × EP spezifisch) – die EP-Basis (Bedarf oder
  max. Belastung) wird beim Import aus der Excel-Formel der jeweiligen Zeile übernommen.
- GP = Rundung(Anzahl × EP, -2), nur für Positionszeilen mit Unternummer > 0.
- Importierte Beispielwerte aus `7V16EFH4-261116_Kosten_Rev_5.xlsx` ergeben identische Summen
  (BASIS 7.252.800 €, VAR 1 6.170.300 €, VAR 2 6.049.900 €, VAR 3 5.979.900 €).
