"""
project_schema.py
─────────────────
プロジェクト管理用の Pydantic モデル定義。

主要なモデル:
  - ProjectCreateRequest : プロジェクト作成
  - ProjectUpdateRequest : プロジェクト更新
  - ProjectResponse : プロジェクト詳細情報
  - ProjectListResponse : プロジェクト一覧
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class ProjectStatus(str, Enum):
    """プロジェクトステータス"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ProjectCreateRequest(BaseModel):
    """プロジェクト作成リクエスト"""
    name: str = Field(..., min_length=1, max_length=255, description="プロジェクト名")
    description: Optional[str] = Field(default="", max_length=1000, description="プロジェクト説明")
    tags: List[str] = Field(default_factory=list, description="タグ")

    class Config:
        example = {
            "name": "My Amazing Font Project",
            "description": "A custom font for branding",
            "tags": ["branding", "custom"],
        }


class ProjectUpdateRequest(BaseModel):
    """プロジェクト更新リクエスト"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255, description="プロジェクト名")
    description: Optional[str] = Field(default=None, max_length=1000, description="プロジェクト説明")
    tags: Optional[List[str]] = Field(default=None, description="タグ")
    status: Optional[ProjectStatus] = Field(default=None, description="ステータス")


class ProjectSettingsResponse(BaseModel):
    """プロジェクト設定"""
    auto_save_enabled: bool = Field(default=True, description="自動保存を有効にするか")
    auto_save_interval_seconds: int = Field(default=30, description="自動保存間隔（秒）")
    export_default_format: str = Field(default="ttf", description="デフォルトエクスポート形式")


class ProjectStatistics(BaseModel):
    """プロジェクト統計情報"""
    font_count: int = Field(default=0, description="フォント数")
    total_glyphs: int = Field(default=0, description="総グリフ数")
    export_count: int = Field(default=0, description="エクスポート数")
    total_size_bytes: int = Field(default=0, description="プロジェクト合計サイズ（バイト）")
    ai_requests_count: int = Field(default=0, description="AI リクエスト数")


class ProjectResponse(BaseModel):
    """プロジェクト詳細情報（レスポンス）"""
    id: str = Field(..., description="プロジェクトID（UUID）")
    name: str = Field(..., description="プロジェクト名")
    description: str = Field(..., description="プロジェクト説明")
    tags: List[str] = Field(..., description="タグ")
    status: ProjectStatus = Field(..., description="ステータス")
    settings: ProjectSettingsResponse = Field(..., description="設定")
    statistics: ProjectStatistics = Field(..., description="統計情報")
    owner_id: str = Field(..., description="所有者ID")
    created_at: str = Field(..., description="作成日時（ISO 8601）")
    updated_at: str = Field(..., description="更新日時（ISO 8601）")
    last_modified_by: str = Field(..., description="最後に変更したユーザーID")


class ProjectListResponse(BaseModel):
    """プロジェクト一覧"""
    total: int = Field(..., description="合計件数", ge=0)
    page: int = Field(..., description="ページ番号", ge=1)
    per_page: int = Field(..., description="1ページあたりの件数", ge=1, le=100)
    items: List[ProjectResponse] = Field(..., description="プロジェクトのリスト")


class ProjectDetailResponse(BaseModel):
    """プロジェクト詳細（フル情報）"""
    id: str
    name: str
    description: str
    tags: List[str]
    status: ProjectStatus
    settings: ProjectSettingsResponse
    statistics: ProjectStatistics
    owner_id: str
    created_at: str
    updated_at: str
    last_modified_by: str
    custom_metadata: Dict[str, Any] = Field(default_factory=dict, description="カスタムメタデータ")
