from __future__ import annotations

from io import BytesIO
from statistics import mean, pstdev

from fontTools.ttLib import TTFont

from python_backend.core.font_cache import FontCache
from python_backend.schemas.font_analytics_schema import TypographyRecommendation


CONTEXT_PRESETS: dict[str, dict[str, float | tuple[float, float]]] = {
    "body": {
        "size_range": (14.0, 18.0),
        "letter_spacing_factor": 0.5,
        "line_height_factor": 1.6,
    },
    "heading": {
        "size_range": (24.0, 36.0),
        "letter_spacing_factor": 1.0,
        "line_height_factor": 1.2,
    },
    "caption": {
        "size_range": (10.0, 12.0),
        "letter_spacing_factor": 0.3,
        "line_height_factor": 1.4,
    },
}


class FontAnalyticsEngine:
    """Font メタデータから Typography 推奨値を分析・生成"""

    def __init__(self, cache: FontCache | None = None) -> None:
        self._cache = cache or FontCache.instance()

    def load_font_data(self, font_id: str) -> tuple[dict, list[dict]] | None:
        entry = self._cache.get(font_id)
        if entry is None:
            return None

        font = TTFont(BytesIO(entry.font_bytes))
        hhea = font.get("hhea")
        os2 = font.get("OS/2")
        head = font.get("head")
        metadata = {
            "metrics": {
                "ascender": getattr(hhea, "ascent", getattr(hhea, "ascender", None)),
                "descender": getattr(hhea, "descent", getattr(hhea, "descender", None)),
                "line_gap": getattr(hhea, "lineGap", None),
                "cap_height": getattr(os2, "sCapHeight", None),
                "x_height": getattr(os2, "sxHeight", None),
                "units_per_em": getattr(head, "unitsPerEm", None),
            },
            "weights": [int(getattr(os2, "usWeightClass", 400) or 400)],
        }
        glyphs = self._extract_glyphs(font)
        return metadata, glyphs

    def analyze_font_metrics(self, font_metadata: dict, glyphs: list) -> dict:
        advance_widths = [
            float(glyph["metrics"]["advance_width"])
            for glyph in glyphs
            if isinstance(glyph, dict)
            and isinstance(glyph.get("metrics"), dict)
            and isinstance(glyph["metrics"].get("advance_width"), (int, float))
        ]

        metrics = font_metadata.get("metrics", {}) if isinstance(font_metadata, dict) else {}
        glyph_stats = {
            "advance_width_min": min(advance_widths) if advance_widths else 0.0,
            "advance_width_max": max(advance_widths) if advance_widths else 0.0,
            "advance_width_avg": mean(advance_widths) if advance_widths else 0.0,
            "advance_width_std_dev": pstdev(advance_widths) if len(advance_widths) > 1 else 0.0,
            "sample_size": len(advance_widths),
            "units_per_em": float(metrics.get("units_per_em") or 1000.0),
            "x_height_to_cap_ratio": self._ratio(metrics.get("x_height"), metrics.get("cap_height")),
            "ascender_to_descender_ratio": self._ratio(
                metrics.get("ascender"),
                self._abs_numeric(metrics.get("descender")),
            ),
        }

        return {
            "optimal_sizes": self._compute_optimal_sizes(glyph_stats),
            "letter_spacing_map": self._compute_letter_spacing(metrics),
            "line_height_map": self._compute_line_height(metrics),
            "has_cjk": self._has_cjk_glyphs(glyphs),
            "available_weights": self._normalize_weights(font_metadata.get("weights")),
            "glyph_stats": glyph_stats,
        }

    def recommend_typography(self, font_id: str, context: str = "body") -> TypographyRecommendation:
        loaded = self.load_font_data(font_id)
        if loaded is None:
            raise KeyError(font_id)

        font_metadata, glyphs = loaded
        analysis = self.analyze_font_metrics(font_metadata, glyphs)
        normalized_context = self._normalize_context(context)

        return TypographyRecommendation(
            optimal_sizes={normalized_context: analysis["optimal_sizes"][normalized_context]},
            letter_spacing_map={normalized_context: analysis["letter_spacing_map"][normalized_context]},
            line_height_map={normalized_context: analysis["line_height_map"][normalized_context]},
        )

    def _compute_optimal_sizes(self, glyph_stats: dict) -> dict:
        avg = float(glyph_stats.get("advance_width_avg") or 0.0)
        upm = float(glyph_stats.get("units_per_em") or 1000.0)
        width_ratio = avg / upm if upm > 0 else 0.0

        if width_ratio >= 0.62:
            delta = 1.0
        elif width_ratio <= 0.48:
            delta = -1.0
        else:
            delta = 0.0

        result: dict[str, tuple[float, float]] = {}
        for key, preset in CONTEXT_PRESETS.items():
            size_min, size_max = preset["size_range"] if isinstance(preset["size_range"], tuple) else (14.0, 18.0)
            result[key] = (
                max(8.0, round(float(size_min) + delta, 2)),
                max(10.0, round(float(size_max) + delta, 2)),
            )
        return result

    def _compute_letter_spacing(self, font_metrics: dict) -> dict:
        ratio = self._ratio(font_metrics.get("x_height"), font_metrics.get("cap_height"))
        if ratio == 0.0:
            ratio = 0.7
        adjustment = (0.72 - ratio) * 0.5

        return {
            key: round(
                max(0.0, float(preset["letter_spacing_factor"]) + adjustment), 2
            )
            for key, preset in CONTEXT_PRESETS.items()
        }

    def _compute_line_height(self, font_metrics: dict) -> dict:
        ratio = self._ratio(font_metrics.get("ascender"), self._abs_numeric(font_metrics.get("descender")))
        if ratio == 0.0:
            ratio = 2.0
        adjustment = (2.0 - ratio) * 0.08

        return {
            key: round(
                min(2.0, max(1.0, float(preset["line_height_factor"]) + adjustment)), 2
            )
            for key, preset in CONTEXT_PRESETS.items()
        }

    def _extract_glyphs(self, font: TTFont) -> list[dict]:
        cmap = font.getBestCmap() or {}
        hmtx = font["hmtx"].metrics if "hmtx" in font else {}
        glyphs: list[dict] = []

        if cmap:
            for codepoint, glyph_name in cmap.items():
                advance_width = hmtx.get(glyph_name, (0, 0))[0]
                glyphs.append(
                    {
                        "name": glyph_name,
                        "unicode": int(codepoint),
                        "metrics": {"advance_width": int(advance_width)},
                    }
                )
            return glyphs

        for glyph_name in font.getGlyphOrder():
            if glyph_name == ".notdef":
                continue
            advance_width = hmtx.get(glyph_name, (0, 0))[0]
            glyphs.append(
                {
                    "name": glyph_name,
                    "unicode": None,
                    "metrics": {"advance_width": int(advance_width)},
                }
            )
        return glyphs

    def _has_cjk_glyphs(self, glyphs: list) -> bool:
        cjk_ranges = (
            (0x3040, 0x309F),
            (0x30A0, 0x30FF),
            (0x3400, 0x4DBF),
            (0x4E00, 0x9FFF),
            (0xF900, 0xFAFF),
        )
        for glyph in glyphs:
            if not isinstance(glyph, dict):
                continue
            codepoint = glyph.get("unicode")
            if not isinstance(codepoint, int):
                continue
            if any(start <= codepoint <= end for start, end in cjk_ranges):
                return True
        return False

    def _normalize_context(self, context: str) -> str:
        normalized = context.strip().lower()
        return normalized if normalized in CONTEXT_PRESETS else "body"

    def _normalize_weights(self, weights: object) -> list[int]:
        if isinstance(weights, list):
            values: list[int] = []
            for weight in weights:
                if not isinstance(weight, (int, float, str)):
                    continue
                try:
                    parsed = int(float(str(weight)))
                except ValueError:
                    continue
                if parsed > 0:
                    values.append(parsed)
            return sorted(set(values)) or [400]
        return [400]

    def _ratio(self, numerator: object, denominator: object) -> float:
        if not isinstance(numerator, (int, float)) or not isinstance(denominator, (int, float)):
            return 0.0
        if denominator == 0:
            return 0.0
        return float(numerator) / float(denominator)

    def _abs_numeric(self, value: object) -> float:
        if not isinstance(value, (int, float)):
            return 0.0
        return abs(float(value))
