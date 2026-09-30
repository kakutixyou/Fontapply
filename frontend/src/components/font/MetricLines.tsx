/**
 * MetricLines.tsx
 *
 * タイポグラフィ基準線の SVG レイヤー。
 * Baseline だけ実線・ブルー系、他は真鍮色の破線。
 * 各線の左端にラベルチップ、右端に数値。
 */

import React from 'react';
import type { FontMetrics } from './GlyphEditor.types';
import type { GlyphTransform } from '../../hooks/useGlyphTransform';

interface MetricLinesProps {
  metrics: FontMetrics;
  transform: GlyphTransform;
  canvasW: number;
  /** ラベルエリアのオフセット */
  labelX?: number;
}

interface LineSpec {
  key:      string;
  label:    string;
  value:    number;
  /** 'baseline' | 'capheight' | 'secondary' | 'descender' */
  role:     'baseline' | 'capheight' | 'secondary' | 'descender';
}

const LABEL_W  = 42;
const LABEL_H  = 13;
const LINE_X0  = 58;   // ラベルの右端からパスが始まる
const CHIP_PAD = 4;    // ラベルチップの左パディング

export const MetricLines: React.FC<MetricLinesProps> = ({
  metrics, transform, canvasW,
}) => {
  const lines: LineSpec[] = [
    { key: 'ascender',  label: 'ASCDR',  value: metrics.ascender,  role: 'secondary'  },
    { key: 'capHeight', label: 'CAP H',  value: metrics.capHeight, role: 'capheight'  },
    { key: 'xHeight',   label: 'X-HGT',  value: metrics.xHeight,   role: 'secondary'  },
    { key: 'baseline',  label: 'BASLN',  value: metrics.baseline,  role: 'baseline'   },
    { key: 'descender', label: 'DESCN',  value: metrics.descender, role: 'descender'  },
  ];

  // ロール別スタイル
  const style = {
    baseline:  { stroke: 'rgba(58,124,232,.55)',  dasharray: 'none',      textColor: 'rgba(58,124,232,.75)',  chipFill: 'rgba(58,124,232,.15)'  },
    capheight: { stroke: 'rgba(192,155,78,.55)',  dasharray: '5,5',       textColor: 'rgba(192,155,78,.85)',  chipFill: 'rgba(192,155,78,.15)'  },
    secondary: { stroke: 'rgba(192,155,78,.28)',  dasharray: '4,6',       textColor: 'rgba(192,155,78,.45)',  chipFill: 'rgba(192,155,78,.08)'  },
    descender: { stroke: 'rgba(58,124,232,.2)',   dasharray: '3,7',       textColor: 'rgba(58,124,232,.4)',   chipFill: 'rgba(58,124,232,.07)'  },
  };
  const weight = { baseline: 1.25, capheight: 1.0, secondary: 0.75, descender: 0.75 };

  // 右端の数値エリア
  const rightNumX = canvasW - 8;

  // ティック（右端の小さな印）
  const tickX1 = canvasW - 28;
  const tickX2 = canvasW - 18;

  return (
    <g role="group" aria-label="Typographic metric lines">
      {lines.map(line => {
        const cy  = transform.toCanvas({ x: 0, y: line.value }).y;
        const s   = style[line.role];
        const sw  = weight[line.role];

        return (
          <g key={line.key}>
            {/* 本線 */}
            <line
              x1={LINE_X0} y1={cy}
              x2={tickX1}  y2={cy}
              stroke={s.stroke}
              strokeWidth={sw}
              strokeDasharray={s.dasharray === 'none' ? undefined : s.dasharray}
            />
            {/* 右ティック */}
            <line
              x1={tickX1} y1={cy}
              x2={tickX2} y2={cy}
              stroke={s.stroke}
              strokeWidth={sw * 1.2}
            />

            {/* 左ラベルチップ */}
            <rect
              x={CHIP_PAD}
              y={cy - LABEL_H / 2}
              width={LABEL_W}
              height={LABEL_H}
              rx={2}
              fill={s.chipFill}
            />
            <text
              x={CHIP_PAD + 4}
              y={cy + 4.5}
              fontFamily="'DM Mono', monospace"
              fontSize={8}
              fill={s.textColor}
              letterSpacing="0.06em"
            >
              {line.label}
            </text>

            {/* 右数値 */}
            <text
              x={rightNumX}
              y={cy + 4.5}
              fontFamily="'DM Mono', monospace"
              fontSize={8}
              fill={s.textColor}
              textAnchor="end"
            >
              {line.value}
            </text>
          </g>
        );
      })}
    </g>
  );
};