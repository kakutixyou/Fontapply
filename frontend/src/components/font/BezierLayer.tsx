// BezierLayer.tsx (修正版)

import React from 'react';
import type {
  GlyphData, AnchorPoint, SelectionState, EditorTool,
} from './GlyphEditor.types';

type GlyphTransform = {
  toCanvas: (point: { x: number; y: number }) => { x: number; y: number };
};

// ── 定数・カラー ──────────────────────────────────────────────────────────
// （※ここは元のコードから変更ありません）
const ANCHOR_SIZE    = 7;
const SMOOTH_RADIUS  = 5.5;
const HANDLE_RADIUS  = 3.5;
const HIT_RADIUS     = 10;

const C = {
  path:          'rgba(224,251,252,.8)',   /* 白水色のパス */
  pathFill:      'rgba(72,202,228,.1)',    /* うっすらシアンの塗り */
  anchorFill:    '#48cae4',                /* シアンのアンカー */
  anchorActive:  '#00f5ff',                /* 選択中は発光シアン */
  anchorSmooth:  'rgba(224,251,252,.7)',   /* スムーズポイントは少し白っぽく */
  anchorBorder:  '#0b1528',                /* 枠線は背景と同じ深海色 */
  handleLine:    'rgba(138,180,248,.5)',   /* ハンドルの線は柔らかい青 */
  handleFill:    'rgba(138,180,248,.8)',
  selectedRing:  '#00f5ff',                /* 選択時のリング */
  badgeBg:       'rgba(11,21,40,.9)',
  badgeBorder:   'rgba(72,202,228,.4)',
  badgeText:     'rgba(224,251,252,.8)',
  badgeLabel:    'rgba(72,202,228,.8)',
} as const;

// 🟢 【追加】新旧データ両方に対応する安全な座標ゲッター
// pt.pos があればそれを、無ければ pt.x / pt.y を使います
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const getPos = (pt: any): { x: number; y: number } => {
  if (pt?.pos) return pt.pos;
  if (typeof pt?.x === 'number' && typeof pt?.y === 'number') return { x: pt.x, y: pt.y };
  return { x: 0, y: 0 }; // 最悪のケースでもクラッシュを防ぐ
};

// ── コンターを SVG d 文字列に変換 ────────────────────────────────────────────

function contourToPath(
  points: AnchorPoint[],
  closed: boolean,
  toCanvas: GlyphTransform['toCanvas'],
): string {
  if (points.length === 0) return '';

  const cv = (p: { x: number; y: number }) => toCanvas(p);

  const segs: string[] = [];
  // 🟢 getPos を使用
  const first = cv(getPos(points[0]));
  segs.push(`M ${first.x.toFixed(2)},${first.y.toFixed(2)}`);

  for (let i = 0; i < points.length; i++) {
    const curr  = points[i];
    const next  = points[(i + 1) % points.length];
    if (!closed && i === points.length - 1) break;

    // 🟢 getPos を使用
    const p1 = cv(getPos(curr));
    const p2 = cv(getPos(next));
    const ho = curr.handleOut  ? cv(curr.handleOut)  : null;
    const hi = next.handleIn   ? cv(next.handleIn)   : null;

    if (!ho && !hi) {
      segs.push(`L ${p2.x.toFixed(2)},${p2.y.toFixed(2)}`);
    } else {
      const c1 = ho ?? p1;
      const c2 = hi ?? p2;
      segs.push(
        `C ${c1.x.toFixed(2)},${c1.y.toFixed(2)} ` +
        `${c2.x.toFixed(2)},${c2.y.toFixed(2)} ` +
        `${p2.x.toFixed(2)},${p2.y.toFixed(2)}`,
      );
    }
  }

  if (closed) segs.push('Z');
  return segs.join(' ');
}

// ── コーディネートバッジ ─────────────────────────────────────────────────────

const CoordBadge: React.FC<{
  cx: number; cy: number;
  anchor: AnchorPoint;
  isHandle?: boolean;
}> = ({ cx, cy, anchor, isHandle }) => {
  const label = isHandle ? 'handle' : anchor.type;
  const bw = 76, bh = 44;
  const bx = cx - bw / 2;
  const by = cy - bh - 12;
  const borderColor = isHandle ? 'rgba(58,170,106,.4)' : 'rgba(192,155,78,.35)';
  const labelColor  = isHandle ? 'rgba(58,170,106,.75)' : 'rgba(192,155,78,.75)';
  
  // 🟢 getPos を使用
  const pos = getPos(anchor);

  return (
    <g>
      <rect x={bx} y={by} width={bw} height={bh} rx={4}
        fill={C.badgeBg} stroke={borderColor} strokeWidth={1}/>
      <text x={bx+7} y={by+14}
        fontFamily="'DM Mono',monospace" fontSize={8.5}
        fill={labelColor} letterSpacing="0.04em">
        {label}
      </text>
      <text x={bx+7} y={by+26}
        fontFamily="'DM Mono',monospace" fontSize={9.5} fill={C.badgeText}>
        x: {Math.round(pos.x)}
      </text>
      <text x={bx+7} y={by+38}
        fontFamily="'DM Mono',monospace" fontSize={9.5} fill={C.badgeText}>
        y: {Math.round(pos.y)}
      </text>
      <line x1={cx} y1={by + bh} x2={cx} y2={cy - SMOOTH_RADIUS - 2}
        stroke={borderColor} strokeWidth={0.75} strokeDasharray="2,3"/>
    </g>
  );
};

