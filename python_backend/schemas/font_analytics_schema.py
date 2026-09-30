from __future__ import annotations

from pydantic import BaseModel, Field


class TypographyRecommendation(BaseModel):
    """Typography 推奨値"""

    optimal_sizes: dict[str, tuple[float, float]] = Field(default_factory=dict)
    letter_spacing_map: dict[str, float] = Field(default_factory=dict)
    line_height_map: dict[str, float] = Field(default_factory=dict)


class MetricsAnalysisResponse(BaseModel):
    """Font metrics 分析結果"""

    font_id: str
    recommendations: TypographyRecommendation
    has_cjk: bool
    available_weights: list[int] = Field(default_factory=list)
