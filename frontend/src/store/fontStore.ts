// webforge-ai-desktop/frontend/src/store/fontStore.ts

import { create } from 'zustand';
import type { 
  GlyphData, 
  AnchorPoint, 
  Vec2, 
  PointType, 
  FontMetrics 
} from '../components/font/GlyphEditor.types';

// ══════════════════════════════════════════════════════════════════
// 1. Python JSON → フロントエンド用データへの変換 (Adapter)
// ══════════════════════════════════════════════════════════════════

/**
 * Pythonの snake_case レスポンスをフロントエンドの GlyphData に変換します。
 * 旧仕様の x, y 直書きから、新仕様の pos: { x, y } へマッピングします。
 */
export function fromPythonGlyph(raw: Record<string, unknown>): GlyphData {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const contours = (raw.contours as any[] ?? []).map((c: any) => ({
    id: String(c.id ?? c.contour_id ?? `c_${Math.random().toString(36).substring(7)}`),
    closed: Boolean(c.closed ?? true),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    points: (c.points as any[] ?? []).map((p: any): AnchorPoint => ({
      id: String(p.id ?? p.point_id),
      pos: { x: Number(p.x), y: Number(p.y) },
      type: (p.type ?? 'corner') as PointType,
      handleIn: p.handle_in ? { x: Number(p.handle_in.x), y: Number(p.handle_in.y) } : null,
      handleOut: p.handle_out ? { x: Number(p.handle_out.x), y: Number(p.handle_out.y) } : null,
      linked: p.type === 'smooth',
    })),
  }));

  return {
    id: String(raw.unicode ?? '0000'), // 一意なIDとしてUnicodeを使用
    char: String(raw.char ?? ''),
    unicode: String(raw.unicode ?? '0000'),
    width: Number(raw.width ?? 500),
    contours,
  };
}

/**
 * Pythonのメトリクスデータをフロントエンド用に変換します。
 */
export function fromPythonMetrics(raw: Record<string, unknown>): FontMetrics {
  return {
    ascender: Number(raw.ascender ?? 720),
    capHeight: Number(raw.cap_height ?? 680),
    xHeight: Number(raw.x_height ?? 490),
    baseline: 0,
    descender: Number(raw.descender ?? -200),
    lsb: Number(raw.lsb ?? 80),
    rsb: Number(raw.rsb ?? 72),
  };
}

export const DEFAULT_METRICS: FontMetrics = {
  ascender: 720,
  capHeight: 680,
  xHeight: 490,
  baseline: 0,
  descender: -200,
  lsb: 80,
  rsb: 72,
};

// ══════════════════════════════════════════════════════════════════
// 2. ストアの型定義
// ══════════════════════════════════════════════════════════════════

interface FontStoreState {
  currentGlyph: GlyphData | null;
  fontMetrics: FontMetrics;
  
  // Undo/Redo 履歴
  undoStack: GlyphData[];
  redoStack: GlyphData[];

  // ── データセット ──
  setCurrentGlyph: (glyph: GlyphData | Record<string, unknown>) => void;
  setFontMetrics: (metrics: FontMetrics | Record<string, unknown>) => void;

  // ── 編集操作 ──
  movePoint: (contourId: string, pointId: string, pos: Vec2) => void;
  moveHandle: (contourId: string, pointId: string, which: 'in' | 'out', pos: Vec2) => void;
  changePointType: (contourId: string, pointId: string, type: PointType) => void;
  deletePoint: (contourId: string, pointId: string) => void;

  // ── 履歴操作 ──
  undo: () => void;
  redo: () => void;
  pushUndo: () => void;
}

// ══════════════════════════════════════════════════════════════════
// 3. 内部ヘルパー関数
// ══════════════════════════════════════════════════════════════════

function isRawPython(v: GlyphData | Record<string, unknown>): v is Record<string, unknown> {
  // contours 配列を持っていない、または Python 特有の構造であれば生データと判定
  return !('contours' in v) || Array.isArray((v as GlyphData).contours) === false;
}

function updatePointInGlyph(
  glyph: GlyphData,
  contourId: string,
  pointId: string,
  updater: (p: AnchorPoint) => AnchorPoint,
): GlyphData {
  return {
    ...glyph,
    contours: glyph.contours.map(c =>
      c.id !== contourId ? c : {
        ...c,
        points: c.points.map(p => p.id !== pointId ? p : updater(p)),
      },
    ),
  };
}