// ── BezierLayer ──────────────────────────────────────────────────────────────

interface BezierLayerProps {
  glyph:     GlyphData;
  transform: GlyphTransform;
  selection: SelectionState;
  tool:      EditorTool;
  showFill:  boolean;
  onAnchorPointerDown?: (contourId: string, pointId: string, e: React.PointerEvent) => void;
  onHandlePointerDown?: (contourId: string, pointId: string, which: 'in' | 'out', e: React.PointerEvent) => void;
}

export const BezierLayer: React.FC<BezierLayerProps> = ({
  glyph, transform, selection, tool, showFill,
  onAnchorPointerDown, onHandlePointerDown,
}) => {
  const { toCanvas } = transform;
  const isEditMode   = tool === 'select' || tool === 'pen';

  return (
    <g role="group" aria-label="Glyph bezier paths">
      {glyph.contours.map(contour => {
        const d = contourToPath(contour.points, contour.closed, toCanvas);

        return (
          <g key={contour.id}>
            {showFill && (
              <path d={d} fill={C.pathFill} stroke="none"/>
            )}

            {/* ── ハンドルライン ── */}
            {isEditMode && contour.points.map(pt => {
              const pc = toCanvas(getPos(pt)); // 🟢 getPos を使用
              return (
                <g key={`hl-${pt.id}`}>
                  {pt.handleOut && (() => {
                    const hc = toCanvas(pt.handleOut);
                    return <line x1={pc.x} y1={pc.y} x2={hc.x} y2={hc.y}
                      stroke={C.handleLine} strokeWidth={1} strokeDasharray="2,4"/>;
                  })()}
                  {pt.handleIn && (() => {
                    const hc = toCanvas(pt.handleIn);
                    return <line x1={pc.x} y1={pc.y} x2={hc.x} y2={hc.y}
                      stroke={C.handleLine} strokeWidth={1} strokeDasharray="2,4"/>;
                  })()}
                </g>
              );
            })}

            {/* ── パス ── */}
            <path
              d={d} fill="none" stroke={C.path} strokeWidth={2.5}
              strokeLinecap="round" strokeLinejoin="round"
            />

            {/* ── アンカー + ハンドル端点 ── */}
            {isEditMode && contour.points.map(pt => {
              const pos = getPos(pt);          // 🟢 getPos を使用
              const pc  = toCanvas(pos); 
              const sel = selection.pointIds.includes(pt.id);
              const isSmooth = pt.type === 'smooth';

              return (
                <g key={`ap-${pt.id}`}>
                  <circle
                    cx={pc.x} cy={pc.y} r={HIT_RADIUS} fill="transparent"
                    style={{ cursor: 'grab' }}
                    onPointerDown={e => onAnchorPointerDown?.(contour.id, pt.id, e)}
                    aria-label={`Anchor ${pt.id} at x:${Math.round(pos.x)} y:${Math.round(pos.y)}`}
                  />

                  {sel && (
                    isSmooth
                      ? <circle cx={pc.x} cy={pc.y} r={SMOOTH_RADIUS + 4}
                          fill="none" stroke={C.selectedRing} strokeWidth={1.5}
                          strokeDasharray="2,2"/>
                      : <rect
                          x={pc.x - ANCHOR_SIZE - 4} y={pc.y - ANCHOR_SIZE - 4}
                          width={(ANCHOR_SIZE + 4) * 2} height={(ANCHOR_SIZE + 4) * 2}
                          rx={1.5} fill="none"
                          stroke={C.selectedRing} strokeWidth={1.5}
                          strokeDasharray="2,2"/>
                  )}

                  {isSmooth ? (
                    <circle cx={pc.x} cy={pc.y} r={SMOOTH_RADIUS}
                      fill={sel ? C.anchorActive : C.anchorSmooth}
                      stroke={C.anchorBorder} strokeWidth={1.5}/>
                  ) : (
                    <rect
                      x={pc.x - ANCHOR_SIZE / 2} y={pc.y - ANCHOR_SIZE / 2}
                      width={ANCHOR_SIZE} height={ANCHOR_SIZE} rx={1.5}
                      fill={sel ? C.anchorActive : C.anchorFill}
                      stroke={C.anchorBorder} strokeWidth={1.5}/>
                  )}

                  {[
                    { handle: pt.handleOut, which: 'out' as const },
                    { handle: pt.handleIn,  which: 'in'  as const },
                  ].map(({ handle, which }) => {
                    if (!handle) return null;
                    const hc = toCanvas(handle);
                    return (
                      <g key={which}>
                        <circle
                          cx={hc.x} cy={hc.y} r={HIT_RADIUS * 0.8} fill="transparent"
                          style={{ cursor: 'crosshair' }}
                          onPointerDown={e => onHandlePointerDown?.(contour.id, pt.id, which, e)}
                        />
                        <circle cx={hc.x} cy={hc.y} r={HANDLE_RADIUS}
                          fill={C.handleFill} stroke={C.anchorBorder} strokeWidth={1.5}/>
                      </g>
                    );
                  })}

                  {sel && (
                    <CoordBadge cx={pc.x} cy={pc.y} anchor={pt}/>
                  )}
                </g>
              );
            })}
          </g>
        );
      })}
    </g>
  );
};