from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FontImportPreset(str, Enum):
    ascii = "ascii"
    jp = "jp"
    all = "all"


class ImportedGlyphPoint(BaseModel):
    x: int
    y: int


class ImportedGlyphContour(BaseModel):
    points: list[ImportedGlyphPoint] = Field(default_factory=list)
    flags: list[bool] = Field(default_factory=list)


class ImportedGlyphMetrics(BaseModel):
    advance_width: int
    lsb: int


class ImportedGlyph(BaseModel):
    name: str
    unicode: Optional[int] = Field(default=None, ge=0, le=0x10FFFF)
    contours: list[ImportedGlyphContour] = Field(default_factory=list)
    metrics: ImportedGlyphMetrics


class ImportedFontMetadata(BaseModel):
    family: str = ""
    style: str = ""
    version: str = ""


class ImportedFontMetrics(BaseModel):
    units_per_em: int = Field(serialization_alias="unitsPerEm")
    ascender: Optional[int] = None
    descender: Optional[int] = None
    line_gap: Optional[int] = Field(default=None, serialization_alias="lineGap")
    cap_height: Optional[int] = Field(default=None, serialization_alias="capHeight")
    x_height: Optional[int] = Field(default=None, serialization_alias="xHeight")


class FontImportResponse(BaseModel):
    metadata: ImportedFontMetadata
    metrics: ImportedFontMetrics
    glyphs: list[ImportedGlyph] = Field(default_factory=list)
