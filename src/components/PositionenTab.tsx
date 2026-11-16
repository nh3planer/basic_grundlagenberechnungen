import { useMemo, useState } from "react";
import { useStore } from "../store";
import { Position, VariantKey, VARIANT_KEYS, emptyPosition } from "../types";
import { ep, gp, roundTo, fmtEUR, istKalkulationszeile } from "../calc";
import { PrintHeader } from "./Logo";

function sortPos(a: Position, b: Position) {
  return a.nr - b.nr || a.ebene - b.ebene || a.unternr - b.unternr;
}

export default function PositionenTab() {
  const { project, update } = useStore();
  const [filter, setFilter] = useState<"alle" | VariantKey>("alle");
  const [suche, setSuche] = useState("");

  const positionen = useMemo(() => [...project.positionen].sort(sortPos), [project.positionen]);

  const sichtbar = useMemo(() => {
    const q = suche.trim().toLowerCase();
    return positionen.filter((p) => {
      if (filter !== "alle" && istKalkulationszeile(p) && !p.flags[filter]) return false;
      if (!q) return true;
      return (
        p.benennung.toLowerCase().includes(q) ||
        p.bemerkung.toLowerCase().includes(q) ||
        p.bt.toLowerCase().includes(q)
      );
    });
  }, [positionen, filter, suche]);

  const setPos = (id: string, fn: (p: Position) => void) =>
    update((proj) => {
      const p = proj.positionen.find((x) => x.id === id);
      if (p) fn(p);
    });

  const addPosition = (ebene = 2) => {
    const maxNr = positionen.reduce((m, p) => Math.max(m, p.nr), 0);
    const pos = emptyPosition(maxNr, ebene, 0);
    update((p) => void p.positionen.push(pos));
  };

  const addChapter = () => {
    const maxNr = positionen.reduce((m, p) => Math.max(m, p.nr), 0) + 1;
    const pos = emptyPosition(maxNr, 1, 0);
    pos.benennung = "Neues Gewerk";
    update((p) => void p.positionen.push(pos));
  };

  const dupPosition = (id: string) =>
    update((proj) => {
      const idx = proj.positionen.findIndex((x) => x.id === id);
      if (idx < 0) return;
      const copy = structuredClone(proj.positionen[idx]);
      copy.id = crypto.randomUUID();
      copy.unternr = proj.positionen.filter((p) => p.nr === copy.nr && p.ebene === copy.ebene).reduce(
        (m, p) => Math.max(m, p.unternr),
        0
      ) + 1;
      proj.positionen.splice(idx + 1, 0, copy);
    });

  const delPosition = (id: string) =>
    update((p) => void (p.positionen = p.positionen.filter((x) => x.id !== id)));

  const summe = positionen.reduce((s, p) => s + gp(p), 0);

  const numCell = (pos: Position, field: "bedarf" | "maxBelastung" | "epSpezifisch" | "epManuell" | "anz") => (
    <input
      type="number"
      value={pos[field] ?? ""}
      onChange={(e) =>
        setPos(pos.id, (p) => void (p[field] = e.target.value === "" ? null : Number(e.target.value)))
      }
    />
  );

  return (
    <div>
      <div className="card no-print">
        <div className="toolbar">
          <button className="primary" onClick={() => addPosition(2)}>+ Position</button>
          <button className="ghost" onClick={addChapter}>+ Gewerk / Kapitel</button>
          <select value={filter} onChange={(e) => setFilter(e.target.value as typeof filter)}>
            <option value="alle">Alle Varianten</option>
            {VARIANT_KEYS.map((v) => (
              <option key={v} value={v}>
                {project.variantenNamen[v]}
              </option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Suchen (Benennung, Bemerkung, BT)…"
            value={suche}
            onChange={(e) => setSuche(e.target.value)}
            style={{ maxWidth: 260 }}
          />
          <span style={{ marginLeft: "auto", fontWeight: 600 }}>
            Summe (Basis, gefiltert): {fmtEUR(summe)}
          </span>
        </div>
      </div>

      <div className="card">
        <PrintHeader titel="Berechnungsblatt (POS)" />
        <div style={{ overflowX: "auto" }}>
          <table className="data pos-table">
            <thead>
              <tr>
                <th>Nr</th>
                <th style={{ minWidth: 220 }}>Benennung</th>
                <th>T1</th>
                <th>T2</th>
                <th className="num">Bedarf</th>
                <th className="num">max. Bel.</th>
                <th title="EP-Basis: L = Bedarf, M = max. Belastung">Basis</th>
                <th>EH</th>
                <th className="num">EP spez.</th>
                <th className="num">EP man.</th>
                <th className="num">EP</th>
                <th className="num">ANZ</th>
                <th className="num">GP</th>
                <th>KG</th>
                <th>BT</th>
                <th style={{ minWidth: 160 }}>Bemerkung</th>
                {VARIANT_KEYS.map((v) => (
                  <th key={v} className="flag-cell">
                    {project.variantenNamen[v].replace("VAR ", "V")}
                  </th>
                ))}
                <th className="no-print"></th>
              </tr>
            </thead>
            <tbody>
              {sichtbar.map((pos) => {
                const isChapter = pos.ebene === 1 && !istKalkulationszeile(pos);
                return (
                  <tr key={pos.id} className={isChapter ? "ebene1" : ""}>
                    <td className="num" style={{ whiteSpace: "nowrap" }}>
                      {pos.nr}.{pos.ebene}
                      {pos.unternr ? `.${pos.unternr}` : ""}
                    </td>
                    <td>
                      <input
                        type="text"
                        value={pos.benennung}
                        onChange={(e) => setPos(pos.id, (p) => void (p.benennung = e.target.value))}
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        value={pos.t1Value}
                        style={{ width: 60 }}
                        onChange={(e) => setPos(pos.id, (p) => void (p.t1Value = e.target.value))}
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        value={pos.t2Value}
                        style={{ width: 60 }}
                        onChange={(e) => setPos(pos.id, (p) => void (p.t2Value = e.target.value))}
                      />
                    </td>
                    <td className="num">{isChapter ? "" : numCell(pos, "bedarf")}</td>
                    <td className="num">{isChapter ? "" : numCell(pos, "maxBelastung")}</td>
                    <td>
                      {isChapter ? null : (
                        <select
                          value={pos.epBasis}
                          onChange={(e) =>
                            setPos(pos.id, (p) => void (p.epBasis = e.target.value as "bedarf" | "belastung"))
                          }
                          style={{ width: 46 }}
                        >
                          <option value="belastung">M</option>
                          <option value="bedarf">L</option>
                        </select>
                      )}
                    </td>
                    <td>
                      {isChapter ? null : (
                        <select
                          value={pos.einheit}
                          onChange={(e) => setPos(pos.id, (p) => void (p.einheit = e.target.value))}
                        >
                          <option value=""></option>
                          {project.einheiten.map((e) => (
                            <option key={e} value={e}>{e}</option>
                          ))}
                        </select>
                      )}
                    </td>
                    <td className="num">{isChapter ? "" : numCell(pos, "epSpezifisch")}</td>
                    <td className="num">{isChapter ? "" : numCell(pos, "epManuell")}</td>
                    <td className="num computed">{isChapter ? "" : fmtEUR(roundTo(ep(pos), 0))}</td>
                    <td className="num">{isChapter ? "" : numCell(pos, "anz")}</td>
                    <td className="num computed" style={{ fontWeight: 600 }}>
                      {isChapter ? "" : fmtEUR(gp(pos))}
                    </td>
                    <td>
                      {isChapter ? null : (
                        <select
                          value={pos.kg ?? ""}
                          onChange={(e) =>
                            setPos(
                              pos.id,
                              (p) => void (p.kg = e.target.value === "" ? null : Number(e.target.value))
                            )
                          }
                          style={{ width: 80 }}
                        >
                          <option value=""></option>
                          {project.kostengruppen.map((k) => (
                            <option key={k.nr} value={k.nr}>
                              {k.nr}
                            </option>
                          ))}
                        </select>
                      )}
                    </td>
                    <td>
                      <input
                        type="text"
                        value={pos.bt}
                        style={{ width: 55 }}
                        list="bt-liste"
                        onChange={(e) => setPos(pos.id, (p) => void (p.bt = e.target.value))}
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        value={pos.bemerkung}
                        onChange={(e) => setPos(pos.id, (p) => void (p.bemerkung = e.target.value))}
                      />
                    </td>
                    {VARIANT_KEYS.map((v) => (
                      <td key={v} className="flag-cell">
                        <input
                          type="checkbox"
                          className="flag"
                          checked={pos.flags[v]}
                          onChange={(e) => setPos(pos.id, (p) => void (p.flags[v] = e.target.checked))}
                        />
                      </td>
                    ))}
                    <td className="no-print" style={{ whiteSpace: "nowrap" }}>
                      <button className="danger" title="Duplizieren" onClick={() => dupPosition(pos.id)}>⧉</button>
                      <button className="danger" title="Löschen" onClick={() => delPosition(pos.id)}>✕</button>
                    </td>
                  </tr>
                );
              })}
              <tr className="total">
                <td colSpan={12}>SUMME (alle Positionen, Basis)</td>
                <td className="num">{fmtEUR(summe)}</td>
                <td colSpan={VARIANT_KEYS.length + 5}></td>
              </tr>
            </tbody>
          </table>
        </div>
        <datalist id="bt-liste">
          {project.gruppen.map((g) => (
            <option key={g.id} value={g.bt}>
              {g.beschreibung}
            </option>
          ))}
        </datalist>
        <p className="hint no-print">
          EP = EP manuell, falls vorhanden, sonst max. Belastung × EP spezifisch. GP = Anzahl × EP
          (gerundet). Gewerkszeilen (Ebene 1) dienen der Gliederung. Kontrollkästchen ordnen die
          Position den Varianten zu.
        </p>
      </div>
    </div>
  );
}
