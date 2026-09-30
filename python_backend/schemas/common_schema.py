"""
common_schema.py
────────────────
FastAPI全体で共通して使用する Pydantic モデル定義。

主要なモデル:
  - ErrorResponse / ValidationErrorResponse : エラーレスポンス
  - PaginationRequest / PaginationMeta : ページング
  - StatusResponse / HealthCheckResponse : ステータス
  - SearchFilter / SearchRequest : 検索・フィルタリング
  - AsyncOperationRequest / AsyncOperationStatus : 非同期操作
  - AuditLogEntry : 監査ログ
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Generic, TypeVar
from datetime import datetime
from enum import Enum


# ─────────────────────────────────────────────────────────────────
# 1. エラーレスポンス
# ─────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """標準的なエラーレスポンス"""
    error_code: str = Field(..., description="エラーコード（e.g., 'NOT_FOUND', 'INVALID_REQUEST'）")
    message: str = Field(..., description="エラーメッセージ")
    details: Optional[Dict[str, Any]] = Field(default=None, description="詳細情報")
    request_id: Optional[str] = Field(default=None, description="リクエストID（トレーシング用）")
    timestamp: str = Field(..., description="エラー発生時刻（ISO 8601）")

    class Config:
        example = {
            "error_code": "NOT_FOUND",
            "message": "The requested resource does not exist",
            "details": {"resource_type": "font", "resource_id": "font-abc123"},
            "request_id": "req-xyz789",
            "timestamp": "2026-05-14T12:34:56Z",
        }


class ValidationErrorDetail(BaseModel):
    """バリデーションエラーの詳細"""
    field: str = Field(..., description="フィールド名")
    message: str = Field(..., description="エラーメッセージ")
    type: str = Field(..., description="エラータイプ（value_error, type_error など）")


class ValidationErrorResponse(BaseModel):
    """バリデーションエラーレスポンス"""
    error_code: str = Field(default="VALIDATION_ERROR", description="エラーコード")
    message: str = Field(..., description="エラー概要")
    errors: List[ValidationErrorDetail] = Field(..., description="エラー詳細リスト")
    request_id: Optional[str] = Field(default=None, description="リクエストID")
    timestamp: str = Field(..., description="エラー発生時刻")


# ─────────────────────────────────────────────────────────────────
# 2. ページング
# ─────────────────────────────────────────────────────────────────

class PaginationRequest(BaseModel):
    """ページングリクエスト（任意で使用可能）"""
    page: int = Field(default=1, description="ページ番号", ge=1)
    per_page: int = Field(default=20, description="1ページあたりの件数", ge=1, le=100)
    sort_by: Optional[str] = Field(default=None, description="ソートキー")
    sort_order: str = Field(default="asc", description="ソート順序（asc | desc）")


class PaginationMeta(BaseModel):
    """ページングメタデータ"""
    page: int = Field(..., description="現在のページ")
    per_page: int = Field(..., description="1ページあたりの件数")
    total_items: int = Field(..., description="合計アイテム数", ge=0)
    total_pages: int = Field(..., description="合計ページ数", ge=0)
    has_next: bool = Field(..., description="次ページがあるか")
    has_prev: bool = Field(..., description="前ページがあるか")


T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """ジェネリック ページング付きレスポンス"""
    data: List[T] = Field(..., description="アイテムリスト")
    pagination: PaginationMeta = Field(..., description="ページングメタデータ")


# ─────────────────────────────────────────────────────────────────
# 3. ステータス・ヘルスチェック
# ─────────────────────────────────────────────────────────────────

class ServiceStatus(str, Enum):
    """サービスステータス"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class StatusResponse(BaseModel):
    """API ステータスレスポンス"""
    status: ServiceStatus = Field(..., description="ステータス")
    version: str = Field(..., description="APIバージョン")
    timestamp: str = Field(..., description="確認時刻")


class DatabaseHealthResponse(BaseModel):
    """データベースヘルスチェック"""
    status: ServiceStatus = Field(..., description="ステータス")
    response_time_ms: float = Field(..., description="レスポンスタイム（ms）")
    error: Optional[str] = Field(default=None, description="エラーメッセージ")


class PythonBackendHealthResponse(BaseModel):
    """Python バックエンドヘルスチェック"""
    status: ServiceStatus = Field(..., description="ステータス")
    uptime_seconds: float = Field(..., description="稼働時間（秒）")
    memory_usage_mb: float = Field(..., description="メモリ使用量（MB）")
    cpu_usage_percent: float = Field(..., description="CPU使用率（%）")


class HealthCheckResponse(BaseModel):
    """全体ヘルスチェック"""
    status: ServiceStatus = Field(..., description="全体ステータス")
    api: StatusResponse = Field(..., description="API ステータス")
    database: DatabaseHealthResponse = Field(..., description="DB ステータス")
    backend: PythonBackendHealthResponse = Field(..., description="バックエンド ステータス")
    timestamp: str = Field(..., description="確認時刻")


# ─────────────────────────────────────────────────────────────────
# 4. 検索・フィルタリング
# ─────────────────────────────────────────────────────────────────

class FilterOperator(str, Enum):
    """フィルタ演算子"""
    EQ = "eq"  # 等しい
    NE = "ne"  # 等しくない
    GT = "gt"  # より大きい
    GTE = "gte"  # 以上
    LT = "lt"  # より小さい
    LTE = "lte"  # 以下
    IN = "in"  # 含まれている
    NIN = "nin"  # 含まれていない
    CONTAINS = "contains"  # 含む
    STARTSWITH = "startswith"  # で始まる
    ENDSWITH = "endswith"  # で終わる


