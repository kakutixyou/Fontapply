from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any

class FontStyleProfile(BaseModel):
    """
    フォントのDNA（スタイル特性）を一元管理するクラス。
    100〜900のWeightや50〜200のWidthなどの連続値を、内部の具体的な幾何学パラメータに変形します。
    """
    # 基本軸パラメータ（連続値）
    weight: float = Field(400.0, ge=100.0, le=900.0, description="フォントの太さ (100-900)")
    width: float = Field(100.0, ge=50.0, le=200.0, description="フォントの幅 (50-200)")
    slant: float = Field(0.0, ge=-45.0, le=45.0, description="傾き角度（度数法、右傾斜がプラス）")
    
    # 内部幾何学パラメータ（プロファイル特性）
    style_type: str = Field("sans", description="フォントスタイル（Phase Aは'sans'のみ）")
    stroke_width: float = Field(10.0, description="標準的なストロークの太さ")
    corner_radius: float = Field(0.0, description="コーナーの丸み（セリフや角の処理用）")
    contrast: float = Field(1.0, description="縦線と横線の比率（1.0は均等、Sansの基本）")
    x_height_ratio: float = Field(0.7, ge=0.0, le=1.0, description="大文字に対する小文字の高さの比率")

    @field_validator("style_type")
    @classmethod
    def validate_style_type(cls, v: str) -> str:
        if v != "sans":
            raise ValueError("Phase Aでは 'sans' スタイルのみをサポートしています。")
        return v

    def model_post_init(self, __context: Any) -> None:
        """
        入力された weight や width に応じて、内部の幾何学パラメータを自動計算（補正）します。
        固定の段階値ではなく、連続値として滑らかに変形するためのロジックです。
        """
        # Weight(100-900)を基準のストローク幅にマッピング (例: 100->3.0px, 400->10.0px, 900->25.0px)
        # 線形補間を用いて連続値に対応
        self.stroke_width = 3.0 + ((self.weight - 100.0) / 800.0) * 22.0
        
        # Width(50-200)が極端に細い・太い場合、視覚的バランスを取るためにストローク幅を微調整
        # (Condensed時は線を少し細く、Expanded時は少し太くしないと不自然に見えるため)
        scale_factor = self.width / 100.0
        if scale_factor < 1.0:
            # 凝縮（Condensed）時は少しだけ線を細く補正
            self.stroke_width *= (1.0 + (scale_factor - 1.0) * 0.3)
        else:
            # 拡張（Expanded）時は少しだけ線を太く補正
            self.stroke_width *= (1.0 + (scale_factor - 1.0) * 0.15)

    @classmethod
    def create_sans_preset(cls, weight: float = 400.0, width: float = 100.0, slant: float = 0.0) -> "FontStyleProfile":
        """標準的なSans-Serifのプロファイルを生成するファクトリメソッド"""
        return cls(
            weight=weight,
            width=width,
            slant=slant,
            style_type="sans",
            contrast=1.0,  # Sansは基本的に縦横の太さが均等に近い
            x_height_ratio=0.7
        )
