import { useStore } from "../store";
import { VariantKey, VARIANT_KEYS } from "../types";

export default function ProjektTab() {
  const { project, update } = useStore();

  return (
    <div>
      <div className="card">
        <h2>Projektdaten</h2>
        <div className="grid2">
          <label className="field">
            <span>Firma</span>
            <input
              type="text"
              value={project.firma}
              onChange={(e) => update((p) => void (p.firma = e.target.value))}
            />
          </label>
          <label className="field">
            <span>Adresse</span>
            <input
              type="text"
              value={project.adresse}
              onChange={(e) => update((p) => void (p.adresse = e.target.value))}
            />
          </label>
          <label className="field">
            <span>Projekt</span>
            <input
              type="text"
              value={project.projekt}
              onChange={(e) => update((p) => void (p.projekt = e.target.value))}
            />
          </label>
          <label className="field">
            <span>Bearbeiter</span>
            <input
              type="text"
              value={project.bearbeiter}
              onChange={(e) => update((p) => void (p.bearbeiter = e.target.value))}
            />
          </label>
          <label className="field">
            <span>Stand</span>
            <input
              type="text"
              value={project.stand}
              onChange={(e) => update((p) => void (p.stand = e.target.value))}
            />
          </label>
        </div>
      </div>

      <div className="card">
        <h2>Varianten</h2>
        <div className="grid2">
          {VARIANT_KEYS.map((v: VariantKey) => (
            <label className="field" key={v}>
              <span>Bezeichnung {v === "basis" ? "(Basisvariante)" : ""}</span>
              <input
                type="text"
                value={project.variantenNamen[v]}
                onChange={(e) => update((p) => void (p.variantenNamen[v] = e.target.value))}
              />
            </label>
          ))}
        </div>
        <p className="hint">
          Jede Position kann über die Kontrollkästchen (ja/nein) den Varianten zugeordnet werden.
          Die Basisvariante entspricht der Spalte „POS/BASIS" in der Excel-Liste.
        </p>
      </div>

      <div className="card">
        <h2>Einheiten</h2>
        <div className="field">
          <span>Kommagetrennte Liste für die Einheiten-Auswahl</span>
          <textarea
            rows={2}
            value={project.einheiten.join(", ")}
            onChange={(e) =>
              update(
                (p) =>
                  void (p.einheiten = e.target.value
                    .split(",")
                    .map((s) => s.trim())
                    .filter(Boolean))
              )
            }
          />
        </div>
      </div>

      <div className="card">
        <h2>Kostengruppen (DIN 276)</h2>
        <p className="hint">
          {project.kostengruppen.length > 0
            ? project.kostengruppen.length +
              " Kostengruppen geladen. Beispiel KG 475: " +
              (project.kostengruppen.find((k) => k.nr === 475)?.name ?? "–")
            : "Noch keine Kostengruppen geladen – bitte im Tab ‚Import / Export / PDF' die Excel-Liste importieren."}
        </p>
      </div>
    </div>
  );
}
