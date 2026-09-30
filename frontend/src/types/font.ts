/** Font manifest entry type shared between Electron, React, and Python. */

export type FontFormat = 'ttf' | 'otf' | 'woff2';

export interface FontManifestEntry {
  id: string;
  projectId: string;
  family: string;
  filePath: string;
  format: FontFormat;
  isVariable: boolean;
  createdAt: string;
}

export interface VariableAxis {
  tag: string;   // e.g. "wght"
  name: string;  // e.g. "Weight"
  min: number;
  max: number;
  default: number;
}

export interface FontSubsetRequest {
  fontId: string;
  unicodeRanges: string[];
}

export interface FontConvertRequest {
  fontId: string;
}

export interface FontGenerateRequest {
  metadata?: Record<string, unknown>;
  metrics?: Record<string, unknown>;
  glyphs?: Array<Record<string, unknown>>;
  include_kerning?: boolean;
  output_format?: FontFormat;
}

export interface FontGenerateResponse {
  status?: string;
  font_id: string;
  family_name?: string;
  file_path?: string;
  format?: FontFormat;
}

export interface FontConvertResponse {
  status?: string;
  font_id: string;
  family_name?: string;
  file_path?: string;
  format?: FontFormat;
}
