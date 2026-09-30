export interface DesignElement {
  id: string;
  type: 'container' | 'text' | 'button' | 'image' | 'input' | 'unknown';
  x: number;
  y: number;
  width: number;
  height: number;
  text?: string;
  class_name?: string;
}

export interface UploadResponse {
  project_id: string;
  image_path: string;
  created_at: string;
}

export interface AnalyzeResponse {
  analysis_id: string;
  project_id: string;
  elements: DesignElement[];
  layout_summary: string;
  source: 'claude_vision' | 'fallback';
}

export interface GenerateCodeResponse {
  analysis_id: string;
  jsx: string;
  css: string;
}
