import { Position, Project, VariantKey, VARIANT_KEYS } from "./types";

export function roundTo(v: number, digits: number): number {
  const f = Math.pow(10, digits);
  return Math.round(v * f) / f;
}

export function ep(pos: Position): number {
  if (pos.epManuell != null && pos.epManuell > 0) return pos.epManuell;
  const primaer = pos.epBasis === "bedarf" ? pos.bedarf : pos.maxBelastung;
  const fallback = pos.epBasis === "bedarf" ? pos.maxBelastung : pos.bedarf;
  const menge = primaer ?? fallback ?? 0;
  return menge * (pos.epSpezifisch ?? 0);
}

export function istKalkulationszeile(pos: Position): boolean {
  return pos.unternr > 0;
}

export function gp(pos: Position): number {
  if (!istKalkulationszeile(pos)) return 0;
  return roundTo((pos.anz ?? 0) * ep(pos), -2);
}

export function gpVariant(pos: Position, variant: VariantKey): number {
  if (!pos.flags[variant]) return 0;
  return gp(pos);
}

export function sumVariant(positionen: Position[], variant: VariantKey, bt?: string): number {
  return positionen.reduce(
    (s, p) => s + (bt == null || p.bt === bt ? gpVariant(p, variant) : 0),
    0
  );
}

export function sumKg(positionen: Position[], variant: VariantKey, kg: number): number {
  return positionen.reduce((s, p) => s + (p.kg === kg ? gpVariant(p, variant) : 0), 0);
}

export interface GroupSum {
  bt: string;
  beschreibung: string;
  entwurf: string;
  beruecksichtigt: boolean;
  summen: Record<VariantKey, number>;
}

export function groupSums(project: Project): GroupSum[] {
  return project.gruppen.map((g) => {
    const summen = {} as Record<VariantKey, number>;
    for (const v of VARIANT_KEYS) summen[v] = sumVariant(project.positionen, v, g.bt);
    return {
      bt: g.bt,
      beschreibung: g.beschreibung,
      entwurf: g.entwurf,
      beruecksichtigt: g.beruecksichtigt,
      summen,
    };
  });
}

export function totalSums(project: Project, nurBeruecksichtigt: boolean): Record<VariantKey, number> {
  const result = {} as Record<VariantKey, number>;
  const relevant = nurBeruecksichtigt
    ? project.positionen.filter((p) => {
        const g = project.gruppen.find((gr) => gr.bt === p.bt);
        return g == null || g.beruecksichtigt;
      })
    : project.positionen;
  for (const v of VARIANT_KEYS) result[v] = sumVariant(relevant, v);
  return result;
}

export function kgSums(project: Project, variant: VariantKey): { kg: number; name: string; sum: number }[] {
  const map = new Map<number, number>();
  for (const p of project.positionen) {
    if (p.kg == null) continue;
    map.set(p.kg, (map.get(p.kg) ?? 0) + gpVariant(p, variant));
  }
  return [...map.entries()]
    .map(([kg, sum]) => ({ kg, name: kgName(project, kg), sum }))
    .sort((a, b) => b.sum - a.sum);
}

export function kgName(project: Project, kg: number): string {
  return project.kostengruppen.find((k) => k.nr === kg)?.name ?? "";
}

export function fmt(v: number): string {
  return v.toLocaleString("de-AT", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

export function fmtEUR(v: number): string {
  return fmt(v) + " €";
}
