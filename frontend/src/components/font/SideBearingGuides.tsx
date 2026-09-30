/**
 * SideBearingGuides.tsx
 *
 * LSB / RSB の縦ガイド線と上端ラベル。
 * フォントユニット座標を transform で変換して描画。
 */

import React from 'react';
import type { FontMetrics } from './GlyphEditor.types';
import type { GlyphTransform } from '../../hooks/useGlyphTransform';

interface SideBearingGuidesProps {
  metrics:    FontMetrics;
  glyphWidth: number;
  transform:  GlyphTransform;
  canvasH:    number;
}

export const SideBearingGuides: React.FC<SideBearingGuidesProps> = ({
  metrics, glyphWidth, transform, canvasH,
}) => {
  const lsbX = transform.toCanvas({ x: metrics.lsb,               y: 0 }).x;
  const rsbX = transform.toCanvas({ x: glyphWidth - metrics.rsb,   y: 0 }).x;
  const topY  = 46;
  const botY  = canvasH - 16;

  const lineStyle = {
    stroke: 'rgba(192,155,78,.32)',
    strokeWidth: 0.75,
    strokeDasharray: '3,8',
  } as const;

  const labelStyle = {
    fontFamily: "'DM Mono', monospace",
    fontSize: 8,
    fill: 'rgba(192,155,78,.42)',
    textAnchor: 'middle',
  } as const;

  return (
    <g role="group" aria-label="Side bearing guides">
      {/* LSB */}
      <line x1={lsbX} y1={topY} x2={lsbX} y2={botY} {...lineStyle}/>
      <text x={lsbX} y={topY - 4} {...labelStyle}>LSB {metrics.lsb}</text>

      {/* RSB */}
      <line x1={rsbX} y1={topY} x2={rsbX} y2={botY} {...lineStyle}/>
      <text x={rsbX} y={topY - 4} {...labelStyle}>RSB {metrics.rsb}</text>

      {/* Advance width tick at baseline */}
      {(() => {
        const zeroX = transform.toCanvas({ x: 0,          y: 0 }).x;
        const advX  = transform.toCanvas({ x: glyphWidth, y: 0 }).x;
        const baseY = transform.toCanvas({ x: 0, y: metrics.baseline }).y;
        return (
          <>
            {/* origin tick */}
            <line
              x1={zeroX} y1={baseY - 8}
              x2={zeroX} y2={baseY + 8}
              stroke="rgba(58,124,232,.35)"
              strokeWidth={1}
            />
            {/* advance width tick */}
            <line
              x1={advX} y1={baseY - 8}
              x2={advX} y2={baseY + 8}
              stroke="rgba(58,124,232,.25)"
              strokeWidth={1}
            />
            {/* width label */}
            <text
              x={(zeroX + advX) / 2}
              y={baseY + 20}
              fontFamily="'DM Mono', monospace"
              fontSize={8}
              fill="rgba(192,155,78,.4)"
              textAnchor="middle"
            >
              {glyphWidth}u
            </text>
          </>
        );
      })()}
    </g>
  );
};