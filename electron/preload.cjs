const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("desktop", {
  istDesktop: true,
  dateiOeffnen: (filters) => ipcRenderer.invoke("datei-oeffnen", filters),
  dateiSpeichern: (vorschlag, data) => ipcRenderer.invoke("datei-speichern", vorschlag, data),
  pdfDrucken: () => ipcRenderer.invoke("pdf-drucken"),
});
