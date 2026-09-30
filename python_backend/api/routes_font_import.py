from __future__ import annotations

import json
from collections.abc import Iterable
from io import BytesIO

from fastapi import APIRouter, HTTPException, Request
from fontTools.ttLib import TTFont, TTLibError

from python_backend.schemas.font_import_schema import (
    FontImportPreset,
    FontImportResponse,
    ImportedFontMetadata,
    ImportedFontMetrics,
    ImportedGlyph,
    ImportedGlyphContour,
    ImportedGlyphMetrics,
    ImportedGlyphPoint,
)


router = APIRouter(prefix="/fonts", tags=["font-import"])

DEFAULT_JP_MAX_GLYPHS = 1000
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
ASCII_RANGES = ((0x20, 0x7E), (0xA0, 0xFF))
JP_BASE_RANGES = ASCII_RANGES + ((0x3000, 0x303F), (0x3040, 0x309F), (0x30A0, 0x30FF), (0xFF00, 0xFFEF))
CJK_RANGE = (0x4E00, 0x9FFF)


class ImportValidationError(Exception):
    def __init__(self, status_code: int, code: str, message: str, location: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.location = location
        super().__init__(message)


@router.post("/import", response_model=FontImportResponse)
async def import_font(request: Request) -> FontImportResponse:
    try:
        form = await request.form()
        upload = form.get("file")
        if upload is None or not hasattr(upload, "read"):
            raise ImportValidationError(422, "missing_field", "file is required", "file")

        preset_raw = str(form.get("preset", FontImportPreset.jp.value)).strip() or FontImportPreset.jp.value
        try:
            preset = FontImportPreset(preset_raw)
        except ValueError as exc:
            raise ImportValidationError(
                422,
                "invalid_preset",
                f"preset must be one of: {', '.join(p.value for p in FontImportPreset)}",
                "preset",
            ) from exc

        unicodes = _parse_unicodes(form.getlist("unicodes"))
        max_glyphs = _parse_optional_positive_int(form.get("max_glyphs"), "max_glyphs")

        font_bytes = await upload.read()
        if not font_bytes:
            raise ImportValidationError(422, "missing_field", "uploaded file is empty", "file")
        if len(font_bytes) > MAX_UPLOAD_SIZE_BYTES:
            raise ImportValidationError(
                400,
                "file_too_large",
                f"uploaded file exceeds {MAX_UPLOAD_SIZE_BYTES} bytes",
                "file",
            )

        font = _load_ttf(font_bytes)
        return FontImportResponse(
            metadata=_extract_metadata(font),
            metrics=_extract_metrics(font),
            glyphs=_extract_glyphs(font, preset, unicodes, max_glyphs),
        )
    except ImportValidationError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": exc.message, "location": exc.location},
        )
    except TTLibError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "fonttools_error", "message": str(exc), "location": "file"},
        )
    except Exception as exc:
        if exc.__class__.__module__.startswith("fontTools"):
            raise HTTPException(
                status_code=422,
                detail={"code": "fonttools_error", "message": str(exc), "location": "file"},
            )
        raise HTTPException(
            status_code=400,
            detail={"code": "parse_error", "message": str(exc), "location": "file"},
        )


def _parse_unicodes(values: list[object]) -> list[int] | None:
    if not values:
        return None

    parsed_values: list[object] = []
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        if text.startswith("["):
            try:
                decoded = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ImportValidationError(
                    422,
                    "invalid_unicodes",
                    "unicodes must be a valid JSON array when bracket syntax is used",
                    "unicodes",
                ) from exc
            if not isinstance(decoded, list):
                raise ImportValidationError(422, "invalid_unicodes", "unicodes must be a list of integers", "unicodes")
            parsed_values.extend(decoded)
            continue
        if "," in text:
            parsed_values.extend(part.strip() for part in text.split(","))
            continue
        parsed_values.append(text)

    if not parsed_values:
        return None

    result: list[int] = []
    seen: set[int] = set()
    for value in parsed_values:
        try:
            codepoint = int(value, 0) if isinstance(value, str) else int(value)
        except (TypeError, ValueError) as exc:
            raise ImportValidationError(422, "invalid_unicodes", "unicodes must be valid integers", "unicodes") from exc
        if not 0 <= codepoint <= 0x10FFFF:
            raise ImportValidationError(422, "invalid_unicodes", "unicodes must be between 0 and 0x10FFFF", "unicodes")
        if codepoint not in seen:
            seen.add(codepoint)
            result.append(codepoint)
    return result or None


def _parse_optional_positive_int(value: object, location: str) -> int | None:
    if value in (None, ""):
        return None
    try:
        parsed = int(str(value))
    except ValueError as exc:
        raise ImportValidationError(422, "invalid_integer", f"{location} must be an integer", location) from exc
    if parsed <= 0:
        raise ImportValidationError(422, "invalid_integer", f"{location} must be greater than 0", location)
    return parsed


def _load_ttf(font_bytes: bytes) -> TTFont:
    try:
        font = TTFont(BytesIO(font_bytes))
    except TTLibError as exc:
        raise ImportValidationError(422, "fonttools_error", str(exc), "file") from exc
    if "glyf" not in font:
        raise ImportValidationError(422, "missing_glyf", "TTF glyf outlines are required", "file")
    return font


