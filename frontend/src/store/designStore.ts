import { create } from 'zustand';
import type { AnalyzeResponse, GenerateCodeResponse, UploadResponse } from '../types/design';
import type { ProjectRecord } from '../types/project';

interface DesignStore {
  projects: ProjectRecord[];
  currentProject?: ProjectRecord;
  upload?: UploadResponse;
  analysis?: AnalyzeResponse;
  generated?: GenerateCodeResponse;
  isLoading: boolean;
  error?: string;
  exportPath?: string;
  setProjects: (projects: ProjectRecord[]) => void;
  setCurrentProject: (project?: ProjectRecord) => void;
  setUpload: (upload?: UploadResponse) => void;
  setAnalysis: (analysis?: AnalyzeResponse) => void;
  setGenerated: (generated?: GenerateCodeResponse) => void;
  setLoading: (loading: boolean) => void;
  setError: (error?: string) => void;
  setExportPath: (path?: string) => void;
  resetWorkspace: () => void;
}

export const useDesignStore = create<DesignStore>((set) => ({
  projects: [],
  isLoading: false,
  setProjects: (projects) => set({ projects }),
  setCurrentProject: (currentProject) => set({ currentProject }),
  setUpload: (upload) => set({ upload }),
  setAnalysis: (analysis) => set({ analysis }),
  setGenerated: (generated) => set({ generated }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  setExportPath: (exportPath) => set({ exportPath }),
  resetWorkspace: () => set({ upload: undefined, analysis: undefined, generated: undefined, exportPath: undefined, error: undefined }),
}));
