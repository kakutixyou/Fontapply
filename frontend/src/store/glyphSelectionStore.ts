// webforge-ai-desktop/frontend/src/store/glyphSelectionStore.ts

import { create } from 'zustand';
import type { CharSetKey, GlyphMeta } from '../components/font/CharacterGrid.types';
import { useFontStore } from './fontStore';

const FONT_API_BASE_URL = import.meta.env.VITE_FONT_API_BASE_URL || 'http://127.0.0.1:8000';
let latestGlyphRequest = 0;

export type GlyphLoadStatus = 'idle' | 'loading' | 'ready' | 'error';

interface GlyphSelectionState {
  selectedUnicode: string | null;
  selectedChar:    string | null;
  selectedProjectId: number | null;
  activeCharSet:   CharSetKey;
  loadStatus:      GlyphLoadStatus;
  errorMessage:    string | null;
  glyphMetaCache:  Map<string, GlyphMeta>;

  selectGlyph:      (unicode: string, char: string, projectId?: number | null) => Promise<void>;
  setActiveCharSet: (key: CharSetKey) => void;
  setGlyphMeta:     (meta: GlyphMeta[]) => void;
  clearSelection:   () => void;
}

export const useGlyphSelectionStore = create<GlyphSelectionState>((set, get) => ({
  selectedUnicode: null,
  selectedChar:    null,
  selectedProjectId: null,
  activeCharSet:   'latin',
  loadStatus:      'idle',
  errorMessage:    null,
  glyphMetaCache:  new Map(),

  selectGlyph: async (unicode, char, projectId = null) => {
    // 同じグリフが既に選択中なら何もしない
    if (
      get().selectedUnicode === unicode &&
      get().selectedProjectId === projectId &&
      get().loadStatus === 'ready'
    ) return;

    const fontState = useFontStore.getState();
    const switchingDirtyGlyph = Boolean(
      fontState.isDirty &&
      fontState.currentGlyph &&
      (fontState.currentGlyph.unicode !== unicode || get().selectedProjectId !== projectId),
    );
    if (switchingDirtyGlyph) {
      if (
        typeof window === 'undefined' ||
        !window.confirm('グリフに未保存の変更があります。保存せずに破棄して別の文字を開きますか？')
      ) return;
      useFontStore.getState().discardGlyphChanges();
    }

    const requestId = ++latestGlyphRequest;
    set({
      loadStatus:      'loading',
      errorMessage:    null,
      selectedUnicode: unicode,
      selectedChar:    char,
      selectedProjectId: projectId,
    });

    try {
      let glyphData: Record<string, unknown>;
      let metricsData: Record<string, unknown> | null = null;

      if (typeof window !== 'undefined' && window.electronAPI) {
        // ① Electron 環境: IPCを経由してPythonと通信
        const response = await window.electronAPI.invoke('font:getGlyphData', { unicode, projectId });

        if (!response || response.error) {
          throw new Error(response?.error ?? 'IPC returned empty response');
        }

        glyphData   = response.glyph  ?? response;
        metricsData = response.metrics ?? null;

      } else {
        // ② ブラウザ開発環境
        console.log(`🔵 [React] Pythonに U+${unicode} を要求します...`);
        const query = projectId === null ? '' : `?project_id=${projectId}`;
        const res = await fetch(`${FONT_API_BASE_URL}/api/glyphs/${unicode}${query}`);
        
        if (!res.ok) {
           console.error(`🔴 [React] Pythonがエラーを返しました: ${res.status}`);
           throw new Error(`Python API Error: ${res.status} ${res.statusText}`);
        }
        
        const response = await res.json();
        console.log(`🟢 [React] Pythonからデータを受け取りました！:`, response);
        
        glyphData   = response.glyph  ?? response;
        metricsData = response.metrics ?? null;
      }

      if (requestId !== latestGlyphRequest) return;

      // ── fontStore に書き込んでUIを更新する ──
      const { setCurrentGlyph, setFontMetrics } = useFontStore.getState();
      setCurrentGlyph(glyphData);
      if (metricsData) setFontMetrics(metricsData);

      set({ loadStatus: 'ready' });

    } catch (err) {
      if (requestId !== latestGlyphRequest) return;
      const msg = err instanceof Error ? err.message : String(err);
      console.error('[glyphSelectionStore] Failed to load glyph', unicode, msg);
      set({ loadStatus: 'error', errorMessage: msg });
    }
  },

  setActiveCharSet: (key) => set({ activeCharSet: key }),

  setGlyphMeta: (metaList) => {
    const cache = new Map<string, GlyphMeta>();
    metaList.forEach(m => cache.set(m.unicode, m));
    set({ glyphMetaCache: cache });
  },

  clearSelection: () => {
    latestGlyphRequest += 1;
    set({
      selectedUnicode: null,
      selectedChar:    null,
      selectedProjectId: null,
      loadStatus:      'idle',
      errorMessage:    null,
    });
  },
}));