import { contextBridge, ipcRenderer } from 'electron';

// Expose secure API to renderer
contextBridge.exposeInMainWorld('electronAPI', {
  // ══════════════════════════════════════════════════════════════════
  // 大動脈: 汎用 invoke (これが一番重要)
  // ══════════════════════════════════════════════════════════════════
  invoke: (channel: string, ...args: unknown[]) =>
    ipcRenderer.invoke(channel, ...args),

  // ── Project operations ──
  createProject: (data: any) => ipcRenderer.invoke('project:create', data),
  readProject: (id: string) => ipcRenderer.invoke('project:read', id),
  updateProject: (id: string, data: any) => ipcRenderer.invoke('project:update', id, data),
  deleteProject: (id: string) => ipcRenderer.invoke('project:delete', id),
  listProjects: () => ipcRenderer.invoke('project:list'),

  // ── AI operations ──
  chatAI: (message: string) => ipcRenderer.invoke('ai:chat', message),
  generateAI: (prompt: string) => ipcRenderer.invoke('ai:generate', prompt),

  // ── System status ──
  getPythonStatus: () => ipcRenderer.invoke('python:status'),
  checkBackendStatus: () => ipcRenderer.invoke('system:check-backend'),

  // ── AI Analytics Pipeline (一旦キープ) ──
  onPipelineUpdate: (callback: (payload: any) => void) => {
    const subscription = (_event: any, payload: any) => callback(payload);
    ipcRenderer.on('ai-pipeline:update', subscription);
    return () => {
      ipcRenderer.removeListener('ai-pipeline:update', subscription);
    };
  },
  setPipelineToggle: (key: string, enabled: boolean) => 
    ipcRenderer.invoke('ai-pipeline:set-toggle', { key, enabled }),
  requestPipelineExtract: (unicode: string) => 
    ipcRenderer.invoke('ai-pipeline:request-extract', unicode),

  // ── Collab (一旦キープ) ──
  getCollabUsers: () => ipcRenderer.invoke('collab:get-users'),
});