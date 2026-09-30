/**
 * AIPipelinePanel.tsx
 *
 * Analytics タブに差し込むパネル。
 * props として PipelinePayload を受け取る — モック or 実データどちらでも可。
 *
 * 子コンポーネント:
 *   <DatapointSummaryBar>   — 上部4セル
 *   <SkeletonRadarChart>    — SVG レーダー
 *   <FeatureWeightList>     — 特徴量バーリスト
 *   <StrokePhaseTrack>      — ストロークフェーズ
 *   <ConfidenceGrid>        — 信頼度リング 2×2
 *   <PipelineStageRow>      — パイプラインステージ
 *   <CaptureToggleList>     — キャプチャトグル
 *   <ExportQueueList>       — エクスポートキュー
 */

import React, { useEffect, useRef, useState } from 'react';
import type {
  PipelinePayload, SkeletonRadar, FeatureWeight,
  StrokeStats, ConfidenceMetric, PipelineStage,
  CaptureToggle, QueueItem, DatapointSummary,
} from './aiPipeline.types';
import './AIPipelinePanel.css';

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

/** 0–1 の値をレーダーチャートの座標に変換 (6角形) */
function radarPoint(value: number, idx: number, cx: number, cy: number, r: number) {
  const angle = (Math.PI / 3) * idx - Math.PI / 2;
  return {
    x: cx + r * value * Math.cos(angle),
    y: cy + r * value * Math.sin(angle),
  };
}

function radarPolygon(radar: SkeletonRadar, cx: number, cy: number, r: number) {
  const vals = [
    radar.verticality, radar.symmetry,    radar.contrast,
    radar.counter,     radar.aperture,    radar.axisAngle,
  ];
  return vals
    .map((v, i) => { const p = radarPoint(v, i, cx, cy, r); return `${p.x},${p.y}`; })
    .join(' ');
}

/** 信頼度のカラーロールを CSS カラー文字列に変換 */
const ROLE_COLOR: Record<ConfidenceMetric['colorRole'], string> = {
  success: '#1d9e75',
  brass:   '#c09b4e',
  info:    '#3a7ce8',
  danger:  'rgba(232,93,58,.75)',
};

/** SVG 円弧の stroke-dasharray 計算 (半径14, 周長≒88) */
const RING_CIRCUMFERENCE = 2 * Math.PI * 14;
function ringDash(score: number) {
  const filled = (score / 100) * RING_CIRCUMFERENCE;
  return `${filled.toFixed(1)} ${RING_CIRCUMFERENCE.toFixed(1)}`;
}

/** キューステータスのラベル・スタイル */
const QUEUE_BADGE: Record<QueueItem['status'], { label: string; cls: string }> = {
  exported:   { label: 'exported',   cls: 'wf-queue__badge--done'  },
  extracting: { label: 'extracting', cls: 'wf-queue__badge--pend'  },
  queued:     { label: 'queued',     cls: 'wf-queue__badge--skip'  },
  error:      { label: 'error',      cls: 'wf-queue__badge--error' },
};

const QUEUE_DOT_COLOR: Record<QueueItem['status'], string> = {
  exported:   '#1d9e75',
  extracting: '#c09b4e',
  queued:     'rgba(255,255,255,.18)',
  error:      '#e85d3a',
};

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

