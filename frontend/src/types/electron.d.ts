// webforge-ai-desktop/frontend/src/types/electron.d.ts

import type {
  ConvertRequest,
  ConvertResponse,
  GenerateFontRequest,
  GenerateFontResponse,
  PreviewRequest,
  SubsetRequest,
  SubsetResponse,
} from '../../../shared/types/font';
import type { PipelinePayload } from '../components/font/aiPipeline.types';

export interface ElectronAPI {
  invoke: (channel: string, ...args: unknown[]) => Promise<any>;
  // ── 既存のプロジェクト・AI機能 ──
  createProject: (data: any) => Promise<any>;
  readProject: (id: number | string) => Promise<any>;
  updateProject: (id: number | string, data: any) => Promise<any>;
  deleteProject: (id: number | string) => Promise<any>;
  listProjects: () => Promise<any[]>;
  chatAI: (message: string) => Promise<any>;
  generateAI: (prompt: string) => Promise<any>;
  getPythonStatus: () => Promise<any>;

  // ── 既存のフォント処理機能 ──
  generateFont: (data: GenerateFontRequest) => Promise<GenerateFontResponse>;
  convertFont: (data: ConvertRequest) => Promise<ConvertResponse>;
  subsetFont: (data: SubsetRequest) => Promise<SubsetResponse>;
  previewFont: (data: PreviewRequest) => Promise<Blob>;

  // ── システム連携 ──
  checkBackendStatus: () => Promise<'connected' | 'disconnected' | 'error'>;
  
  // ── フォント・グリフデータ管理 ──
  getGlyphs: () => Promise<any[]>;
  getGlyphData: (unicode: string) => Promise<any>;
  saveGlyph: (unicode: string, glyph: import('../components/font/GlyphEditor.types').GlyphData) => Promise<{ glyph: import('../components/font/GlyphEditor.types').GlyphData }>;
  saveFont: (fontData: any) => Promise<{ success: boolean; message?: string }>;
  updateGlyphPoint: (unicode: string, contourId: string, pointId: string, position: {x: number, y: number}) => Promise<any>;
  // ── AI学習データパイプライン ──
  onPipelineUpdate: (callback: (payload: PipelinePayload) => void) => () => void;
  setPipelineToggle: (key: string, enabled: boolean) => Promise<void>;
  requestPipelineExtract: (unicode: string) => Promise<void>;

  // ── コラボレーション ──
  getCollabUsers: () => Promise<any[]>;

  // ── ウィンドウ制御 ──
  window?: {
    minimize?: () => void;
    maximize?: () => void;
    close?: () => void;
  };
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}