// useGlyphTransform.ts

import { useMemo } from 'react';
import type { Viewport, FontMetrics, Vec2 } from '../components/font/GlyphEditor.types';

interface UseGlyphTransformOptions {
  canvasW: number;
  canvasH: number;
  metrics: FontMetrics;
  glyphWidth: number;
  zoomFactor?: number;
  pan?: Vec2; // ✨ ここを追加：スライドの座標を受け取る
}

export interface GlyphTransform {
  viewport: Viewport;
  toCanvas: (p?: Vec2 | null) => Vec2;
  toFont:   (p?: Vec2 | null) => Vec2;
  scale:    number;
}

export function useGlyphTransform({
  canvasW,
  canvasH,
  metrics,
  glyphWidth,
  zoomFactor = 1.0,
  pan = { x: 0, y: 0 }, // ✨ デフォルト値を設定
}: UseGlyphTransformOptions): GlyphTransform {
  return useMemo(() => {
    const totalH = metrics.ascender - metrics.descender;
    const totalW = glyphWidth;

    const marginH = 0.15;
    const marginV = 0.12;

    const scaleX = (canvasW * (1 - marginH * 2)) / totalW;
    const scaleY = (canvasH * (1 - marginV * 2)) / totalH;
    const baseScale = Math.min(scaleX, scaleY) * zoomFactor;

    // ✨ スライド移動（pan.x / pan.y）を原点に足し込む
    const originX = canvasW / 2 - (totalW / 2) * baseScale + pan.x;
    const originY = canvasH * (1 - marginV) - (-metrics.descender) * baseScale + pan.y;

    const viewport: Viewport = { scale: baseScale, originX, originY };

    const toCanvas = (p?: Vec2 | null): Vec2 => {
      if (!p) {
        console.warn('⚠️ toCanvas received undefined/null', p);
        return { x: 0, y: 0 }; 
      }
      return {
        x: originX + p.x * baseScale,
        y: originY - p.y * baseScale, 
      };
    };

    const toFont = (p?: Vec2 | null): Vec2 => {
      if (!p) return { x: 0, y: 0 };
      return {
        x: (p.x - originX) / baseScale,
        y: (originY - p.y) / baseScale,
      };
    };

    return { viewport, toCanvas, toFont, scale: baseScale };
  }, [canvasW, canvasH, metrics, glyphWidth, zoomFactor, pan]); // ✨ panを監視対象に追加
}