const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const fs = require("fs");
const path = require("path");

let win = null;

function createWindow() {
  win = new BrowserWindow({
    width: 1500,
    height: 950,
    minWidth: 1100,
    minHeight: 700,
    title: "Kostenabschätzung",
    autoHideMenuBar: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  win.setMenu(null);
  if (process.env.VITE_DEV_SERVER_URL) {
    win.loadURL(process.env.VITE_DEV_SERVER_URL);
  } else {
    win.loadFile(path.join(__dirname, "..", "dist", "index.html"));
  }
}

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

ipcMain.handle("datei-oeffnen", async (event, filters) => {
  const result = await dialog.showOpenDialog(win, {
    properties: ["openFile"],
    filters: filters || [{ name: "Excel-Liste", extensions: ["xlsx", "xlsm"] }],
  });
  if (result.canceled || result.filePaths.length === 0) return null;
  const filePath = result.filePaths[0];
  const data = fs.readFileSync(filePath);
  return { name: path.basename(filePath), path: filePath, data: new Uint8Array(data) };
});

ipcMain.handle("datei-speichern", async (event, vorschlag, data) => {
  const result = await dialog.showSaveDialog(win, {
    defaultPath: vorschlag,
    filters: [
      { name: "Excel-Liste", extensions: ["xlsx"] },
      { name: "Projektdatei", extensions: ["json"] },
    ],
  });
  if (result.canceled || !result.filePath) return null;
  fs.writeFileSync(result.filePath, Uint8Array.from(data));
  return result.filePath;
});

ipcMain.handle("pdf-drucken", async () => {
  const pdf = await win.webContents.printToPDF({
    printBackground: true,
    landscape: true,
    pageSize: "A4",
    margins: { top: 0.4, bottom: 0.4, left: 0.4, right: 0.4 },
  });
  const result = await dialog.showSaveDialog(win, {
    defaultPath: "Kostenabschaetzung.pdf",
    filters: [{ name: "PDF", extensions: ["pdf"] }],
  });
  if (result.canceled || !result.filePath) return null;
  fs.writeFileSync(result.filePath, pdf);
  return result.filePath;
});