/** 上部サマリー 4セル — カウントアップアニメーション付き */
const DatapointSummaryBar: React.FC<{ data: DatapointSummary }> = ({ data }) => {
  const items = [
    { label: 'skeleton pts', value: data.skeletonPts,   color: 'var(--brass2)' },
    { label: 'strokes',      value: data.strokeCount,   color: 'var(--blue)'   },
    { label: 'intersections',value: data.intersections, color: 'var(--teal)'   },
    { label: 'curvature pts',value: data.curvaturePts,  color: 'rgba(255,255,255,.5)' },
  ];

  // カウントアップ
  const [displayed, setDisplayed] = useState(items.map(() => 0));
  useEffect(() => {
    const targets = items.map(i => i.value);
    const duration = 900;
    const start = performance.now();
    const raf = requestAnimationFrame(function tick(now) {
      const p = Math.min((now - start) / duration, 1);
      setDisplayed(targets.map(t => Math.round(t * p)));
      if (p < 1) requestAnimationFrame(tick);
    });
    return () => cancelAnimationFrame(raf);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  return (
    <div className="wf-dp-grid">
      {items.map((item, i) => (
        <div className="wf-dp-cell" key={item.label}>
          <span className="wf-dp-num" style={{ color: item.color }}>{displayed[i]}</span>
          <div className="wf-dp-lbl">{item.label}</div>
        </div>
      ))}
    </div>
  );
};

/** SVG レーダーチャート */
const SkeletonRadarChart: React.FC<{ radar: SkeletonRadar }> = ({ radar }) => {
  const CX = 44, CY = 44, R = 34;
  const LABELS = ['verticality','symmetry','contrast','counter','aperture','axis angle'];
  const gridRatios = [1, 0.667, 0.333];

  return (
    <div className="wf-radar-wrap">
      <svg width="88" height="88" viewBox="0 0 88 88" aria-hidden="true">
        {gridRatios.map((ratio) => {
          const pts = [0,1,2,3,4,5]
            .map(i => { const p = radarPoint(ratio, i, CX, CY, R); return `${p.x},${p.y}`; })
            .join(' ');
          return <polygon key={ratio} points={pts} fill="none" stroke="rgba(255,255,255,.07)" strokeWidth="1"/>;
        })}
        {[0,1,2,3,4,5].map(i => {
          const p = radarPoint(1, i, CX, CY, R);
          return <line key={i} x1={CX} y1={CY} x2={p.x} y2={p.y} stroke="rgba(255,255,255,.05)" strokeWidth="1"/>;
        })}
        <polygon
          points={radarPolygon(radar, CX, CY, R)}
          fill="rgba(192,155,78,.18)"
          stroke="#c09b4e"
          strokeWidth="1.5"
        />
        {[0,1,2,3,4,5].map(i => {
          const vals = [radar.verticality, radar.symmetry, radar.contrast, radar.counter, radar.aperture, radar.axisAngle];
          const p = radarPoint(vals[i], i, CX, CY, R);
          return <circle key={i} cx={p.x} cy={p.y} r="3" fill="#e6c97a"/>;
        })}
      </svg>
      <div className="wf-radar-legend">
        {LABELS.map(label => (
          <div className="wf-radar-legend__row" key={label}>
            <div className="wf-radar-legend__dot"/>
            {label}
          </div>
        ))}
      </div>
    </div>
  );
};

/** 特徴量バーリスト */
const FeatureWeightList: React.FC<{ features: FeatureWeight[] }> = ({ features }) => {
  const tierColor = { primary: 'var(--brass)', accent: 'var(--blue)', warning: 'var(--red)' };
  const tierTextColor = { primary: undefined, accent: undefined, warning: 'var(--red)' };

  return (
    <div className="wf-feat-list">
      {features.map(f => (
        <div className="wf-feat-row" key={f.name}>
          <div className="wf-feat-name">{f.name}</div>
          <div className="wf-feat-bar-wrap">
            <div
              className="wf-feat-bar"
              style={{ width: `${Math.round(f.value * 100)}%`, background: tierColor[f.tier] }}
            />
          </div>
          <div
            className="wf-feat-val"
            style={{ color: tierTextColor[f.tier] }}
          >
            {f.value.toFixed(2)}
          </div>
        </div>
      ))}
    </div>
  );
};

/** ストロークフェーズトラック */
const StrokePhaseTrack: React.FC<{ strokeStats: StrokeStats }> = ({ strokeStats }) => {
  const { phases, velocityPeak, pressureAvg } = strokeStats;
  const totalWeight = phases.reduce((s, p) => s + p.weight, 0);

  const uniqueLabels = phases
    .filter(p => !p.label.startsWith('transition'))
    .map(p => p.label);

  return (
    <div className="wf-phase">
      <div className="wf-phase-track">
        {phases.map((phase, i) => (
          <div
            key={i}
            className={`wf-phase-seg ${phase.isActive ? 'wf-phase-seg--active' : ''}`}
            style={{
              flex: phase.weight / totalWeight,
              background: phase.color,
            }}
            title={phase.label}
          />
        ))}
      </div>
      <div className="wf-phase-labels">
        {uniqueLabels.map(l => <span key={l}>{l}</span>)}
      </div>
      <div className="wf-phase-stats">
        <span className="wf-phase-stats__label">velocity peak</span>
        <span className="wf-phase-stats__val">t={velocityPeak.toFixed(2)}</span>
        <span className="wf-phase-stats__label" style={{ marginLeft: 10 }}>pressure avg</span>
        <span className="wf-phase-stats__val">{pressureAvg.toFixed(2)}</span>
      </div>
    </div>
  );
};

/** 信頼度リング 2×2 グリッド */
const ConfidenceGrid: React.FC<{ metrics: ConfidenceMetric[] }> = ({ metrics }) => (
  <div className="wf-conf-grid">
    {metrics.map(m => {
      const color = ROLE_COLOR[m.colorRole];
      const dash  = ringDash(m.score);
      const scoreLabel = m.key === 'anomaly'
        ? (m.score < 20 ? 'low' : m.score < 50 ? 'mid' : 'high')
        : `${Math.round(m.score)}%`;

      return (
        <div className="wf-conf-card" key={m.key}>
          <div className="wf-conf-card__header">
            <span className="wf-conf-card__label">{m.label}</span>
            <span className="wf-conf-card__val" style={{ color }}>{scoreLabel}</span>
          </div>
          <div className="wf-conf-card__body">
            <svg width="36" height="36" viewBox="0 0 36 36" aria-hidden="true">
              <circle cx="18" cy="18" r="14" fill="none" stroke="rgba(255,255,255,.08)" strokeWidth="3"/>
              <circle
                cx="18" cy="18" r="14"
                fill="none"
                stroke={color}
                strokeWidth="3"
                strokeDasharray={dash}
                strokeDashoffset={RING_CIRCUMFERENCE * 0.25}
                strokeLinecap="round"
              />
            </svg>
            <div className="wf-conf-card__desc">
              {m.detail.split('\n').map((line, i) => (
                <span key={i}>{line}{i < m.detail.split('\n').length - 1 && <br/>}</span>
              ))}
            </div>
          </div>
        </div>
      );
    })}
  </div>
);

/** パイプラインステージ行 (2段3ノード構成) */
const PipelineStageRow: React.FC<{ stages: PipelineStage[] }> = ({ stages }) => {
  const [dotCount, setDotCount] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setDotCount(c => (c + 1) % 4), 600);
    return () => clearInterval(id);
  }, []);

  const row1 = stages.slice(0, 3);
  const row2 = stages.slice(3, 6);

  const renderRow = (row: PipelineStage[]) => (
    <div className="wf-pipe-row">
      {row.map((stage, i) => {
        const isActive = stage.status === 'active';
        const valText = stage.status === 'done'
          ? '✓ done'
          : isActive
            ? `extracting${'.'.repeat(dotCount)}`
            : stage.status;
        return (
          <React.Fragment key={stage.key}>
            <div className={`wf-pipe-node wf-pipe-node--${stage.status}`}>
              <div className="wf-pipe-node__label">{stage.label}</div>
              <div className="wf-pipe-node__val">{valText}</div>
            </div>
            {i < row.length - 1 && <div className="wf-pipe-arrow" aria-hidden="true">→</div>}
          </React.Fragment>
        );
      })}
    </div>
  );

  return (
    <div className="wf-pipe">
      {renderRow(row1)}
      {renderRow(row2)}
    </div>
  );
};

