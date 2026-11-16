import React, { createContext, useContext, useEffect, useState } from "react";
import { Project, defaultProject } from "./types";

const STORAGE_KEY = "kostenabschaetzung_v1";

interface Store {
  project: Project;
  setProject: (p: Project) => void;
  update: (fn: (p: Project) => void) => void;
  replaceData: (partial: Partial<Project>) => void;
  reset: () => void;
}

const StoreContext = createContext<Store | null>(null);

function load(): Project {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return { ...defaultProject(), ...parsed };
    }
  } catch {
    /* ignore */
  }
  return defaultProject();
}

export function StoreProvider({ children }: { children: React.ReactNode }) {
  const [project, setProject] = useState<Project>(load);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(project));
    } catch {
      /* ignore */
    }
  }, [project]);

  const update = (fn: (p: Project) => void) => {
    setProject((prev) => {
      const next = structuredClone(prev);
      fn(next);
      return next;
    });
  };

  const replaceData = (partial: Partial<Project>) => {
    setProject((prev) => ({ ...prev, ...partial }));
  };

  const reset = () => setProject(defaultProject());

  return (
    <StoreContext.Provider value={{ project, setProject, update, replaceData, reset }}>
      {children}
    </StoreContext.Provider>
  );
}

export function useStore(): Store {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error("StoreContext fehlt");
  return ctx;
}
