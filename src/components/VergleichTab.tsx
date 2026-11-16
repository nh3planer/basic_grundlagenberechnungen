import { useStore } from "../store";
import { groupSums, totalSums, fmtEUR } from "../calc";
import { VARIANT_KEYS } from "../types";

export default function VergleichTab() {
  const { project } = useStore();
  const gruppen = groupSums(project);
  const totals = totalSums(project, false);
  const basis = totals.basis || 1;
  const maxTotal = Math.max(...VARIANT_KEYS.map((v) => totals[v]), 1);

  const delta = totals[project.gesamtQuelle] - totals.basis;

  return (
    <div>
      <div className="kpi-row">
        {VARIANT_KEYS.map((v) => {
          const d = totals[v] - totals.basis;
          return (
            <div className="kpi" key={v}>
              <div className="label">{project.variantenNamen[v]}</div>
              <div className="value">{fmtEUR(totals[v])}</div>
              <div style={{ fontSize: 12, marginTop: 4 }}>
                {v === "basis" ? (
                  <span className="badge">Referenz</span>
                ) : d <= 0 ? (
                  <span className="delta-neg">{d === 0 ? "= Basis" : `↓ ${fmtEUR(Math.abs(d))}`}</span>
                ) : (
                  <span className="delta-pos">↑ {fmtEUR(d)}</span>
                )}
              </div>
              <div className="bar-wrap" style={{ marginTop: 8 }}>
                <div className="bar-fill" style={{ width: `${(totals[v] / maxTotal) * 100}%` }} />
              </div>
            </div>
          );
        })}
      </div>

      <div className="card">
        <h2>Variantenvergleich je Gruppe (BT)</h2>
        <div className="print-only">
          <h2>Variantenvergleich – {project.projekt}</h2>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table className="data">
            <thead>
              <tr>
                <th>BT</th>
                <th>Beschreibung</th>
                {VARIANT_KEYS.map((v) => (
                  <th key={v} className="num">{project.variantenNamen[v]}</th>
                ))}
                <th className="num">Δ zur Basis</th>
                <th className="num">anteilig</th>
              </tr>
            </thead>
            <tbody>
              {gruppen.map((g) => {
                const gTotal = Math.max(...VARIANT_KEYS.map((v) => g.summen[v]), 1);
                return (
                  <tr key={g.bt}>
                    <td>{g.bt}</td>
                    <td>{g.beschreibung}</td>
                    {VARIANT_KEYS.map((v) => (
                      <td key={v} className="num">{g.summen[v] ? fmtEUR(g.summen[v]) : "–"}</td>
                    ))}
                    <td className="num">
                      {g.summen.basis ? (
                        <span className={g.summen.var1 - g.summen.basis <= 0 ? "delta-neg" : "delta-pos"}>
                          {fmtEUR(g.summen.var1 - g.summen.basis)}
                        </span>
                      ) : (
                        "–"
                      )}
                    </td>
                    <td>
                      <div className="bar-wrap">
                        <div
                          className="bar-fill"
                          style={{ width: `${(g.summen.var1 / gTotal) * 100}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                );
              })}
              <tr className="total">
                <td colSpan={2}>GESAMT</td>
                {VARIANT_KEYS.map((v) => (
                  <td key={v} className="num">{fmtEUR(totals[v])}</td>
                ))}
                <td className="num">{fmtEUR(delta)}</td>
                <td></td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="hint">
          „Δ zur Basis" vergleicht {project.variantenNamen.var1} mit {project.variantenNamen.basis}.
          Die Gesamt-KPIs oben zeigen die Differenz jeder Variante zur Basis.
        </p>
      </div>
    </div>
  );
}
