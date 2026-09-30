"""
font_engine.pipeline
────────────────────
既存フォントファイルの加工・変換・軽量化を担う層。

層の役割:
  pipeline/ … TTF/OTF を受け取って加工・変換（変換領域）
  generator/ … ゼロからグリフ・フォントを設計（設計領域）

接続点:
  font_loader.py が読み込んだグリフは
  generator.glyph_modifier.GlyphModifier に渡して編集できる。

Public API:
  from font_engine.pipeline import FontLoader, VariableAdjuster
  from font_engine.pipeline import SubsetExporter, Woff2Converter
  from font_engine.pipeline import PreviewRenderer
"""

from .font_loader import FontLoader, LoadedFont
from .variable_adjuster import VariableAdjuster
from .subset_exporter import SubsetExporter
from .woff2_converter import Woff2Converter
from .preview_renderer import PreviewRenderer

__all__ = [
    "FontLoader",
    "LoadedFont",
    "VariableAdjuster",
    "SubsetExporter",
    "Woff2Converter",
    "PreviewRenderer",
]