"""
metrics_engine.py
─────────────────
フォントのメトリクス（幅・高さ・行間など）を管理する。

用語解説（em 単位, UPM=1000 基準）:
  UPM        … Units Per eM。フォントのグリッド解像度（通常1000）
  ascender   … ベースラインから上の最大高さ（大文字の上端）
  descender  … ベースラインより下の深さ（g, p などの下部）負の値
  cap_height … 大文字の高さ（H や I の上端）
  x_height   … 小文字の高さ（x の上端）
  advance    … グリフの「幅」（次のグリフの開始位置まで）
  lsb        … Left Side Bearing（グリフ左端からアウトライン開始までの余白）
  rsb        … Right Side Bearing（アウトライン終端から advance 端までの余白）
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────
# フォントレベルのメトリクス
# ──────────────────────────────────────────────

@dataclass
class FontMetrics:
    """
    フォント全体に適用されるメトリクス定義。
    GlyphBuilder や FontAssembler が参照する「設計基準値」。
    """
    upm: int = 1000             # Units Per eM

    # 縦方向
    ascender: int = 800         # ベースライン上端
    descender: int = -200       # ベースライン下端（負の値）
    line_gap: int = 0           # 行と行の間の追加スペース

    # 代表高さ
    cap_height: int = 700       # 大文字の高さ
    x_height: int = 500         # 小文字の高さ

    # OS/2 ウィンドウズ用メトリクス（Webフォントで重要）
    win_ascent: Optional[int] = None
    win_descent: Optional[int] = None  # 正の値で指定（内部で-に変換）

    # イタリック・傾き
    italic_angle: float = 0.0

    def __post_init__(self) -> None:
        # win_ascent/descent を未設定なら ascender から導出
        if self.win_ascent is None:
            self.win_ascent = self.ascender
        if self.win_descent is None:
            self.win_descent = abs(self.descender)

    @property
    def em_height(self) -> int:
        return self.ascender - self.descender

    @property
    def line_height(self) -> int:
        return self.em_height + self.line_gap

    def scale_to(self, new_upm: int) -> "FontMetrics":
        """
        UPM を変更したときに全メトリクスをスケールする。
        例: 1000 UPM → 2048 UPM への変換。
        """
        ratio = new_upm / self.upm
        return FontMetrics(
            upm=new_upm,
            ascender=round(self.ascender * ratio),
            descender=round(self.descender * ratio),
            line_gap=round(self.line_gap * ratio),
            cap_height=round(self.cap_height * ratio),
            x_height=round(self.x_height * ratio),
            italic_angle=self.italic_angle,
        )

    @classmethod
    def preset_latin(cls) -> "FontMetrics":
        """欧文フォントの標準的なメトリクス。"""
        return cls(upm=1000, ascender=800, descender=-200, cap_height=700, x_height=520)

    @classmethod
    def preset_japanese(cls) -> "FontMetrics":
        """和文フォントの標準的なメトリクス（全角正方形ベース）。"""
        return cls(upm=1000, ascender=880, descender=-120, cap_height=880, x_height=880)


# ──────────────────────────────────────────────
# グリフレベルのメトリクス
# ──────────────────────────────────────────────

@dataclass
class GlyphMetrics:
    """
    1グリフに対応するメトリクス。

    advance_width:
      このグリフを描画した後、次のグリフ開始点を何ユニット進めるか。
      フォントの「幅」として最も重要な値。

    lsb (Left Side Bearing):
      グリフの左端（x=0）からアウトラインの最左点までの距離。
      正なら余白あり、負なら左にはみ出し。

    rsb (Right Side Bearing):
      advance_width - (lsb + アウトラインの幅)
      自動計算も可能（compute_rsb() を使う）。
    """
    advance_width: int = 500
    advance_height: Optional[int] = None  # 縦書き用（通常は None）
    lsb: int = 0
    rsb: Optional[int] = None           # None = 自動

    # バウンディングボックス（アウトラインの外接矩形）
    bbox_x_min: Optional[float] = None
    bbox_y_min: Optional[float] = None
    bbox_x_max: Optional[float] = None
    bbox_y_max: Optional[float] = None

    def compute_rsb(self) -> int:
        """rsb を bbox から自動計算する。"""
        if self.bbox_x_max is None:
            return 0
        outline_width = self.bbox_x_max - (self.bbox_x_min or 0)
        return self.advance_width - self.lsb - round(outline_width)

    def set_bbox(
        self,
        x_min: float, y_min: float,
        x_max: float, y_max: float,
    ) -> None:
        self.bbox_x_min = x_min
        self.bbox_y_min = y_min
        self.bbox_x_max = x_max
        self.bbox_y_max = y_max


# ──────────────────────────────────────────────
# MetricsEngine: メトリクス計算のロジック集
# ──────────────────────────────────────────────

class MetricsEngine:
    """
    フォントデザインのガイドラインから各グリフのメトリクスを計算する。

    使い方:
        fm = FontMetrics.preset_latin()
        engine = MetricsEngine(fm)

        # 大文字の標準的な幅を取得
        gm = engine.default_uppercase_metrics(char_width_ratio=0.7)
    """

    def __init__(self, font_metrics: FontMetrics) -> None:
        self.fm = font_metrics

    # ──────────────────────────────
    # グリフメトリクス生成
    # ──────────────────────────────

    def default_uppercase_metrics(self, char_width_ratio: float = 0.7) -> GlyphMetrics:
        """大文字のデフォルトメトリクス。width_ratio は cap_height に対する比率。"""
        width = round(self.fm.cap_height * char_width_ratio)
        lsb = round(width * 0.08)
        return GlyphMetrics(advance_width=width + lsb * 2, lsb=lsb)

    def default_lowercase_metrics(self, char_width_ratio: float = 0.55) -> GlyphMetrics:
        """小文字のデフォルトメトリクス。"""
        width = round(self.fm.x_height * char_width_ratio)
        lsb = round(width * 0.08)
        return GlyphMetrics(advance_width=width + lsb * 2, lsb=lsb)

    def monospace_metrics(self) -> GlyphMetrics:
        """等幅フォント用: 全グリフ同一幅。"""
        width = round(self.fm.cap_height * 0.6)
        return GlyphMetrics(advance_width=width, lsb=round(width * 0.05))

    def fullwidth_metrics(self) -> GlyphMetrics:
        """全角（和文）グリフ用メトリクス。advance = UPM。"""
        return GlyphMetrics(
            advance_width=self.fm.upm,
            lsb=0,
        )

    # ──────────────────────────────
    # 検証
    # ──────────────────────────────

    def validate(self, gm: GlyphMetrics) -> list[str]:
        """
        メトリクスの妥当性チェック。警告メッセージのリストを返す。
        空リスト = OK。
        """
        warnings: list[str] = []
        if gm.advance_width <= 0:
            warnings.append(f"advance_width が0以下です: {gm.advance_width}")
        if gm.lsb < 0:
            warnings.append(f"lsb が負です（左はみ出し）: {gm.lsb}")
        if gm.advance_width > self.fm.upm * 2:
            warnings.append(f"advance_width が UPM の2倍を超えています: {gm.advance_width}")
        return warnings