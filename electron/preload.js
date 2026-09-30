"use strict";
var __spreadArray = (this && this.__spreadArray) || function (to, from, pack) {
    if (pack || arguments.length === 2) for (var i = 0, l = from.length, ar; i < l; i++) {
        if (ar || !(i in from)) {
            if (!ar) ar = Array.prototype.slice.call(from, 0, i);
            ar[i] = from[i];
        }
    }
    return to.concat(ar || Array.prototype.slice.call(from));
};
Object.defineProperty(exports, "__esModule", { value: true });
var electron_1 = require("electron");
// Expose secure API to renderer
electron_1.contextBridge.exposeInMainWorld('electronAPI', {
    // ══════════════════════════════════════════════════════════════════
    // 大動脈: 汎用 invoke (これが一番重要)
    // ══════════════════════════════════════════════════════════════════
    invoke: function (channel) {
        var args = [];
        for (var _i = 1; _i < arguments.length; _i++) {
            args[_i - 1] = arguments[_i];
        }
        return electron_1.ipcRenderer.invoke.apply(electron_1.ipcRenderer, __spreadArray([channel], args, false));
    },
    // ── Project operations ──
    createProject: function (data) { return electron_1.ipcRenderer.invoke('project:create', data); },
    readProject: function (id) { return electron_1.ipcRenderer.invoke('project:read', id); },
    updateProject: function (id, data) { return electron_1.ipcRenderer.invoke('project:update', id, data); },
    deleteProject: function (id) { return electron_1.ipcRenderer.invoke('project:delete', id); },
    listProjects: function () { return electron_1.ipcRenderer.invoke('project:list'); },
    // ── AI operations ──
    chatAI: function (message) { return electron_1.ipcRenderer.invoke('ai:chat', message); },
    generateAI: function (prompt) { return electron_1.ipcRenderer.invoke('ai:generate', prompt); },
    // ── System status ──
    getPythonStatus: function () { return electron_1.ipcRenderer.invoke('python:status'); },
    checkBackendStatus: function () { return electron_1.ipcRenderer.invoke('system:check-backend'); },
    // ── AI Analytics Pipeline (一旦キープ) ──
    onPipelineUpdate: function (callback) {
        var subscription = function (_event, payload) { return callback(payload); };
        electron_1.ipcRenderer.on('ai-pipeline:update', subscription);
        return function () {
            electron_1.ipcRenderer.removeListener('ai-pipeline:update', subscription);
        };
    },
    setPipelineToggle: function (key, enabled) {
        return electron_1.ipcRenderer.invoke('ai-pipeline:set-toggle', { key: key, enabled: enabled });
    },
    requestPipelineExtract: function (unicode) {
        return electron_1.ipcRenderer.invoke('ai-pipeline:request-extract', unicode);
    },
    // ── Collab (一旦キープ) ──
    getCollabUsers: function () { return electron_1.ipcRenderer.invoke('collab:get-users'); },
});
