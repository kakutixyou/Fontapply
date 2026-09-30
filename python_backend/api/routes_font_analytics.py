from __future__ import annotations

import logging
import time
import json
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from python_backend.core.font_cache import FontCacheManager
from python_backend.schemas.font_analytics_schema import (
    MetricsAnalysisResponse,
    TypographyRecommendation,
)
from python_backend.services.font_analytics_engine import FontAnalyticsEngine

router = APIRouter(prefix="/fonts", tags=["font-analytics"])
engine = FontAnalyticsEngine()
cache_manager = FontCacheManager(max_memory_entries=100)
logger = logging.getLogger(__name__)


class RecommendTypographyRequest(BaseModel):
    font_id: str = Field(min_length=1)
    context: str = Field(min_length=1)


class RecommendTypographyResponse(BaseModel):
    css_vars: dict[str, str]
    tailwind_config: dict[str, Any]


@router.get("/{font_id}/metrics-analysis", response_model=MetricsAnalysisResponse)
async def get_font_metrics_analysis(font_id: str) -> MetricsAnalysisResponse:
    """Font metrics 分析 + Typography 推奨値を返す。"""
    started = time.perf_counter()

    def _compute() -> dict[str, object]:
        loaded = engine.load_font_data(font_id)
        if loaded is None:
            raise HTTPException(
                status_code=404, detail=f"font_id {font_id!r} が見つかりません"
            )
        font_metadata, glyphs = loaded
        analysis = engine.analyze_font_metrics(font_metadata, glyphs)
        return {
            "font_id": font_id,
            "metrics": font_metadata.get("metrics", {}),
            "recommendations": {
                "optimal_sizes": analysis["optimal_sizes"],
                "letter_spacing_map": analysis["letter_spacing_map"],
                "line_height_map": analysis["line_height_map"],
            },
            "glyph_stats": analysis.get("glyph_stats", {}),
            "has_cjk": analysis["has_cjk"],
            "available_weights": analysis["available_weights"],
        }

    payload, layer = cache_manager.get_or_compute(font_id, _compute)
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "font analytics cache layer=%s font_id=%s elapsed=%.2fms",
        layer,
        font_id,
        elapsed_ms,
    )

    try:
        recommendations = dict(payload["recommendations"])
        optimal_sizes = recommendations.get("optimal_sizes", {})
        recommendations["optimal_sizes"] = {
            key: tuple(value) if isinstance(value, list) else value
            for key, value in dict(optimal_sizes).items()
        }
        for key in ("letter_spacing_map", "line_height_map"):
            if isinstance(recommendations.get(key), str):
                recommendations[key] = json.loads(recommendations[key])
        return MetricsAnalysisResponse(
            font_id=str(payload["font_id"]),
            recommendations=TypographyRecommendation(**recommendations),
            has_cjk=bool(payload["has_cjk"]),
            available_weights=[int(v) for v in list(payload["available_weights"])],
        )
    except Exception as exc:
        logger.warning(
            "Corrupted cache payload detected for font_id=%s (%s)", font_id, exc
        )
        cache_manager.clear(font_id)
        raise HTTPException(
            status_code=500, detail="Analytics cache data is corrupted"
        ) from exc


@router.post("/recommend-typography", response_model=RecommendTypographyResponse)
async def recommend_typography(
    req: RecommendTypographyRequest,
) -> RecommendTypographyResponse:
    """Font ID + context から Typography 推奨値を生成する。"""
    context = req.context.strip().lower()
    try:
        recommendation = engine.recommend_typography(req.font_id, context=context)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"font_id {req.font_id!r} が見つかりません"
        )

    resolved_context = next(iter(recommendation.optimal_sizes.keys()))
    size_min, size_max = recommendation.optimal_sizes[resolved_context]
    font_size = round((size_min + size_max) / 2, 1)
    letter_spacing = recommendation.letter_spacing_map[resolved_context]
    line_height = recommendation.line_height_map[resolved_context]
    css_vars = {
        f"--font-size-{resolved_context}": f"{font_size}px",
        f"--line-height-{resolved_context}": str(line_height),
        f"--letter-spacing-{resolved_context}": f"{letter_spacing}px",
    }
    return RecommendTypographyResponse(
        css_vars=css_vars,
        tailwind_config={
            "theme": {
                "extend": {
                    "fontSize": {resolved_context: f"{font_size}px"},
                    "lineHeight": {resolved_context: str(line_height)},
                    "letterSpacing": {resolved_context: f"{letter_spacing}px"},
                }
            },
            "meta": {"font_id": req.font_id},
        },
    )


@router.post("/clear-cache")
async def clear_cache(font_id: str | None = None) -> dict[str, object]:
    """Analytics キャッシュを削除する。"""
    if font_id:
        return {
            "status": "cleared",
            "font_id": font_id,
            "deleted": cache_manager.clear(font_id),
        }
    cache_manager.clear_all()
    return {"status": "all_cache_cleared"}


@router.get("/cache-stats")
async def get_cache_statistics() -> dict[str, object]:
    """Analytics キャッシュ統計を返す。"""
    return cache_manager.get_statistics()
