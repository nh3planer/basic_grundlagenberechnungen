import { useState } from "react";
import { useStore } from "../store";
import { importExcel, exportExcel, exportName } from "../excel";
import { Project } from "../types";

declare global {
  interface Window {
    desktop?: {
      istDesktop: boolean;
      dateiOeffnen: (filters?: unknown) => Promise<{ name: string; data: Uint8Array } | null>;
      dateiSpeichern: (vorschlag: string, data: Uint8Array) => Promise<string | null>;
      pdfDrucken: () => Promise<string | null>;
    };
  }
}

function toast(msg: string) {
  const el = document.createElement("div");
  el.className = "toast";
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

export default function DatenTab() {
  const { project, replaceData, reset } = useStore();
  const [merge, setMerge] = useState(false);
  const [busy, setBusy] = useState(false);

  const handleImport = async () => {
    if (!window.desktop) {
      toast("Import ist nur in der Desktop-Anwendung verfügbar.");
      return;
    }
    const file = await window.desktop.dateiOeffnen();
    if (!file) return;
    setBusy(true);
    try {
      const data = importExcel(file.data);
      if (merge) {
        replaceData(data);
        toast(`"${file.name}" importiert (vorhandene Daten ersetzt).`);
      } else {
        const posImport = data.positionen ?? [];
        const grImport = data.gruppen ?? [];
        const kgNeu = data.kostengruppen ?? [];
        replaceData({
          positionen: [...project.positionen, ...posImport],
          gruppen: [
            ...project.gruppen,
            ...grImport.filter((g) => !project.gruppen.some((x) => x.bt === g.bt)),
          ],
          kostengruppen: kgNeu.length ? kgNeu : project.kostengruppen,
          einheiten: data.einheiten ?? project.einheiten,
          projekt: data.projekt || project.projekt,
          bearbeiter: data.bearbeiter || project.bearbeiter,
          stand: data.stand || project.stand,
        });
        toast(`"${file.name}" importiert: ${posImport.length} Position(en), ${grImport.length} Gruppe(n) hinzugefügt.`);
      }
    } catch (e) {
      toast("Import fehlgeschlagen: " + (e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const handleExport = async () => {
    const data = exportExcel(project);
    const name = exportName(project);
    if (window.desktop) {
      const pfad = await window.desktop.dateiSpeichern(name, data);
      if (pfad) toast("Gespeichert: " + pfad);
    } else {
      const blob = new Blob([data as unknown as BlobPart], {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = name;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const handleProjektSpeichern = async () => {
    const data = new TextEncoder().encode(JSON.stringify(project, null, 2));
    const name = `${(project.projekt || "Projekt").replace(/[^\w\-]+/g, "_")}.kproj.json`;
    if (window.desktop) {
      const pfad = await window.desktop.dateiSpeichern(name, data);
      if (pfad) toast("Projekt gespeichert: " + pfad);
    } else {
      const blob = new Blob([data as unknown as BlobPart], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = name;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const handleProjektLaden = async () => {
    if (!window.desktop) return;
    const file = await window.desktop.dateiOeffnen([
      { name: "Projektdatei", extensions: ["json", "kproj"] },
    ]);
    if (!file) return;
    try {
      const parsed = JSON.parse(new TextDecoder().decode(file.data)) as Project;
      replaceData(parsed);
      toast("Projekt geladen: " + file.name);
    } catch (e) {
      toast("Projektdatei ungültig: " + (e as Error).message);
    }
  };

  const handlePdf = async () => {
    if (window.desktop) {
      const pfad = await window.desktop.pdfDrucken();
      if (pfad) toast("PDF gespeichert: " + pfad);
    } else {
      window.print();
    }
  };

  return (
    <div>
      <div className="card">
        <h2>Excel-Import</h2>
        <p className="hint" style={{ marginBottom: 12 }}>
          Liest die Blätter POS (Positionen), SUM_Entwurf (Gruppen), KG_NR (Kostengruppen) und drop
          (Einheiten) der bestehenden Kostenliste ein – Werte, Formeln und Logik werden in der
          Software neu aufgebaut.
        </p>
        <div className="toolbar">
          <button className="primary" onClick={handleImport} disabled={busy}>
            {busy ? "Importiere…" : "Excel-Liste importieren…"}
          </button>
          <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <input
              type="checkbox"
              className="flag"
              checked={merge}
              onChange={(e) => setMerge(e.target.checked)}
            />
            Bestehende Daten vollständig ersetzen
          </label>
        </div>
      </div>

      <div className="card">
        <h2>Export</h2>
        <div className="toolbar">
          <button className="ghost" onClick={handleExport}>Als Excel-Liste speichern…</button>
          <button className="ghost" onClick={handleProjektSpeichern}>Projektdatei speichern…</button>
          <button className="ghost" onClick={handleProjektLaden}>Projektdatei laden…</button>
          <button className="primary" onClick={handlePdf}>PDF erstellen…</button>
        </div>
        <p className="hint">
          Der PDF-Export druckt das aktuell geöffnete Blatt (Übersicht, Positionen oder
          Variantenvergleich) im A4-Querformat mit Firmenkopf.
        </p>
      </div>

      <div className="card">
        <h2>Projekt zurücksetzen</h2>
        <button
          className="ghost"
          onClick={() => {
            if (confirm("Alle Daten löschen und neu beginnen?")) reset();
          }}
        >
          Neues Projekt (alles löschen)
        </button>
      </div>
    </div>
  );
}