// ══════════════════════════════════════════════════════════════════
// 4. Zustand ストア実装
// ══════════════════════════════════════════════════════════════════

export const useFontStore = create<FontStoreState>((set, get) => ({
  currentGlyph: null,
  fontMetrics: DEFAULT_METRICS,
  undoStack: [],
  redoStack: [],

  // ── データセット処理 ──
  setCurrentGlyph: (input) => {
    const glyph = isRawPython(input)
      ? fromPythonGlyph(input as Record<string, unknown>)
      : input as GlyphData;
      
    console.log('[fontStore] currentGlyph updated:', glyph); // デバッグ用
    set({ currentGlyph: glyph, undoStack: [], redoStack: [] });
  },

  setFontMetrics: (input) => {
    const metrics = ('cap_height' in input || 'x_height' in input)
      ? fromPythonMetrics(input as Record<string, unknown>)
      : input as FontMetrics;
    set({ fontMetrics: metrics });
  },

  // ── 履歴の保存 ──
  pushUndo: () => {
    const { currentGlyph, undoStack } = get();
    if (!currentGlyph) return;
    // 履歴は最大50件まで保持
    set({ undoStack: [...undoStack.slice(-49), currentGlyph], redoStack: [] });
  },

  // ── ポイント（点）の移動 ──
  movePoint: (cid, pid, pos) => {
    const { currentGlyph } = get();
    if (!currentGlyph) return;
    
    get().pushUndo();
    set({
      currentGlyph: updatePointInGlyph(currentGlyph, cid, pid, p => ({ ...p, pos })),
    });
    
    // TODO: ここでIPC（バックエンド）に変更を同期する処理を将来的に追加
  },

  // ── ハンドル（ベジェ曲線の制御点）の移動 ──
  moveHandle: (cid, pid, which, pos) => {
    const { currentGlyph } = get();
    if (!currentGlyph) return;
    
    get().pushUndo();
    set({
      currentGlyph: updatePointInGlyph(currentGlyph, cid, pid, p => {
        if (which === 'out') {
          return {
            ...p,
            handleOut: pos,
            // smooth(連動)タイプの場合は、反対側のハンドルを点対称に動かす
            handleIn: p.linked && p.handleIn
              ? { x: p.pos.x - (pos.x - p.pos.x), y: p.pos.y - (pos.y - p.pos.y) }
              : p.handleIn
          };
        } else {
          return {
            ...p,
            handleIn: pos,
            handleOut: p.linked && p.handleOut
              ? { x: p.pos.x - (pos.x - p.pos.x), y: p.pos.y - (pos.y - p.pos.y) }
              : p.handleOut
          };
        }
      }),
    });
  },

  // ── ポイントのタイプ（corner / smooth / curve）変更 ──
  changePointType: (cid, pid, type) => {
    const { currentGlyph } = get();
    if (!currentGlyph) return;
    
    get().pushUndo();
    set({
      currentGlyph: updatePointInGlyph(currentGlyph, cid, pid,
        p => ({ ...p, type, linked: type === 'smooth' }),
      ),
    });
  },

  // ── ポイントの削除 ──
  deletePoint: (cid, pid) => {
    const { currentGlyph } = get();
    if (!currentGlyph) return;
    
    get().pushUndo();
    set({
      currentGlyph: {
        ...currentGlyph,
        contours: currentGlyph.contours.map(c =>
          c.id !== cid ? c : { ...c, points: c.points.filter(p => p.id !== pid) },
        ),
      },
    });
  },

  // ── Undo (元に戻す) ──
  undo: () => {
    const { undoStack, currentGlyph, redoStack } = get();
    if (undoStack.length === 0) return;
    
    const prev = undoStack[undoStack.length - 1];
    set({
      currentGlyph: prev,
      undoStack: undoStack.slice(0, -1),
      redoStack: currentGlyph ? [...redoStack, currentGlyph] : redoStack,
    });
  },

  // ── Redo (やり直す) ──
  redo: () => {
    const { redoStack, currentGlyph, undoStack } = get();
    if (redoStack.length === 0) return;
    
    const next = redoStack[redoStack.length - 1];
    set({
      currentGlyph: next,
      redoStack: redoStack.slice(0, -1),
      undoStack: currentGlyph ? [...undoStack, currentGlyph] : undoStack,
    });
  },
}));