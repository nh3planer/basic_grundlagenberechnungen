import { useStore } from "../store";
import { groupSums, totalSums, kgSums, fmtEUR } from "./../calc";
import { VARIANT_KEYS, VariantKey, Group } from "../types";
import { PrintHeader } from "./Logo";

export default function UebersichtTab() {
  const { project, update } = useStore();
  const gruppen = groupSums(project);
  const totals = totalSums(project, false);
  const totalsBeruecks = totalSums(project, true);
  const quelle = project.gesamtQuelle;
  const kgListe = kgSums(project, quelle);
  const kgTotal = kgListe.reduce((s, k) => s + k.sum, 0) || 1;

  const addGruppe = () => {
    const g: Group = {
      id: crypto.randomUUID(),
      bt: "NEU",
      beschreibung: "Neue Gruppe",
      entwurf: "",
      beruecksichtigt: true,
    };
    update((p) => void p.gruppen.push(g));
  };

  return (
    <div>
      <div className="kpi-row no-print">
        {VARIANT_KEYS.map((v) => (
          <div className="kpi" key={v}>
            <div className="label">{project.variantenNamen[v]}</div>
            <div className="value">{fmtEUR(totals[v])}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="toolbar no-print">
          <button className="primary" onClick={addGruppe}>+ Gruppe</button>
          <label className="field" style={{ width: 220 }}>
            <span>Gesamtbildung nach Variante</span>
            <select
              value={quelle}
              onChange={(e) => update((p) => void (p.gesamtQuelle = e.target.value as VariantKey))}
            >
              {VARIANT_KEYS.map((v) => (
                <option key={v} value={v}>{project.variantenNamen[v]}</option>
              ))}
            </select>
          </label>
        </div>
        <PrintHeader titel="Kostenberechnung – Entwurf" />
        <div style={{ overflowX: "auto" }}>
          <table className="data">
            <thead>
              <tr>
                <th>BT</th>
                <th>Beschreibung</th>
                <th>Entwurf / Umfang</th>
                {VARIANT_KEYS.map((v) => (
                  <th key={v} className="num">{project.variantenNamen[v]}</th>
                ))}
                <th className="num">Gesamt</th>
                <th className="flag-cell">berücksichtigt</th>
                <th className="no-print"></th>
              </tr>
            </thead>
            <tbody>
              {gruppen.map((g) => {
                const gruppe = project.gruppen.find((gr) => gr.bt === g.bt)!;
                return (
                  <tr key={gruppe.id}>
                    <td>
                      <input
                        type="text"
                        value={g.bt}
                        style={{ width: 48 }}
                        onChange={(e) => update((p) => {
                          const gr = p.gruppen.find((x) => x.id === gruppe.id);
                          if (gr) {
                            const alt = gr.bt;
                            gr.bt = e.target.value;
                            for (const pos of p.positionen) if (pos.bt === alt) pos.bt = gr.bt;
                          }
                        })}
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        value={g.beschreibung}
                        onChange={(e) => update((p) => {
                          const gr = p.gruppen.find((x) => x.id === gruppe.id);
                          if (gr) gr.beschreibung = e.target.value;
                        })}
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        value={g.entwurf}
                        onChange={(e) => update((p) => {
                          const gr = p.gruppen.find((x) => x.id === gruppe.id);
                          if (gr) gr.entwurf = e.target.value;
                        })}
                      />
                    </td>
                    {VARIANT_KEYS.map((v) => (
                      <td key={v} className="num">{g.summen[v] ? fmtEUR(g.summen[v]) : "–"}</td>
                    ))}
                    <td className="num">
                      {g.beruecksichtigt ? fmtEUR(g.summen[quelle]) : "–"}
                    </td>
                    <td className="flag-cell">
                      <input
                        type="checkbox"
                        className="flag"
                        checked={g.beruecksichtigt}
                        onChange={(e) => update((p) => {
                          const gr = p.gruppen.find((x) => x.id === gruppe.id);
                          if (gr) gr.beruecksichtigt = e.target.checked;
                        })}
                      />
                    </td>
                    <td className="no-print">
                      <button
                        className="danger"
                        onClick={() =>
                          update((p) => void (p.gruppen = p.gruppen.filter((x) => x.id !== gruppe.id)))
                        }
                      >✕</button>
                    </td>
                  </tr>
                );
              })}
              <tr className="total">
                <td colSpan={2}>GESAMT (alle Gruppen)</td>
                <td></td>
                {VARIANT_KEYS.map((v) => (
                  <td key={v} className="num">{fmtEUR(totals[v])}</td>
                ))}
                <td className="num">{fmtEUR(totalsBeruecks[quelle])}</td>
                <td colSpan={2}></td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="hint no-print">
          Spalte „Gesamt" zeigt die Summen der gewählten Variante ({project.variantenNamen[quelle]}) für
          berücksichtigte Gruppen – analog zur Excel-Logik (berücksichtigt = ja/nein).
        </p>
      </div>

      <div className="card">
        <h2>Anteil Kostengruppen – {project.variantenNamen[quelle]}</h2>
        <table className="data">
          <thead>
            <tr>
              <th>KG</th>
              <th>Kostengruppe</th>
              <th className="num">Summe</th>
              <th className="num">Anteil</th>
              <th style={{ width: 220 }}></th>
            </tr>
          </thead>
          <tbody>
            {kgListe.map((k) => (
              <tr key={k.kg}>
                <td>{k.kg}</td>
                <td>{k.name}</td>
                <td className="num">{fmtEUR(k.sum)}</td>
                <td className="num">{((k.sum / kgTotal) * 100).toFixed(1)} %</td>
                <td>
                  <div className="bar-wrap">
                    <div className="bar-fill" style={{ width: `${(k.sum / kgTotal) * 100}%` }} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
