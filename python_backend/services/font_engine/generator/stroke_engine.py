"""
stroke_engine.py
────────────────
「ペンで書いたストローク」→「アウトライン（閉じた輪郭）」に変換する。

考え方:
  フォントのグリフは「黒いアウトライン」で定義される。
  しかし人間がフォントをデザインするときは「ペンの軌跡」で考える。
  StrokeEngine はその変換を担う。

入力: 中心線のパス (center_path) + 太さ (weight) + 端点スタイル
出力: Contour（外輪郭 + 内輪郭）

依存: curve_engine.py のみ（最下層に近い）
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import math
from .curve_engine import Contour, Point, CurveEngine


class CapStyle(Enum):
    BUTT = "butt"       # 直角端（線の終端でぴったり止まる）
    ROUND = "round"     # 半円端
    SQUARE = "square"   # バットより少し伸びる正方形端


class JoinStyle(Enum):
    MITER = "miter"     # 尖ったコーナー
    ROUND = "round"     # 丸いコーナー
    BEVEL = "bevel"     # 斜めカット


@dataclass
class StrokePath:
    """
    ストロークの中心線を定義する。
    points: オンカーブ点のリスト（順番通りに繋がる）
    closed: True なら閉じたパス（例: O, 0 などの閉じた文字）
    """
    points: list[Point] = field(default_factory=list)
    closed: bool = False

    def add_point(self, x: float, y: float) -> "StrokePath":
        self.points.append(Point(x, y))
        return self  # メソッドチェーン用


class StrokeEngine:
    """
    中心線パスからアウトライン輪郭を生成する。

    使い方:
        engine = StrokeEngine(weight=80, cap=CapStyle.ROUND)
        path = StrokePath().add_point(100, 0).add_point(400, 0)
        outer, inner = engine.expand(path)
        # outer, inner は Contour オブジェクト
    """

    def __init__(
        self,
        weight: float = 100,         # ストローク幅（em単位）
        cap: CapStyle = CapStyle.ROUND,
        join: JoinStyle = JoinStyle.ROUND,
        miter_limit: float = 4.0,
    ) -> None:
        self.weight = weight
        self.half = weight / 2
        self.cap = cap
        self.join = join
        self.miter_limit = miter_limit

    # ──────────────────────────────
    # パブリックAPI
    # ──────────────────────────────

    def expand(self, path: StrokePath) -> tuple[Contour, Contour]:
        """
        ストロークパスをアウトライン化する。
        返り値: (外側輪郭, 内側輪郭)
        内側輪郭は穴（カウンター）として使う。
        """
        if len(path.points) < 2:
            raise ValueError("ストロークには最低2点必要です")

        left_pts, right_pts = self._offset_path(path)

        outer = self._points_to_contour(left_pts)
        inner = self._points_to_contour(list(reversed(right_pts)))

        if not path.closed:
            self._add_caps(outer, inner, path)

        return outer, inner

    def expand_to_single_contour(self, path: StrokePath) -> Contour:
        """
        開いたパス専用: 外側→端点→内側→端点 を1つの輪郭にまとめる。
        fonttools の simple glyph に直接渡せる形式。
        """
        if path.closed:
            raise ValueError("closed パスには expand() を使ってください")

        left_pts, right_pts = self._offset_path(path)
        c = Contour()

        # 外側（左側オフセット）を前進方向に追加
        for p in left_pts:
            c.add_on_curve(p.x, p.y)

        # 終端キャップ
        self._append_cap(c, left_pts[-1], right_pts[-1], path.points[-1], path.points[-2], end=True)

        # 内側（右側オフセット）を逆方向に追加
        for p in reversed(right_pts):
            c.add_on_curve(p.x, p.y)

        # 始端キャップ
        self._append_cap(c, right_pts[0], left_pts[0], path.points[0], path.points[1], end=False)

        return c

    # ──────────────────────────────
    # 内部実装
    # ──────────────────────────────

    def _offset_path(
        self, path: StrokePath
    ) -> tuple[list[Point], list[Point]]:
        """中心線の左右にオフセット点列を生成する。"""
        pts = path.points
        left: list[Point] = []
        right: list[Point] = []

        for i, pt in enumerate(pts):
            # 各点での接線方向を計算
            if i == 0:
                tangent = self._tangent(pts[0], pts[1])
            elif i == len(pts) - 1:
                tangent = self._tangent(pts[-2], pts[-1])
            else:
                # 前後の平均で滑らかなジョイン
                t1 = self._tangent(pts[i - 1], pts[i])
                t2 = self._tangent(pts[i], pts[i + 1])
                tangent = self._normalize(Point(t1.x + t2.x, t1.y + t2.y))

            # 法線方向（接線を90度回転）
            normal = Point(-tangent.y, tangent.x)

            left.append(Point(
                pt.x + normal.x * self.half,
                pt.y + normal.y * self.half,
            ))
            right.append(Point(
                pt.x - normal.x * self.half,
                pt.y - normal.y * self.half,
            ))

        return left, right

    def _points_to_contour(self, pts: list[Point]) -> Contour:
        c = Contour()
        for p in pts:
            c.add_on_curve(p.x, p.y)
        return c

    def _add_caps(
        self, outer: Contour, inner: Contour, path: StrokePath
    ) -> None:
        """開きパスの端点にキャップを追加（始端・終端）。"""
        # 始端
        tangent_start = self._tangent(path.points[0], path.points[1])
        # 終端
        tangent_end = self._tangent(path.points[-2], path.points[-1])

        if self.cap == CapStyle.ROUND:
            self._add_round_cap(outer, path.points[0], tangent_start, start=True)
            self._add_round_cap(inner, path.points[-1], tangent_end, start=False)
        elif self.cap == CapStyle.SQUARE:
            self._add_square_cap(outer, path.points[0], tangent_start, start=True)
            self._add_square_cap(inner, path.points[-1], tangent_end, start=False)
        # BUTT: キャップなし（そのまま直線で繋ぐ）

    def _append_cap(
        self,
        contour: Contour,
        from_pt: Point,
        to_pt: Point,
        center: Point,
        prev_center: Point,
        end: bool,
    ) -> None:
        """expand_to_single_contour 用のキャップ追加。"""
        if self.cap == CapStyle.ROUND:
            arc_pts = CurveEngine.arc(
                center.x, center.y, self.half,
                self._angle(from_pt, center),
                self._angle(to_pt, center),
                n_segs=4,
            )
            for p in arc_pts[1:-1]:
                contour.add_on_curve(p.x, p.y)
        elif self.cap == CapStyle.SQUARE:
            tangent = self._tangent(prev_center, center) if end else self._tangent(center, prev_center)
            ext = Point(tangent.x * self.half, tangent.y * self.half)
            contour.add_on_curve(from_pt.x + ext.x, from_pt.y + ext.y)
            contour.add_on_curve(to_pt.x + ext.x, to_pt.y + ext.y)
        # BUTT: 何も追加しない

    # ──────────────────────────────
    # ベクトルユーティリティ
    # ──────────────────────────────

    @staticmethod
    def _tangent(a: Point, b: Point) -> Point:
        return StrokeEngine._normalize(Point(b.x - a.x, b.y - a.y))

    @staticmethod
    def _normalize(v: Point) -> Point:
        length = math.hypot(v.x, v.y)
        if length < 1e-9:
            return Point(1.0, 0.0)
        return Point(v.x / length, v.y / length)

    @staticmethod
    def _angle(from_pt: Point, center: Point) -> float:
        return math.degrees(math.atan2(from_pt.y - center.y, from_pt.x - center.x))

    def _add_round_cap(
        self, contour: Contour, center: Point, tangent: Point, start: bool
    ) -> None:
        """ラウンドキャップを輪郭に追加（簡略化版）。"""
        normal = Point(-tangent.y, tangent.x)
        if start:
            pts = CurveEngine.arc(center.x, center.y, self.half, 90, 270, n_segs=4)
        else:
            pts = CurveEngine.arc(center.x, center.y, self.half, -90, 90, n_segs=4)
        for p in pts:
            contour.add_on_curve(p.x, p.y)

    def _add_square_cap(
        self, contour: Contour, center: Point, tangent: Point, start: bool
    ) -> None:
        sign = -1 if start else 1
        ext = Point(tangent.x * sign * self.half, tangent.y * sign * self.half)
        normal = Point(-tangent.y * self.half, tangent.x * self.half)
        contour.add_on_curve(center.x - normal.x + ext.x, center.y - normal.y + ext.y)
        contour.add_on_curve(center.x + normal.x + ext.x, center.y + normal.y + ext.y)