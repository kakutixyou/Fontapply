"""
curve_engine.py
───────────────
ベジェ曲線のプリミティブ生成。
generator 内の他モジュール（stroke_engine, glyph_builder）が使う最下層。

fonttools の座標系:
  - origin (0, 0) = ベースライン左端
  - Y 上方向が正
  - 単位は em ユニット（通常 UPM=1000）
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Sequence
import math


# ──────────────────────────────────────────────
# データ型
# ──────────────────────────────────────────────

@dataclass
class Point:
    
    x: float
    y: float
    id: str = ""
    def __add__(self, other: "Point") -> "Point":
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Point") -> "Point":
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Point":
        return Point(self.x * scalar, self.y * scalar)

    def lerp(self, other: "Point", t: float) -> "Point":
        """線形補間。t=0 で self、t=1 で other。"""
        return Point(
            self.x + (other.x - self.x) * t,
            self.y + (other.y - self.y) * t,
        )

    def distance(self, other: "Point") -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


@dataclass
class CubicSegment:
    """3次ベジェ曲線の1セグメント（4点: start, cp1, cp2, end）。"""
    start: Point
    cp1: Point     # コントロールポイント 1
    cp2: Point     # コントロールポイント 2
    end: Point

    def point_at(self, t: float) -> Point:
        """t ∈ [0,1] での座標。"""
        u = 1 - t
        return Point(
            u**3 * self.start.x
            + 3 * u**2 * t * self.cp1.x
            + 3 * u * t**2 * self.cp2.x
            + t**3 * self.end.x,
            u**3 * self.start.y
            + 3 * u**2 * t * self.cp1.y
            + 3 * u * t**2 * self.cp2.y
            + t**3 * self.end.y,
        )

    def to_quadratic_approx(self, n_segments: int = 4) -> list["QuadSegment"]:
        """
        3次ベジェを2次ベジェ列に近似変換。
        TrueType は2次ベジェのみ使うため、TTF出力前に必要。
        n_segments を増やすと精度が上がる（通常 4〜8 で十分）。
        """
        # 均等にサンプリングして QuadSegment で近似
        result: list[QuadSegment] = []
        pts = [self.point_at(i / n_segments) for i in range(n_segments + 1)]
        for i in range(n_segments):
            p0, p2 = pts[i], pts[i + 1]
            # 中点コントロールポイント（直線近似の中間）
            cp = Point((p0.x + p2.x) / 2, (p0.y + p2.y) / 2)
            result.append(QuadSegment(p0, cp, p2))
        return result


@dataclass
class QuadSegment:
    """2次ベジェ曲線の1セグメント（3点: start, cp, end）。TrueType用。"""
    start: Point
    cp: Point
    end: Point

    def point_at(self, t: float) -> Point:
        u = 1 - t
        return Point(
            u**2 * self.start.x + 2 * u * t * self.cp.x + t**2 * self.end.x,
            u**2 * self.start.y + 2 * u * t * self.cp.y + t**2 * self.end.y,
        )


@dataclass
class Contour:
    """
    グリフを構成する1閉じた輪郭。
    points と flags のペアを fonttools の PointPen 形式で保持する。

    flags:
      True  = オンカーブ点（輪郭上の点）
      False = オフカーブ点（コントロールポイント）
    """
    id: str = ""
    points: list[Point] = field(default_factory=list)
    flags: list[bool] = field(default_factory=list)  # True=on-curve

    def add_on_curve(self, x: float, y: float) -> None:
        self.points.append(Point(x, y))
        self.flags.append(True)

    def add_off_curve(self, x: float, y: float) -> None:
        self.points.append(Point(x, y))
        self.flags.append(False)

    def to_fonttools_format(self) -> list[tuple[tuple[float, float], bool, dict]]:
        """
        fonttools PointPen.addComponent 互換の形式に変換。
        返り値: [(座標, on_curve, {}), ...]
        """
        return [
            (p.as_tuple(), flag, {})
            for p, flag in zip(self.points, self.flags)
        ]


# ──────────────────────────────────────────────
# プリミティブ生成ユーティリティ
# ──────────────────────────────────────────────

class CurveEngine:
    """
    よく使う形状を Contour として生成するファクトリ。
    glyph_builder.py と stroke_engine.py から呼ばれる。
    """

    @staticmethod
    def circle(cx: float, cy: float, r: float) -> Contour:
        """
        円をベジェ近似で生成（4つの3次ベジェ → 2次変換）。
        k = 0.5522847... は円の4分割ベジェ近似定数。
        """
        k = 0.5522847498
        c = Contour()

        # 上 → 右 → 下 → 左 の順で4象限
        # （fonttools は反時計回りが外輪郭）
        points_on = [
            Point(cx, cy + r),   # top
            Point(cx + r, cy),   # right
            Point(cx, cy - r),   # bottom
            Point(cx - r, cy),   # left
        ]
        offsets = [
            (Point(cx + r * k, cy + r), Point(cx + r, cy + r * k)),
            (Point(cx + r, cy - r * k), Point(cx + r * k, cy - r)),
            (Point(cx - r * k, cy - r), Point(cx - r, cy - r * k)),
            (Point(cx - r, cy + r * k), Point(cx - r * k, cy + r)),
        ]

        for i, (on_pt, (cp1, cp2)) in enumerate(zip(points_on, offsets)):
            c.add_on_curve(on_pt.x, on_pt.y)
            c.add_off_curve(cp1.x, cp1.y)
            c.add_off_curve(cp2.x, cp2.y)

        return c

    @staticmethod
    def rectangle(x: float, y: float, w: float, h: float) -> Contour:
        """矩形（反時計回り）。"""
        c = Contour()
        c.add_on_curve(x, y)
        c.add_on_curve(x + w, y)
        c.add_on_curve(x + w, y + h)
        c.add_on_curve(x, y + h)
        return c

    @staticmethod
    def rounded_rectangle(
        x: float, y: float, w: float, h: float, r: float
    ) -> Contour:
        """
        角丸矩形。r はコーナー半径（em単位）。
        r > min(w,h)/2 の場合は自動的にクランプ。
        """
        r = min(r, w / 2, h / 2)
        k = 0.5522847498 * r
        c = Contour()

        # 下辺左端から反時計回り
        c.add_on_curve(x + r, y)
        c.add_on_curve(x + w - r, y)
        c.add_off_curve(x + w - r + k, y)
        c.add_off_curve(x + w, y + r - k)
        c.add_on_curve(x + w, y + r)
        c.add_on_curve(x + w, y + h - r)
        c.add_off_curve(x + w, y + h - r + k)
        c.add_off_curve(x + w - r + k, y + h)
        c.add_on_curve(x + w - r, y + h)
        c.add_on_curve(x + r, y + h)
        c.add_off_curve(x + r - k, y + h)
        c.add_off_curve(x, y + h - r + k)
        c.add_on_curve(x, y + h - r)
        c.add_on_curve(x, y + r)
        c.add_off_curve(x, y + r - k)
        c.add_off_curve(x + r - k, y)

        return c

    @staticmethod
    def arc(
        cx: float, cy: float, r: float,
        start_angle_deg: float, end_angle_deg: float,
        n_segs: int = 4,
    ) -> list[Point]:
        """
        円弧のオンカーブ点列を返す（Contour には変換しない）。
        stroke_engine.py がストロークパスを作るときに利用。
        """
        start = math.radians(start_angle_deg)
        end = math.radians(end_angle_deg)
        pts = []
        for i in range(n_segs + 1):
            t = start + (end - start) * i / n_segs
            pts.append(Point(cx + r * math.cos(t), cy + r * math.sin(t)))
        return pts

    @staticmethod
    def blend_contours(a: Contour, b: Contour, t: float) -> Contour:
        """
        2つの輪郭を補間（モーフィング用）。
        a と b は同数・同トポロジーの点を持つ必要がある。
        """
        if len(a.points) != len(b.points):
            raise ValueError(
                f"輪郭の点数が一致しません: {len(a.points)} vs {len(b.points)}"
            )
        c = Contour()
        for pa, pb, flag in zip(a.points, b.points, a.flags):
            blended = pa.lerp(pb, t)
            c.points.append(blended)
            c.flags.append(flag)
        return c