const { app, BrowserWindow, Menu } = require("electron");
const path = require("path");
const fs = require("fs");

const isDev = process.env.NODE_ENV === "development" || !app.isPackaged;

// ── 语言 → 菜单文件映射 ─────────────────────────────
const MENU_FILES = {
  "zh":    "menu_zn_cn.json",   // 中文（简体）
  "zh-CN": "menu_zn_cn.json",
  "zh-TW": "menu_zn_cn.json",
  "ja":    "menu.json",         // 未翻译时回退英文
  "ko":    "menu.json",
};

function resolveMenuFile() {
  const locale = app.getLocale();                     // e.g. "zh-CN"
  const base = locale.split("-")[0];                  // e.g. "zh"
  const filename = MENU_FILES[locale] || MENU_FILES[base] || "menu.json";
  const resolved = path.join(__dirname, filename);

  // 翻译文件不存在则回退英文
  if (!fs.existsSync(resolved)) {
    return path.join(__dirname, "menu.json");
  }
  return resolved;
}

// ── 从 JSON 构建菜单 ────────────────────────────────
function buildMenu() {
  const menuPath = resolveMenuFile();
  const raw = fs.readFileSync(menuPath, "utf-8");
  const { menu } = JSON.parse(raw);

  return Menu.buildFromTemplate(
    menu.map((item) => ({
      label: item.label,
      submenu: item.submenu.map((sub) => {
        const entry = { role: sub.role };
        if (sub.type) entry.type = sub.type;
        if (sub.label) entry.label = sub.label;
        if (sub.accelerator) entry.accelerator = sub.accelerator;
        return entry;
      }),
    }))
  );
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    center: true,
    title: "Chat",
    icon: path.join(__dirname, "icon.png"),
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  Menu.setApplicationMenu(buildMenu());

  if (isDev) {
    const port = process.env.VITE_PORT || 5173;
    win.loadURL(`http://127.0.0.1:${port}`);
    win.webContents.openDevTools({ mode: "detach" });
  } else {
    win.loadFile(path.join(__dirname, "..", "dist", "index.html"));
  }
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
