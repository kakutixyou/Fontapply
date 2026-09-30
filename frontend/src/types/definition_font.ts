/**
 * フォントプロジェクト全体のグローバルメトリクス
 */
export interface FontProjectMetrics {
  emSize: number;         // 一般的には 1000 や 2048
  ascender: number;       // 上限値 (例: 800)
  descender: number;      // 下限値 (例: -200)
  lineGap: number;        // 行間
  underlinePosition: number;
  underlineThickness: number;
}

/**
 * ベジェ曲線のコマンド定義 (curve_engine.pyとの通信用)
 * SVGのパスデータ(d属性)にそのまま変換できる、または配列で扱える形式
 */
export interface PathCommand {
  type: 'M' | 'L' | 'Q' | 'C' | 'Z'; // MoveTo, LineTo, QuadBezier, CubicBezier, ClosePath
  points: number[];                  // 座標値の配列 [x, y, x1, y1, ...]
}

/**
 * 個々の文字（グリフ）の配置・幅に関するメトリクス
 */
export interface GlyphMetrics {
  advanceWidth: number;   // 文字の送り幅
  leftSideBearing: number; // 左側の余白
  rightSideBearing: number;// 右側の余白
  boundingBox: {
    xMin: number;
    yMin: number;
    xMax: number;
    yMax: number;
  };
}

/**
 * バックエンドの stroke_analyzer / font_analytics から返される解析データ
 */
export interface StrokeAnalytics {
  strokeCount: number;      // 画数（日本語では特に重要）
  averageThickness: number; // 平均の太さ
  isSkeleton: boolean;      // 骨格データかどうか
  density: number;          // 文字の密集度・黒み（漢字のウェイト調整用）
}

/**
 * 単一の文字（グリフ）を表す中心的な型
 */
export interface GlyphData {
  id: string;               // 一意の識別子
  character: string;        // 実際の文字 (例: "あ", "A")
  unicode: string;          // Unicode表記 (例: "U+3042", "U+0041")
  category: 'latin' | 'hiragana' | 'katakana' | 'kanji' | 'other'; // 日本語対応のためのカテゴリ分類
  paths: PathCommand[];     // ベジェパスデータの配列
  metrics: GlyphMetrics;    // グリフ個別のメトリクス
  analytics?: StrokeAnalytics; // バックエンドから計算されたアナリティクス（オプショナル）
  updatedAt: number;        // 最終更新タイムスタンプ
}

/**
 * バックエンドとのカーニング（文字間隔）調整データ
 */
export interface KerningPair {
  leftUnicode: string;      // 左側の文字のUnicode
  rightUnicode: string;     // 右側の文字のUnicode
  value: number;            // 調整値
}

/**
 * フロントとバックで同期するフォントプロジェクト全体の型
 */
export interface FontProject {
  id: string;
  name: string;
  globalMetrics: FontProjectMetrics;
  glyphs: Record<string, GlyphData>; // Unicode、または文字をキーにした辞書
  kerningPairs: KerningPair[];
}