"""Glyph generation, retrieval, and persistent edit endpoints."""

from __future__ import annotations

import json
import logging
import re
import sqlite3
from contextlib import closing
from pathlib import Path

from fastapi import APIRouter, HTTPException, Path as ApiPath, Query
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat
from typing import Any, Literal, Optional

from ..services.font_engine.generator.glyph_builder import (
    build_glyph,
    get_supported_unicodes,
)

router = APIRouter(prefix="/glyphs", tags=["glyphs"])
logger = logging.getLogger(__name__)
DB_PATH = Path(__file__).resolve().parents[2] / "database" / "font_studio.db"


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
    x:          FiniteFloat
    y:          FiniteFloat
    which:      Optional[Literal["handle_in", "handle_out"]] = None

class Vec2(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: FiniteFloat
    y: FiniteFloat

class GlyphPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    pos: Vec2
    type: Literal["corner", "smooth", "tangent"]
    handleIn: Optional[Vec2] = None
    handleOut: Optional[Vec2] = None
    linked: bool

class GlyphContour(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    points: list[GlyphPoint]
    closed: bool

class GlyphSaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = None
    char: str
    unicode: str
    width: FiniteFloat = Field(gt=0)
    contours: list[GlyphContour]


def init_glyph_overrides_table() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(DB_PATH)) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS glyph_overrides (
                project_id INTEGER NOT NULL DEFAULT 0,
                unicode TEXT NOT NULL,
                glyph_json TEXT NOT NULL,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (project_id, unicode)
            )
        """)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(glyph_overrides)")}
        primary_key = [
            row[1] for row in sorted(
                (row for row in conn.execute("PRAGMA table_info(glyph_overrides)") if row[5]),
                key=lambda row: row[5],
            )
        ]
        if "project_id" not in columns or primary_key != ["project_id", "unicode"]:
            conn.execute("""
                CREATE TABLE glyph_overrides_migrated (
                    project_id INTEGER NOT NULL DEFAULT 0,
                    unicode TEXT NOT NULL,
                    glyph_json TEXT NOT NULL,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (project_id, unicode)
                )
            """)
            legacy_project = "project_id" if "project_id" in columns else "0"
            legacy_updated_at = "updated_at" if "updated_at" in columns else "CURRENT_TIMESTAMP"
            conn.execute(f"""
                INSERT OR REPLACE INTO glyph_overrides_migrated
                    (project_id, unicode, glyph_json, updated_at)
                SELECT {legacy_project}, unicode, glyph_json, {legacy_updated_at}
                FROM glyph_overrides
            """)
            conn.execute("DROP TABLE glyph_overrides")
            conn.execute("ALTER TABLE glyph_overrides_migrated RENAME TO glyph_overrides")


def normalize_unicode(unicode: str) -> str:
    value = unicode.upper().removeprefix("U+")
    if not re.fullmatch(r"[0-9A-F]{1,6}", value):
        raise HTTPException(status_code=422, detail="Unicode must be hexadecimal")
    normalized = value.zfill(4)
    codepoint = int(normalized, 16)
    if codepoint > 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF:
        raise HTTPException(status_code=422, detail="Unicode is outside the valid codepoint range")
    return normalized


def validate_project_id(project_id: int) -> None:
    if project_id == 0:
        return
    with closing(sqlite3.connect(DB_PATH)) as conn, conn:
        exists = conn.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail=f"Project {project_id} was not found")


def get_saved_glyph(unicode: str, project_id: int) -> dict[str, Any] | None:
    with closing(sqlite3.connect(DB_PATH)) as conn, conn:
        row = conn.execute(
            "SELECT glyph_json FROM glyph_overrides WHERE project_id = ? AND unicode = ?",
            (project_id, unicode),
        ).fetchone()
    return json.loads(row[0]) if row else None


def store_glyph_override(project_id: int, unicode: str, glyph: dict[str, Any]) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(DB_PATH)) as conn, conn:
        conn.execute("""
            INSERT INTO glyph_overrides (project_id, unicode, glyph_json, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(project_id, unicode) DO UPDATE SET
                glyph_json = excluded.glyph_json,
                updated_at = CURRENT_TIMESTAMP
        """, (project_id, unicode, json.dumps(glyph, allow_nan=False)))


# ── エンドポイント ────────────────────────────────────────────────────────────

@router.get("", response_model=GlyphListResponse)
async def list_glyphs() -> GlyphListResponse:
    """対応グリフの Unicode リストを返す"""
    supported = get_supported_unicodes()
    return GlyphListResponse(supported=supported, total=len(supported))


# python_backend/api/routes_font_generator.py

@router.get("/{unicode}", response_model=GlyphResponse)
async def get_glyph(
    unicode: str,
    project_id: int = Query(default=0, ge=0),
) -> GlyphResponse:
    normalized = normalize_unicode(unicode)
    logger.info("Glyph request received: U+%s", normalized)
    validate_project_id(project_id)
    glyph_data = get_saved_glyph(normalized, project_id)
    if glyph_data is None:
        glyph_data = build_glyph(normalized)
    
    if glyph_data is None:
        logger.warning("Glyph not implemented: U+%s", normalized)
        raise HTTPException(
            status_code=404,
            detail=f"Glyph U+{normalized} is not yet implemented in glyph_builder.py"
        )

    return GlyphResponse(glyph=glyph_data, metrics=FONT_METRICS)

@router.put("/{unicode}", response_model=GlyphResponse)
async def save_glyph(
    unicode: str = ApiPath(...),
    glyph: GlyphSaveRequest = ...,
    project_id: int = Query(default=0, ge=0),
) -> GlyphResponse:
    normalized = normalize_unicode(unicode)
    validate_project_id(project_id)
    if glyph.unicode.upper().removeprefix("U+").zfill(4) != normalized:
        raise HTTPException(status_code=422, detail="Glyph Unicode does not match the URL")
    if glyph.char != chr(int(normalized, 16)):
        raise HTTPException(status_code=422, detail="Glyph character does not match its Unicode")
    if build_glyph(normalized) is None:
        raise HTTPException(status_code=404, detail=f"Glyph U+{normalized} is not supported")

    glyph_data = glyph.model_dump()
    store_glyph_override(project_id, normalized, glyph_data)
    return GlyphResponse(glyph=glyph_data, metrics=FONT_METRICS)

@router.get("/{unicode}/metrics", response_model=MetricsResponse)
async def get_metrics(unicode: str) -> MetricsResponse:
    """メトリクスのみを返す（グリフ非依存）"""
    return MetricsResponse(metrics=FONT_METRICS)


@router.post("/{unicode}/point")
async def update_point(
    unicode: str,
    req: PointUpdateRequest,
    project_id: int = Query(default=0, ge=0),
) -> dict[str, str]:
    normalized = normalize_unicode(unicode)
    validate_project_id(project_id)
    glyph_data = get_saved_glyph(normalized, project_id) or build_glyph(normalized)
    if glyph_data is None:
        raise HTTPException(status_code=404, detail=f"Glyph U+{normalized} is not supported")

    contour = next(
        (item for item in glyph_data["contours"] if item.get("id") == req.contour_id),
        None,
    )
    if contour is None:
        raise HTTPException(status_code=404, detail=f"Contour {req.contour_id} was not found")
    point = next(
        (item for item in contour.get("points", []) if item.get("id") == req.point_id),
        None,
    )
    if point is None:
        raise HTTPException(status_code=404, detail=f"Point {req.point_id} was not found")

    if "pos" in point:
        key = {"handle_in": "handleIn", "handle_out": "handleOut"}.get(req.which, "pos")
        point[key] = {"x": req.x, "y": req.y}
    else:
        key = {"handle_in": "handle_in", "handle_out": "handle_out"}.get(req.which)
        if key:
            point[key] = {"x": req.x, "y": req.y}
        else:
            point["x"], point["y"] = req.x, req.y
    store_glyph_override(project_id, normalized, glyph_data)
    return {
        "status": "ok",
        "message": f"Point {req.point_id} in {req.contour_id} saved"
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