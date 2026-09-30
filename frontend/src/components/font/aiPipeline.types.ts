/**
 * aiPipeline.types.ts
 *
 * Python バックエンド（font_analytics_engine.py / stroke_analyzer.py など）が
 * Electron IPC 経由で送り込む解析データの型定義。
 *
 * 実データを流し込む際は preload.ts / font.ipc.ts でこの型に合わせて
 * シリアライズ → window.electronAPI.onPipelineUpdate(cb) で受け取る。
 */

// ── 骨格レーダーチャート (6軸) ─────────────────────────────────────────────
export interface SkeletonRadar {
  verticality: number;   // 0–1
  symmetry:    number;
  contrast:    number;   // thick/thin ratio
  counter:     number;   // enclosed space ratio
  aperture:    number;   // open/closed degree
  axisAngle:   number;   // stress axis angle normalised
}

// ── 特徴量ウェイト ─────────────────────────────────────────────────────────
export interface FeatureWeight {
  name:  string;
  value: number;  // 0–1
  /** 'primary' | 'accent' | 'warning' — UIの色分けに使う */
  tier:  'primary' | 'accent' | 'warning';
}

// ── ストロークフェーズ ─────────────────────────────────────────────────────
export interface StrokePhase {
  label:         string;
  /** 相対的な長さ比率 (合計が1になるとは限らない — 正規化はUI側で行う) */
  weight:        number;
  color:         string;   // CSS color string
  isActive:      boolean;  // 現在フォーカスされているフェーズ
}

export interface StrokeStats {
  phases:       StrokePhase[];
  velocityPeak: number;   // 0–1 (stroke時間軸上の正規化位置)
  pressureAvg:  number;   // 0–1
}

// ── AI認識信頼度 ───────────────────────────────────────────────────────────
export interface ConfidenceMetric {
  key:   'class' | 'style' | 'skeleton' | 'anomaly';
  label: string;
  /** 0–100 */
  score:     number;
  detail:    string;   // 2行の説明テキスト (改行は \n)
  /** 'success' | 'brass' | 'info' | 'danger' — リングの色カテゴリ */
  colorRole: 'success' | 'brass' | 'info' | 'danger';
}

// ── データポイントサマリー ─────────────────────────────────────────────────
export interface DatapointSummary {
  skeletonPts:   number;
  strokeCount:   number;
  intersections: number;
  curvaturePts:  number;
}

// ── パイプラインステージ ───────────────────────────────────────────────────
export type StageStatus = 'done' | 'active' | 'pending' | 'error';

export interface PipelineStage {
  key:    string;
  label:  string;
  status: StageStatus;
}

// ── キャプチャトグル ───────────────────────────────────────────────────────
export interface CaptureToggle {
  key:     string;
  label:   string;
  sub:     string;
  enabled: boolean;
}

// ── エクスポートキュー ─────────────────────────────────────────────────────
export type QueueStatus = 'exported' | 'extracting' | 'queued' | 'error';

export interface QueueItem {
  filename: string;
  sizeKB:   number | null;
  status:   QueueStatus;
}

// ── パネル全体のペイロード ─────────────────────────────────────────────────
/**
 * window.electronAPI.onPipelineUpdate((payload: PipelinePayload) => { ... })
 * という形で受け取ることを想定。
 */
export interface PipelinePayload {
  glyphChar:    string;
  glyphUnicode: string;
  sessionId:    string;
  isLive:       boolean;

  datapoints:   DatapointSummary;
  radar:        SkeletonRadar;
  features:     FeatureWeight[];
  strokeStats:  StrokeStats;
  confidence:   ConfidenceMetric[];
  stages:       PipelineStage[];
  toggles:      CaptureToggle[];
  queue:        QueueItem[];
}