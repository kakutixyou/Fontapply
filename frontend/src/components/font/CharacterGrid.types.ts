/**
 * CharacterGrid.types.ts
 *
 * CharacterGrid が扱う型と、文字セット定義。
 * Python バックエンドが返す「グリフ存在フラグ」もここに合わせる。
 */

// ── 文字セットキー ──────────────────────────────────────────────────────────

export type CharSetKey = 'latin' | 'hiragana';

// ── グリフのメタ情報（バックエンドが返す想定） ─────────────────────────────

export type GlyphStatus =
  | 'drawn'        // パスあり・保存済み
  | 'draft'        // 作業中（未保存変更あり）
  | 'not_started'; // まだ何もない

export interface GlyphMeta {
  unicode: string;
  status: 'drawn' | 'draft' | 'not_started'; // ← これを期待している！
                    
  char:     string;   // 'D'
  // status:   GlyphStatus;
  /** AI パイプラインで学習データ収集済みかどうか */
  captured: boolean;
}

// ── CharacterGrid props ─────────────────────────────────────────────────────

export interface CharacterGridProps {
  /**
   * グリフのメタ情報マップ（unicode → GlyphMeta）。
   * 渡されない場合は全グリフを not_started として表示。
   */
  glyphMeta: Map<string, GlyphMeta>;
  // glyphMeta?:      Map<string, GlyphMeta>;
  selectedUnicode: string | null;
  onSelect:        (unicode: string, char: string) => void;
  /** サイドバー組み込み時は true（セクションラベルを省略、コンパクト化） */
  compact?:        boolean;
}

// ── 文字セット定義 ──────────────────────────────────────────────────────────

export interface CharEntry {
  char:    string;
  unicode: string;
}

export interface CharSection {
  key:     string;
  label:   string;
  entries: CharEntry[];
}

export interface CharSet {
  key:      CharSetKey;
  label:    string;
  sections: CharSection[];
}

// ── ユーティリティ ──────────────────────────────────────────────────────────

export function charToUnicode(char: string): string {
  return char.codePointAt(0)!.toString(16).toUpperCase().padStart(4, '0');
}

export function unicodeToChar(unicode: string): string {
  return String.fromCodePoint(parseInt(unicode, 16));
}

// ── Unicode 文字名（抜粋） ──────────────────────────────────────────────────

