"""
subset_exporter.py
──────────────────
フォントから必要な文字だけを抽出してサブセットを生成する。

なぜサブセット化が重要か:
  日本語フォントは 1 万以上のグリフを持つことが多く、
  ファイルサイズが 5〜20MB になる。
  Web で使う場合は必要な文字だけに絞ることで
  100KB 以下にまで圧縮できる。

fontTools の subset モジュールを使う。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import io

from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options

from .font_loader import LoadedFont


# ──────────────────────────────────────────────
# Unicode レンジのプリセット定数
# ──────────────────────────────────────────────

class UnicodeRange:
    """よく使うサブセット範囲のプリセット。"""

    # 基本ラテン
    ASCII = set(range(0x0020, 0x007F))
    LATIN_EXTENDED = set(range(0x0020, 0x024F))

    # 日本語
    HIRAGANA = set(range(0x3041, 0x3097))
    KATAKANA = set(range(0x30A1, 0x30FB))
    KANA = HIRAGANA | KATAKANA
    JIS_LEVEL1 = set(range(0x4E00, 0x9FFF))   # 漢字（簡易）
    JAPANESE_BASIC = KANA | set(range(0x3000, 0x303F))  # 仮名 + 句読点

    # 数字・記号
    DIGITS = set(range(0x0030, 0x003A))
    PUNCTUATION = set(range(0x0021, 0x0030)) | set(range(0x003A, 0x0041))

    # ランディングページでよく使うセット
    LANDING_JP = ASCII | HIRAGANA | KATAKANA | set(range(0x3000, 0x303F))
    LANDING_EN = ASCII | LATIN_EXTENDED


# ──────────────────────────────────────────────
# サブセット設定
# ──────────────────────────────────────────────

@dataclass
class SubsetConfig:
    """
    サブセット化の設定。

    unicodes: 含めるコードポイントの集合
    text: unicodes の代わりに文字列で指定することも可能
           例: "あいうえおABCDEF"
    retain_gids: グリフIDを保持する（Variable Font の互換性のため）
    layout_features: 保持する OpenType フィーチャー
    """
    unicodes: set[int] = field(default_factory=set)
    text: str = ""
    retain_gids: bool = False
    layout_features: list[str] = field(default_factory=lambda: [
        "kern", "liga", "calt", "palt", "vkrn", "vert"
    ])
    hinting: bool = False           # ヒンティングを除去するか（Web 用は False 推奨）
    desubroutinize: bool = True     # CFF の subroutine を展開（圧縮率向上）
    name_ids: list[int] = field(default_factory=lambda: [1, 2, 4, 6])

    def all_unicodes(self) -> set[int]:
        """unicodes と text を合わせた全コードポイントを返す。"""
        result = set(self.unicodes)
        for char in self.text:
            result.add(ord(char))
        return result

    @classmethod
    def from_text(cls, text: str, **kwargs) -> "SubsetConfig":
        """文字列から設定を生成するショートカット。"""
        return cls(text=text, **kwargs)

    @classmethod
    def preset_landing_jp(cls) -> "SubsetConfig":
        return cls(unicodes=UnicodeRange.LANDING_JP)

    @classmethod
    def preset_landing_en(cls) -> "SubsetConfig":
        return cls(unicodes=UnicodeRange.LANDING_EN)


# ──────────────────────────────────────────────
# SubsetExporter 本体
# ──────────────────────────────────────────────

@dataclass
class SubsetResult:
    """サブセット化の結果。"""
    original_glyph_count: int
    subset_glyph_count: int
    original_size_bytes: int
    subset_size_bytes: int
    tt_font: TTFont

    @property
    def reduction_ratio(self) -> float:
        """圧縮率（0.0〜1.0）。"""
        if self.original_size_bytes == 0:
            return 0.0
        return 1.0 - self.subset_size_bytes / self.original_size_bytes

    @property
    def reduction_percent(self) -> str:
        return f"{self.reduction_ratio * 100:.1f}%"

    def to_bytes(self) -> bytes:
        buf = io.BytesIO()
        self.tt_font.save(buf)
        return buf.getvalue()

    def __repr__(self) -> str:
        return (
            f"SubsetResult("
            f"glyphs: {self.original_glyph_count}→{self.subset_glyph_count}, "
            f"size: {self.original_size_bytes//1024}KB→{self.subset_size_bytes//1024}KB, "
            f"削減: {self.reduction_percent})"
        )


class SubsetExporter:
    """
    フォントのサブセット化を担う。

    使い方:
        loader = FontLoader()
        loaded = loader.load("NotoSansJP-Variable.ttf")

        exporter = SubsetExporter()

        # 文字列からサブセット
        result = exporter.subset(loaded, SubsetConfig.from_text("あいうえお"))

        # プリセット使用
        result = exporter.subset(loaded, SubsetConfig.preset_landing_jp())

        print(result)
        # SubsetResult(glyphs: 7958→342, size: 8192KB→312KB, 削減: 96.2%)

        # ファイルに保存
        exporter.save(result, "/tmp/subset.ttf")
    """

    def subset(
        self,
        loaded: LoadedFont,
        config: SubsetConfig,
    ) -> SubsetResult:
        """
        フォントをサブセット化する。
        元の LoadedFont は変更しない（コピーして処理）。
        """
        unicodes = config.all_unicodes()
        if not unicodes:
            raise ValueError("サブセットの文字が指定されていません")

        # 元サイズを記録
        original_size = self._font_size(loaded.tt_font)
        original_count = len(loaded.tt_font.getGlyphOrder())

        # fontTools の Options を設定
        opts = Options()
        opts.layout_features = config.layout_features
        opts.hinting = config.hinting
        opts.desubroutinize = config.desubroutinize
        opts.name_IDs = config.name_ids
        opts.retain_gids = config.retain_gids
        # 存在しないグリフは無視（エラーにしない）
        opts.ignore_missing_unicodes = True
        opts.ignore_missing_glyphs = True

        # TTFont のコピーを作成
        tt_copy = self._copy_font(loaded.tt_font)

        # サブセット実行
        subsetter = Subsetter(options=opts)
        subsetter.populate(unicodes=list(unicodes))
        subsetter.subset(tt_copy)

        subset_size = self._font_size(tt_copy)
        subset_count = len(tt_copy.getGlyphOrder())

        return SubsetResult(
            original_glyph_count=original_count,
            subset_glyph_count=subset_count,
            original_size_bytes=original_size,
            subset_size_bytes=subset_size,
            tt_font=tt_copy,
        )

    def subset_by_text(
        self, loaded: LoadedFont, text: str
    ) -> SubsetResult:
        """文字列を直接渡すショートカット。"""
        return self.subset(loaded, SubsetConfig.from_text(text))

    def save(
        self,
        result: SubsetResult,
        path: str | Path,
    ) -> Path:
        """サブセットをファイルに保存する。"""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        result.tt_font.save(str(out))
        return out

    def subset_and_save(
        self,
        loaded: LoadedFont,
        config: SubsetConfig,
        output_path: str | Path,
    ) -> SubsetResult:
        """サブセット化してファイル保存まで一括実行。"""
        result = self.subset(loaded, config)
        self.save(result, output_path)
        return result

    # ──────────────────────────────
    # 内部ユーティリティ
    # ──────────────────────────────

    @staticmethod
    def _font_size(tt: TTFont) -> int:
        """TTFont の bytes サイズを計測する。"""
        buf = io.BytesIO()
        tt.save(buf)
        return buf.tell()

    @staticmethod
    def _copy_font(tt: TTFont) -> TTFont:
        buf = io.BytesIO()
        tt.save(buf)
        buf.seek(0)
        return TTFont(buf)