"""
variable_adjuster.py
─────────────────────
Variable Font の軸（wght, wdth, ital など）を調整し、
特定のインスタンスを静的フォントとして書き出す。

Variable Font の仕組み:
  1つの TTF ファイルに「軸」と「デルタ値」が含まれており、
  軸の値を変えると座標がそれに応じて変化する。
  例: wght=400 が Regular、wght=700 が Bold。

このモジュールでやること:
  - 軸の値を変更してインスタンス化（静的フォントに変換）
  - 軸の範囲を確認・クランプ（範囲外の値を弾く）
  - 複数インスタンスの一括生成

使う fontTools API:
  fontTools.varLib.instancer … 軸を固定して静的フォントに変換
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import io
import copy

from fontTools.ttLib import TTFont

from .font_loader import LoadedFont, AxisInfo


# ──────────────────────────────────────────────
# データ型
# ──────────────────────────────────────────────

@dataclass
class AxisValue:
    """1軸に対して設定する値。"""
    tag: str      # 例: "wght"
    value: float  # 例: 700.0


@dataclass
class InstanceResult:
    """インスタンス化の結果。"""
    axis_values: dict[str, float]  # 適用した軸値
    tt_font: TTFont                # インスタンス化済みフォント
    is_variable: bool = False      # 残りの軸がある場合は True

    def to_bytes(self, flavor: Optional[str] = None) -> bytes:
        """
        TTFont を bytes に変換する。
        flavor: None=TTF, "woff"=WOFF, "woff2"=WOFF2
        """
        buf = io.BytesIO()
        self.tt_font.flavor = flavor
        self.tt_font.save(buf)
        return buf.getvalue()


# ──────────────────────────────────────────────
# VariableAdjuster 本体
# ──────────────────────────────────────────────

class VariableAdjuster:
    """
    Variable Font の軸値を調整してインスタンスを生成する。

    使い方:
        loader = FontLoader()
        loaded = loader.load("NotoSansJP-Variable.ttf")

        adjuster = VariableAdjuster(loaded)
        print(adjuster.available_axes())
        # [Axis('wght': 100–400–900), ...]

        # wght=700 に固定したフォントを生成
        result = adjuster.instantiate({"wght": 700})
        ttf_bytes = result.to_bytes()
    """

    def __init__(self, loaded: LoadedFont) -> None:
        if not loaded.is_variable:
            raise ValueError(
                f"{loaded.full_name!r} は Variable Font ではありません。"
            )
        self.loaded = loaded
        self._axes: dict[str, AxisInfo] = {
            ax.tag: ax for ax in loaded.axes
        }

    # ──────────────────────────────
    # パブリック API
    # ──────────────────────────────

    def available_axes(self) -> list[AxisInfo]:
        """利用可能な軸一覧を返す。"""
        return list(self._axes.values())

    def get_axis(self, tag: str) -> Optional[AxisInfo]:
        """タグで軸情報を取得する。見つからなければ None。"""
        return self._axes.get(tag)

    def clamp(self, tag: str, value: float) -> float:
        """値を軸の有効範囲にクランプして返す。"""
        axis = self._axes.get(tag)
        if axis is None:
            raise ValueError(f"軸 {tag!r} は存在しません")
        return max(axis.minimum, min(axis.maximum, value))

    def instantiate(
        self,
        axis_values: dict[str, float],
        clamp: bool = True,
    ) -> InstanceResult:
        """
        指定した軸値でインスタンスを生成する。

        axis_values: {"wght": 700, "wdth": 100} のように指定。
        clamp=True なら範囲外の値を自動クランプ（デフォルト）。

        未指定の軸はデフォルト値のまま残す（部分インスタンス化）。
        全軸を指定すると静的フォントになる。
        """
        try:
            from fontTools.varLib.instancer import instantiateVariableFont
        except ImportError:
            raise ImportError(
                "fontTools.varLib.instancer が見つかりません。"
                "fonttools >= 4.0 が必要です。"
            )

        # 値のバリデーション & クランプ
        validated: dict[str, float] = {}
        for tag, value in axis_values.items():
            if tag not in self._axes:
                raise ValueError(f"軸 {tag!r} は存在しません。利用可能: {list(self._axes.keys())}")
            validated[tag] = self.clamp(tag, value) if clamp else value

        # TTFont のコピーに対してインスタンス化（元データを保護）
        tt_copy = self._copy_font()

        result_font = instantiateVariableFont(
            tt_copy,
            validated,
            inPlace=True,
            optimize=True,
            updateFontNames=True,
        )

        remaining_variable = "fvar" in result_font
        return InstanceResult(
            axis_values=validated,
            tt_font=result_font,
            is_variable=remaining_variable,
        )

    def instantiate_many(
        self,
        presets: list[dict[str, float]],
    ) -> list[InstanceResult]:
        """
        複数のインスタンスを一括生成する。

        例:
            adjuster.instantiate_many([
                {"wght": 300},
                {"wght": 400},
                {"wght": 700},
                {"wght": 900},
            ])
        """
        return [self.instantiate(preset) for preset in presets]

    def default_instance(self) -> InstanceResult:
        """全軸をデフォルト値に固定したインスタンスを返す。"""
        defaults = {tag: ax.default for tag, ax in self._axes.items()}
        return self.instantiate(defaults)

    def weight_instances(
        self,
        weights: list[float] | None = None,
    ) -> list[InstanceResult]:
        """
        wght 軸を持つフォントの代表的なウェイトを一括生成する。
        weights を省略すると [100, 300, 400, 500, 700, 900] を使用。
        """
        if "wght" not in self._axes:
            raise ValueError("このフォントには wght 軸がありません")

        if weights is None:
            weights = [100, 300, 400, 500, 700, 900]

        axis = self._axes["wght"]
        valid_weights = [
            w for w in weights
            if axis.minimum <= w <= axis.maximum
        ]

        return self.instantiate_many([{"wght": w} for w in valid_weights])

    # ──────────────────────────────
    # 内部ユーティリティ
    # ──────────────────────────────

    def _copy_font(self) -> TTFont:
        """
        TTFont を bytes 経由でコピーする。
        fontTools の TTFont はディープコピーに対応していないため。
        """
        buf = io.BytesIO()
        self.loaded.tt_font.save(buf)
        buf.seek(0)
        return TTFont(buf)