"""
font_schema.py
──────────────
FastAPI リクエスト/レスポンス用の Pydantic モデル定義。
FontAssembler や GlyphBuilder との連携を想定した設計。

主要なモデル:
  - FontMetricsInput / FontMetricsResponse : フォント全体のメトリクス
  - GlyphDataInput / GlyphDataResponse : 個別グリフデータ
  - FontMetadataInput / FontMetadataResponse : フォント名・バージョン等
  - FontGenerateRequest : フォント生成リクエスト
  - FontResponse : フォント情報レスポンス
  - FontSubsetRequest / FontConvertRequest : Phase 2+ オペレーション
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ─────────────────────────────────────────────────────────────────
# 1. メトリクス関連
# ─────────────────────────────────────────────────────────────────

class FontMetricsInput(BaseModel):
    """フォント生成時のメトリクス入力（font_assembler.py の FontMetrics に対応）"""
    upm: int = Field(default=1000, description="Units Per Em", ge=512, le=4096)
    ascender: int = Field(default=800, description="上端の高さ")
    descender: int = Field(default=-200, description="下端の深さ（負の値）")
    cap_height: int = Field(default=700, description="大文字の高さ")
    x_height: int = Field(default=500, description="小文字xの高さ")
    line_gap: int = Field(default=0, description="行間")
    italic_angle: float = Field(default=0.0, description="イタリック角度（度）")

    class Config:
        example = {
            "upm": 1000,
            "ascender": 800,
            "descender": -200,
            "cap_height": 700,
            "x_height": 500,
            "line_gap": 0,
            "italic_angle": 0.0,
        }


class FontMetricsResponse(BaseModel):
    """メトリクス情報（レスポンス）"""
    upm: int
    ascender: int
    descender: int
    cap_height: int
    x_height: int
    line_gap: int
    italic_angle: float


# ─────────────────────────────────────────────────────────────────
# 2. グリフ関連
# ─────────────────────────────────────────────────────────────────

class ContourPointInput(BaseModel):
    """輪郭上の1点（curve_engine.py の Point に対応）"""
    x: float = Field(..., description="X座標")
    y: float = Field(..., description="Y座標")
    on_curve: bool = Field(default=True, description="オンカーブ点か（True=on, False=off）")


class ContourInput(BaseModel):
    """1つの輪郭（閉じた曲線）"""
    points: List[ContourPointInput] = Field(..., min_items=3, description="最低3点必要")

    class Config:
        example = {
            "points": [
                {"x": 0, "y": 0, "on_curve": True},
                {"x": 100, "y": 0, "on_curve": True},
                {"x": 100, "y": 100, "on_curve": True},
                {"x": 0, "y": 100, "on_curve": True},
            ]
        }


class GlyphMetricsInput(BaseModel):
    """グリフのメトリクス（GlyphData.metrics に対応）"""
    advance_width: int = Field(..., description="グリフ前進幅", ge=0)
    left_side_bearing: int = Field(default=0, description="左サイドベアリング")


class GlyphDataInput(BaseModel):
    """グリフデータ（リクエスト）- GlyphData に対応"""
    name: str = Field(..., min_length=1, description="グリフ名（e.g., 'A', 'a', 'space'）")
    unicode: Optional[int] = Field(default=None, description="Unicode コードポイント", ge=0, le=0x10FFFF)
    contours: List[ContourInput] = Field(default_factory=list, description="輪郭リスト")
    metrics: GlyphMetricsInput

    class Config:
        example = {
            "name": "A",
            "unicode": 65,
            "contours": [
                {
                    "points": [
                        {"x": 0, "y": 0, "on_curve": True},
                        {"x": 100, "y": 0, "on_curve": True},
                        {"x": 100, "y": 100, "on_curve": True},
                        {"x": 0, "y": 100, "on_curve": True},
                    ]
                }
            ],
            "metrics": {
                "advance_width": 100,
                "left_side_bearing": 0,
            },
        }


class GlyphDataResponse(BaseModel):
    """グリフ情報（レスポンス）"""
    id: str = Field(..., description="グリフID")
    font_id: str = Field(..., description="親フォントID")
    name: str = Field(..., description="グリフ名")
    unicode: Optional[int] = Field(default=None, description="Unicode コードポイント")
    contour_count: int = Field(..., description="輪郭数")
    created_at: str = Field(..., description="作成日時（ISO 8601）")


# ─────────────────────────────────────────────────────────────────
# 3. メタデータ関連
# ─────────────────────────────────────────────────────────────────

class FontMetadataInput(BaseModel):
    """フォントメタデータ（リクエスト）- FontMetadata に対応"""
    family_name: str = Field(..., min_length=1, description="フォント族名（e.g., 'MyFont'）")
    style_name: str = Field(default="Regular", description="スタイル名（e.g., 'Regular', 'Bold', 'Italic'）")
    version: str = Field(default="1.0", description="バージョン文字列")
    copyright: str = Field(default="", description="著作権表記")
    designer: str = Field(default="", description="デザイナー名")
    description: str = Field(default="", description="フォント説明")
    url: str = Field(default="", description="フォント関連のURL")

    class Config:
        example = {
            "family_name": "WebForge",
            "style_name": "Regular",
            "version": "1.0",
            "copyright": "Copyright 2026",
            "designer": "Designer Name",
            "description": "A beautiful font",
            "url": "https://example.com",
        }


class FontMetadataResponse(BaseModel):
    """フォントメタデータ（レスポンス）"""
    family_name: str
    style_name: str
    version: str
    full_name: str = Field(..., description="full_name = family_name + style_name")
    postscript_name: str = Field(..., description="PostScript名（スペースなし）")
    copyright: str
    designer: str
    description: str
    url: str


# ─────────────────────────────────────────────────────────────────
# 4. フォント生成リクエスト
# ─────────────────────────────────────────────────────────────────

class FontGenerateRequest(BaseModel):
    """フォント生成リクエスト - FontAssembler.build_ttf() に対応"""
    project_id: str = Field(..., description="プロジェクトID")
    metadata: FontMetadataInput = Field(..., description="フォントメタデータ")
    metrics: FontMetricsInput = Field(..., description="フォントメトリクス")
    glyphs: List[GlyphDataInput] = Field(
        default_factory=list,
        description="グリフリスト（空でもOK）"
    )

    class Config:
        example = {
            "project_id": "proj-abc123",
            "metadata": {
                "family_name": "WebForge",
                "style_name": "Regular",
                "version": "1.0",
            },
            "metrics": {
                "upm": 1000,
                "ascender": 800,
                "descender": -200,
                "cap_height": 700,
                "x_height": 500,
            },
            "glyphs": [],
        }


# ─────────────────────────────────────────────────────────────────
# 5. フォント情報レスポンス
# ─────────────────────────────────────────────────────────────────

class FontResponse(BaseModel):
    """フォント情報（レスポンス）"""
    id: str = Field(..., description="フォントID（UUID）")
    project_id: str = Field(..., description="プロジェクトID")
    metadata: FontMetadataResponse = Field(..., description="メタデータ")
    metrics: FontMetricsResponse = Field(..., description="メトリクス")
    glyph_count: int = Field(..., description="含まれるグリフ数", ge=0)
    file_path: str = Field(..., description="ファイル保存パス")
    format: str = Field(default="ttf", description="フォーマット（ttf | woff2 | woff）")
    file_size: int = Field(..., description="ファイルサイズ（バイト）", ge=0)
    created_at: str = Field(..., description="作成日時（ISO 8601）")
    updated_at: str = Field(..., description="更新日時（ISO 8601）")


class FontListResponse(BaseModel):
    """フォント一覧"""
    total: int = Field(..., description="合計件数", ge=0)
    items: List[FontResponse] = Field(..., description="フォントのリスト")


# ─────────────────────────────────────────────────────────────────
# 6. フォント操作リクエスト（Phase 2+）
# ─────────────────────────────────────────────────────────────────

class FontSubsetRequest(BaseModel):
    """サブセット化リクエスト（Phase 2）"""
    font_id: str = Field(..., description="対象フォントID")
    unicode_ranges: List[str] = Field(
        default=["latin"],
        description="Unicode範囲（プリセット: 'latin', 'latin_extended', 'greek', 'cyrillic', 'cjk', 'hiragana', 'katakana'）"
    )
    custom_codepoints: Optional[List[int]] = Field(
        default=None,
        description="カスタムコードポイント（ここで指定したら unicode_ranges は無視される）"
    )
    output_format: str = Field(default="ttf", description="出力フォーマット（ttf | woff2）")

    class Config:
        example = {
            "font_id": "font-abc123",
            "unicode_ranges": ["latin", "greek"],
            "output_format": "woff2",
        }


class FontConvertRequest(BaseModel):
    """フォーマット変換リクエスト（Phase 2）"""
    font_id: str = Field(..., description="対象フォントID")
    output_format: str = Field(
        default="woff2",
        description="出力フォーマット（woff2 | woff | ttf）"
    )

    class Config:
        example = {
            "font_id": "font-abc123",
            "output_format": "woff2",
        }


class FontVariableAdjustRequest(BaseModel):
    """Variable Font軸調整リクエスト（Phase 1+）"""
    font_id: str = Field(..., description="対象フォントID")
    axis_name: str = Field(
        ...,
        description="軸名（'weight', 'width', 'slant', 'italic' など）"
    )
    axis_value: float = Field(
        ...,
        description="軸値（0.0 ～ 1.0、またはスケール値）",
        ge=0.0,
        le=1.0
    )

    class Config:
        example = {
            "font_id": "font-abc123",
            "axis_name": "weight",
            "axis_value": 0.5,
        }


# ─────────────────────────────────────────────────────────────────
# 7. フォント操作レスポンス
# ─────────────────────────────────────────────────────────────────

class FontSubsetResponse(BaseModel):
    """サブセット化結果"""
    subset_id: str = Field(..., description="サブセットID")
    parent_font_id: str = Field(..., description="元のフォントID")
    included_ranges: List[str] = Field(..., description="含まれるUnicode範囲")
    glyph_count: int = Field(..., description="サブセット後のグリフ数")
    file_path: str = Field(..., description="サブセット後のファイルパス")
    file_size: int = Field(..., description="ファイルサイズ")
    created_at: str = Field(..., description="作成日時")


class FontConvertResponse(BaseModel):
    """フォーマット変換結果"""
    converted_id: str = Field(..., description="変換後のフォントID")
    parent_font_id: str = Field(..., description="元のフォントID")
    output_format: str = Field(..., description="出力フォーマット")
    file_path: str = Field(..., description="変換後のファイルパス")
    file_size: int = Field(..., description="ファイルサイズ")
    created_at: str = Field(..., description="作成日時")


# ─────────────────────────────────────────────────────────────────
# 8. プレビュー関連
# ─────────────────────────────────────────────────────────────────

class FontPreviewRequest(BaseModel):
    """フォントプレビュー生成リクエスト"""
    font_id: str = Field(..., description="対象フォントID")
    preview_text: str = Field(
        default="AaBbCc123",
        description="プレビュー用テキスト"
    )
    font_size: int = Field(default=48, description="プレビューのフォントサイズ", ge=12, le=256)


class FontPreviewResponse(BaseModel):
    """フォントプレビュー（レスポンス）"""
    font_id: str = Field(..., description="フォントID")
    preview_image_base64: str = Field(..., description="プレビュー画像（Base64エンコード）")
    preview_text: str = Field(..., description="プレビューに使用したテキスト")
    font_size: int = Field(..., description="フォントサイズ")
    generated_at: str = Field(..., description="生成日時")


# ─────────────────────────────────────────────────────────────────
# 9. エクスポート関連
# ─────────────────────────────────────────────────────────────────

class FontExportRequest(BaseModel):
    """フォントエクスポートリクエスト"""
    font_id: str = Field(..., description="対象フォントID")
    format: str = Field(default="ttf", description="エクスポート形式（ttf | woff2 | woff）")
    include_variations: bool = Field(
        default=False,
        description="Variable Font情報を含めるか"
    )

    class Config:
        example = {
            "font_id": "font-abc123",
            "format": "woff2",
            "include_variations": False,
        }


class FontExportResponse(BaseModel):
    """エクスポート結果"""
    export_id: str = Field(..., description="エクスポートID")
    font_id: str = Field(..., description="対象フォントID")
    file_path: str = Field(..., description="エクスポートファイルパス")
    download_url: str = Field(..., description="ダウンロードURL")
    format: str = Field(..., description="エクスポート形式")
    file_size: int = Field(..., description="ファイルサイズ")
    created_at: str = Field(..., description="作成日時")


# ─────────────────────────────────────────────────────────────────
# 10. ストローク関連（Phase 2+ 拡張用）
# ─────────────────────────────────────────────────────────────────

class StrokeSettingsInput(BaseModel):
    """ストローク設定（stroke_engine.py に対応）"""
    width: float = Field(..., description="ストローク幅", ge=0.0)
    cap_style: str = Field(
        default="round",
        description="キャップスタイル（butt | round | square）"
    )
    join_style: str = Field(
        default="miter",
        description="ジョインスタイル（miter | round | bevel）"
    )
    miter_limit: float = Field(default=10.0, description="ミターリミット", ge=1.0)

    class Config:
        example = {
            "width": 50.0,
            "cap_style": "round",
            "join_style": "miter",
            "miter_limit": 10.0,
        }


class StrokeSettingsResponse(BaseModel):
    """ストローク設定（レスポンス）"""
    width: float
    cap_style: str
    join_style: str
    miter_limit: float


class FontWithStrokeRequest(BaseModel):
    """ストロークパラメータ付きフォント生成（Phase 2+）"""
    project_id: str = Field(..., description="プロジェクトID")
    metadata: FontMetadataInput = Field(..., description="メタデータ")
    metrics: FontMetricsInput = Field(..., description="メトリクス")
    stroke_settings: StrokeSettingsInput = Field(..., description="ストローク設定")
    glyphs: List[GlyphDataInput] = Field(..., description="グリフリスト")

    class Config:
        example = {
            "project_id": "proj-abc123",
            "metadata": {
                "family_name": "WebForge Stroke",
                "style_name": "Regular",
            },
            "metrics": {
                "upm": 1000,
                "ascender": 800,
                "descender": -200,
            },
            "stroke_settings": {
                "width": 50.0,
                "cap_style": "round",
                "join_style": "miter",
            },
            "glyphs": [],
        }


# ─────────────────────────────────────────────────────────────────
# 11. キャッシュ・履歴関連
# ─────────────────────────────────────────────────────────────────

class FontGenerationHistoryEntry(BaseModel):
    """フォント生成履歴"""
    generation_id: str = Field(..., description="生成ID（UUID）")
    project_id: str = Field(..., description="プロジェクトID")
    font_id: str = Field(..., description="生成されたフォントID")
    request_data: Dict[str, Any] = Field(..., description="リクエストデータ（JSON）")
    generated_at: str = Field(..., description="生成日時（ISO 8601）")
    status: str = Field(
        ...,
        description="ステータス（success | failed | pending）"
    )
    error_message: Optional[str] = Field(default=None, description="エラーメッセージ")


class FontGenerationHistoryListResponse(BaseModel):
    """生成履歴一覧"""
    total: int = Field(..., description="合計件数")
    items: List[FontGenerationHistoryEntry] = Field(..., description="履歴エントリ")


class FontCacheInfo(BaseModel):
    """キャッシュ情報"""
    font_id: str = Field(..., description="フォントID")
    cached_at: str = Field(..., description="キャッシュ日時（ISO 8601）")
    cache_size: int = Field(..., description="キャッシュサイズ（バイト）")
    ttl_seconds: int = Field(..., description="TTL（秒）")
    is_valid: bool = Field(..., description="キャッシュは有効か")


# ─────────────────────────────────────────────────────────────────
# 12. エラーレスポンス
# ─────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """エラーレスポンス"""
    error_code: str = Field(..., description="エラーコード（e.g., 'INVALID_FONT_ID'）")
    message: str = Field(..., description="エラーメッセージ")
    details: Optional[Dict[str, Any]] = Field(default=None, description="詳細情報")
    timestamp: str = Field(..., description="エラー発生時刻（ISO 8601）")

    class Config:
        example = {
            "error_code": "FONT_NOT_FOUND",
            "message": "The specified font does not exist",
            "details": {"font_id": "font-abc123"},
            "timestamp": "2026-05-14T12:34:56Z",
        }


class ValidationErrorResponse(BaseModel):
    """バリデーションエラーレスポンス"""
    error_code: str = Field(default="VALIDATION_ERROR", description="エラーコード")
    message: str = Field(..., description="バリデーションエラーの概要")
    fields: Dict[str, List[str]] = Field(..., description="フィールド別エラーリスト")
    timestamp: str = Field(..., description="エラー発生時刻（ISO 8601）")


# ─────────────────────────────────────────────────────────────────
# routes_font_generator.py 互換モデル
# ─────────────────────────────────────────────────────────────────

class FontOutputFormat(str, Enum):
    ttf = "ttf"
    woff2 = "woff2"


class PreviewType(str, Enum):
    sample = "sample"
    grid = "grid"
    sizes = "sizes"
    weights = "weights"


class StrokeStyle(str, Enum):
    butt = "butt"
    round = "round"
    square = "square"
    miter = "miter"
    bevel = "bevel"


class GenerateMetadata(BaseModel):
    family_name: str = Field(..., min_length=1)
    style_name: str = Field(default="Regular", min_length=1)
    version: str = Field(default="Version 1.000")
    copyright: str = Field(default="")
    designer: str = Field(default="")
    description: str = Field(default="")
    url: str = Field(default="")


class GenerateMetrics(BaseModel):
    upm: int = Field(default=1000, ge=256, le=4096)
    ascender: int = Field(default=800)
    descender: int = Field(default=-200, le=0)
    cap_height: int = Field(default=700)
    x_height: int = Field(default=500)
    line_gap: int = Field(default=0)


class StrokeParams(BaseModel):
    weight: float = Field(default=80.0, gt=0)
    cap_style: StrokeStyle = Field(default=StrokeStyle.round)
    join_style: StrokeStyle = Field(default=StrokeStyle.round)


class GenerateGlyph(BaseModel):
    name: str = Field(..., min_length=1)
    unicode: Optional[int] = Field(default=None, ge=0, le=0x10FFFF)
    shape: str = Field(..., min_length=1)
    advance_width: Optional[int] = Field(default=None, gt=0)
    lsb: int = Field(default=0)
    stroke: Optional[StrokeParams] = None


class GenerateFontRequest(BaseModel):
    metadata: GenerateMetadata
    glyphs: List[GenerateGlyph] = Field(..., min_length=1)
    metrics: Optional[GenerateMetrics] = None
    include_kerning: bool = True
    output_format: FontOutputFormat = FontOutputFormat.woff2


class GenerateFontResponse(BaseModel):
    font_id: str
    family_name: str
    style_name: str
    glyph_count: int
    output_format: str
    file_size_bytes: int
    font_face_css: str
    data_url: str


class SubsetRequest(BaseModel):
    font_id: Optional[str] = None
    file_b64: Optional[str] = None
    text: Optional[str] = None
    unicodes: Optional[List[int]] = None
    preset: Optional[str] = None
    hinting: bool = False
    output_format: FontOutputFormat = FontOutputFormat.woff2

    def has_content(self) -> bool:
        return bool(self.text) or bool(self.unicodes) or bool(self.preset)


class SubsetResponse(BaseModel):
    font_id: str
    original_glyph_count: int
    subset_glyph_count: int
    original_size_bytes: int
    subset_size_bytes: int
    reduction_percent: str
    font_face_css: str
    data_url: str


class ConvertRequest(BaseModel):
    font_id: Optional[str] = None
    file_b64: Optional[str] = None
    family_name: str = Field(..., min_length=1)
    style_name: str = Field(default="Regular")
    weight: int = Field(default=0, ge=0, le=1000)


class ConvertResponse(BaseModel):
    font_id: str
    family_name: str
    style_name: str
    weight: int
    original_size_bytes: int
    converted_size_bytes: int
    reduction_percent: str
    font_face_css: str
    data_url: str


class PreviewParams(BaseModel):
    type: PreviewType = PreviewType.sample
    text: str = "Aa Bb 123"
    width: int = Field(default=800, ge=100, le=2400)
    height: int = Field(default=200, ge=50, le=1200)
    font_size: int = Field(default=80, ge=8, le=400)
    columns: int = Field(default=16, ge=4, le=64)
