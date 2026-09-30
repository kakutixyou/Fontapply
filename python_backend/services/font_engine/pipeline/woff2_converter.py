"""
woff2_converter.py
──────────────────
TTF / OTF → WOFF2 への変換と @font-face CSS 生成を担う。

WOFF2 とは:
  Web Open Font Format 2。Brotli 圧縮を使い、
  TTF より 30〜50% 小さい Web 専用フォント形式。
  すべてのモダンブラウザがサポートしている。

このモジュールでやること:
  1. TTF/OTF → WOFF2 変換
  2. WOFF2 → Base64 エンコード（HTML インライン埋め込み用）
  3. @font-face CSS の自動生成
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import base64
import io

from fontTools.ttLib import TTFont
from fontTools.ttLib.woff2 import compress as woff2_compress, decompress as woff2_decompress

from .font_loader import LoadedFont


# ──────────────────────────────────────────────
# 変換結果
# ──────────────────────────────────────────────

@dataclass
class Woff2Result:
    """WOFF2 変換の結果。"""
    woff2_bytes: bytes
    original_size: int      # 変換前のバイト数
    family_name: str
    style_name: str
    weight: int = 400
    style: str = "normal"   # "normal" | "italic"

    @property
    def size(self) -> int:
        return len(self.woff2_bytes)

    @property
    def reduction_ratio(self) -> float:
        """圧縮率（0.0〜1.0）。"""
        if self.original_size == 0:
            return 0.0
        return max(0.0, 1.0 - self.size / self.original_size)

    @property
    def reduction_percent(self) -> str:
        if self.original_size == 0:
            return "N/A"
        ratio = (1 - self.size / self.original_size) * 100
        return f"{ratio:.1f}%"

    def to_base64(self) -> str:
        """WOFF2 バイナリを Base64 エンコードして返す。"""
        return base64.b64encode(self.woff2_bytes).decode("ascii")

    def to_data_url(self) -> str:
        """data: URL 形式（HTML/CSS に直接埋め込む用）。"""
        return f"data:font/woff2;base64,{self.to_base64()}"

    def to_font_face_css(
        self,
        src_type: str = "url",
        url: Optional[str] = None,
    ) -> str:
        """
        @font-face CSS を生成する。

        src_type:
          "url"    … url('/path/to/font.woff2') 形式
          "base64" … data: URL でインライン埋め込み
          "local"  … local() 参照（ファイルなし）

        url: src_type="url" のときのフォントファイルパス
        """
        if src_type == "base64":
            src = f"url('{self.to_data_url()}') format('woff2')"
        elif src_type == "url":
            font_url = url or f"./fonts/{self.family_name.replace(' ', '')}-{self.style_name}.woff2"
            src = f"url('{font_url}') format('woff2')"
        elif src_type == "local":
            src = f"local('{self.family_name}')"
        else:
            raise ValueError(f"不明な src_type: {src_type!r}")

        return (
            f"@font-face {{\n"
            f"  font-family: '{self.family_name}';\n"
            f"  font-style: {self.style};\n"
            f"  font-weight: {self.weight};\n"
            f"  font-display: swap;\n"
            f"  src: {src};\n"
            f"}}"
        )

    def save(self, path: str | Path) -> Path:
        """WOFF2 ファイルに保存する。"""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(self.woff2_bytes)
        return out

    def __repr__(self) -> str:
        return (
            f"Woff2Result("
            f"{self.family_name!r} {self.style_name!r}, "
            f"{self.original_size // 1024}KB → {self.size // 1024}KB, "
            f"削減: {self.reduction_percent})"
        )


# ──────────────────────────────────────────────
# Woff2Converter 本体
# ──────────────────────────────────────────────

class Woff2Converter:
    """
    TTF/OTF → WOFF2 変換器。

    使い方:
        converter = Woff2Converter()

        # LoadedFont から変換
        loader = FontLoader()
        loaded = loader.load("MyFont.ttf")
        result = converter.convert(loaded)
        print(result)

        # ファイルに保存
        result.save("/output/MyFont.woff2")

        # CSS を生成
        print(result.to_font_face_css(src_type="url", url="./fonts/MyFont.woff2"))

        # bytes から直接変換
        result = converter.convert_bytes(ttf_bytes, "MyFont", "Regular")
    """

    def convert(self, loaded: LoadedFont) -> Woff2Result:
        """LoadedFont を WOFF2 に変換する。"""
        # 元サイズを計測
        original_bytes = self._font_to_bytes(loaded.tt_font)
        original_size = len(original_bytes)

        # WOFF2 に変換
        woff2_bytes = self._to_woff2(original_bytes)

        # ウェイト・スタイルを name テーブルから推定
        weight = self._detect_weight(loaded.style_name)
        style = "italic" if "italic" in loaded.style_name.lower() else "normal"

        return Woff2Result(
            woff2_bytes=woff2_bytes,
            original_size=original_size,
            family_name=loaded.family_name,
            style_name=loaded.style_name,
            weight=weight,
            style=style,
        )

    def convert_bytes(
        self,
        font_bytes: bytes,
        family_name: str,
        style_name: str = "Regular",
        weight: int = 0,       # 0 = style_name から自動推定
        style: str = "normal",
    ) -> Woff2Result:
        """bytes から直接 WOFF2 に変換する。"""
        original_size = len(font_bytes)

        # weight=0 のときだけ style_name から推定
        resolved_weight = weight if weight != 0 else self._detect_weight(style_name)

        # 入力が既に WOFF2 の場合はそのまま返す
        if font_bytes[:4] == b"wOF2":
            return Woff2Result(
                woff2_bytes=font_bytes,
                original_size=original_size,
                family_name=family_name,
                style_name=style_name,
                weight=resolved_weight,
                style=style,
            )

        woff2_bytes = self._to_woff2(font_bytes)

        return Woff2Result(
            woff2_bytes=woff2_bytes,
            original_size=original_size,
            family_name=family_name,
            style_name=style_name,
            weight=resolved_weight,
            style=style,
        )

    def convert_and_save(
        self,
        loaded: LoadedFont,
        output_dir: str | Path,
    ) -> Woff2Result:
        """変換してディレクトリに保存。ファイル名は自動生成。"""
        result = self.convert(loaded)
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{loaded.family_name.replace(' ', '')}-{loaded.style_name}.woff2"
        result.save(out_dir / filename)
        return result

    def generate_font_face_bundle(
        self,
        results: list[Woff2Result],
        src_type: str = "url",
        base_url: str = "./fonts",
    ) -> str:
        """
        複数の WOFF2 結果から @font-face CSS を一括生成する。
        複数ウェイトのフォントセットに使う。
        """
        lines = []
        for result in results:
            url = f"{base_url}/{result.family_name.replace(' ', '')}-{result.style_name}.woff2"
            lines.append(result.to_font_face_css(src_type=src_type, url=url))
            lines.append("")  # 空行で区切る
        return "\n".join(lines).rstrip()

    # ──────────────────────────────
    # 内部ユーティリティ
    # ──────────────────────────────

    @staticmethod
    def _to_woff2(ttf_bytes: bytes) -> bytes:
        """TTF bytes → WOFF2 bytes に変換する。"""
        in_buf = io.BytesIO(ttf_bytes)
        out_buf = io.BytesIO()
        woff2_compress(in_buf, out_buf)
        return out_buf.getvalue()

    @staticmethod
    def _font_to_bytes(tt: TTFont) -> bytes:
        """TTFont → bytes（TTF 形式）。"""
        # WOFF/WOFF2 フォントは一時的に TTF に戻す
        tt_copy_flavor = tt.flavor
        tt.flavor = None
        buf = io.BytesIO()
        tt.save(buf)
        tt.flavor = tt_copy_flavor
        return buf.getvalue()

    @staticmethod
    def _detect_weight(style_name: str) -> int:
        """スタイル名からフォントウェイトを推定する。"""
        name = style_name.lower()
        weight_map = {
            "thin": 100, "hairline": 100,
            "extralight": 200, "ultralight": 200,
            "light": 300,
            "regular": 400, "normal": 400, "book": 400,
            "medium": 500,
            "semibold": 600, "demibold": 600,
            "bold": 700,
            "extrabold": 800, "ultrabold": 800,
            "black": 900, "heavy": 900,
        }
        # 複合語でも対応（例: "ExtraBold"）
        for key, weight in sorted(weight_map.items(), key=lambda x: -len(x[0])):
            if key in name.replace(" ", "").replace("-", ""):
                return weight
        return 400