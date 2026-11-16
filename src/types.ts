export const VARIANT_KEYS = ["basis", "var1", "var2", "var3", "var4"] as const;
export type VariantKey = (typeof VARIANT_KEYS)[number];

export interface Position {
  id: string;
  nr: number;
  ebene: number;
  unternr: number;
  benennung: string;
  t1Label: string;
  t1Value: string;
  t2Label: string;
  t2Value: string;
  bedarf: number | null;
  maxBelastung: number | null;
  einheit: string;
  epSpezifisch: number | null;
  epManuell: number | null;
  epBasis: "bedarf" | "belastung";
  anz: number | null;
  kg: number | null;
  bt: string;
  bemerkung: string;
  flags: Record<VariantKey, boolean>;
}

export interface Group {
  id: string;
  bt: string;
  beschreibung: string;
  entwurf: string;
  beruecksichtigt: boolean;
}

export interface Project {
  firma: string;
  adresse: string;
  logo: string;
  logoKuerzel: string;
  projekt: string;
  bearbeiter: string;
  stand: string;
  variantenNamen: Record<VariantKey, string>;
  gesamtQuelle: VariantKey;
  einheiten: string[];
  kostengruppen: { nr: number; name: string }[];
  positionen: Position[];
  gruppen: Group[];
}

export const DEFAULT_EINHEITEN = [
  "Stk", "Pa", "lfm", "kg", "kg/h", "kW", "m²", "m² BGF", "m³", "m³/h", "m³/min", "MW", "PS",
];

export function emptyPosition(nr = 1, ebene = 1, unternr = 0): Position {
  return {
    id: crypto.randomUUID(),
    nr,
    ebene,
    unternr,
    benennung: "",
    t1Label: "T1:",
    t1Value: "",
    t2Label: "T2:",
    t2Value: "",
    bedarf: null,
    maxBelastung: null,
    einheit: "",
    epSpezifisch: null,
    epManuell: null,
    epBasis: "belastung",
    anz: null,
    kg: null,
    bt: "",
    bemerkung: "",
    flags: { basis: true, var1: false, var2: false, var3: false, var4: false },
  };
}

export function defaultProject(): Project {
  const today = new Date().toLocaleDateString("de-AT");
  return {
    firma: "Eckert & Partner beratende Ingenieure GmbH",
    adresse: "Adamgasse 21, 6120 Innsbruck",
    logo: "",
    logoKuerzel: "E&P",
    projekt: "",
    bearbeiter: "",
    stand: today,
    variantenNamen: { basis: "BASIS", var1: "VAR 1", var2: "VAR 2", var3: "VAR 3", var4: "VAR 4" },
    gesamtQuelle: "basis",
    einheiten: [...DEFAULT_EINHEITEN],
    kostengruppen: [],
    positionen: [],
    gruppen: [],
  };
}
