/**
 * GlyphEditor.types.ts
 *
 * GlyphEditor が扱うすべての型定義。
 * Python バックエンド（glyph_builder.py / curve_engine.py）が
 * IPC 経由で送り込む座標データもここに合わせる。
 *
 * 座標系: フォントユニット空間 (em = 1000u)
 *   +y 上方向（SVG への変換は useGlyphTransform で行う）
 */

// ── ポイント ────────────────────────────────────────────────────────────────

export type PointType = 'corner' | 'smooth' | 'tangent';

export interface Vec2 {
  x: number;
  y: number;
}

/** ベジェ曲線のアンカーポイント */
export interface AnchorPoint {
  id: string;
  pos: Vec2;
  type: PointType;
  /** in-handle (前の曲線セグメントの制御点) */
  handleIn:  Vec2 | null;
  /** out-handle (次の曲線セグメントの制御点) */
  handleOut: Vec2 | null;
  /** スムーズ点では handleIn / handleOut を反転コピー */
  linked: boolean;
}

// ── コンター（輪郭）────────────────────────────────────────────────────────

export interface Contour {
  id:     string;
  points: AnchorPoint[];//注意 points: GlyphPoint[];
  closed: boolean;
}

// ── グリフ ──────────────────────────────────────────────────────────────────

export interface GlyphData {
  id?: string;         // 💡 ? をつけてオプショナルにするか、行ごと削除する
  char: string;
  unicode: string;
  width: number;
  contours: Contour[];
}

// ── メトリクス ──────────────────────────────────────────────────────────────

export interface FontMetrics {
  ascender:   number;
  capHeight:  number;
  xHeight:    number;
  baseline:   number;  // 常に 0
  descender:  number;
  lsb:        number;  // left side bearing
  rsb:        number;  // right side bearing (width - lsb - glyphWidth)
}

// ── ツール ──────────────────────────────────────────────────────────────────

export type EditorTool =
  | 'select'
  | 'pen'
  | 'knife'
  | 'measure';

// ── 選択状態 ────────────────────────────────────────────────────────────────

export interface SelectionState {
  contourId: string | null;
  pointIds:  string[];
}

// ── カメラ（ビューポート変換）───────────────────────────────────────────────

export interface Viewport {
  /** canvas pixel per font unit */
  scale:  number;
  /** canvas pixel offset of font origin */
  originX: number;
  originY: number;
}

// ── エディタ全体の状態（useGlyphEditorStore で管理）────────────────────────

export interface GlyphEditorState {
  glyph:     GlyphData;
  metrics:   FontMetrics;
  viewport:  Viewport;
  tool:      EditorTool;
  selection: SelectionState;

  showGrid:    boolean;
  showGuides:  boolean;
  showFill:    boolean;
  snapToGrid:  boolean;
  gridSize:    number;   // font units
}

// ── コールバック props ───────────────────────────────────────────────────────

export interface GlyphEditorCallbacks {
  onPointMove:    (contourId: string, pointId: string, pos: Vec2) => void;
  onHandleMove:   (contourId: string, pointId: string, which: 'in' | 'out', pos: Vec2) => void;
  onPointTypeChange: (contourId: string, pointId: string, type: PointType) => void;
  onAddPoint:     (contourId: string, pos: Vec2) => void;
  onDeletePoint:  (contourId: string, pointId: string) => void;
  onToolChange:   (tool: EditorTool) => void;
}
// frontend/src/components/font/GlyphEditor.types.ts

export interface Vec2 {
  x: number;
  y: number;
}


export interface GlyphPoint {
  id: string;
  pos: Vec2;
  type: PointType;
  handleIn?: Vec2;  // 入力ハンドルの絶対座標
  handleOut?: Vec2; // 出力ハンドルの絶対座標
  linked?: boolean; // ハンドルが連動して動くかどうか
}



export interface GlyphMetrics {
  unitsPerEm: number;
  ascender: number;
  descender: number;
  capHeight: number;
  xHeight: number;
  advanceWidth: number;
  lsb: number; // Left Side Bearing
  rsb: number; // Right Side Bearing
}