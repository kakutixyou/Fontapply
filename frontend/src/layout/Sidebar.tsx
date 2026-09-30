/**
 * Sidebar.integration.tsx
 *
 * 既存 Sidebar.tsx の「Glyphs」タブを CharacterGrid に差し替えるパッチ。
 *
 * やること:
 *   1. useGlyphSelectionStore から selectedUnicode / selectGlyph を取得
 *   2. <Sidebar> の glyphs タブ内で <CharacterGrid compact> を描画
 *   3. 既存の wf-glyph-grid / wf-glyph-cell はそのまま残しておくか、
 *      CharacterGrid で完全置き換えする（どちらでも OK）
 *
 * ── 最小パッチ版 (Sidebar.tsx の既存コードへの差分) ──
 *
 * Before:
 *   <div className="wf-sidebar__glyph-grid" ...>
 *     {DEMO_GLYPHS.map(g => <GlyphCell ... />)}
 *   </div>
 *
 * After:
 *   <CharacterGrid
 *     compact
 *     glyphMeta={glyphMetaCache}
 *     selectedUnicode={selectedUnicode}
 *     onSelect={selectGlyph}
 *   />
 */

import React from 'react';
import { useGlyphSelectionStore } from '../store/glyphSelectionStore';
import { CharacterGrid }          from '../components/font/CharacterGrid';

/**
 * サイドバーの「Glyphs」ペインに直接貼り込む小コンポーネント。
 * Sidebar.tsx の activeTab === 'glyphs' のブロックを丸ごとこれに差し替える。
 */
export const SidebarGlyphPane: React.FC = () => {
  const {
    selectedUnicode,
    selectGlyph,
    glyphMetaCache,
  } = useGlyphSelectionStore();

  return (
    <CharacterGrid
      compact
      glyphMeta={glyphMetaCache.size > 0 ? glyphMetaCache : undefined}
      selectedUnicode={selectedUnicode}
      onSelect={selectGlyph}
    />
  );
};

/* ──────────────────────────────────────────────────────────────
   Sidebar.tsx への差し替え手順:

   1. import { SidebarGlyphPane } from './Sidebar.integration';

   2. 既存の wf-sidebar__glyph-grid 部分をすべて削除し、
      下記に差し替える:

      {activeTab === 'glyphs' && (
        <div className="wf-sidebar__sidebar-inner">
          <SidebarGlyphPane />
        </div>
      )}

   3. Sidebar.tsx から DEMO_GLYPHS / useGlyphSelectionStore の
      重複 import を削除する。
   ────────────────────────────────────────────────────────────── */