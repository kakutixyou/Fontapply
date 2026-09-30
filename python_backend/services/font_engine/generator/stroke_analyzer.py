import math
from typing import Optional
from .glyph_builder import GlyphData

class StrokeCharacteristics:
    """解析によって抽出されたフォントの特徴量"""
    estimated_stem_width: float = 10.0
    estimated_crossbar_width: float = 10.0
    has_serif: bool = False
    max_x: float = 0.0
    min_x: float = 0.0
    max_y: float = 0.0
    min_y: float = 0.0

class StrokeAnalyzer:
    """既存のグリフデータから幾何学的な特徴やストローク幅を解析・抽出するクラス"""

    @staticmethod
    def analyze_glyph(glyph_data: Optional[GlyphData]) -> StrokeCharacteristics:
        """
        GlyphDataのアウトライン（Contour）をスキャンし、
        縦棒（stem）と横棒（crossbar）の標準的な太さを推定します。
        """
        chars = StrokeCharacteristics()
        if not glyph_data or not glyph_data.contours:
            return chars

        all_points = []
        for contour in glyph_data.contours:
            for pt in contour.points:
                all_points.append((pt.x, pt.y))

        if not all_points:
            return chars

        # バウンディングボックス（文字全体のサイズ）を計測
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]
        chars.min_x, chars.max_x = min(xs), max(xs)
        chars.min_y, chars.max_y = min(ys), max(ys)

        # 簡易的なストローク幅の推定ロジック
        # 輪郭の対向する2点間の水平・垂直距離の最小値をサンプリング
        horizontal_distances = []
        vertical_distances = []

        # 計算負荷を下げるため、代表的な点の間隔を走査
        for i, p1 in enumerate(all_points[:50]):  # 上位50点程度でサンプリング
            for p2 in all_points[i+1:100]:
                dx = abs(p1[0] - p2[0])
                dy = abs(p1[1] - p2[1])

                # ほぼ水平（Y座標が近い）な関係の2点間のX距離＝縦線の太さ（Stem）の候補
                if dy < 5.0 and 5.0 < dx < 200.0:
                    horizontal_distances.append(dx)
                
                # ほぼ垂直（X座標が近い）な関係の2点間のY距離＝横線の太さ（Crossbar）の候補
                if dx < 5.0 and 5.0 < dy < 150.0:
                    vertical_distances.append(dy)

        # 最頻値に近い、最もまとまっている最小の距離を線の太さとみなす
        if horizontal_distances:
            horizontal_distances.sort()
            # 下位25%あたりの厚みを実質的なストローク幅と推定（セリフなどの飛び出しを排除するため）
            chars.estimated_stem_width = horizontal_distances[len(horizontal_distances) // 4]
        
        if vertical_distances:
            vertical_distances.sort()
            chars.estimated_crossbar_width = vertical_distances[len(vertical_distances) // 4]

        # 縦横比に極端な差がないか（SansSerifの特徴）を確認、安全弁として初期値をガード
        chars.estimated_stem_width = max(2.0, min(chars.estimated_stem_width, 150.0))
        chars.estimated_crossbar_width = max(2.0, min(chars.estimated_crossbar_width, 150.0))

        return chars
