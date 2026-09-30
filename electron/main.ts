import { app, BrowserWindow, ipcMain } from 'electron';
import path from 'path';

// 🚨 修正箇所1: electron-is-dev のインポートを削除

import { registerFontIpcHandlers } from './ipc/font.ipc';
import { initHttpClient } from './ipc/utils';

let mainWindow: BrowserWindow | null = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 768,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      // enableRemoteModule: false, <- 🚨 最新のElectronでは非推奨・不要なのでコメントアウト推奨
      sandbox: true,
    },
  });

  // 🚨 修正箇所2: app.isPackaged を使って開発環境かどうかを判定する
  // アプリがパッケージ化されていなければ（!）開発環境（isDev）という判定です
  const isDev = !app.isPackaged;

  const startUrl = isDev
    ? 'http://localhost:5173'
    : `file://${path.join(__dirname, '../dist/renderer/index.html')}`;

  mainWindow.loadURL(startUrl);

  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.on('ready', () => {
  const backendUrl = process.env.FONT_API_BASE_URL || process.env.WEBFORGE_FONT_API_BASE_URL || 'http://127.0.0.1:8000';

  try {
    initHttpClient({ baseUrl: backendUrl, timeoutMs: 30_000, retries: 2 });
    registerFontIpcHandlers();
    console.info('[main] Font IPC initialized', { backendUrl });
  } catch (error) {
    console.error('[main] Failed to initialize Font IPC', error);
    app.quit();
    return;
  }

  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

// IPC Handlers
ipcMain.handle('project:create', async (_event, projectData) => {
  // TODO: Implement project creation
  return { success: true, projectId: 'new-project-id' };
});

ipcMain.handle('python:status', async () => {
  // TODO: Check Python backend status
  return { connected: true, version: '1.0.0' };
});