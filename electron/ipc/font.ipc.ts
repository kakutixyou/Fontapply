import { ipcMain, IpcMainInvokeEvent } from 'electron';

// const API_BASE = 'http://localhost:8000';//非推奨
const API_BASE = 'http://127.0.0.1:8000';
// ── ヘルパー: タイムアウト付きの安全なFetch ──
async function apiFetch(path: string, options?: RequestInit): Promise<any> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      signal: controller.signal,
    });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`API ${res.status}: ${text || res.statusText}`);
    }
    return await res.json();
  } finally {
    clearTimeout(timeout);
  }
}

export function registerFontIpcHandlers(): void {
  // 開発中のホットリロードでハンドラーが重複登録されるのを防ぐ
  ipcMain.removeHandler('font:getGlyphData');
  ipcMain.removeHandler('font:generate');

  // ══════════════════════════════════════════════════════════════════
  // 大動脈 1: 文字データとメトリクスの取得
  // フロントエンドから呼ばれ、Pythonの /api/glyphs/{unicode} を叩く
  // ══════════════════════════════════════════════════════════════════
  ipcMain.handle(
    'font:getGlyphData',
    async (_event: IpcMainInvokeEvent, { unicode }: { unicode: string }) => {
      console.log(`[font.ipc] 文字データ取得リクエスト: U+${unicode}`);
      try {
        // Pythonから { glyph: {...}, metrics: {...} } を受け取る
        const data = await apiFetch(`/api/glyphs/${unicode}`);
        return data; 
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        console.error('[font.ipc] getGlyphData failed:', unicode, msg);
        // エラー時はフロントエンドが 'error' ステータスとして処理できるように返す
        return { error: msg };
      }
    }
  );

  // ══════════════════════════════════════════════════════════════════
  // 一時停止中の機能（エクスポート等）
  // ※バックエンド側を整理したため、フロントが呼ばないようモック化
  // ══════════════════════════════════════════════════════════════════
  ipcMain.handle('font:generate', async () => {
    return { error: "Export engine is currently upgrading to the new architecture." };
  });

  console.info('[font.ipc] registered font IPC handlers (Aorta version)');
}