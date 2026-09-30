const API_BASE_URL = import.meta.env.VITE_DESIGN_API_BASE_URL || 'http://localhost:8000';
async function requestJson(url, init = {}) {
    const response = await fetch(url, init);
    if (!response.ok) {
        throw new Error(await response.text() || `HTTP ${response.status}`);
    }
    if (response.status === 204) {
        return undefined;
    }
    return (await response.json());
}
async function uploadViaHttp(file, projectId) {
    const formData = new FormData();
    formData.append('file', file);
    if (projectId) {
        formData.append('project_id', projectId);
    }
    return requestJson(`${API_BASE_URL}/design/upload`, { method: 'POST', body: formData });
}
function downloadTextFile(fileName, content) {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = fileName;
    anchor.click();
    URL.revokeObjectURL(url);
}
export const electronAPI = {
    upload: (file, projectId) => {
        if (window.designAPI?.uploadDesign) {
            return window.designAPI.uploadDesign(file, projectId);
        }
        return uploadViaHttp(file, projectId);
    },
    analyze: (projectId) => {
        if (window.designAPI?.analyzeDesign) {
            return window.designAPI.analyzeDesign(projectId);
        }
        return requestJson(`${API_BASE_URL}/design/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_id: projectId }),
        });
    },
    generate: (analysisId, componentName = 'GeneratedScreen') => {
        if (window.designAPI?.generateJsx) {
            return window.designAPI.generateJsx(analysisId, componentName);
        }
        return requestJson(`${API_BASE_URL}/design/generate-jsx`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ analysis_id: analysisId, component_name: componentName }),
        });
    },
    exportCode: async (name, jsx, css) => {
        if (window.designAPI?.exportCode) {
            return window.designAPI.exportCode(name, jsx, css);
        }
        downloadTextFile(`${name}.tsx`, jsx);
        downloadTextFile(`${name}.css`, css);
        return { path: 'browser-download' };
    },
    projects: {
        list: () => {
            if (window.designAPI?.listProjects) {
                return window.designAPI.listProjects();
            }
            return requestJson(`${API_BASE_URL}/projects`);
        },
        get: (projectId) => {
            if (window.designAPI?.getProject) {
                return window.designAPI.getProject(projectId);
            }
            return requestJson(`${API_BASE_URL}/projects/${projectId}`);
        },
        create: (input) => {
            if (window.designAPI?.createProject) {
                return window.designAPI.createProject(input);
            }
            return requestJson(`${API_BASE_URL}/projects`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(input),
            });
        },
        update: (projectId, input) => {
            if (window.designAPI?.updateProject) {
                return window.designAPI.updateProject(projectId, input);
            }
            return requestJson(`${API_BASE_URL}/projects/${projectId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(input),
            });
        },
        delete: async (projectId) => {
            if (window.designAPI?.deleteProject) {
                return window.designAPI.deleteProject(projectId);
            }
            await requestJson(`${API_BASE_URL}/projects/${projectId}`, { method: 'DELETE' });
        },
    },
};
