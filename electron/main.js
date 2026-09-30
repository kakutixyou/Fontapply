"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
var electron_1 = require("electron");
var path_1 = __importDefault(require("path"));
// 🚨 修正箇所1: electron-is-dev のインポートを削除
var font_ipc_1 = require("./ipc/font.ipc");
var utils_1 = require("./ipc/utils");
var mainWindow = null;
function createWindow() {
    mainWindow = new electron_1.BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1024,
        minHeight: 768,
        webPreferences: {
            preload: path_1.default.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
            // enableRemoteModule: false, <- 🚨 最新のElectronでは非推奨・不要なのでコメントアウト推奨
            sandbox: true,
        },
    });
    // 🚨 修正箇所2: app.isPackaged を使って開発環境かどうかを判定する
    // アプリがパッケージ化されていなければ（!）開発環境（isDev）という判定です
    var isDev = !electron_1.app.isPackaged;
    var startUrl = isDev
        ? 'http://localhost:5173'
        : "file://".concat(path_1.default.join(__dirname, '../dist/renderer/index.html'));
    mainWindow.loadURL(startUrl);
    if (isDev) {
        mainWindow.webContents.openDevTools();
    }
    mainWindow.on('closed', function () {
        mainWindow = null;
    });
}
electron_1.app.on('ready', function () {
    var backendUrl = process.env.FONT_API_BASE_URL || process.env.WEBFORGE_FONT_API_BASE_URL || 'http://localhost:8000';
    try {
        (0, utils_1.initHttpClient)({ baseUrl: backendUrl, timeoutMs: 30000, retries: 2 });
        (0, font_ipc_1.registerFontIpcHandlers)();
        console.info('[main] Font IPC initialized', { backendUrl: backendUrl });
    }
    catch (error) {
        console.error('[main] Failed to initialize Font IPC', error);
        electron_1.app.quit();
        return;
    }
    createWindow();
});
electron_1.app.on('window-all-closed', function () {
    if (process.platform !== 'darwin') {
        electron_1.app.quit();
    }
});
electron_1.app.on('activate', function () {
    if (mainWindow === null) {
        createWindow();
    }
});
// IPC Handlers
electron_1.ipcMain.handle('project:create', function (_event, projectData) { return __awaiter(void 0, void 0, void 0, function () {
    return __generator(this, function (_a) {
        // TODO: Implement project creation
        return [2 /*return*/, { success: true, projectId: 'new-project-id' }];
    });
}); });
electron_1.ipcMain.handle('python:status', function () { return __awaiter(void 0, void 0, void 0, function () {
    return __generator(this, function (_a) {
        // TODO: Check Python backend status
        return [2 /*return*/, { connected: true, version: '1.0.0' }];
    });
}); });
