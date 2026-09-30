"use strict";
var __extends = (this && this.__extends) || (function () {
    var extendStatics = function (d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (Object.prototype.hasOwnProperty.call(b, p)) d[p] = b[p]; };
        return extendStatics(d, b);
    };
    return function (d, b) {
        if (typeof b !== "function" && b !== null)
            throw new TypeError("Class extends value " + String(b) + " is not a constructor or null");
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
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
Object.defineProperty(exports, "__esModule", { value: true });
exports.HttpClientError = void 0;
exports.initHttpClient = initHttpClient;
exports.postJson = postJson;
exports.getBlob = getBlob;
var HttpClientError = /** @class */ (function (_super) {
    __extends(HttpClientError, _super);
    function HttpClientError(message, options) {
        var _a, _b;
        var _this = _super.call(this, message) || this;
        _this.name = 'HttpClientError';
        _this.status = options === null || options === void 0 ? void 0 : options.status;
        _this.detail = options === null || options === void 0 ? void 0 : options.detail;
        _this.isTimeout = (_a = options === null || options === void 0 ? void 0 : options.isTimeout) !== null && _a !== void 0 ? _a : false;
        _this.isNetworkError = (_b = options === null || options === void 0 ? void 0 : options.isNetworkError) !== null && _b !== void 0 ? _b : false;
        return _this;
    }
    return HttpClientError;
}(Error));
exports.HttpClientError = HttpClientError;
var DEFAULT_HTTP_CONFIG = {
    baseUrl: 'http://127.0.0.1:8000',
    timeoutMs: 30000,
    retries: 2,
};
var httpConfig = __assign({}, DEFAULT_HTTP_CONFIG);
function initHttpClient(init) {
    var _a, _b, _c;
    httpConfig = {
        baseUrl: ((_a = init === null || init === void 0 ? void 0 : init.baseUrl) !== null && _a !== void 0 ? _a : DEFAULT_HTTP_CONFIG.baseUrl).replace(/\/+$/, ''),
        timeoutMs: (_b = init === null || init === void 0 ? void 0 : init.timeoutMs) !== null && _b !== void 0 ? _b : DEFAULT_HTTP_CONFIG.timeoutMs,
        retries: (_c = init === null || init === void 0 ? void 0 : init.retries) !== null && _c !== void 0 ? _c : DEFAULT_HTTP_CONFIG.retries,
    };
}
function sleep(ms) {
    return new Promise(function (resolve) { return setTimeout(resolve, ms); });
}
function shouldRetry(error, attempt) {
    if (attempt >= httpConfig.retries) {
        return false;
    }
    if (error instanceof HttpClientError) {
        if (error.isTimeout || error.isNetworkError) {
            return true;
        }
        if (typeof error.status === 'number') {
            return error.status === 429 || error.status >= 500;
        }
    }
    return false;
}
function buildUrl(path) {
    if (/^https?:\/\//.test(path)) {
        return path;
    }
    return "".concat(httpConfig.baseUrl).concat(path.startsWith('/') ? path : "/".concat(path));
}
function toHttpClientError(response) {
    return __awaiter(this, void 0, void 0, function () {
        var detail, _a, message;
        var _b;
        return __generator(this, function (_c) {
            switch (_c.label) {
                case 0:
                    _c.trys.push([0, 2, , 4]);
                    return [4 /*yield*/, response.json()];
                case 1:
                    detail = _c.sent();
                    return [3 /*break*/, 4];
                case 2:
                    _a = _c.sent();
                    return [4 /*yield*/, response.text().catch(function () { return ''; })];
                case 3:
                    detail = _c.sent();
                    return [3 /*break*/, 4];
                case 4:
                    message = typeof detail === 'object' && detail !== null && 'detail' in detail
                        ? String((_b = detail.detail) !== null && _b !== void 0 ? _b : response.statusText)
                        : String(detail || response.statusText || 'Unknown backend error');
                    return [2 /*return*/, new HttpClientError("HTTP ".concat(response.status, ": ").concat(message), {
                            status: response.status,
                            detail: detail,
                        })];
            }
        });
    });
}
function request(path, init) {
    return __awaiter(this, void 0, void 0, function () {
        var url, _loop_1, attempt, state_1;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    url = buildUrl(path);
                    _loop_1 = function (attempt) {
                        var controller, timeoutId, response, error_1, normalizedError;
                        return __generator(this, function (_b) {
                            switch (_b.label) {
                                case 0:
                                    controller = new AbortController();
                                    timeoutId = setTimeout(function () { return controller.abort(); }, httpConfig.timeoutMs);
                                    _b.label = 1;
                                case 1:
                                    _b.trys.push([1, 5, 8, 9]);
                                    return [4 /*yield*/, fetch(url, __assign(__assign({}, init), { signal: controller.signal, headers: __assign({ Accept: 'application/json' }, init.headers) }))];
                                case 2:
                                    response = _b.sent();
                                    if (!!response.ok) return [3 /*break*/, 4];
                                    return [4 /*yield*/, toHttpClientError(response)];
                                case 3: throw _b.sent();
                                case 4: return [2 /*return*/, { value: response }];
                                case 5:
                                    error_1 = _b.sent();
                                    normalizedError = error_1 instanceof HttpClientError
                                        ? error_1
                                        : error_1 instanceof Error && error_1.name === 'AbortError'
                                            ? new HttpClientError("Request timeout after ".concat(httpConfig.timeoutMs, "ms: ").concat(url), {
                                                isTimeout: true,
                                            })
                                            : new HttpClientError("Network request failed: ".concat(error_1 instanceof Error ? error_1.message : String(error_1)), { isNetworkError: true });
                                    if (!shouldRetry(normalizedError, attempt)) return [3 /*break*/, 7];
                                    return [4 /*yield*/, sleep(250 * (attempt + 1))];
                                case 6:
                                    _b.sent();
                                    return [2 /*return*/, "continue"];
                                case 7: throw normalizedError;
                                case 8:
                                    clearTimeout(timeoutId);
                                    return [7 /*endfinally*/];
                                case 9: return [2 /*return*/];
                            }
                        });
                    };
                    attempt = 0;
                    _a.label = 1;
                case 1: return [5 /*yield**/, _loop_1(attempt)];
                case 2:
                    state_1 = _a.sent();
                    if (typeof state_1 === "object")
                        return [2 /*return*/, state_1.value];
                    _a.label = 3;
                case 3:
                    attempt += 1;
                    return [3 /*break*/, 1];
                case 4: return [2 /*return*/];
            }
        });
    });
}
function postJson(path, body) {
    return __awaiter(this, void 0, void 0, function () {
        var response;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0: return [4 /*yield*/, request(path, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(body),
                    })];
                case 1:
                    response = _a.sent();
                    return [4 /*yield*/, response.json()];
                case 2: return [2 /*return*/, (_a.sent())];
            }
        });
    });
}
function getBlob(path) {
    return __awaiter(this, void 0, void 0, function () {
        var response;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0: return [4 /*yield*/, request(path, {
                        method: 'GET',
                        headers: {
                            Accept: 'image/png',
                        },
                    })];
                case 1:
                    response = _a.sent();
                    return [2 /*return*/, response.blob()];
            }
        });
    });
}
