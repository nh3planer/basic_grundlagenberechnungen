import * as XLSX from "xlsx";
import { Project, Group, Position, VariantKey, VARIANT_KEYS, emptyPosition } from "./types";
import { roundTo, ep, gp, groupSums, totalSums } from "./calc";

const JA = "ja";

function col(row: XLSX.WorkSheet, r: number, c: number): any {
  const cell = (XLSX.utils.encode_cell({ r, c }) as any) && row[XLSX.utils.encode_cell({ r, c })];
  return cell?.v ?? cell?.w ?? null;
}

function num(v: any): number | null {
  if (v == null || v === "" || v === "-") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function str(v: any): string {
  return v == null ? "" : String(v).trim();
}

function ja(v: any): boolean {
  return str(v).toLowerCase() === "ja";
}

export function importExcel(data: Uint8Array): Partial<Project> {
  const wb = XLSX.read(data, { cellDates: true });
  const result: Partial<Project> = {};

  const posSheet = wb.Sheets["POS"];
  const sumSheet = wb.Sheets["SUM_Entwurf"];
  const kgSheet = wb.Sheets["KG_NR"];
  const dropSheet = wb.Sheets["drop"];

  if (posSheet) {
    const range = XLSX.utils.decode_range(posSheet["!ref"] ?? "A1");
    const positionen: Position[] = [];
    for (let r = 8; r <= range.e.r; r++) {
      const nrCell = col(posSheet, r, 3);
      if (typeof nrCell === "string" && nrCell.trim() !== "") continue;
      const nr = num(nrCell);
      const benennung = str(col(posSheet, r, 6));
      const bedarf = num(col(posSheet, r, 11));
      const belastung = num(col(posSheet, r, 12));
      const spez = num(col(posSheet, r, 14));
      const manuell = num(col(posSheet, r, 15));
      const anz = num(col(posSheet, r, 17));
      if (nr == null && !benennung) continue;
      if (bedarf == null && belastung == null && spez == null && manuell == null && anz == null && !benennung) continue;
      const p = emptyPosition(nr ?? 1, num(col(posSheet, r, 4)) ?? 1, num(col(posSheet, r, 5)) ?? 0);
      p.benennung = benennung;
      p.t1Label = str(col(posSheet, r, 7)) || "T1:";
      p.t1Value = str(col(posSheet, r, 8));
      p.t2Label = str(col(posSheet, r, 9)) || "T2:";
      p.t2Value = str(col(posSheet, r, 10));
      p.bedarf = bedarf;
      p.maxBelastung = belastung;
      p.einheit = str(col(posSheet, r, 13));
      p.epSpezifisch = spez;
      p.epManuell = manuell;
      p.epBasis = "belastung";
      const qCell = posSheet[XLSX.utils.encode_cell({ r, c: 16 })];
      if (qCell?.f && /L\d+\s*\*\s*O\d+/.test(qCell.f)) p.epBasis = "bedarf";
      if (!qCell?.f && typeof qCell?.v === "number") p.epManuell = qCell.v;
      p.anz = anz;
      p.kg = num(col(posSheet, r, 19));
      p.bt = str(col(posSheet, r, 21));
      p.bemerkung = str(col(posSheet, r, 22));
      p.flags = {
        basis: ja(col(posSheet, r, 23)),
        var1: ja(col(posSheet, r, 24)),
        var2: ja(col(posSheet, r, 25)),
        var3: ja(col(posSheet, r, 26)),
        var4: ja(col(posSheet, r, 27)),
      };
      positionen.push(p);
    }
    result.positionen = positionen;
  }

  if (sumSheet) {
    const range = XLSX.utils.decode_range(sumSheet["!ref"] ?? "A1");
    const gruppen: Group[] = [];
    for (let r = 7; r <= range.e.r; r++) {
      const bt = str(col(sumSheet, r, 2));
      const beschreibung = str(col(sumSheet, r, 3));
      if (!bt && !beschreibung) continue;
      if (bt === "-" && beschreibung === "GESAMT") continue;
      if (!beschreibung) continue;
      const g: Group = {
        id: crypto.randomUUID(),
        bt,
        beschreibung,
        entwurf: str(col(sumSheet, r, 4)),
        beruecksichtigt: ja(col(sumSheet, r, 14)),
      };
      gruppen.push(g);
    }
    result.gruppen = gruppen;
    const projekt = str(col(sumSheet, 1, 14));
    if (projekt) result.projekt = projekt;
    const bearbeiterStand = str(col(sumSheet, 1, 16));
    if (bearbeiterStand) {
      const parts = bearbeiterStand.split("/");
      if (parts.length === 2) {
        result.bearbeiter = parts[0].trim();
        result.stand = parts[1].trim();
      }
    }
  }

  if (kgSheet) {
    const range = XLSX.utils.decode_range(kgSheet["!ref"] ?? "A1");
    const kg: { nr: number; name: string }[] = [];
    const seen = new Set<number>();
    for (let r = 0; r <= range.e.r; r++) {
      const nr = num(col(kgSheet, r, 1));
      const name = str(col(kgSheet, r, 2));
      if (nr == null || !name || seen.has(nr)) continue;
      seen.add(nr);
      kg.push({ nr, name });
    }
    result.kostengruppen = kg;
  }

  if (dropSheet) {
    const range = XLSX.utils.decode_range(dropSheet["!ref"] ?? "A1");
    const einheiten: string[] = [];
    for (let r = 3; r <= range.e.r; r++) {
      const e = str(col(dropSheet, r, 0));
      if (!e) continue;
      einheiten.push(e);
    }
    if (einheiten.length) result.einheiten = einheiten;
  }

  return result;
}

export function exportExcel(project: Project): Uint8Array {
  const wb = XLSX.utils.book_new();

  const kopf = [
    [project.firma],
    [project.adresse],
    [],
    ["Projekt", project.projekt],
    ["Bearbeiter / Stand", `${project.bearbeiter} / ${project.stand}`],
    [],
  ];

  const gs = groupSums(project);
  const sumRows: any[][] = [];
  sumRows.push(["BT", "Beschreibung", ...VARIANT_KEYS.map((v) => project.variantenNamen[v]), "berücksichtigt"]);
  for (const g of gs) {
    sumRows.push([
      g.bt,
      g.beschreibung,
      ...VARIANT_KEYS.map((v) => (g.summen[v] ? Math.round(g.summen[v]) : 0)),
      g.beruecksichtigt ? "ja" : "nein",
    ]);
  }
  const totals = totalSums(project, false);
  sumRows.push([
    "-",
    "GESAMT",
    ...VARIANT_KEYS.map((v) => Math.round(totals[v])),
    "",
  ]);
  const sumAoA = [...kopf, [], ...sumRows];
  const sumWs = XLSX.utils.aoa_to_sheet(sumAoA);
  sumWs["!cols"] = [{ wch: 6 }, { wch: 40 }, { wch: 14 }, { wch: 14 }, { wch: 14 }, { wch: 14 }, { wch: 14 }, { wch: 12 }];
  XLSX.utils.book_append_sheet(wb, sumWs, "SUM_Entwurf");

  const posHeader = [
    "Nr",
    "Ebene",
    "Unternr",
    "Benennung",
    "T1",
    "T2",
    "Bedarf",
    "max. Belastung",
    "Einheit",
    "EP spezifisch",
    "EP manuell",
    "EP",
    "Anzahl",
    "GP",
    "KG",
    "BT",
    "Bemerkung",
    ...VARIANT_KEYS.map((v) => project.variantenNamen[v]),
  ];
  const posRows: any[][] = project.positionen.map((p) => [
    p.nr,
    p.ebene,
    p.unternr,
    p.benennung,
    p.t1Value,
    p.t2Value,
    p.bedarf,
    p.maxBelastung,
    p.einheit,
    p.epSpezifisch,
    p.epManuell,
    roundTo(ep(p), 0),
    p.anz,
    gp(p),
    p.kg,
    p.bt,
    p.bemerkung,
    ...VARIANT_KEYS.map((v) => (p.flags[v] ? "ja" : "nein")),
  ]);
  const posWs = XLSX.utils.aoa_to_sheet([posHeader, ...posRows]);
  posWs["!cols"] = [
    { wch: 5 }, { wch: 6 }, { wch: 7 }, { wch: 42 }, { wch: 10 }, { wch: 8 },
    { wch: 10 }, { wch: 12 }, { wch: 9 }, { wch: 12 }, { wch: 12 }, { wch: 12 },
    { wch: 8 }, { wch: 12 }, { wch: 7 }, { wch: 6 }, { wch: 30 },
    ...VARIANT_KEYS.map(() => ({ wch: 8 })),
  ];
  XLSX.utils.book_append_sheet(wb, posWs, "POS");

  if (project.kostengruppen.length) {
    const kgWs = XLSX.utils.aoa_to_sheet([
      ["KG Nr.", "Kostengruppe lt. DIN 276 - 2018"],
      ...project.kostengruppen.map((k) => [k.nr, k.name]),
    ]);
    XLSX.utils.book_append_sheet(wb, kgWs, "KG_NR");
  }

  const dropWs = XLSX.utils.aoa_to_sheet([["Einheit"], ...project.einheiten.map((e) => [e])]);
  XLSX.utils.book_append_sheet(wb, dropWs, "drop");

  const out = XLSX.write(wb, { bookType: "xlsx", type: "array" }) as ArrayBuffer;
  return new Uint8Array(out);
}

export function exportName(project: Project): string {
  return `Kostenabschaetzung_${(project.projekt || "Projekt").replace(/[^\w\-]+/g, "_")}.xlsx`;
}
