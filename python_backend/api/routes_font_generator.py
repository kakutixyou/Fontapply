"""
routes_font_generator.py  ← glyph_builder ブリッジ版

エンドポイント:
  GET  /api/glyphs/{unicode}           グリフデータ取得
  GET  /api/glyphs                     対応グリフ一覧
  GET  /api/glyphs/{unicode}/metrics   フォントメトリクス（グリフ共通）
  POST /api/glyphs/{unicode}/point     ポイント座標更新（将来の保存用）
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Optional

from ..services.font_engine.generator.glyph_builder import (
    build_glyph,
    get_supported_unicodes,
)

router = APIRouter(prefix="/glyphs", tags=["glyphs"])


# ── フォントメトリクス（全グリフ共通） ────────────────────────────────────────

FONT_METRICS = {
    "ascender":   720,
    "cap_height": 680,
    "x_height":   490,
    "descender":  -200,
    "lsb":        80,
    "rsb":        72,
    "units_per_em": 1000,
}


# ── レスポンスモデル ──────────────────────────────────────────────────────────

class GlyphResponse(BaseModel):
    glyph: dict[str, Any]
    metrics: dict[str, Any]


class GlyphListResponse(BaseModel):
    supported: list[str]
    total: int


class MetricsResponse(BaseModel):
    metrics: dict[str, Any]


class PointUpdateRequest(BaseModel):
    contour_id: str
    point_id:   str
    x:          float
    y:          float
    which:      Optional[str] = None   # 'handle_in' | 'handle_out' | None(=anchor)


# ── エンドポイント ────────────────────────────────────────────────────────────

@router.get("", response_model=GlyphListResponse)
async def list_glyphs() -> GlyphListResponse:
    """対応グリフの Unicode リストを返す"""
    supported = get_supported_unicodes()
    return GlyphListResponse(supported=supported, total=len(supported))


# python_backend/api/routes_font_generator.py

@router.get("/{unicode}", response_model=GlyphResponse)
async def get_glyph(unicode: str) -> GlyphResponse:
    print(f"\n★★★ [ルーター] リクエスト到着! 要求された文字: {unicode} ★★★")
    
    normalized = unicode.upper().zfill(4)
    print(f"★★★ [ルーター] 正規化後: {normalized} ★★★")
    
    glyph_data = build_glyph(normalized)
    
    if glyph_data is None:
        print(f"❌❌❌ [ルーター] エラー: {normalized} は _SPECS 辞書に見つかりません！ ❌❌❌")
        raise HTTPException(
            status_code=404,
            detail=f"Glyph U+{normalized} is not yet implemented in glyph_builder.py"
        )

    print(f"✅✅✅ [ルーター] 成功! {normalized} のデータをフロントエンドに返却します ✅✅✅")
    return GlyphResponse(glyph=glyph_data, metrics=FONT_METRICS)

@router.get("/{unicode}/metrics", response_model=MetricsResponse)
async def get_metrics(unicode: str) -> MetricsResponse:
    """メトリクスのみを返す（グリフ非依存）"""
    return MetricsResponse(metrics=FONT_METRICS)


@router.post("/{unicode}/point")
async def update_point(unicode: str, req: PointUpdateRequest) -> dict[str, str]:
    """
    ポイント座標の更新。
    現状は受け取って 200 を返すだけ（SQLite への永続化は TODO）。
    将来: font_studio.db の glyph_points テーブルに保存
    """
    # TODO: SQLite への永続化
    # db.execute(
    #   "UPDATE glyph_points SET x=?, y=? WHERE unicode=? AND contour_id=? AND point_id=?",
    #   (req.x, req.y, unicode.upper(), req.contour_id, req.point_id)
    # )
    return {
        "status": "ok",
        "message": f"Point {req.point_id} in {req.contour_id} updated (in-memory only)"
    }
    
# @router.get("/{unicode_hex}")
# async def get_glyph(unicode_hex: str):
# 上の書き方のほうがきれい
#     """
#     指定されたUnicodeの文字の頂点データを生成して返す
#     """
#     # glyph_builder_full.py の関数を呼び出して文字データを生成
#     glyph_data = build_glyph(unicode_hex)
    
#     if glyph_data is None:
#         raise HTTPException(status_code=404, detail=f"Glyph not found for unicode: {unicode_hex}")
        
#     return {
#         "glyph": glyph_data,
#         "metrics": {
#             # 必要に応じてメトリクス情報もここで返す
#             "ascender": 800,
#             "cap_height": 680,
#             "x_height": 480,
#             "descender": -200,
#             "lsb": 60,
#             "rsb": 60,
#             "units_per_em": 1000
#         }
#     }