/** キャプチャトグルリスト (controlled) */
const CaptureToggleList: React.FC<{
  toggles: CaptureToggle[];
  onToggle: (key: string, val: boolean) => void;
}> = ({ toggles, onToggle }) => (
  <div className="wf-toggle-list">
    {toggles.map(t => (
      <div className="wf-toggle-row" key={t.key}>
        <div className="wf-toggle-info">
          <div className="wf-toggle-title">{t.label}</div>
          <div className="wf-toggle-sub">{t.sub}</div>
        </div>
        <button
          className={`wf-switch ${t.enabled ? 'wf-switch--on' : 'wf-switch--off'}`}
          onClick={() => onToggle(t.key, !t.enabled)}
          role="switch"
          aria-checked={t.enabled}
          aria-label={t.label}
        >
          <div className="wf-switch__knob"/>
        </button>
      </div>
    ))}
  </div>
);

/** エクスポートキュー */
const ExportQueueList: React.FC<{ queue: QueueItem[] }> = ({ queue }) => (
  <div className="wf-queue">
    {queue.map(item => {
      const badge = QUEUE_BADGE[item.status];
      const isBlinking = item.status === 'extracting';
      return (
        <div className="wf-queue__row" key={item.filename}>
          <div
            className={`wf-queue__dot ${isBlinking ? 'wf-queue__dot--blink' : ''}`}
            style={{ background: QUEUE_DOT_COLOR[item.status] }}
          />
          <div className="wf-queue__name">{item.filename}</div>
          <div className="wf-queue__size">
            {item.sizeKB !== null ? `${item.sizeKB} KB` : '—'}
          </div>
          <div className={`wf-queue__badge ${badge.cls}`}>{badge.label}</div>
        </div>
      );
    })}
  </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// Main panel
// ─────────────────────────────────────────────────────────────────────────────

interface AIPipelinePanelProps {
  payload: PipelinePayload;
  /**
   * トグル変更時のコールバック。
   * 本番では window.electronAPI.setPipelineToggle(key, val) を呼ぶ。
   */
  onToggle?: (key: string, enabled: boolean) => void;
}

export const AIPipelinePanel: React.FC<AIPipelinePanelProps> = ({
  payload, onToggle,
}) => {
  // toggles のローカル管理（IPC 往復なしで即座に反映）
  const [toggles, setToggles] = useState(payload.toggles);
  useEffect(() => setToggles(payload.toggles), [payload.toggles]);

  const handleToggle = (key: string, val: boolean) => {
    setToggles(prev => prev.map(t => t.key === key ? { ...t, enabled: val } : t));
    onToggle?.(key, val);
  };

  return (
    <div className="wf-ai-panel">

      {/* ─ Header strip ─ */}
      <div className="wf-ai-panel__strip">
        <div className="wf-ai-panel__strip-dot"/>
        <span className="wf-ai-panel__strip-label">AI pipeline</span>
        <div className="wf-ai-panel__chip wf-ai-panel__chip--live">live</div>
        <div className="wf-ai-panel__chip wf-ai-panel__chip--glyph">
          {payload.glyphChar} — U+{payload.glyphUnicode}
        </div>
        <span className="wf-ai-panel__session">session {payload.sessionId}</span>
      </div>

      {/* ─ Datapoint summary ─ */}
      <div className="wf-ai-panel__section">
        <div className="wf-ai-panel__sec-label">Extracted datapoints — current glyph</div>
        <DatapointSummaryBar data={payload.datapoints}/>
      </div>

      {/* ─ Radar + Features ─ */}
      <div className="wf-ai-panel__row2">
        <div className="wf-ai-panel__col">
          <div className="wf-ai-panel__sec-label">Skeleton structure</div>
          <SkeletonRadarChart radar={payload.radar}/>
        </div>
        <div className="wf-ai-panel__col">
          <div className="wf-ai-panel__sec-label">Feature extraction</div>
          <FeatureWeightList features={payload.features}/>
        </div>
      </div>

      {/* ─ Stroke phase + Confidence ─ */}
      <div className="wf-ai-panel__row2">
        <div className="wf-ai-panel__col">
          <div className="wf-ai-panel__sec-label">Stroke phase decomposition</div>
          <StrokePhaseTrack strokeStats={payload.strokeStats}/>
        </div>
        <div className="wf-ai-panel__col">
          <div className="wf-ai-panel__sec-label">AI structural recognition</div>
          <ConfidenceGrid metrics={payload.confidence}/>
        </div>
      </div>

      {/* ─ Pipeline stages + Toggles ─ */}
      <div className="wf-ai-panel__row2">
        <div className="wf-ai-panel__col">
          <div className="wf-ai-panel__sec-label">Pipeline stages</div>
          <PipelineStageRow stages={payload.stages}/>
        </div>
        <div className="wf-ai-panel__col">
          <div className="wf-ai-panel__sec-label">Capture toggles</div>
          <CaptureToggleList toggles={toggles} onToggle={handleToggle}/>
        </div>
      </div>

      {/* ─ Export queue ─ */}
      <div className="wf-ai-panel__section" style={{ borderTop: '1px solid rgba(255,255,255,.05)' }}>
        <div className="wf-ai-panel__sec-label">Export queue — session</div>
        <ExportQueueList queue={payload.queue}/>
      </div>

    </div>
  );
};