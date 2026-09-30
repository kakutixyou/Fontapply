"""
preview_renderer.py
───────────────────
フォントのプレビュー画像（PNG）を生成する。

FastAPI の GET /fonts/preview/{id} から呼ばれ、
フロントの FontPreview.tsx に表示される。

生成するプレビューの種類:
  1. テキストサンプル … "Aa" や任意のテキストを描画
  2. グリフグリッド   … 収録グリフを一覧表示
  3. サイズ比較       … 複数サイズで同じテキストを並べる
  4. ウェイト比較     … Variable Font の wght 軸を段階表示
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import io

from PIL import Image, ImageDraw, ImageFont as PILFont

from .font_loader import LoadedFont


# ──────────────────────────────────────────────
# プレビュー設定
# ──────────────────────────────────────────────

@dataclass
class PreviewConfig:
    """プレビュー画像の設定。"""
    width: int = 800
    height: int = 200
    bg_color: tuple = (255, 255, 255)     # 背景色 (R, G, B)
    text_color: tuple = (30, 30, 30)      # 文字色
    font_size: int = 80
    padding: int = 24
    sample_text: str = "Aa Bb Cc 123"
    show_metrics: bool = False            # ベースライン・キャップハイトを表示

    @classmethod
    def compact(cls) -> "PreviewConfig":
        """サイドバーやカード用の小さいプレビュー。"""
        return cls(width=400, height=100, font_size=48)

    @classmethod
    def large(cls) -> "PreviewConfig":
        """詳細表示用の大きいプレビュー。"""
        return cls(width=1200, height=300, font_size=120)

    @classmethod
    def japanese(cls) -> "PreviewConfig":
        """日本語フォント用プレビュー。"""
        return cls(
            width=800, height=200,
            font_size=72,
            sample_text="あいう漢字ABC 123",
        )


# ──────────────────────────────────────────────
# PreviewRenderer 本体
# ──────────────────────────────────────────────

@dataclass
class PreviewResult:
    """プレビュー生成の結果。"""
    image: Image.Image
    format: str = "PNG"

    def to_bytes(self) -> bytes:
        buf = io.BytesIO()
        self.image.save(buf, format=self.format, optimize=True)
        return buf.getvalue()

    def save(self, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        self.image.save(str(out), format=self.format)
        return out

    @property
    def size(self) -> tuple[int, int]:
        return self.image.size


class PreviewRenderer:
    """
    フォントのプレビュー画像を生成する。

    使い方:
        renderer = PreviewRenderer()

        # テキストサンプル
        result = renderer.render_sample(loaded, config=PreviewConfig())
        png_bytes = result.to_bytes()

        # グリフグリッド
        result = renderer.render_glyph_grid(loaded, columns=16)

        # ウェイト比較（Variable Font）
        result = renderer.render_weight_comparison(loaded)
    """

    def render_sample(
        self,
        loaded: LoadedFont,
        config: Optional[PreviewConfig] = None,
        text: Optional[str] = None,
    ) -> PreviewResult:
        """
        テキストサンプルのプレビューを生成する。
        text を省略すると config.sample_text を使用。
        """
        cfg = config or PreviewConfig()
        sample = text or cfg.sample_text

        img = Image.new("RGB", (cfg.width, cfg.height), cfg.bg_color)
        draw = ImageDraw.Draw(img)

        pil_font = self._load_pil_font(loaded, cfg.font_size)

        # テキストを中央揃えで描画
        try:
            bbox = draw.textbbox((0, 0), sample, font=pil_font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except Exception:
            # 古い Pillow のフォールバック
            text_w, text_h = draw.textsize(sample, font=pil_font)

        x = max(cfg.padding, (cfg.width - text_w) // 2)
        y = max(cfg.padding, (cfg.height - text_h) // 2)

        draw.text((x, y), sample, font=pil_font, fill=cfg.text_color)

        if cfg.show_metrics:
            self._draw_metric_lines(draw, cfg, y, text_h)

        # フォント名を左下に表示
        self._draw_footer(draw, loaded, cfg)

        return PreviewResult(image=img)

    def render_size_comparison(
        self,
        loaded: LoadedFont,
        sizes: Optional[list[int]] = None,
        text: str = "The quick brown fox",
        config: Optional[PreviewConfig] = None,
    ) -> PreviewResult:
        """複数サイズで同じテキストを並べたプレビューを生成する。"""
        sizes = sizes or [12, 18, 24, 36, 48, 72]
        cfg = config or PreviewConfig()
        total_height = sum(s + 8 for s in sizes) + cfg.padding * 2

        img = Image.new("RGB", (cfg.width, total_height), cfg.bg_color)
        draw = ImageDraw.Draw(img)

        y = cfg.padding
        for size in sizes:
            pil_font = self._load_pil_font(loaded, size)
            draw.text((cfg.padding, y), text, font=pil_font, fill=cfg.text_color)
            y += size + 8

        return PreviewResult(image=img)

    def render_glyph_grid(
        self,
        loaded: LoadedFont,
        columns: int = 16,
        cell_size: int = 48,
        max_glyphs: int = 256,
    ) -> PreviewResult:
        """収録グリフを一覧表示するグリッドプレビューを生成する。"""
        cmap = loaded.tt_font.getBestCmap() or {}
        codepoints = sorted(cmap.keys())[:max_glyphs]

        if not codepoints:
            return self._empty_preview(400, 100, "グリフが見つかりません")

        rows = (len(codepoints) + columns - 1) // columns
        width = columns * cell_size
        height = rows * cell_size + 20  # 下部に余白

        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        pil_font = self._load_pil_font(loaded, cell_size - 8)
        fallback = self._get_fallback_font(14)

        for i, cp in enumerate(codepoints):
            col = i % columns
            row = i // columns
            x = col * cell_size
            y = row * cell_size

            # セルの背景（交互に薄いグレー）
            if (col + row) % 2 == 0:
                draw.rectangle([x, y, x + cell_size, y + cell_size],
                               fill=(248, 248, 248))

            # グリフを描画
            char = chr(cp)
            try:
                bbox = draw.textbbox((0, 0), char, font=pil_font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                cx = x + (cell_size - tw) // 2
                cy = y + (cell_size - th) // 2
                draw.text((cx, cy), char, font=pil_font, fill=(30, 30, 30))
            except Exception:
                pass

        return PreviewResult(image=img)

    def render_weight_comparison(
        self,
        loaded: LoadedFont,
        text: str = "WebForge",
        weights: Optional[list[int]] = None,
    ) -> PreviewResult:
        """
        Variable Font の wght 軸を段階的に表示するプレビュー。
        Variable Font でない場合は通常のサンプルにフォールバック。
        """
        if not loaded.is_variable:
            return self.render_sample(loaded, text=text)

        wght_axis = next(
            (ax for ax in loaded.axes if ax.tag == "wght"), None
        )
        if wght_axis is None:
            return self.render_sample(loaded, text=text)

        weights = weights or [100, 300, 400, 500, 700, 900]
        valid = [w for w in weights
                 if wght_axis.minimum <= w <= wght_axis.maximum]
        if not valid:
            return self.render_sample(loaded, text=text)

        font_size = 52
        row_height = font_size + 16
        height = row_height * len(valid) + 48
        width = 800

        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Variable Font の wght をリアルタイムに変えてレンダリング
        # PIL は Variable Font に対応していないため、
        # ここでは wght ラベルを付けてフォールバック描画する
        pil_font = self._load_pil_font(loaded, font_size)
        label_font = self._get_fallback_font(14)

        for i, weight in enumerate(valid):
            y = 24 + i * row_height
            label = f"wght {weight}"
            draw.text((16, y + 4), label, font=label_font, fill=(160, 160, 160))
            draw.text((120, y), text, font=pil_font, fill=(30, 30, 30))

        return PreviewResult(image=img)

    # ──────────────────────────────
    # 内部ユーティリティ
    # ──────────────────────────────

    @staticmethod
    def _load_pil_font(loaded: LoadedFont, size: int) -> PILFont.FreeTypeFont:
        """
        LoadedFont から PIL フォントを生成する。
        フォントファイルが存在する場合はそれを使い、
        bytes 読み込みの場合は一時ファイル経由で読む。
        """
        if loaded.path and loaded.path.exists():
            return PILFont.truetype(str(loaded.path), size)

        # bytes から読み込んだフォントは一時的に書き出す
        buf = io.BytesIO()
        loaded.tt_font.save(buf)
        buf.seek(0)
        return PILFont.truetype(buf, size)

    @staticmethod
    def _get_fallback_font(size: int) -> PILFont.ImageFont:
        """フォールバックフォント（システムデフォルト）を取得する。"""
        try:
            return PILFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except Exception:
            return PILFont.load_default()

    @staticmethod
    def _draw_metric_lines(
        draw: ImageDraw.ImageDraw,
        cfg: PreviewConfig,
        text_y: int,
        text_h: int,
    ) -> None:
        """ベースライン・キャップハイトのガイドラインを描画する。"""
        baseline_y = text_y + round(text_h * 0.85)
        draw.line([(cfg.padding, baseline_y), (cfg.width - cfg.padding, baseline_y)],
                  fill=(200, 100, 100), width=1)

    @staticmethod
    def _draw_footer(
        draw: ImageDraw.ImageDraw,
        loaded: LoadedFont,
        cfg: PreviewConfig,
    ) -> None:
        """画像左下にフォント名を描画する。"""
        try:
            footer_font = PILFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11
            )
        except Exception:
            footer_font = PILFont.load_default()

        label = f"{loaded.full_name}  ·  {loaded.glyph_count} glyphs"
        draw.text(
            (cfg.padding, cfg.height - 18),
            label,
            font=footer_font,
            fill=(180, 180, 180),
        )

    @staticmethod
    def _empty_preview(width: int, height: int, message: str) -> PreviewResult:
        """エラー時の空プレビューを返す。"""
        img = Image.new("RGB", (width, height), (245, 245, 245))
        draw = ImageDraw.Draw(img)
        draw.text((16, height // 2 - 8), message, fill=(160, 160, 160))
        return PreviewResult(image=img)