"""
export_schema.py
────────────────
エクスポートと成果物パッケージング用の Pydantic モデル定義。

主要なモデル:
  - ExportFormat / ExportPackageFormat : エクスポート形式
  - FontExportOptions / HTMLExportOptions : フォーマット別オプション
  - ExportRequest / ProjectExportRequest : エクスポートリクエスト
  - ExportResponse / ExportStatusResponse : エクスポート結果
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class ExportFormat(str, Enum):
    """フォントエクスポート形式"""
    TTF = "ttf"
    WOFF = "woff"
    WOFF2 = "woff2"
    OTF = "otf"

class ExportPackageFormat(str, Enum):
    """プロジェクト/サイトエクスポート形式"""
    ZIP = "zip"
    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    PYTHON = "py"

class BlenderExportOptions(BaseModel):
    """Blender連携用エクスポートオプション"""
    export_as_curves: bool = Field(default=True, description="ベジェ曲線データとして出力する")
    scale_factor: float = Field(default=0.01, description="Blender用のスケール調整")
    generate_runnable_script: bool = Field(default=True, description="Blenderで即実行可能なbpyスクリプトを含める")
    
class FontExportOptions(BaseModel):
    """フォントエクスポートオプション"""
    format: ExportFormat = Field(..., description="エクスポート形式")
    include_variations: bool = Field(default=False, description="Variable Font情報を含める")
    include_metadata: bool = Field(default=True, description="メタデータを含める")
    compress: bool = Field(default=True, description="圧縮するか")

    class Config:
        example = {
            "format": "woff2",
            "include_variations": False,
            "include_metadata": True,
            "compress": True,
        }


class HTMLExportOptions(BaseModel):
    """HTML/Webサイトエクスポートオプション"""
    include_fonts: bool = Field(default=True, description="フォントをインライン化するか")
    include_css: bool = Field(default=True, description="CSSを含める")
    include_js: bool = Field(default=False, description="JavaScriptを含める")
    minify: bool = Field(default=True, description="コードを最小化するか")
    responsive: bool = Field(default=True, description="レスポンシブ対応")


class ZipExportOptions(BaseModel):
    """ZIP/パッケージエクスポートオプション"""
    include_source: bool = Field(default=False, description="ソースファイルを含める")
    include_preview: bool = Field(default=True, description="プレビューHTMLを含める")
    include_readme: bool = Field(default=True, description="README.mdを含める")
    folder_structure: str = Field(default="flat", description="フォルダ構成（flat | nested）")


class ExportRequest(BaseModel):
    """フォントエクスポートリクエスト"""
    font_id: str = Field(..., description="対象フォントID")
    options: FontExportOptions = Field(..., description="エクスポートオプション")
    filename: Optional[str] = Field(default=None, description="出力ファイル名")

    class Config:
        example = {
            "font_id": "font-abc123",
            "options": {
                "format": "woff2",
                "include_variations": False,
            },
            "filename": "my-font.woff2",
        }


class ProjectExportRequest(BaseModel):
    """プロジェクト全体エクスポートリクエスト"""
    project_id: str = Field(..., description="対象プロジェクトID")
    package_format: ExportPackageFormat = Field(..., description="パッケージ形式")
    include_fonts: bool = Field(default=True, description="フォントを含める")
    include_html: bool = Field(default=False, description="HTMLを含める")
    include_metadata: bool = Field(default=True, description="メタデータを含める")
    zip_options: Optional[ZipExportOptions] = Field(default=None, description="ZIPオプション")


class ExportResponse(BaseModel):
    """エクスポート結果"""
    export_id: str = Field(..., description="エクスポートID（UUID）")
    source_id: str = Field(..., description="ソースID（フォントIDまたはプロジェクトID）")
    source_type: str = Field(..., description="ソースタイプ（font | project）")
    format: str = Field(..., description="出力形式")
    file_path: str = Field(..., description="出力ファイルパス")
    download_url: str = Field(..., description="ダウンロードURL")
    file_size: int = Field(..., description="ファイルサイズ（バイト）", ge=0)
    created_at: str = Field(..., description="作成日時（ISO 8601）")
    expires_at: Optional[str] = Field(default=None, description="有効期限（ISO 8601）")

    class Config:
        example = {
            "export_id": "exp-xyz789",
            "source_id": "font-abc123",
            "source_type": "font",
            "format": "woff2",
            "file_path": "/exports/exp-xyz789/my-font.woff2",
            "download_url": "http://localhost:8000/api/exports/exp-xyz789/download",
            "file_size": 45000,
            "created_at": "2026-05-14T12:34:56Z",
            "expires_at": "2026-05-21T12:34:56Z",
        }


class BulkExportResponse(BaseModel):
    """複数エクスポート結果"""
    bulk_export_id: str = Field(..., description="バルクエクスポートID")
    total_exports: int = Field(..., description="エクスポート数")
    successful: int = Field(..., description="成功数")
    failed: int = Field(..., description="失敗数")
    exports: List[ExportResponse] = Field(..., description="エクスポート結果リスト")
    created_at: str = Field(..., description="作成日時")


class ExportStatusResponse(BaseModel):
    """エクスポート進捗状態"""
    export_id: str = Field(..., description="エクスポートID")
    status: str = Field(..., description="ステータス（pending | processing | completed | failed）")
    progress_percent: int = Field(default=0, description="進捗率（0-100）", ge=0, le=100)
    current_step: Optional[str] = Field(default=None, description="現在のステップ")
    error_message: Optional[str] = Field(default=None, description="エラーメッセージ")
    estimated_time_remaining_seconds: Optional[int] = Field(
        default=None,
        description="残り時間（秒）"
    )
    result: Optional[ExportResponse] = Field(default=None, description="完了時の結果")


class ExportHistoryEntry(BaseModel):
    """エクスポート履歴エントリ"""
    export_id: str = Field(..., description="エクスポートID")
    source_id: str = Field(..., description="ソースID")
    source_type: str = Field(..., description="ソースタイプ")
    format: str = Field(..., description="出力形式")
    status: str = Field(..., description="ステータス（success | failed）")
    file_size: int = Field(default=0, description="ファイルサイズ", ge=0)
    created_at: str = Field(..., description="作成日時")
    created_by: str = Field(..., description="作成ユーザーID")


class ExportHistoryResponse(BaseModel):
    """エクスポート履歴一覧"""
    total: int = Field(..., description="合計件数", ge=0)
    items: List[ExportHistoryEntry] = Field(..., description="履歴エントリ")


class ExportStatistics(BaseModel):
    """エクスポート使用統計"""
    total_exports: int = Field(default=0, description="総エクスポート数")
    successful_exports: int = Field(default=0, description="成功したエクスポート")
    failed_exports: int = Field(default=0, description="失敗したエクスポート")
    total_exported_data_bytes: int = Field(default=0, description="エクスポートデータ総容量")
    most_used_format: Optional[str] = Field(default=None, description="最も使用されたフォーマット")
    average_export_time_seconds: float = Field(default=0.0, description="平均エクスポート時間")
