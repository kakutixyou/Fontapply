from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class FontExportFormat(str, Enum):
    ttf = "ttf"
    woff2 = "woff2"


class FontExportPoint(BaseModel):
    x: float = Field(...)
    y: float = Field(...)
    on_curve: bool = Field(default=True)


class FontExportContour(BaseModel):
    points: List[FontExportPoint] = Field(..., min_length=3)


class FontExportGlyphMetrics(BaseModel):
    advance_width: int = Field(..., gt=0)
    left_side_bearing: int = Field(default=0)


class FontExportGlyph(BaseModel):
    name: str = Field(..., min_length=1)
    unicode: Optional[int] = Field(default=None, ge=0, le=0x10FFFF)
    contours: List[FontExportContour] = Field(default_factory=list)
    metrics: FontExportGlyphMetrics


class FontExportMetadata(BaseModel):
    family_name: str = Field(..., min_length=1)
    style_name: str = Field(default="Regular", min_length=1)
    version: str = Field(default="1.0")
    copyright: str = Field(default="")
    designer: str = Field(default="")
    description: str = Field(default="")
    url: str = Field(default="")


class FontExportMetrics(BaseModel):
    upm: int = Field(default=1000, ge=512, le=4096)
    ascender: int = Field(default=800)
    descender: int = Field(default=-200, le=0)
    cap_height: int = Field(default=700)
    x_height: int = Field(default=500)
    line_gap: int = Field(default=0)
    italic_angle: float = Field(default=0.0)


class FontExportRequest(BaseModel):
    metadata: FontExportMetadata
    glyphs: List[FontExportGlyph] = Field(..., min_length=1)
    metrics: FontExportMetrics = Field(default_factory=FontExportMetrics)
    format: FontExportFormat = Field(default=FontExportFormat.ttf)


class ValidationErrorDetail(BaseModel):
    code: str
    message: str
    location: str


class FontExportValidateResponse(BaseModel):
    ok: bool
    error: Optional[ValidationErrorDetail] = None
