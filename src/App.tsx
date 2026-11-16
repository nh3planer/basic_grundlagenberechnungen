import { useState } from "react";
import { useStore } from "./store";
import { totalSums, fmtEUR } from "./calc";
import { VARIANT_KEYS } from "./types";
import ProjektTab from "./components/ProjektTab";
import PositionenTab from "./components/PositionenTab";
import UebersichtTab from "./components/UebersichtTab";
import VergleichTab from "./components/VergleichTab";
import DatenTab from "./components/DatenTab";
import { Logo } from "./components/Logo";

const TABS = [
  { id: "uebersicht", label: "Übersicht (SUM_Entwurf)" },
  { id: "positionen", label: "Positionen (POS)" },
  { id: "vergleich", label: "Variantenvergleich" },
  { id: "projekt", label: "Projekt" },
  { id: "daten", label: "Import / Export / PDF" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function App() {
  const { project } = useStore();
  const [tab, setTab] = useState<TabId>("uebersicht");
  const totals = totalSums(project, false);

  return (
    <div className="app">
      <header className="topbar">
        <Logo size={36} />
        <div className="meta">
          <div className="projekt">{project.projekt || "Neues Projekt"}</div>
          <div className="sub">
            {project.firma} · {project.bearbeiter || "–"} / {project.stand}
          </div>
        </div>
        <div style={{ textAlign: "right", fontSize: 12, color: "#9fb2cc" }}>
          {VARIANT_KEYS.map((v) => (
            <div key={v}>
              {project.variantenNamen[v]}: {fmtEUR(totals[v])}
            </div>
          ))}
        </div>
      </header>
      <nav className="tabs">
        {TABS.map((t) => (
          <button key={t.id} className={tab === t.id ? "active" : ""} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </nav>
      <main className="main">
        {tab === "uebersicht" && <UebersichtTab />}
        {tab === "positionen" && <PositionenTab />}
        {tab === "vergleich" && <VergleichTab />}
        {tab === "projekt" && <ProjektTab />}
        {tab === "daten" && <DatenTab />}
      </main>
    </div>
  );
}
