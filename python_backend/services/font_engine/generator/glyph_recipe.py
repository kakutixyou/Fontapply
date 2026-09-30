from pydantic import BaseModel, Field
from typing import List, Dict, Tuple, Optional

class StrokePart(BaseModel):
    """グリフを構成する部品（ストローク単位）の定義"""
    part_type: str = Field(..., description="部品の種類 ('stem', 'crossbar', 'bowl', 'terminal')")
    base_points: List[Tuple[float, float]] = Field(..., description="部品の基準となる骨格座標(x, y)のリスト")
    role: Optional[str] = Field(None, description="役割（例: 'left_stem', 'center_bar'）")

class GlyphRecipe(BaseModel):
    """1つの文字（グリフ）の設計図"""
    glyph_name: str = Field(..., description="対応する文字（例: 'A', 'b', '7'）")
    parts: List[StrokePart] = Field(default_factory=list, description="構成する部品のリスト")
    anchors: Dict[str, Tuple[float, float]] = Field(
        default_factory=dict, 
        description="位置合わせの基準点（将来のマルチグリフ/マーク合成用）"
    )

class GlyphRecipeBook(BaseModel):
    """複数グリフのレシピを管理するデータベース"""
    recipes: Dict[str, GlyphRecipe] = Field(default_factory=dict)

    def get_recipe(self, glyph_name: str) -> Optional[GlyphRecipe]:
        return self.recipes.get(glyph_name)

    def register_recipe(self, recipe: GlyphRecipe) -> None:
        self.recipes[recipe.glyph_name] = recipe