const UNICODE_NAMES: Record<string, string> = {
  // Latin uppercase
  '0041': 'LATIN CAPITAL LETTER A', '0042': 'LATIN CAPITAL LETTER B',
  '0043': 'LATIN CAPITAL LETTER C', '0044': 'LATIN CAPITAL LETTER D',
  '0045': 'LATIN CAPITAL LETTER E', '0046': 'LATIN CAPITAL LETTER F',
  '0047': 'LATIN CAPITAL LETTER G', '0048': 'LATIN CAPITAL LETTER H',
  '0049': 'LATIN CAPITAL LETTER I', '004A': 'LATIN CAPITAL LETTER J',
  '004B': 'LATIN CAPITAL LETTER K', '004C': 'LATIN CAPITAL LETTER L',
  '004D': 'LATIN CAPITAL LETTER M', '004E': 'LATIN CAPITAL LETTER N',
  '004F': 'LATIN CAPITAL LETTER O', '0050': 'LATIN CAPITAL LETTER P',
  '0051': 'LATIN CAPITAL LETTER Q', '0052': 'LATIN CAPITAL LETTER R',
  '0053': 'LATIN CAPITAL LETTER S', '0054': 'LATIN CAPITAL LETTER T',
  '0055': 'LATIN CAPITAL LETTER U', '0056': 'LATIN CAPITAL LETTER V',
  '0057': 'LATIN CAPITAL LETTER W', '0058': 'LATIN CAPITAL LETTER X',
  '0059': 'LATIN CAPITAL LETTER Y', '005A': 'LATIN CAPITAL LETTER Z',
  // Latin lowercase
  '0061': 'LATIN SMALL LETTER A',   '0062': 'LATIN SMALL LETTER B',
  '0063': 'LATIN SMALL LETTER C',   '0064': 'LATIN SMALL LETTER D',
  '0065': 'LATIN SMALL LETTER E',   '0066': 'LATIN SMALL LETTER F',
  '0067': 'LATIN SMALL LETTER G',   '0068': 'LATIN SMALL LETTER H',
  '0069': 'LATIN SMALL LETTER I',   '006A': 'LATIN SMALL LETTER J',
  '006B': 'LATIN SMALL LETTER K',   '006C': 'LATIN SMALL LETTER L',
  '006D': 'LATIN SMALL LETTER M',   '006E': 'LATIN SMALL LETTER N',
  '006F': 'LATIN SMALL LETTER O',   '0070': 'LATIN SMALL LETTER P',
  '0071': 'LATIN SMALL LETTER Q',   '0072': 'LATIN SMALL LETTER R',
  '0073': 'LATIN SMALL LETTER S',   '0074': 'LATIN SMALL LETTER T',
  '0075': 'LATIN SMALL LETTER U',   '0076': 'LATIN SMALL LETTER V',
  '0077': 'LATIN SMALL LETTER W',   '0078': 'LATIN SMALL LETTER X',
  '0079': 'LATIN SMALL LETTER Y',   '007A': 'LATIN SMALL LETTER Z',
  // Hiragana（代表的なもの）
  '3042': 'HIRAGANA LETTER A',      '3044': 'HIRAGANA LETTER I',
  '3046': 'HIRAGANA LETTER U',      '3048': 'HIRAGANA LETTER E',
  '304A': 'HIRAGANA LETTER O',      '304B': 'HIRAGANA LETTER KA',
  '304D': 'HIRAGANA LETTER KI',     '304F': 'HIRAGANA LETTER KU',
  '3051': 'HIRAGANA LETTER KE',     '3053': 'HIRAGANA LETTER KO',
  '3093': 'HIRAGANA LETTER N',
};

export function getUnicodeName(unicode: string): string {
  return UNICODE_NAMES[unicode] ?? `U+${unicode}`;
}

// ── 文字セットデータ ────────────────────────────────────────────────────────

function makeEntries(chars: string): CharEntry[] {
  return chars.split('').map(char => ({ char, unicode: charToUnicode(char) }));
}

export const CHAR_SETS: CharSet[] = [
  {
    key:   'latin',
    label: 'Latin',
    sections: [
      {
        key:     'uppercase',
        label:   'Uppercase — A–Z',
        entries: makeEntries('ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
      },
      {
        key:     'lowercase',
        label:   'Lowercase — a–z',
        entries: makeEntries('abcdefghijklmnopqrstuvwxyz'),
      },
    ],
  },
  {
    key:   'hiragana',
    label: 'Hiragana',
    sections: [
      {
        key:     'hiragana_vowels',
        label:   'あいうえお段',
        entries: makeEntries('あいうえお'),
      },
      {
        key:     'hiragana_ka',
        label:   'か行',
        entries: makeEntries('かきくけこ'),
      },
      {
        key:     'hiragana_sa',
        label:   'さ行',
        entries: makeEntries('さしすせそ'),
      },
      {
        key:     'hiragana_ta',
        label:   'た行',
        entries: makeEntries('たちつてと'),
      },
      {
        key:     'hiragana_na',
        label:   'な行',
        entries: makeEntries('なにぬねの'),
      },
      {
        key:     'hiragana_ha',
        label:   'は行',
        entries: makeEntries('はひふへほ'),
      },
      {
        key:     'hiragana_ma',
        label:   'ま行',
        entries: makeEntries('まみむめも'),
      },
      {
        key:     'hiragana_ya',
        label:   'や行',
        entries: makeEntries('やゆよ'),
      },
      {
        key:     'hiragana_ra',
        label:   'ら行',
        entries: makeEntries('らりるれろ'),
      },
      {
        key:     'hiragana_wa',
        label:   'わをん',
        entries: makeEntries('わをん'),
      },
    ],
  },
];