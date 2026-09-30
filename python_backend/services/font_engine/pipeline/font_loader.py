"""
font_loader.py
──────────────
TTF / OTF フォントファイルを読み込み、検証し、
pipeline の他モジュールや generator に渡せる形に変換する。

主な責務:
  1. ファイル読み込み（パス / bytes 両対応）
  2. 基本バリデーション（壊れていないか・必須テーブルがあるか）
  3. メタ情報の抽出（ファミリー名・スタイル・UPM・Variable か否か）
  4. グリフ→ GlyphData への変換（generator との接続点）
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Iterator
import io

from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

# generator 側のデータ型（接続点）
from ..generator.curve_engine import Contour, Point
from ..generator.metrics_engine import FontMetrics, GlyphMetrics
from ..generator.glyph_builder import GlyphData


# ──────────────────────────────────────────────
# 読み込み結果の型
# ──────────────────────────────────────────────

@dataclass
class AxisInfo:
    """Variable Font の1軸の情報。"""
    tag: str            # 例: "wght", "wdth", "ital"
    name: str           # 人間向けの名前
    minimum: float
    default: float
    maximum: float

    def __repr__(self) -> str:
        return f"Axis({self.tag!r}: {self.minimum}–{self.default}–{self.maximum})"


@dataclass
class LoadedFont:
    """
    フォントファイルの読み込み結果。
    TTFont オブジェクトと抽出したメタ情報をまとめて保持する。
    """
    path: Optional[Path]            # None = bytes から読み込んだ場合
    tt_font: TTFont                 # fontTools オブジェクト本体

    # メタ情報（抽出済み）
    family_name: str = ""
    style_name: str = ""
    upm: int = 1000
    is_variable: bool = False
    axes: list[AxisInfo] = field(default_factory=list)
    glyph_count: int = 0
    unicode_count: int = 0          # cmap に登録された文字数
    has_cjk: bool = False           # CJK グリフを含むか（サブセット判断に使う）

    @property
    def full_name(self) -> str:
        return f"{self.family_name} {self.style_name}".strip()

    @property
    def font_metrics(self) -> FontMetrics:
        """fontTools テーブルから FontMetrics を生成して返す。"""
        hhea = self.tt_font.get("hhea")
        os2 = self.tt_font.get("OS/2")
        head = self.tt_font.get("head")

        ascender = getattr(hhea, "ascent", 800) if hhea else 800
        descender = getattr(hhea, "descent", -200) if hhea else -200
        line_gap = getattr(hhea, "lineGap", 0) if hhea else 0
        cap_height = getattr(os2, "sCapHeight", 700) if os2 else 700
        x_height = getattr(os2, "sxHeight", 500) if os2 else 500
        upm = getattr(head, "unitsPerEm", 1000) if head else 1000

        return FontMetrics(
            upm=upm,
            ascender=ascender,
            descender=descender,
            line_gap=line_gap,
            cap_height=cap_height or round(upm * 0.7),
            x_height=x_height or round(upm * 0.5),
        )


# ──────────────────────────────────────────────
# FontLoader 本体
# ──────────────────────────────────────────────

class FontLoader:
    """
    フォントファイルの読み込みと検証を担う。

    使い方:
        loader = FontLoader()

        # ファイルから
        loaded = loader.load("/path/to/font.ttf")

        # bytes から（API 経由でアップロードされた場合など）
        loaded = loader.load_bytes(font_bytes, name="MyFont.ttf")

        # メタ情報
        print(loaded.family_name, loaded.upm, loaded.is_variable)

        # グリフを GlyphData に変換（generator との接続）
        glyph_data = loader.extract_glyph(loaded, "A")
    """

    REQUIRED_TABLES = {"cmap", "glyf", "head", "hhea", "hmtx", "loca", "maxp", "post"}
    CFF_REQUIRED = {"cmap", "CFF ", "head", "hhea", "hmtx", "maxp", "post"}

    def load(self, path: str | Path) -> LoadedFont:
        """ファイルパスからフォントを読み込む。"""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"フォントファイルが見つかりません: {path}")
        if path.suffix.lower() not in {".ttf", ".otf"}:
            raise ValueError(f"対応していない拡張子: {path.suffix}（.ttf / .otf のみ）")

        try:
            tt = TTFont(str(path))
        except Exception as e:
            raise ValueError(f"フォントファイルの読み込みに失敗しました: {e}") from e

        loaded = self._build_loaded_font(tt, path=path)
        self._validate(loaded)
        return loaded

    def load_bytes(self, data: bytes, name: str = "unknown") -> LoadedFont:
        """bytes からフォントを読み込む。"""
        if not data:
            raise ValueError("空のデータは読み込めません")
        try:
            tt = TTFont(io.BytesIO(data))
        except Exception as e:
            raise ValueError(f"フォントデータの解析に失敗しました: {e}") from e

        loaded = self._build_loaded_font(tt, path=None)
        self._validate(loaded)
        return loaded

    # ──────────────────────────────
    # グリフ抽出（generator との接続点）
    # ──────────────────────────────

    def extract_glyph(
        self, loaded: LoadedFont, glyph_name: str
    ) -> Optional[GlyphData]:
        """
        TTFont からグリフを抽出して GlyphData に変換する。
        generator.GlyphModifier に渡して編集できる形式。

        CFF (OTF) フォントには対応していない（TrueType のみ）。
        対応グリフ名一覧は loaded.tt_font.getGlyphOrder() で確認。
        """
        tt = loaded.tt_font

        if "glyf" not in tt:
            # CFF フォント（OTF）はパス変換が複雑なため今回はスキップ
            return None

        if glyph_name not in tt.getGlyphOrder():
            return None

        # Unicode を逆引き
        cmap = tt.getBestCmap() or {}
        unicode_val = next(
            (cp for cp, name in cmap.items() if name == glyph_name), None
        )

        # hmtx からメトリクス取得
        hmtx = tt["hmtx"]
        advance_width, lsb = hmtx.metrics.get(glyph_name, (500, 0))

        gm = GlyphMetrics(advance_width=advance_width, lsb=lsb)

        # glyf からアウトライン取得
        contours = self._extract_contours(tt, glyph_name)

        return GlyphData(
            name=glyph_name,
            unicode=unicode_val,
            contours=contours,
            metrics=gm,
        )

    def iter_glyphs(
        self, loaded: LoadedFont, limit: int = 0
    ) -> Iterator[GlyphData]:
        """
        フォント内の全グリフを GlyphData として順番に返すジェネレーター。
        limit > 0 で取得数を制限できる（大きなフォントの処理に便利）。
        """
        order = loaded.tt_font.getGlyphOrder()
        for i, name in enumerate(order):
            if limit and i >= limit:
                break
            g = self.extract_glyph(loaded, name)
            if g is not None:
                yield g

    # ──────────────────────────────
    # 内部: メタ情報抽出
    # ──────────────────────────────

    def _build_loaded_font(
        self, tt: TTFont, path: Optional[Path]
    ) -> LoadedFont:
        family = self._get_name(tt, 1) or (path.stem if path else "Unknown")
        style = self._get_name(tt, 2) or "Regular"
        upm = tt["head"].unitsPerEm if "head" in tt else 1000

        is_variable = "fvar" in tt
        axes: list[AxisInfo] = []
        if is_variable:
            axes = self._extract_axes(tt)

        glyph_order = tt.getGlyphOrder()
        cmap = tt.getBestCmap() or {}

        # CJK 判定（U+4E00–U+9FFF が含まれるか）
        has_cjk = any(0x4E00 <= cp <= 0x9FFF for cp in cmap.keys())

        return LoadedFont(
            path=path,
            tt_font=tt,
            family_name=family,
            style_name=style,
            upm=upm,
            is_variable=is_variable,
            axes=axes,
            glyph_count=len(glyph_order),
            unicode_count=len(cmap),
            has_cjk=has_cjk,
        )

    def _validate(self, loaded: LoadedFont) -> None:
        """必須テーブルが存在するか確認する。警告のみ（例外は投げない）。"""
        tt = loaded.tt_font
        tables = set(tt.keys())

        if "CFF " in tables:
            required = self.CFF_REQUIRED
        else:
            required = self.REQUIRED_TABLES

        missing = required - tables
        if missing:
            # 警告にとどめる（壊れていても一部処理は可能）
            print(f"[FontLoader] 警告: 必須テーブルが不足 {missing} ({loaded.full_name})")

    @staticmethod
    def _get_name(tt: TTFont, name_id: int) -> str:
        """name テーブルから指定 ID の文字列を取得する。"""
        if "name" not in tt:
            return ""
        record = tt["name"].getName(name_id, 3, 1, 0x0409)  # Windows / English
        if record is None:
            record = tt["name"].getName(name_id, 1, 0, 0)   # Mac フォールバック
        if record is None:
            return ""
        try:
            return record.toUnicode()
        except Exception:
            return record.string.decode("latin-1", errors="replace")

    @staticmethod
    def _extract_axes(tt: TTFont) -> list[AxisInfo]:
        """fvar テーブルから軸情報を抽出する。"""
        axes = []
        name_table = tt.get("name")

        for axis in tt["fvar"].axes:
            tag = axis.axisTag
            # 軸名を name テーブルから取得
            name = tag
            if name_table:
                rec = name_table.getName(axis.axisNameID, 3, 1, 0x0409)
                if rec:
                    try:
                        name = rec.toUnicode()
                    except Exception:
                        pass

            axes.append(AxisInfo(
                tag=tag,
                name=name,
                minimum=axis.minValue,
                default=axis.defaultValue,
                maximum=axis.maxValue,
            ))
        return axes

    def _extract_contours(
        self, tt: TTFont, glyph_name: str
    ) -> list[Contour]:
        """
        glyf テーブルからアウトラインを Contour リストに変換する。
        RecordingPen でパスを記録し、fontTools の描画モデルを利用する。
        """
        glyph_set = tt.getGlyphSet()
        if glyph_name not in glyph_set:
            return []

        pen = RecordingPen()
        try:
            glyph_set[glyph_name].draw(pen)
        except Exception:
            return []

        return self._recording_to_contours(pen.value)

    @staticmethod
    def _recording_to_contours(recording: list) -> list[Contour]:
        """
        RecordingPen の記録を Contour リストに変換する。

        RecordingPen の記録形式:
          [("moveTo", ((x, y),)),
           ("lineTo", ((x, y),)),
           ("qCurveTo", ((cx, cy), (x, y))),
           ("curveTo", ((c1x, c1y), (c2x, c2y), (x, y))),
           ("closePath", ())]
        """
        contours: list[Contour] = []
        current: Optional[Contour] = None

        for op, args in recording:
            if op == "moveTo":
                current = Contour()
                x, y = args[0]
                current.add_on_curve(x, y)

            elif op == "lineTo":
                if current is None:
                    continue
                x, y = args[0]
                current.add_on_curve(x, y)

            elif op == "qCurveTo":
                if current is None:
                    continue
                # 2次ベジェ: 最後の点がオンカーブ、それ以外はオフカーブ
                pts = args
                for pt in pts[:-1]:
                    current.add_off_curve(pt[0], pt[1])
                current.add_on_curve(pts[-1][0], pts[-1][1])

            elif op == "curveTo":
                if current is None:
                    continue
                # 3次ベジェ: cp1, cp2 はオフカーブ、最後がオンカーブ
                pts = args
                for pt in pts[:-1]:
                    current.add_off_curve(pt[0], pt[1])
                current.add_on_curve(pts[-1][0], pts[-1][1])

            elif op in ("closePath", "endPath"):
                if current and len(current.points) >= 3:
                    contours.append(current)
                current = None

        return contours