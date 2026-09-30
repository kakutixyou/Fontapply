# python_backend/services/font_engine/generator/__init__.py

# 現在の大動脈（新アーキテクチャ）で使うものだけを公開する
from .glyph_builder import build_glyph

__all__ = ["build_glyph"]