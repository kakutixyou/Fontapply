"""
kerning_engine.py
─────────────────
カーニング（文字ペア間の間隔調整）を管理する。

カーニングの種類:
  ペアカーニング … 特定の2文字ペア (A, V) に対する個別調整
  クラスカーニング … 似た形の文字グループ（例: すべての「丸い左側」）をまとめて調整
                     OpenType GPOS テーブルに格納される。ファイルサイズを大幅削減。

このモジュールが生成するデータは FontAssembler が
fonttools の kern / GPOS テーブルとして書き込む。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────
# データ型
# ──────────────────────────────────────────────

@dataclass
class KernPair:
    """
    2つのグリフ名に対するカーニング値。
    value が負 = 近づける、正 = 離す（em単位）。
    """
    left: str           # グリフ名（例: "A"）
    right: str          # グリフ名（例: "V"）
    value: int          # em単位の調整量（通常 -200〜+50 の範囲）

    def __repr__(self) -> str:
        sign = "+" if self.value >= 0 else ""
        return f"KernPair({self.left!r}, {self.right!r}, {sign}{self.value})"


@dataclass
class KernClass:
    """
    カーニングクラス。同じ振る舞いをするグリフをグループ化する。
    例: left_class["round_left"] = ["C", "G", "O", "Q"]
    """
    name: str
    glyphs: list[str] = field(default_factory=list)

    def add(self, *glyph_names: str) -> "KernClass":
        self.glyphs.extend(glyph_names)
        return self


# ──────────────────────────────────────────────
# KerningEngine
# ──────────────────────────────────────────────

class KerningEngine:
    """
    カーニングデータの構築・クエリ・エクスポートを担う。

    使い方:
        engine = KerningEngine()
        engine.add_pair("A", "V", -80)
        engine.add_pair("T", "o", -60)

        # クラスカーニング
        lc = engine.add_left_class("round_left", ["C", "G", "O", "Q"])
        rc = engine.add_right_class("round_right", ["C", "D", "G", "O"])
        engine.add_class_pair(lc, rc, -30)

        # FontAssembler に渡す
        pairs = engine.export_flat_pairs()
    """

    def __init__(self, upm: int = 1000) -> None:
        self.upm = upm
        self._pairs: dict[tuple[str, str], int] = {}
        self._left_classes: dict[str, KernClass] = {}
        self._right_classes: dict[str, KernClass] = {}
        self._class_pairs: dict[tuple[str, str], int] = {}

    # ──────────────────────────────
    # ペアカーニング
    # ──────────────────────────────

    def add_pair(self, left: str, right: str, value: int) -> None:
        """個別グリフペアのカーニングを追加・上書き。"""
        self._pairs[(left, right)] = value

    def remove_pair(self, left: str, right: str) -> None:
        self._pairs.pop((left, right), None)

    def get_pair(self, left: str, right: str) -> int:
        """
        2グリフ間のカーニング値を返す。
        ペア → クラスの優先順位で検索。見つからなければ 0。
        """
        # 1) 個別ペアが最優先
        if (left, right) in self._pairs:
            return self._pairs[(left, right)]

        # 2) クラスペアにフォールバック
        left_cls = self._find_left_class(left)
        right_cls = self._find_right_class(right)
        if left_cls and right_cls:
            key = (left_cls.name, right_cls.name)
            if key in self._class_pairs:
                return self._class_pairs[key]

        return 0

    # ──────────────────────────────
    # クラスカーニング
    # ──────────────────────────────

    def add_left_class(self, name: str, glyphs: list[str]) -> KernClass:
        cls = KernClass(name=name, glyphs=list(glyphs))
        self._left_classes[name] = cls
        return cls

    def add_right_class(self, name: str, glyphs: list[str]) -> KernClass:
        cls = KernClass(name=name, glyphs=list(glyphs))
        self._right_classes[name] = cls
        return cls

    def add_class_pair(
        self,
        left: KernClass | str,
        right: KernClass | str,
        value: int,
    ) -> None:
        left_name = left.name if isinstance(left, KernClass) else left
        right_name = right.name if isinstance(right, KernClass) else right
        self._class_pairs[(left_name, right_name)] = value

    # ──────────────────────────────
    # エクスポート
    # ──────────────────────────────

    def export_flat_pairs(self) -> list[KernPair]:
        """
        全カーニングデータをフラットな KernPair リストに展開する。
        FontAssembler の kern テーブル書き込みに使う。

        クラスペアはすべてのグリフ組み合わせに展開される。
        個別ペアはクラスペアを上書きする（OpenType の仕様通り）。
        """
        result: dict[tuple[str, str], int] = {}

        # クラスペアを先に展開（優先度低）
        for (left_cls_name, right_cls_name), value in self._class_pairs.items():
            left_cls = self._left_classes.get(left_cls_name)
            right_cls = self._right_classes.get(right_cls_name)
            if not left_cls or not right_cls:
                continue
            for lg in left_cls.glyphs:
                for rg in right_cls.glyphs:
                    result[(lg, rg)] = value

        # 個別ペアで上書き（優先度高）
        result.update(self._pairs)

        return [
            KernPair(left=k[0], right=k[1], value=v)
            for k, v in result.items()
            if v != 0
        ]

    def export_for_fonttools(self) -> dict[str, dict[str, int]]:
        """
        fonttools の font["kern"].kernTables 形式に変換。
        {left_glyph: {right_glyph: value}} のネストした辞書。
        """
        flat = self.export_flat_pairs()
        kern_dict: dict[str, dict[str, int]] = {}
        for pair in flat:
            kern_dict.setdefault(pair.left, {})[pair.right] = pair.value
        return kern_dict

    # ──────────────────────────────
    # プリセット
    # ──────────────────────────────

    @classmethod
    def latin_preset(cls, upm: int = 1000) -> "KerningEngine":
        """
        欧文フォントの典型的なカーニングペアを持つプリセット。
        数値は UPM=1000 基準。
        """
        engine = cls(upm=upm)
        scale = upm / 1000

        def sp(l: str, r: str, v: int) -> None:
            engine.add_pair(l, r, round(v * scale))

        # 大文字ペア（視覚的に隙間ができやすいもの）
        sp("A", "V", -80);  sp("A", "W", -60);  sp("A", "T", -80)
        sp("A", "Y", -80);  sp("V", "A", -80);  sp("W", "A", -60)
        sp("T", "a", -70);  sp("T", "e", -70);  sp("T", "o", -70)
        sp("T", "i", -30);  sp("T", "r", -40);  sp("F", "a", -60)
        sp("F", "e", -60);  sp("F", "o", -60);  sp("L", "T", -80)
        sp("L", "V", -80);  sp("L", "W", -80);  sp("L", "Y", -80)
        sp("P", "A", -80);  sp("V", "o", -60);  sp("V", "e", -60)
        sp("W", "o", -50);  sp("W", "e", -50);  sp("Y", "a", -80)
        sp("Y", "e", -80);  sp("Y", "o", -80);  sp("r", ".", -60)
        sp("r", ",", -60);  sp("f", ".", -30);  sp("f", ",", -30)

        # クラスカーニング（丸い文字グループ）
        lc = engine.add_left_class("round_l", ["C", "G", "O", "Q"])
        rc = engine.add_right_class("round_r", ["C", "D", "G", "O", "Q"])
        engine.add_class_pair(lc, rc, round(-20 * scale))

        return engine

    # ──────────────────────────────
    # 内部ユーティリティ
    # ──────────────────────────────

    def _find_left_class(self, glyph: str) -> Optional[KernClass]:
        for cls in self._left_classes.values():
            if glyph in cls.glyphs:
                return cls
        return None

    def _find_right_class(self, glyph: str) -> Optional[KernClass]:
        for cls in self._right_classes.values():
            if glyph in cls.glyphs:
                return cls
        return None

    def __len__(self) -> int:
        return len(self.export_flat_pairs())

    def __repr__(self) -> str:
        return (
            f"KerningEngine("
            f"{len(self._pairs)} pairs, "
            f"{len(self._class_pairs)} class pairs, "
            f"{len(self._left_classes)} left classes)"
        )