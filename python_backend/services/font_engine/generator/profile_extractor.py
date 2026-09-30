
from typing import Optional
from ...pipeline.font_loader import LoadedFont, FontLoader
from .font_style_profile import FontStyleProfile
from .stroke_analyzer import StrokeAnalyzer

class ProfileExtractor:
    """既存のLoadedFontからフォントのDNA（FontStyleProfile）を自動抽出・生成するクラス"""

    @staticmethod
    def extract_from_existing_font(loaded_font: LoadedFont) -> FontStyleProfile:
        """
        実フォントデータ（Noto Sans等）を解析し、
        WeightやWidthなどを逆算してFontStyleProfileオブジェクトに変換します。
        """
        loader = FontLoader()
        
        # アルファベットの大文字 'I' や 'E'、'A' はストロークの太さを抽出しやすいため
        # 代表グリフとして 'I' を解析対象にする
        target_glyph = "I" if "I" in loaded_font.tt_font.getGlyphOrder() else "A"
        glyph_data = loader.extract_glyph(loaded_font, target_glyph)
        
        # ストローク解析を実行
        characteristics = StrokeAnalyzer.analyze_glyph(glyph_data)
        
        # 抽出された幹の太さ（stem width）からWeight(100-900)を逆算
        # 3.0px -> 100, 10.0px -> 400, 25.0px -> 900 の逆変換（線形補間）
        stem = characteristics.estimated_stem_width
        calculated_weight = 100.0 + ((stem - 3.0) / 22.0) * 800.0
        # 100〜900の範囲内に安全に収める
        final_weight = max(100.0, min(calculated_weight, 900.0))

        # FontMetricsのx_heightとcap_heightから比率を計算
        metrics = loaded_font.font_metrics
        x_height_ratio = 0.7
        if metrics.cap_height and metrics.x_height:
            x_height_ratio = metrics.x_height / metrics.cap_height
            x_height_ratio = max(0.1, min(x_height_ratio, 1.0))

        # イタリック/斜体判定（style_nameや内部の傾き軸から暫定取得）
        is_italic = "italic" in loaded_font.style_name.lower() or "oblique" in loaded_font.style_name.lower()
        final_slant = 12.0 if is_italic else 0.0

        # 解析結果をプロファイルに統合して返却
        profile = FontStyleProfile(
            weight=final_weight,
            width=100.0,  # 初期は標準幅（100）を仮定
            slant=final_slant,
            style_type="sans",
            stroke_width=stem,
            contrast=stem / max(1.0, characteristics.estimated_crossbar_width),
            x_height_ratio=x_height_ratio
        )
        
        return profile
