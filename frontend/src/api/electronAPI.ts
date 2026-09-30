import type { AnalyzeResponse, GenerateCodeResponse, UploadResponse } from '../types/design';
import type {
  FontConvertRequest,
  FontConvertResponse,
  FontGenerateRequest,
  FontGenerateResponse,
} from '../types/font';
import type { CreateProjectInput, ProjectRecord, UpdateProjectInput } from '../types/project';

declare global {
  interface Window {
    designAPI?: {
      uploadDesign?: (file: File, projectId?: string) => Promise<UploadResponse>;
      analyzeDesign?: (projectId: string) => Promise<AnalyzeResponse>;
      generateJsx?: (analysisId: string, componentName: string) => Promise<GenerateCodeResponse>;
      exportCode?: (name: string, jsx: string, css: string) => Promise<{ path: string }>;
      generateFont?: (request: FontGenerateRequest) => Promise<FontGenerateResponse>;
      convertFont?: (request: FontConvertRequest) => Promise<FontConvertResponse>;
      listProjects?: () => Promise<ProjectRecord[]>;
      getProject?: (projectId: string) => Promise<ProjectRecord>;
      createProject?: (input: CreateProjectInput) => Promise<ProjectRecord>;
      updateProject?: (projectId: string, input: UpdateProjectInput) => Promise<ProjectRecord>;
      deleteProject?: (projectId: string) => Promise<void>;
    };
  }
}

const API_BASE_URL = import.meta.env.VITE_DESIGN_API_BASE_URL || 'http://127.0.0.1:8000';
const FONT_API_BASE_URL = import.meta.env.VITE_FONT_API_BASE_URL || 'http://127.0.0.1:8000';

async function requestJson<T>(url: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    throw new Error(await response.text() || `HTTP ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

async function uploadViaHttp(file: File, projectId?: string): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (projectId) {
    formData.append('project_id', projectId);
  }
  return requestJson<UploadResponse>(`${API_BASE_URL}/design/upload`, { method: 'POST', body: formData });
}

function downloadTextFile(fileName: string, content: string): void {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = fileName;
  anchor.click();
  URL.revokeObjectURL(url);
}

export const electronAPI = {
  upload: (file: File, projectId?: string): Promise<UploadResponse> => {
    if (window.designAPI?.uploadDesign) {
      return window.designAPI.uploadDesign(file, projectId);
    }
    return uploadViaHttp(file, projectId);
  },
  analyze: (projectId: string): Promise<AnalyzeResponse> => {
    if (window.designAPI?.analyzeDesign) {
      return window.designAPI.analyzeDesign(projectId);
    }
    return requestJson<AnalyzeResponse>(`${API_BASE_URL}/design/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id: projectId }),
    });
  },
  generate: (analysisId: string, componentName = 'GeneratedScreen'): Promise<GenerateCodeResponse> => {
    if (window.designAPI?.generateJsx) {
      return window.designAPI.generateJsx(analysisId, componentName);
    }
    return requestJson<GenerateCodeResponse>(`${API_BASE_URL}/design/generate-jsx`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ analysis_id: analysisId, component_name: componentName }),
    });
  },
  exportCode: async (name: string, jsx: string, css: string): Promise<{ path: string }> => {
    if (window.designAPI?.exportCode) {
      return window.designAPI.exportCode(name, jsx, css);
    }
    downloadTextFile(`${name}.tsx`, jsx);
    downloadTextFile(`${name}.css`, css);
    return { path: 'browser-download' };
  },
  generateFont: (request: FontGenerateRequest): Promise<FontGenerateResponse> => {
    if (window.designAPI?.generateFont) {
      return window.designAPI.generateFont(request);
    }
    return requestJson<FontGenerateResponse>(`${FONT_API_BASE_URL}/fonts/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
  },
  convertFont: (request: FontConvertRequest): Promise<FontConvertResponse> => {
    if (window.designAPI?.convertFont) {
      return window.designAPI.convertFont(request);
    }
    return requestJson<FontConvertResponse>(`${FONT_API_BASE_URL}/fonts/convert`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        font_id: request.fontId,
      }),
    });
  },
  projects: {
    list: (): Promise<ProjectRecord[]> => {
      if (window.designAPI?.listProjects) {
        return window.designAPI.listProjects();
      }
      return requestJson<ProjectRecord[]>(`${API_BASE_URL}/projects`);
    },
    get: (projectId: string): Promise<ProjectRecord> => {
      if (window.designAPI?.getProject) {
        return window.designAPI.getProject(projectId);
      }
      return requestJson<ProjectRecord>(`${API_BASE_URL}/projects/${projectId}`);
    },
    create: (input: CreateProjectInput): Promise<ProjectRecord> => {
      if (window.designAPI?.createProject) {
        return window.designAPI.createProject(input);
      }
      return requestJson<ProjectRecord>(`${API_BASE_URL}/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input),
      });
    },
    update: (projectId: string, input: UpdateProjectInput): Promise<ProjectRecord> => {
      if (window.designAPI?.updateProject) {
        return window.designAPI.updateProject(projectId, input);
      }
      return requestJson<ProjectRecord>(`${API_BASE_URL}/projects/${projectId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input),
      });
    },
    delete: async (projectId: string): Promise<void> => {
      if (window.designAPI?.deleteProject) {
        return window.designAPI.deleteProject(projectId);
      }
      await requestJson<void>(`${API_BASE_URL}/projects/${projectId}`, { method: 'DELETE' });
    },
  },
};
