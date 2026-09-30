"""
glyph_modifier.py
─────────────────
既存グリフのパスを編集・加工する。

【なぜ generator 層に置くか】
  パス操作（変形・合成・分解）はグリフ設計と同じレイヤー。
  pipeline/ は「フォントファイル全体を変換」するが、
  ここは「1グリフの形を変える」設計領域。
  → generator/ に寄せることで責務が明確になる。

主な用途:
  - 既存 TTF から取り込んだグリフを調整する
  - GlyphBuilder で作ったグリフに後処理を加える
  - アウトラインの簡略化・ノーマライズ
"""

from __future__ import annotations
from typing import Callable
from .curve_engine import Contour, Point
from .glyph_builder import GlyphData, GlyphMetrics


class GlyphModifier:
    """
    GlyphData を受け取り、変形済みの GlyphData を返す変換器。
    イミュータブルに設計（元データを壊さない）。

    使い方:
        mod = GlyphModifier(glyph_data)
        result = (mod
            .translate(dx=50, dy=0)
            .scale_uniform(1.1)
            .remove_overlap()
            .build())
    """

    def __init__(self, glyph: GlyphData) -> None:
        # ディープコピーして元データを保護
        self._name = glyph.name
        self._unicode = glyph.unicode
        self._metrics = GlyphMetrics(
            advance_width=glyph.metrics.advance_width,
            lsb=glyph.metrics.lsb,
        )
        self._contours: list[Contour] = [
            _copy_contour(c) for c in glyph.contours
        ]

    # ──────────────────────────────
    # 幾何変換
    # ──────────────────────────────

    def translate(self, dx: float, dy: float) -> "GlyphModifier":
        """全輪郭を (dx, dy) だけ平行移動。"""
        for c in self._contours:
            c.points = [Point(p.x + dx, p.y + dy) for p in c.points]
        return self

    def scale(self, sx: float, sy: float, cx: float = 0, cy: float = 0) -> "GlyphModifier":
        """
        (cx, cy) を中心にスケール。
        デフォルト原点 (0,0) = ベースライン左端。
        """
        for c in self._contours:
            c.points = [
                Point((p.x - cx) * sx + cx, (p.y - cy) * sy + cy)
                for p in c.points
            ]
        # advance_width もスケール
        self._metrics.advance_width = round(self._metrics.advance_width * sx)
        self._metrics.lsb = round(self._metrics.lsb * sx)
        return self

    def scale_uniform(self, factor: float) -> "GlyphModifier":
        return self.scale(factor, factor)

    def rotate(self, angle_deg: float, cx: float = 0, cy: float = 0) -> "GlyphModifier":
        """
        (cx, cy) を中心に時計回り回転（degree）。
        注: 回転後は advance_width の更新が必要な場合がある。
        """
        import math
        rad = math.radians(angle_deg)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        for c in self._contours:
            new_pts = []
            for p in c.points:
                rx = p.x - cx
                ry = p.y - cy
                new_pts.append(Point(
                    rx * cos_a - ry * sin_a + cx,
                    rx * sin_a + ry * cos_a + cy,
                ))
            c.points = new_pts
        return self

    def flip_horizontal(self) -> "GlyphModifier":
        """左右反転（advance_width 内で反転）。"""
        aw = self._metrics.advance_width
        for c in self._contours:
            c.points = [Point(aw - p.x, p.y) for p in c.points]
            c.points.reverse()
            c.flags.reverse()
        return self

    def flip_vertical(self, axis_y: float | None = None) -> "GlyphModifier":
        """
        上下反転。axis_y を省略するとグリフの垂直中心で反転。
        """
        if axis_y is None:
            all_y = [p.y for c in self._contours for p in c.points]
            axis_y = (max(all_y) + min(all_y)) / 2 if all_y else 0
        for c in self._contours:
            c.points = [Point(p.x, 2 * axis_y - p.y) for p in c.points]
            c.points.reverse()
            c.flags.reverse()
        return self

    # ──────────────────────────────
    # アウトライン処理
    # ──────────────────────────────

    def remove_short_contours(self, min_points: int = 3) -> "GlyphModifier":
        """
        点数が少なすぎる（壊れた）輪郭を除去する。
        最低 3 点ないと有効な輪郭にならない。
        """
        self._contours = [c for c in self._contours if len(c.points) >= min_points]
        return self

    def apply_to_each_contour(
        self, func: Callable[[Contour], Contour]
    ) -> "GlyphModifier":
        """
        各輪郭に任意の変換関数を適用する。
        カスタム処理を差し込む拡張ポイント。

        例:
            def snap_to_grid(c):
                c.points = [Point(round(p.x/4)*4, round(p.y/4)*4) for p in c.points]
                return c
            mod.apply_to_each_contour(snap_to_grid)
        """
        self._contours = [func(c) for c in self._contours]
        return self

    def snap_to_grid(self, grid: int = 4) -> "GlyphModifier":
        """
        全点座標をグリッドにスナップ（ヒンティング改善）。
        grid=4 → 4 em ユニット単位に丸める。
        """
        def snap(c: Contour) -> Contour:
            c.points = [
                Point(round(p.x / grid) * grid, round(p.y / grid) * grid)
                for p in c.points
            ]
            return c
        return self.apply_to_each_contour(snap)

    def round_coordinates(self) -> "GlyphModifier":
        """全座標を整数に丸める（TTF は整数座標のみ）。"""
        def rnd(c: Contour) -> Contour:
            c.points = [Point(round(p.x), round(p.y)) for p in c.points]
            return c
        return self.apply_to_each_contour(rnd)

    # ──────────────────────────────
    # メトリクス操作
    # ──────────────────────────────

    def set_advance(self, width: int) -> "GlyphModifier":
        self._metrics.advance_width = width
        return self

    def add_sidebearing(self, left: int = 0, right: int = 0) -> "GlyphModifier":
        """
        サイドベアリングを追加する。
        left > 0 → グリフ全体を右に移動し、advance を拡げる。
        right > 0 → advance だけ拡げる。
        """
        if left:
            self.translate(left, 0)
            self._metrics.lsb += left
            self._metrics.advance_width += left
        if right:
            self._metrics.advance_width += right
        return self

    # ──────────────────────────────
    # 完成
    # ──────────────────────────────

    def build(self) -> GlyphData:
        """変換済みの GlyphData を返す。"""
        return GlyphData(
            name=self._name,
            unicode=self._unicode,
            contours=self._contours,
            metrics=self._metrics,
        )

    def build_as(self, name: str, unicode: int | None = None) -> GlyphData:
        """別名・別コードポイントで出力（派生グリフ生成に使う）。"""
        self._name = name
        self._unicode = unicode
        return self.build()


# ──────────────────────────────────────────────
# ユーティリティ
# ──────────────────────────────────────────────

def _copy_contour(c: Contour) -> Contour:
    new = Contour()
    new.points = [Point(p.x, p.y) for p in c.points]
    new.flags = list(c.flags)
    return new