class SearchFilter(BaseModel):
    """検索フィルタ"""
    field: str = Field(..., description="フィルタ対象フィールド")
    operator: FilterOperator = Field(..., description="フィルタ演算子")
    value: Any = Field(..., description="フィルタ値")


class SearchRequest(BaseModel):
    """検索リクエスト"""
    query: Optional[str] = Field(default=None, description="テキスト検索クエリ")
    filters: List[SearchFilter] = Field(default_factory=list, description="フィルタ条件")
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = Field(default=None)
    sort_order: str = Field(default="asc")


# ─────────────────────────────────────────────────────────────────
# 5. バッチ操作
# ─────────────────────────────────────────────────────────────────

class BatchRequest(BaseModel):
    """バッチ操作リクエスト"""
    operations: List[Dict[str, Any]] = Field(..., description="操作リスト")
    continue_on_error: bool = Field(default=False, description="エラー時に続行するか")


class BatchOperationResult(BaseModel):
    """バッチ操作の結果（1操作分）"""
    operation_index: int = Field(..., description="操作のインデックス")
    success: bool = Field(..., description="成功したか")
    result: Optional[Dict[str, Any]] = Field(default=None, description="結果")
    error: Optional[str] = Field(default=None, description="エラーメッセージ")


class BatchResponse(BaseModel):
    """バッチ操作レスポンス"""
    batch_id: str = Field(..., description="バッチID")
    total_operations: int = Field(..., description="合計操作数")
    successful: int = Field(..., description="成功した操作数")
    failed: int = Field(..., description="失敗した操作数")
    results: List[BatchOperationResult] = Field(..., description="各操作の結果")


# ─────────────────────────────────────────────────────────────────
# 6. 非同期操作追跡
# ─────────────────────────────────────────────────────────────────

class AsyncOperationStatus(str, Enum):
    """非同期操作ステータス"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AsyncOperationRequest(BaseModel):
    """非同期操作リクエスト"""
    operation_id: str = Field(..., description="操作ID")
    operation_type: str = Field(..., description="操作タイプ")
    payload: Dict[str, Any] = Field(..., description="操作ペイロード")


class AsyncOperationResponse(BaseModel):
    """非同期操作追跡レスポンス"""
    operation_id: str = Field(..., description="操作ID")
    status: AsyncOperationStatus = Field(..., description="ステータス")
    progress_percent: int = Field(default=0, ge=0, le=100)
    current_step: Optional[str] = Field(default=None, description="現在のステップ")
    error_message: Optional[str] = Field(default=None, description="エラーメッセージ")
    estimated_time_remaining_seconds: Optional[int] = Field(default=None)
    result: Optional[Dict[str, Any]] = Field(default=None, description="完了時の結果")
    created_at: str = Field(..., description="作成日時")
    updated_at: str = Field(..., description="更新日時")


# ─────────────────────────────────────────────────────────────────
# 7. 監査ログ
# ─────────────────────────────────────────────────────────────────

class AuditAction(str, Enum):
    """監査アクション"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    IMPORT = "import"
    LOGIN = "login"
    LOGOUT = "logout"


class AuditLogEntry(BaseModel):
    """監査ログエントリ"""
    id: str = Field(..., description="ログID")
    user_id: str = Field(..., description="ユーザーID")
    action: AuditAction = Field(..., description="アクション")
    resource_type: str = Field(..., description="リソースタイプ（font | project など）")
    resource_id: str = Field(..., description="リソースID")
    details: Dict[str, Any] = Field(default_factory=dict, description="詳細情報")
    ip_address: Optional[str] = Field(default=None, description="IPアドレス")
    user_agent: Optional[str] = Field(default=None, description="ユーザーエージェント")
    status: str = Field(..., description="ステータス（success | failure）")
    error_message: Optional[str] = Field(default=None, description="エラーメッセージ")
    timestamp: str = Field(..., description="タイムスタンプ（ISO 8601）")


class AuditLogResponse(BaseModel):
    """監査ログ一覧レスポンス"""
    total: int = Field(..., description="合計ログ数")
    entries: List[AuditLogEntry] = Field(..., description="ログエントリ")


# ─────────────────────────────────────────────────────────────────
# 8. ウェブフック
# ─────────────────────────────────────────────────────────────────

class WebhookEventType(str, Enum):
    """ウェブフック イベントタイプ"""
    FONT_CREATED = "font.created"
    FONT_UPDATED = "font.updated"
    FONT_DELETED = "font.deleted"
    EXPORT_COMPLETED = "export.completed"
    PROJECT_SHARED = "project.shared"


class WebhookEvent(BaseModel):
    """ウェブフック イベント"""
    event_id: str = Field(..., description="イベントID")
    event_type: WebhookEventType = Field(..., description="イベントタイプ")
    resource_type: str = Field(..., description="リソースタイプ")
    resource_id: str = Field(..., description="リソースID")
    data: Dict[str, Any] = Field(..., description="イベントデータ")
    timestamp: str = Field(..., description="タイムスタンプ")


class SubscriptionResponse(BaseModel):
    """ウェブフック サブスクリプション"""
    id: str = Field(..., description="サブスクリプションID")
    url: str = Field(..., description="ウェブフック URL")
    events: List[WebhookEventType] = Field(..., description="リッスンするイベント")
    active: bool = Field(default=True, description="有効か")
    created_at: str = Field(..., description="作成日時")
