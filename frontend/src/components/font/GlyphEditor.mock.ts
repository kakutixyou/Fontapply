/**
 * GlyphEditor.mock.ts
 *
 * 文字 D のダミーグリフデータ。
 * 本番では glyph_builder.py / font_loader.py の出力に差し替える。
 *
 * 座標系: em = 1000u, baseline = 0, cap-height = 680u
 */

import type { GlyphData, FontMetrics } from './GlyphEditor.types';

export const MOCK_METRICS = {
  ascender: 800,
  cap_height: 680,    // ← ここを直す (旧: capHeight)
  x_height: 480,      // ← ここを直す (旧: xHeight)
  descender: -200,
  lsb: 60,
  rsb: 60,
  units_per_em: 1000, // ← ここを直す (旧: unitsPerEm)
};

/** D の輪郭（簡略化した 5 アンカーパス）*/
export const MOCK_GLYPH_D: GlyphData = {
    char: 'D',
    unicode: '0044',
    width: 620,
    contours: [
        {
            id: 'c0',
            closed: true,
            points: [
                {
                    id: 'p0',
                    pos: { x: 80, y: 0 }, // 左下 (baseline)
                    type: 'corner',
                    handleIn: null,
                    handleOut: null,
                    linked: false,
                },
                {
                    id: 'p1',
                    pos: { x: 80, y: 680 }, // 左上 (cap-height)
                    type: 'corner',
                    handleIn: null,
                    handleOut: null,
                    linked: false,
                },
                {
                    id: 'p2',
                    pos: { x: 300, y: 680 }, // 上の肩
                    type: 'smooth',
                    handleIn: { x: 180, y: 680 },
                    handleOut: { x: 460, y: 680 },
                    linked: true,
                },
                {
                    id: 'p3',
                    pos: { x: 520, y: 340 }, // 右の頂点 (ボウル最右端)
                    type: 'smooth',
                    handleIn: { x: 520, y: 530 },
                    handleOut: { x: 520, y: 150 },
                    linked: true,
                },
                {
                    id: 'p4',
                    pos: { x: 300, y: 0 }, // 下の肩
                    type: 'smooth',
                    handleIn: { x: 460, y: 0 },
                    handleOut: { x: 180, y: 0 },
                    linked: true,
                },
            ],
        },
    ],
    id: ''
};
