/**
 * CharacterGrid.tsx
 *
 * 文字ピッカー。Sidebar の analytics タブ、または
 * FontStudio 内のドロワー/パネルとして使う。
 *
 * 機能:
 *   - Latin / Hiragana タブ切り替え
 *   - 文字・U+ 検索フィルター
 *   - グリフ状態バッジ (drawn / draft / not_started)
 *   - AI 収集済みドット
 *   - 選択時プレビューパネル（文字・名称・ステータス・Edit ボタン）
 *   - キーボード操作（矢印キーで移動、Enter で選択）
 */

import React, {
  useState, useCallback, useMemo, useRef, useEffect, KeyboardEvent,
} from 'react';
import type {
  CharacterGridProps, CharEntry, CharSetKey, GlyphStatus,
} from './CharacterGrid.types';
import {
  CHAR_SETS, getUnicodeName, charToUnicode,
} from './CharacterGrid.types';
import './CharacterGrid.css';

// ─────────────────────────────────────────────────────────────────────────────
// Status helpers
// ─────────────────────────────────────────────────────────────────────────────

const STATUS_LABEL: Record<GlyphStatus, string> = {
  drawn:       'drawn',
  draft:       'draft',
  not_started: 'not started',
};

const STATUS_CSS: Record<GlyphStatus, string> = {
  drawn:       'wf-cgrid__badge--drawn',
  draft:       'wf-cgrid__badge--draft',
  not_started: 'wf-cgrid__badge--todo',
};

// ─────────────────────────────────────────────────────────────────────────────
// GlyphCell
// ─────────────────────────────────────────────────────────────────────────────

interface GlyphCellProps {
  entry:     CharEntry;
  status:    GlyphStatus;
  captured:  boolean;
  selected:  boolean;
  tabIndex:  number;
  charSet:   CharSetKey;
  onClick:   () => void;
  onKeyDown: (e: KeyboardEvent<HTMLButtonElement>) => void;
  cellRef?:  (el: HTMLButtonElement | null) => void;
}

const GlyphCell = React.memo<GlyphCellProps>(({
  entry, status, captured, selected, tabIndex, charSet,
  onClick, onKeyDown, cellRef,
}) => {
  const cls = [
    'wf-cgrid__cell',
    charSet === 'hiragana' ? 'wf-cgrid__cell--jp' : 'wf-cgrid__cell--lat',
    selected ? 'wf-cgrid__cell--selected' : '',
    status === 'draft' ? 'wf-cgrid__cell--draft' : '',
  ].filter(Boolean).join(' ');

  return (
    <button
      
      ref={cellRef}
      className={cls}
      onClick={onClick}
      onKeyDown={onKeyDown}
      tabIndex={tabIndex}
      aria-pressed={selected}
      aria-label={`${entry.char} U+${entry.unicode}`}
      title={`U+${entry.unicode}`}
      data-unicode={entry.unicode}
    >
      {entry.char}
      {/* AI 収集済みドット */}
      {captured && <span className="wf-cgrid__captured-dot" aria-label="AI data captured"/>}
      {/* 未着手インジケータ（not_started は薄く表示） */}
      {status === 'not_started' && <span className="wf-cgrid__empty-mark" aria-hidden="true"/>}
    </button>
  );
});
GlyphCell.displayName = 'GlyphCell';

// ─────────────────────────────────────────────────────────────────────────────
// PreviewPanel
// ─────────────────────────────────────────────────────────────────────────────

interface PreviewPanelProps {
  unicode:   string;
  char:      string;
  status:    GlyphStatus;
  captured:  boolean;
  charSet:   CharSetKey;
  onEdit:    () => void;
}

