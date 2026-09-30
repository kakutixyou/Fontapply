// webforge-ai-desktop/frontend/src/pages/FontStudio.tsx

import React, { useEffect } from 'react';
import { CharacterGrid } from '@/components/font/CharacterGrid';
import { GlyphEditor } from '@/components/font/GlyphEditor';
import { MOCK_METRICS } from '@/components/font/GlyphEditor.mock';
import { MOCK_META } from '@/components/font/CharacterGrid.mock';

// ✨ ここが超重要！「本物のストア」をインポートして接続します ✨
import { useGlyphSelectionStore } from '@/store/glyphSelectionStore';
import { useFontStore } from '@/store/fontStore'; 

export interface FontStudioProps {
  mode: string;
  selectedGlyph?: string;
}

export const FontStudio: React.FC<FontStudioProps> = ({ mode, selectedGlyph }) => {
  // ── Stores ──
  const {
    selectedUnicode,
    loadStatus,
    errorMessage,
    selectGlyph,
    glyphMetaCache,
    setGlyphMeta,
  } = useGlyphSelectionStore();

  // 本物の fontStore.ts からデータを引っ張ってくる
  const {
    currentGlyph,
    fontMetrics,
    movePoint,
    moveHandle,
    changePointType,
    deletePoint,
    undo,
    redo,
  } = useFontStore();
  const SAFE_MOCK_META = new Map<string, any>(
    Array.from(MOCK_META.entries()).map(([key, meta]: [string, any]) => [
      key,
      {
        ...meta,
        status: meta.status ?? 'empty',
        captured: meta.captured ?? false,
      },
    ])
  );
  useEffect(() => {
    if (glyphMetaCache.size === 0) {
      // 変換済みの安全なデータを配列にしてストアに渡す
      setGlyphMeta(Array.from(SAFE_MOCK_META.values()));
    }
  }, [glyphMetaCache.size, setGlyphMeta]);
  // ── 初回: モックメタ or API からメタ情報をロード ──
// ── 初回: モックメタ or API からメタ情報をロード ──
  useEffect(() => {
    if (glyphMetaCache.size === 0) {
      // ✨ MOCKデータに足りない必須プロパティ（status, captured）を自動で補完する
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const formattedMeta = Array.from(MOCK_META.values()).map((meta: any) => ({
        ...meta,
        status: meta.status ?? 'empty',  // statusが無ければ 'empty' を入れる
        captured: meta.captured ?? false // capturedが無ければ false を入れる
      }));
      
      setGlyphMeta(formattedMeta);
    }
  }, [glyphMetaCache.size, setGlyphMeta]);
  // ── 初回: デフォルトグリフ (A: 0041) を自動選択 ──
  useEffect(() => {
    if (!selectedUnicode) {
      selectGlyph('0041', 'A');
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── キーボードショートカット: ⌘Z / ⇧⌘Z ──
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if ((e.metaKey || e.ctrlKey) && e.key === 'z') {
        e.preventDefault();
        e.shiftKey ? redo() : undo();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [undo, redo]);

  // ── メトリクス ──
  const metrics = fontMetrics ?? MOCK_METRICS;

  return (
    <div className="wf-fontstudio">
      <div className="wf-fontstudio__canvas-area">

        {/* ── ローディング ── */}
        {loadStatus === 'loading' && (
          <div className="wf-fontstudio__loading" role="status" aria-live="polite">
            <i className="ti ti-loader-2 wf-fontstudio__loading-spinner" aria-hidden="true"/>
            <span>Loading glyph…</span>
          </div>
        )}

        {/* ── エラー ── */}
        {loadStatus === 'error' && (
          <div className="wf-fontstudio__error" role="alert">
            <i className="ti ti-alert-triangle" aria-hidden="true"/>
            <span>Failed to load glyph</span>
            {errorMessage && (
              <code className="wf-fontstudio__error-msg">{errorMessage}</code>
            )}
            
            <div style={{ display: 'flex', gap: '10px', marginTop: '15px' }}>
              <button
                className="wf-fontstudio__error-retry"
                onClick={() => selectedUnicode &&
                  selectGlyph(selectedUnicode, String.fromCodePoint(parseInt(selectedUnicode, 16)))
                }
              >
                Retry
              </button>
              {/* ✨ 魔法の脱出ボタン ✨ */}
              <button
                className="wf-fontstudio__error-retry"
                style={{ backgroundColor: '#c09b4e', color: '#1a1a1a' }}
                onClick={() => selectGlyph('0041', 'A')}
              >
                Go back to 'A'
              </button>
            </div>
          </div>
        )}

        {/* ── グリフエディタ（edit モード、データあり） ── */}
        {mode === 'edit' && loadStatus !== 'loading' && currentGlyph && (
          <GlyphEditor
            key={currentGlyph.unicode}  
            glyph={currentGlyph}        
            metrics={metrics}
            onPointMove={movePoint}
            onHandleMove={moveHandle}
            onPointTypeChange={changePointType}
            onDeletePoint={deletePoint}
            onUndo={undo}
            onRedo={redo}
          />
        )}

        {/* データ未取得（idle）かつ edit モード → 空状態 */}
        {mode === 'edit' && loadStatus === 'idle' && !currentGlyph && (
          <div className="wf-fontstudio__placeholder">
            <i className="ti ti-letter-a" aria-hidden="true"/>
            <span>Select a glyph to edit</span>
          </div>
        )}

        {/* ── preview モード: CharacterGrid をメイン表示 ── */}
        {mode === 'preview' && (
          <div className="wf-fontstudio__picker-main">
            <CharacterGrid
              // ✨ MOCK_META を SAFE_MOCK_META に変更
              glyphMeta={glyphMetaCache.size > 0 ? glyphMetaCache : SAFE_MOCK_META}
              selectedUnicode={selectedUnicode}
              onSelect={selectGlyph}
            />
          </div>
        )}

        {/* ── metrics / kern モード ── */}
        {(mode === 'metrics' || mode === 'kern') && (
          <div className="wf-fontstudio__placeholder">
            <i className="ti ti-tools" aria-hidden="true"/>
            <span>{mode === 'metrics' ? 'Metrics editor' : 'Kern table'} — coming soon</span>
          </div>
        )}

      </div>

      {/* 開発用デバッグストリップ */}
      {import.meta.env.DEV && (
        <div className="wf-fontstudio__dev-strip">
          unicode: <code>{selectedUnicode ?? '—'}</code>
          &nbsp;|&nbsp; status: <code>{loadStatus}</code>
          &nbsp;|&nbsp; glyph: <code>{currentGlyph?.char ?? 'null'}</code>
          &nbsp;|&nbsp; contours: <code>{currentGlyph?.contours.length ?? 0}</code>
          &nbsp;|&nbsp; points: <code>
            {currentGlyph?.contours.reduce((n, c) => n + c.points.length, 0) ?? 0}
          </code>
        </div>
      )}
    </div>
  );
};