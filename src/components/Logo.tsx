import { useStore } from "../store";

export function Logo({ size = 34 }: { size?: number }) {
  const { project } = useStore();
  if (project.logo) {
    return (
      <img
        src={project.logo}
        alt={project.firma}
        style={{ height: size, maxWidth: size * 5, objectFit: "contain" }}
      />
    );
  }
  return (
    <div
      style={{
        height: size,
        minWidth: size,
        padding: "0 8px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#1a5fb4",
        color: "#fff",
        fontWeight: 700,
        fontSize: size * 0.4,
        borderRadius: size * 0.22,
        letterSpacing: 0.5,
      }}
    >
      {project.logoKuerzel || "Logo"}
    </div>
  );
}

export function PrintHeader({ titel }: { titel: string }) {
  const { project } = useStore();
  return (
    <div className="print-kopf print-only">
      <div className="print-kopf-links">
        <Logo size={30} />
        <div>
          <strong>{project.firma}</strong>
          <div>{project.adresse}</div>
        </div>
      </div>
      <div className="print-kopf-rechts">
        <strong>{titel}</strong>
        <div>{project.projekt}</div>
        <div>
          {project.bearbeiter} / {project.stand}
        </div>
      </div>
    </div>
  );
}