def _extract_metadata(font: TTFont) -> ImportedFontMetadata:
    name_table = font.get("name")
    if name_table is None:
        return ImportedFontMetadata()
    return ImportedFontMetadata(
        family=name_table.getDebugName(1) or "",
        style=name_table.getDebugName(2) or "",
        version=name_table.getDebugName(5) or "",
    )


def _extract_metrics(font: TTFont) -> ImportedFontMetrics:
    head = font["head"]
    hhea = font.get("hhea")
    os2 = font.get("OS/2")
    return ImportedFontMetrics(
        units_per_em=head.unitsPerEm,
        ascender=getattr(hhea, "ascent", getattr(hhea, "ascender", None)),
        descender=getattr(hhea, "descent", getattr(hhea, "descender", None)),
        line_gap=getattr(hhea, "lineGap", None),
        cap_height=getattr(os2, "sCapHeight", None),
        x_height=getattr(os2, "sxHeight", None),
    )


def _extract_glyphs(
    font: TTFont,
    preset: FontImportPreset,
    unicodes: list[int] | None,
    max_glyphs: int | None,
) -> list[ImportedGlyph]:
    selected = _select_glyph_entries(font, preset, unicodes, max_glyphs)
    glyf_table = font["glyf"]
    hmtx_metrics = font["hmtx"].metrics
    glyphs: list[ImportedGlyph] = []

    for glyph_name, unicode_value in selected:
        glyph = glyf_table[glyph_name]
        advance_width, lsb = hmtx_metrics.get(glyph_name, (0, 0))
        coords, end_pts, flags = glyph.getCoordinates(glyf_table)
        glyphs.append(
            ImportedGlyph(
                name=glyph_name,
                unicode=unicode_value,
                contours=_coordinates_to_contours(coords, end_pts, flags),
                metrics=ImportedGlyphMetrics(advance_width=advance_width, lsb=lsb),
            )
        )

    return glyphs


def _coordinates_to_contours(
    coords: Iterable[tuple[int, int]],
    end_pts: list[int],
    flags: Iterable[int],
) -> list[ImportedGlyphContour]:
    points = list(coords)
    flag_values = [bool(flag & 0x01) for flag in flags]
    contours: list[ImportedGlyphContour] = []
    start = 0
    for end in end_pts:
        contours.append(
            ImportedGlyphContour(
                points=[
                    ImportedGlyphPoint(x=int(point[0]), y=int(point[1]))
                    for point in points[start : end + 1]
                ],
                flags=flag_values[start : end + 1],
            )
        )
        start = end + 1
    return contours


def _select_glyph_entries(
    font: TTFont,
    preset: FontImportPreset,
    unicodes: list[int] | None,
    max_glyphs: int | None,
) -> list[tuple[str, int | None]]:
    best_cmap = font.getBestCmap() or {}
    reverse_cmap = _build_reverse_cmap(best_cmap)
    glyph_order = [name for name in font.getGlyphOrder() if name != ".notdef"]

    if unicodes:
        selected: list[tuple[str, int | None]] = []
        seen_names: set[str] = set()
        for codepoint in unicodes:
            glyph_name = best_cmap.get(codepoint)
            if glyph_name is None or glyph_name in seen_names:
                continue
            selected.append((glyph_name, codepoint))
            seen_names.add(glyph_name)
            if max_glyphs is not None and len(selected) >= max_glyphs:
                break
        return selected

    if preset == FontImportPreset.all:
        if max_glyphs is not None:
            glyph_order = glyph_order[:max_glyphs]
        return [(glyph_name, reverse_cmap.get(glyph_name)) for glyph_name in glyph_order]

    sorted_cmap = sorted(best_cmap.items())
    if preset == FontImportPreset.ascii:
        return _collect_from_ranges(sorted_cmap, ASCII_RANGES, max_glyphs)

    effective_limit = max_glyphs or DEFAULT_JP_MAX_GLYPHS
    selected = _collect_from_ranges(sorted_cmap, JP_BASE_RANGES, effective_limit)
    seen_names = {glyph_name for glyph_name, _ in selected}

    if len(selected) >= effective_limit:
        return selected[:effective_limit]

    for codepoint, glyph_name in sorted_cmap:
        if not _in_range(codepoint, CJK_RANGE) or glyph_name in seen_names:
            continue
        selected.append((glyph_name, codepoint))
        seen_names.add(glyph_name)
        if len(selected) >= effective_limit:
            break
    return selected


def _collect_from_ranges(
    cmap_items: list[tuple[int, str]],
    ranges: tuple[tuple[int, int], ...],
    max_glyphs: int | None,
) -> list[tuple[str, int | None]]:
    selected: list[tuple[str, int | None]] = []
    seen_names: set[str] = set()
    for codepoint, glyph_name in cmap_items:
        if not any(_in_range(codepoint, codepoint_range) for codepoint_range in ranges):
            continue
        if glyph_name in seen_names:
            continue
        selected.append((glyph_name, codepoint))
        seen_names.add(glyph_name)
        if max_glyphs is not None and len(selected) >= max_glyphs:
            break
    return selected


def _build_reverse_cmap(cmap: dict[int, str]) -> dict[str, int]:
    reverse: dict[str, int] = {}
    for codepoint, glyph_name in sorted(cmap.items()):
        reverse.setdefault(glyph_name, codepoint)
    return reverse


def _in_range(codepoint: int, value_range: tuple[int, int]) -> bool:
    return value_range[0] <= codepoint <= value_range[1]
