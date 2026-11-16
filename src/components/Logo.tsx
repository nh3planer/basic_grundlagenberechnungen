import { useStore } from "../store";
import epLogo from "../assets/ep-logo.png?inline";

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
    <img
      src={epLogo}
      alt={project.firma}
      style={{ height: size, maxWidth: size * 5, objectFit: "contain" }}
    />
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
