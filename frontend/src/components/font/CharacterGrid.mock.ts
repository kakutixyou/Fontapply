// frontend/src/components/font/CharacterGrid.mock.ts

export const MOCK_META = new Map([
  ['0041', { unicode: '0041', char: 'A', name: 'A' }],
  ['0042', { unicode: '0042', char: 'B', name: 'B' }],
  ['0043', { unicode: '0043', char: 'C', name: 'C' }],
  ['0044', { unicode: '0044', char: 'D', name: 'D' }], // ← FontStudioのデフォルト
  ['0045', { unicode: '0045', char: 'E', name: 'E' }],
]);

// frontend/src/components/font/CharacterGrid.mock.ts

// import type { GlyphMeta } from './CharacterGrid.types';

// export const MOCK_META = new Map<string, GlyphMeta>([
//   ['0041', { unicode: '0041', status: 'drawn', captured: true }],
//   ['0042', { unicode: '0042', status: 'draft', captured: false }],
//   ['0043', { unicode: '0043', status: 'not_started', captured: false }],
//   ['0044', { unicode: '0044', status: 'drawn', captured: false }], // ← D
//   ['0045', { unicode: '0045', status: 'not_started', captured: false }],
// ]);