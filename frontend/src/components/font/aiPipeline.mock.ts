/**
 * aiPipeline.mock.ts
 *
 * モックデータファクトリ。
 * Python バックエンドとの IPC が繋がるまではこれを使う。
 * 本番では削除して preload.ts 経由の実データに差し替える。
 */

import type { PipelinePayload } from './aiPipeline.types';

export function makeMockPayload(glyphChar = 'D', unicode = '0044'): PipelinePayload {
  return {
    glyphChar,
    glyphUnicode: unicode,
    sessionId: '#4821',
    isLive: true,

    datapoints: {
      skeletonPts:   847,
      strokeCount:   23,
      intersections: 6,
      curvaturePts:  312,
    },

    radar: {
      verticality: 0.88,
      symmetry:    0.74,
      contrast:    0.82,
      counter:     0.68,
      aperture:    0.91,
      axisAngle:   0.58,
    },

    features: [
      { name: 'stem width',    value: 0.82, tier: 'primary' },
      { name: 'bowl radius',   value: 0.91, tier: 'primary' },
      { name: 'serif depth',   value: 0.34, tier: 'warning' },
      { name: 'weight axis',   value: 0.67, tier: 'accent'  },
      { name: 'x-height ratio',value: 0.78, tier: 'primary' },
      { name: 'angle variance',value: 0.55, tier: 'accent'  },
    ],

    strokeStats: {
      phases: [
        { label: 'approach',   weight: 3, color: '#c09b4e',              isActive: false },
        { label: 'transition', weight: 1, color: 'rgba(192,155,78,.4)',  isActive: false },
        { label: 'main',       weight: 5, color: '#1d9e75',              isActive: true  },
        { label: 'transition', weight: 1, color: 'rgba(29,158,117,.35)', isActive: false },
        { label: 'bowl curve', weight: 4, color: '#3a7ce8',              isActive: false },
        { label: 'transition', weight: 1, color: 'rgba(58,124,232,.3)',  isActive: false },
        { label: 'terminal',   weight: 2, color: 'rgba(255,255,255,.15)',isActive: false },
      ],
      velocityPeak: 0.31,
      pressureAvg:  0.74,
    },

    confidence: [
      { key: 'class',    label: 'class conf.',  score: 94, detail: 'Latin uppercase D\nopen right counter',  colorRole: 'success' },
      { key: 'style',    label: 'style fit',    score: 78, detail: 'humanist sans\nmedium contrast',        colorRole: 'brass'   },
      { key: 'skeleton', label: 'skeleton',     score: 88, detail: '2-segment path\n1 anchor node',         colorRole: 'info'    },
      { key: 'anomaly',  label: 'anomaly',      score: 12, detail: 'serif depth\nbelow avg',               colorRole: 'danger'  },
    ],

    stages: [
      { key: 'vectorize', label: 'vectorize', status: 'done'    },
      { key: 'skeleton',  label: 'skeleton',  status: 'done'    },
      { key: 'features',  label: 'features',  status: 'active'  },
      { key: 'embed',     label: 'embed',     status: 'pending' },
      { key: 'label',     label: 'label',     status: 'pending' },
      { key: 'export',    label: 'export',    status: 'pending' },
    ],

    toggles: [
      { key: 'velocity',  label: 'stroke velocity',    sub: 'tablet pressure + timing',     enabled: true  },
      { key: 'curvature', label: 'curvature tensor',   sub: '2nd derivative of bezier',     enabled: true  },
      { key: 'skeleton',  label: 'skeleton annotation',sub: 'medial axis transform',         enabled: true  },
      { key: 'embed',     label: 'style embedding',    sub: 'CLIP-style latent space',       enabled: false },
      { key: 'errorfix',  label: 'error correction',   sub: 'outlier suppression',           enabled: true  },
    ],

    queue: [
      { filename: 'D_skeleton_847pts.json', sizeKB: 2.1,  status: 'exported'   },
      { filename: 'D_strokes_phase.bin',    sizeKB: 18,   status: 'exported'   },
      { filename: 'D_features_embed.npy',   sizeKB: null, status: 'extracting' },
      { filename: 'D_label_humanist.jsonl', sizeKB: null, status: 'queued'     },
    ],
  };
}