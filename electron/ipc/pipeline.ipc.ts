// webforge-ai-desktop/electron/ipc/pipeline.ipc.ts
import { ipcMain, BrowserWindow } from 'electron';
import WebSocket from 'ws';

let wsClient: WebSocket | null = null;
let mainWindowRef: BrowserWindow | null = null;

export function setupPipelineIPC(mainWindow: BrowserWindow) {
  mainWindowRef = mainWindow;

  // PythonバックエンドのWebSocketに接続
  const connectWebSocket = () => {
    const backendUrl =
      process.env.FONT_API_BASE_URL ||
      process.env.WEBFORGE_FONT_API_BASE_URL ||
      'http://127.0.0.1:8000';
    const websocketUrl = new URL('/ws/pipeline', backendUrl);
    websocketUrl.protocol = websocketUrl.protocol === 'https:' ? 'wss:' : 'ws:';
    wsClient = new WebSocket(websocketUrl);

    wsClient.on('message', (data) => {
      const payload = JSON.parse(data.toString());
      // React側の window.electronAPI.onPipelineUpdate に流し込む
      if (mainWindowRef && !mainWindowRef.isDestroyed()) {
        mainWindowRef.webContents.send('ai-pipeline:update', payload);
      }
    });

    wsClient.on('close', () => {
      console.log('Pipeline WS closed. Reconnecting in 3s...');
      setTimeout(connectWebSocket, 3000);
    });
  };

  connectWebSocket();

  // React -> Electron (トグルの変更)
  ipcMain.handle('ai-pipeline:set-toggle', async (_event, { key, enabled }) => {
    if (wsClient && wsClient.readyState === WebSocket.OPEN) {
      wsClient.send(JSON.stringify({ action: 'SET_TOGGLE', key, enabled }));
    }
  });

  // React -> Electron (抽出リクエスト)
  ipcMain.handle('ai-pipeline:request-extract', async (_event, unicode) => {
    if (wsClient && wsClient.readyState === WebSocket.OPEN) {
      wsClient.send(JSON.stringify({ action: 'REQUEST_EXTRACT', unicode }));
    }
  });
}