const PreviewPanel: React.FC<PreviewPanelProps> = ({
  unicode, char, status, captured, charSet, onEdit,
}) => (
  <div className="wf-cgrid__preview" aria-label={`Preview: ${char}`}>
    <div className={`wf-cgrid__preview-glyph ${charSet === 'hiragana' ? 'wf-cgrid__preview-glyph--jp' : ''}`}
      aria-hidden="true">
      {char}
    </div>

    <div className="wf-cgrid__preview-meta">
      <div className="wf-cgrid__meta-row">
        <span className="wf-cgrid__meta-label">Unicode</span>
        <code className="wf-cgrid__meta-val">U+{unicode}</code>
      </div>
      <div className="wf-cgrid__meta-row">
        <span className="wf-cgrid__meta-label">Name</span>
        <span className="wf-cgrid__meta-name">{getUnicodeName(unicode)}</span>
      </div>
      <div className="wf-cgrid__meta-row">
        <span className="wf-cgrid__meta-label">Status</span>
        <span className={`wf-cgrid__badge ${STATUS_CSS[status]}`}>
          {STATUS_LABEL[status]}
        </span>
        {captured && (
          <span className="wf-cgrid__badge wf-cgrid__badge--ai" aria-label="AI data captured">
            <i className="ti ti-cpu" aria-hidden="true"/> AI
          </span>
        )}
      </div>
    </div>

    <button
      className="wf-cgrid__edit-btn"
      onClick={onEdit}
      // onClick={() => onSelect(glyph.unicode, glyph.char)}
      aria-label={`Edit glyph ${char} in canvas`}
    >
      <i className="ti ti-pencil" aria-hidden="true"/>
      Edit glyph
    </button>
  </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// CharacterGrid (main)
// ─────────────────────────────────────────────────────────────────────────────

export const CharacterGrid: React.FC<CharacterGridProps> = ({
  glyphMeta,
  selectedUnicode,
  onSelect,
  compact = false,
}) => {
  const [activeTab,  setActiveTab]  = useState<CharSetKey>('latin');
  const [searchQuery, setSearchQuery] = useState('');
  // フラット化した全エントリ（キーボードナビ用）
  const allCellsRef = useRef<HTMLButtonElement[]>([]);

  // ── 現在のタブの sections ──
  const activeCharSet = useMemo(
    () => CHAR_SETS.find(cs => cs.key === activeTab)!,
    [activeTab],
  );

  // ── 検索フィルター ──
  const filteredSections = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return activeCharSet.sections;
    return activeCharSet.sections
      .map(sec => ({
        ...sec,
        entries: sec.entries.filter(e =>
          e.char.includes(searchQuery) ||
          e.unicode.toLowerCase().includes(q) ||
          `u+${e.unicode}`.includes(q) ||
          getUnicodeName(e.unicode).toLowerCase().includes(q),
        ),
      }))
      .filter(sec => sec.entries.length > 0);
  }, [activeCharSet, searchQuery]);

  // 全エントリのフラット配列（矢印ナビ用）
  const flatEntries = useMemo(
    () => filteredSections.flatMap(s => s.entries),
    [filteredSections],
  );

  const totalCount = useMemo(
    () => activeCharSet.sections.reduce((n, s) => n + s.entries.length, 0),
    [activeCharSet],
  );
  const filteredCount = flatEntries.length;

  // ── グリフ情報取得 ──
 const getMeta = useCallback((unicode: string) => {
  if (!glyphMeta) return { status: 'not_started' as GlyphStatus, captured: false };
  const m = glyphMeta.get(unicode);
  // 👇 ここで m.status や m.captured を読もうとするが、MOCK_META には存在しないため undefined になる
  return { status: m?.status ?? 'not_started', captured: m?.captured ?? false };
}, [glyphMeta]);

  // ── キーボードナビゲーション ──
  const handleCellKeyDown = useCallback((
    e: KeyboardEvent<HTMLButtonElement>,
    entry: CharEntry,
    flatIdx: number,
  ) => {
    const cols = activeTab === 'hiragana' ? 5 : 13;
    let next = -1;
    switch (e.key) {
      case 'ArrowRight': next = flatIdx + 1;    break;
      case 'ArrowLeft':  next = flatIdx - 1;    break;
      case 'ArrowDown':  next = flatIdx + cols;  break;
      case 'ArrowUp':    next = flatIdx - cols;  break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        onSelect(entry.unicode, entry.char);
        return;
    }
    if (next >= 0 && next < allCellsRef.current.length) {
      e.preventDefault();
      allCellsRef.current[next]?.focus();
    }
  }, [activeTab, onSelect]);

  // ── タブ切り替え時に検索クリア ──
  const handleTabChange = (key: CharSetKey) => {
    setActiveTab(key);
    setSearchQuery('');
    allCellsRef.current = [];
  };

  // ── 選択中グリフのプレビュー情報 ──
  const previewEntry = useMemo(() => {
    if (!selectedUnicode) return null;
    for (const cs of CHAR_SETS) {
      for (const sec of cs.sections) {
        const e = sec.entries.find(e => e.unicode === selectedUnicode);
        if (e) return { entry: e, charSetKey: cs.key as CharSetKey };
      }
    }
    return null;
  }, [selectedUnicode]);

  const previewMeta = previewEntry
    ? getMeta(previewEntry.entry.unicode)
    : null;

  // cellRef のリセット（レンダリングごと）
  let cellIdx = 0;

  return (
    <div className={`wf-cgrid ${compact ? 'wf-cgrid--compact' : ''}`}>

      {/* ─ Header ─ */}
      <div className="wf-cgrid__header">
        {!compact && (
          <span className="wf-cgrid__header-title">Character set</span>
        )}

        {/* タブ */}
        <div className="wf-cgrid__tabs" role="tablist" aria-label="Character set">
          {CHAR_SETS.map(cs => (
            <button
              key={cs.key}
              role="tab"
              className={`wf-cgrid__tab ${activeTab === cs.key ? 'wf-cgrid__tab--active' : ''}`}
              onClick={() => handleTabChange(cs.key)}
              aria-selected={activeTab === cs.key}
            >
              {cs.label}
            </button>
          ))}
        </div>

        {/* カウンター */}
        <span className="wf-cgrid__counter" aria-live="polite">
          {searchQuery ? `${filteredCount} / ${totalCount}` : `${totalCount}`}
        </span>

        {/* 検索 */}
        <div className="wf-cgrid__search-wrap">
          <i className="ti ti-search wf-cgrid__search-icon" aria-hidden="true"/>
          <input
            className="wf-cgrid__search"
            type="search"
            placeholder="U+ or char…"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            aria-label="Search glyphs by character or unicode"
          />
        </div>
      </div>

      {/* ─ Grid sections ─ */}
      <div
        className="wf-cgrid__body"
        role="tabpanel"
        aria-label={`${activeCharSet.label} character grid`}
      >
        {filteredSections.length === 0 && (
          <div className="wf-cgrid__empty">
            <i className="ti ti-search-off" aria-hidden="true"/>
            <span>No glyphs match "{searchQuery}"</span>
          </div>
        )}

        {filteredSections.map(sec => (
          <div key={sec.key} className="wf-cgrid__section">
            {!compact && (
              <div className="wf-cgrid__section-label">{sec.label}</div>
            )}
            <div
              className={`wf-cgrid__grid ${activeTab === 'hiragana' ? 'wf-cgrid__grid--jp' : 'wf-cgrid__grid--lat'}`}
              role="listbox"
              aria-label={sec.label}
              aria-multiselectable="false"
            >
              {sec.entries.map(entry => {
                const idx = cellIdx++;
                const { status, captured } = getMeta(entry.unicode);
                return (
                  <GlyphCell
                    key={entry.unicode}
                    entry={entry}
                    status={status}
                    captured={captured}
                    selected={entry.unicode === selectedUnicode}
                    tabIndex={entry.unicode === selectedUnicode ? 0 : -1}
                    charSet={activeTab}
                    onClick={() => onSelect(entry.unicode, entry.char)}
                    onKeyDown={(e) => handleCellKeyDown(e, entry, idx)}
                    cellRef={el => { allCellsRef.current[idx] = el!; }}
                  />
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* ─ Preview panel ─ */}
      {previewEntry && previewMeta && (
        <PreviewPanel
          unicode={previewEntry.entry.unicode}
          char={previewEntry.entry.char}
          status={previewMeta.status}
          captured={previewMeta.captured}
          charSet={previewEntry.charSetKey}
          onEdit={() => onSelect(previewEntry.entry.unicode, previewEntry.entry.char)}
        />
      )}

    </div>
  );
};