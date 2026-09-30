"""
font_assembler.py
─────────────────
GlyphData のリストを受け取り、TTF ファイルとして組み立てる。

依存ライブラリ: fonttools（pip install fonttools[woff]）

fonttools の主なテーブル:
  cmap  … Unicode → グリフ名のマッピング
  glyf  … グリフのアウトラインデータ（TrueType形式）
  head  … フォント全体のヘッダー
  hhea  … 水平メトリクスヘッダー
  hmtx  … 各グリフの advance_width と lsb
  loca  … glyf テーブルへのオフセット（自動生成）
  maxp  … 最大値テーブル（自動計算）
  name  … フォント名・著作権情報
  OS/2  … Windowsメトリクス・Unicode Range
  post  … PostScript名テーブル
  kern  … カーニングテーブル（オプション）
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import time

from .glyph_builder import GlyphData
from .metrics_engine import FontMetrics
from .kerning_engine import KerningEngine


# fonttools はオプション依存なので、インポートエラーを分かりやすく表示
try:
    from fontTools import ttLib
    from fontTools.ttLib import TTFont
    from fontTools.ttLib.tables import _n_a_m_e as nameTable
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    FONTTOOLS_AVAILABLE = True
except ImportError:
    FONTTOOLS_AVAILABLE = False


# ──────────────────────────────────────────────
# フォントメタデータ
# ──────────────────────────────────────────────

@dataclass
class FontMetadata:
    """name テーブルに書き込むフォント情報。"""
    family_name: str = "WebForge Font"
    style_name: str = "Regular"
    version: str = "1.0"
    copyright: str = ""
    designer: str = ""
    description: str = ""
    url: str = ""

    @property
    def full_name(self) -> str:
        return f"{self.family_name} {self.style_name}".strip()

    @property
    def postscript_name(self) -> str:
        """PostScript名（スペースなし）。"""
        return f"{self.family_name.replace(' ', '')}-{self.style_name.replace(' ', '')}"


# ──────────────────────────────────────────────
# FontAssembler
# ──────────────────────────────────────────────

class FontAssembler:
    """
    GlyphData のコレクションから TTF / WOFF2 フォントを生成する。

    使い方:
        assembler = FontAssembler(
            metrics=FontMetrics.preset_latin(),
            metadata=FontMetadata(family_name="MyFont"),
        )
        assembler.add_glyph(GlyphBuilder.letter_O())
        assembler.add_glyph(GlyphBuilder.letter_I())
        assembler.add_glyph(GlyphBuilder.space())

        # TTF を bytes で取得
        ttf_bytes = assembler.build_ttf()

        # ファイルに保存
        assembler.save("/path/to/MyFont.ttf")
    """

    def __init__(
        self,
        metrics: Optional[FontMetrics] = None,
        metadata: Optional[FontMetadata] = None,
        kerning: Optional[KerningEngine] = None,
    ) -> None:
        self.metrics = metrics or FontMetrics.preset_latin()
        self.metadata = metadata or FontMetadata()
        self.kerning = kerning

        self._glyphs: dict[str, GlyphData] = {}
        self._glyph_order: list[str] = [".notdef"]  # .notdef は必ず先頭

    # ──────────────────────────────
    # グリフ登録
    # ──────────────────────────────

    def add_glyph(self, glyph: GlyphData) -> "FontAssembler":
        """グリフを追加する。同名なら上書き。"""
        self._glyphs[glyph.name] = glyph
        if glyph.name not in self._glyph_order:
            self._glyph_order.append(glyph.name)
        return self

    def add_glyphs(self, glyphs: list[GlyphData]) -> "FontAssembler":
        for g in glyphs:
            self.add_glyph(g)
        return self

    @property
    def glyph_count(self) -> int:
        return len(self._glyphs)

    # ──────────────────────────────
    # ビルド
    # ──────────────────────────────

    def build_ttf(self) -> bytes:
        """
        TTF フォントを bytes として返す。
        fonttools が必要。
        """
        self._check_fonttools()
        font = self._build_font_object()
        import io
        buf = io.BytesIO()
        font.save(buf)
        return buf.getvalue()

    def save(self, path: str | Path, fmt: str = "ttf") -> Path:
        """
        フォントをファイルに保存する。
        fmt: "ttf" | "woff2"
        """
        self._check_fonttools()
        output = Path(path)
        font = self._build_font_object()
        font.save(str(output), reorderTables=False)
        return output

    # ──────────────────────────────
    # 内部: TTFont オブジェクト構築
    # ──────────────────────────────

    def _build_font_object(self) -> "TTFont":
        """fonttools の TTFont オブジェクトを構築して返す。"""
        fm = self.metrics
        meta = self.metadata

        # ── グリフオーダー確定 ──
        order = list(self._glyph_order)
        font = TTFont()
        font.setGlyphOrder(order)

        # ── head テーブル ──
        head = font["head"] = ttLib.newTable("head")
        head.tableVersion = 1.0
        head.fontRevision = 1.0
        head.checkSumAdjustment = 0
        head.magicNumber = 0x5F0F3CF5
        head.flags = 0x000B
        head.unitsPerEm = fm.upm
        import calendar
        mac_epoch_diff = calendar.timegm((1904, 1, 1, 0, 0, 0, 0, 0, 0))
        now = int(time.time()) - mac_epoch_diff
        head.created = head.modified = now
        head.macStyle = 0
        head.lowestRecPPEM = 8
        head.fontDirectionHint = 2
        head.glyphDataFormat = 0
        head.indexToLocFormat = 0
        head.xMin = head.yMin = head.xMax = head.yMax = 0

        # ── hhea テーブル ──
        hhea = font["hhea"] = ttLib.newTable("hhea")
        hhea.tableVersion = 0x00010000
        hhea.ascent = fm.ascender
        hhea.descent = fm.descender
        hhea.lineGap = fm.line_gap
        hhea.advanceWidthMax = max(
            (g.metrics.advance_width for g in self._glyphs.values()), default=fm.upm
        )
        hhea.minLeftSideBearing = 0
        hhea.minRightSideBearing = 0
        hhea.xMaxExtent = 0
        hhea.caretSlopeRise = 1
        hhea.caretSlopeRun = 0
        hhea.caretOffset = 0
        hhea.reserved0 = hhea.reserved1 = hhea.reserved2 = hhea.reserved3 = 0
        hhea.metricDataFormat = 0
        hhea.numberOfHMetrics = len(order)

        # ── maxp テーブル ──
        maxp = font["maxp"] = ttLib.newTable("maxp")
        maxp.tableVersion = 0x00010000
        maxp.numGlyphs = len(order)
        maxp.maxPoints = 0
        maxp.maxContours = 0
        maxp.maxCompositePoints = 0
        maxp.maxCompositeContours = 0
        maxp.maxZones = 2
        maxp.maxTwilightPoints = 0
        maxp.maxStorage = 0
        maxp.maxFunctionDefs = 0
        maxp.maxInstructionDefs = 0
        maxp.maxStackElements = 0
        maxp.maxSizeOfInstructions = 0
        maxp.maxComponentElements = 0
        maxp.maxComponentDepth = 0

        # ── OS/2 テーブル ──
        os2 = font["OS/2"] = ttLib.newTable("OS/2")
        os2.version = 4
        os2.xAvgCharWidth = round(fm.upm * 0.5)
        os2.usWeightClass = 400
        os2.usWidthClass = 5
        os2.fsType = 0
        os2.ySubscriptXSize = round(fm.upm * 0.65)
        os2.ySubscriptYSize = round(fm.upm * 0.60)
        os2.ySubscriptXOffset = 0
        os2.ySubscriptYOffset = round(fm.upm * 0.075)
        os2.ySuperscriptXSize = round(fm.upm * 0.65)
        os2.ySuperscriptYSize = round(fm.upm * 0.60)
        os2.ySuperscriptXOffset = 0
        os2.ySuperscriptYOffset = round(fm.upm * 0.35)
        os2.yStrikeoutSize = round(fm.upm * 0.05)
        os2.yStrikeoutPosition = round(fm.x_height * 0.3)
        os2.sFamilyClass = 0
        from fontTools.ttLib.tables.O_S_2f_2 import Panose
        panose = Panose()
        panose.bFamilyType = panose.bSerifStyle = panose.bWeight = 0
        panose.bProportion = panose.bContrast = panose.bStrokeVariation = 0
        panose.bArmStyle = panose.bLetterForm = panose.bMidline = panose.bXHeight = 0
        os2.panose = panose
        os2.ulUnicodeRange1 = 0x00000003  # Basic Latin + Latin-1
        os2.ulUnicodeRange2 = 0
        os2.ulUnicodeRange3 = 0
        os2.ulUnicodeRange4 = 0
        os2.achVendID = "WFRG"
        os2.fsSelection = 0x0040  # REGULAR
        os2.fsFirstCharIndex = 0x0020
        os2.fsLastCharIndex = 0xFFFF
        os2.sTypoAscender = fm.ascender
        os2.sTypoDescender = fm.descender
        os2.sTypoLineGap = fm.line_gap
        os2.usWinAscent = fm.win_ascent
        os2.usWinDescent = fm.win_descent
        os2.ulCodePageRange1 = 0x00000001
        os2.ulCodePageRange2 = 0
        os2.sxHeight = fm.x_height
        os2.sCapHeight = fm.cap_height
        os2.usDefaultChar = 0
        os2.usBreakChar = 0x0020
        os2.usMaxContext = 0

        # ── name テーブル ──
        font["name"] = self._build_name_table(meta)

        # ── post テーブル ──
        post = font["post"] = ttLib.newTable("post")
        post.formatType = 2.0
        post.italicAngle = fm.italic_angle
        post.underlinePosition = round(fm.descender * 0.5)
        post.underlineThickness = round(fm.upm * 0.05)
        post.isFixedPitch = 0
        post.minMemType42 = 0
        post.maxMemType42 = 0
        post.minMemType1 = 0
        post.maxMemType1 = 0
        post.mapping = {g: g for g in order}
        post.extraNames = []

        # ── cmap テーブル ──
        font["cmap"] = self._build_cmap_table()

        # ── glyf / loca / hmtx テーブル ──
        self._build_glyf_hmtx(font, order)

        # ── kern テーブル（オプション）──
        if self.kerning:
            self._build_kern_table(font)

        return font

    def _build_name_table(self, meta: FontMetadata):
        name = ttLib.newTable("name")
        name.names = []

        def add(name_id: int, string: str) -> None:
            if not string:
                return
            rec = nameTable.NameRecord()
            rec.nameID = name_id
            rec.platformID = 3       # Windows
            rec.platEncID = 1        # Unicode BMP
            rec.langID = 0x0409      # English
            rec.string = string.encode("utf-16-be")
            name.names.append(rec)

        add(0, meta.copyright)
        add(1, meta.family_name)
        add(2, meta.style_name)
        add(3, f"{meta.version};{meta.postscript_name}")
        add(4, meta.full_name)
        add(5, f"Version {meta.version}")
        add(6, meta.postscript_name)
        add(8, meta.designer)
        add(9, meta.designer)
        add(11, meta.url)
        add(13, meta.description)
        return name

    def _build_cmap_table(self):
        cmap = ttLib.newTable("cmap")
        cmap.tableVersion = 0

        fmt4 = ttLib.tables._c_m_a_p.CmapSubtable.newSubtable(4)
        fmt4.platformID = 3
        fmt4.platEncID = 1
        fmt4.language = 0
        fmt4.cmap = {
            g.unicode: g.name
            for g in self._glyphs.values()
            if g.unicode is not None
        }

        fmt0 = ttLib.tables._c_m_a_p.CmapSubtable.newSubtable(0)
        fmt0.platformID = 1
        fmt0.platEncID = 0
        fmt0.language = 0
        fmt0.cmap = {
            cp: name for cp, name in fmt4.cmap.items() if cp < 256
        }

        cmap.tables = [fmt4, fmt0]
        return cmap

    def _build_glyf_hmtx(self, font: "TTFont", order: list[str]) -> None:
        """glyf / loca / hmtx テーブルを構築する。"""
        from fontTools.ttLib.tables._g_l_y_f import Glyph as TTGlyph

        glyf = font["glyf"] = ttLib.newTable("glyf")
        glyf.glyphs = {}
        glyf.glyphOrder = order

        hmtx = font["hmtx"] = ttLib.newTable("hmtx")
        hmtx.metrics = {}

        for name in order:
            glyph_data = self._glyphs.get(name)

            if glyph_data is None or glyph_data.is_empty:
                # 空グリフ（.notdef やスペース）は TTGlyphPen で空輪郭を作る
                pen = TTGlyphPen(None)
                # 最小サイズの不可視矩形（.notdef の慣習）
                if name == ".notdef":
                    w = round(self.metrics.upm * 0.5)
                    pen.moveTo((50, 0))
                    pen.lineTo((w - 50, 0))
                    pen.lineTo((w - 50, self.metrics.cap_height))
                    pen.lineTo((50, self.metrics.cap_height))
                    pen.closePath()
                    # カウンター（内側の穴）
                    pen.moveTo((100, 50))
                    pen.lineTo((100, self.metrics.cap_height - 50))
                    pen.lineTo((w - 100, self.metrics.cap_height - 50))
                    pen.lineTo((w - 100, 50))
                    pen.closePath()
                    ttg = pen.glyph()
                    aw = w
                else:
                    ttg = TTGlyph()
                    ttg.numberOfContours = 0
                    ttg.coordinates = __import__(
                        'fontTools.ttLib.tables._g_l_y_f', fromlist=['GlyphCoordinates']
                    ).GlyphCoordinates([])
                    ttg.flags = []
                    ttg.components = []
                    aw = glyph_data.metrics.advance_width if glyph_data else round(self.metrics.upm * 0.25)

                glyf.glyphs[name] = ttg
                hmtx.metrics[name] = (aw, 0)
                continue

            # Contour → TTGlyphPen 経由で Glyph オブジェクト化
            ttg = self._contours_to_ttglyph(glyph_data)
            glyf.glyphs[name] = ttg

            gm = glyph_data.metrics
            hmtx.metrics[name] = (gm.advance_width, gm.lsb)

        font["loca"] = ttLib.newTable("loca")

    def _contours_to_ttglyph(self, glyph_data: GlyphData):
        """
        Contour リストを TTGlyphPen 経由で fontTools の Glyph に変換。

        オフカーブ点は qCurveTo でまとめて処理する。
        シンプルに全点を走査して on/off を振り分ける。
        """
        pen = TTGlyphPen(None)

        for contour in glyph_data.contours:
            if len(contour.points) < 3:
                continue

            pts = contour.points
            flags = contour.flags
            n = len(pts)
            has_off_curve = any(not f for f in flags)

            if not has_off_curve:
                # すべてオンカーブ → 直線輪郭
                pen.moveTo((round(pts[0].x), round(pts[0].y)))
                for p in pts[1:]:
                    pen.lineTo((round(p.x), round(p.y)))
                pen.closePath()
            else:
                # オフカーブ混在 → 逐次処理でセグメントを組み立てる
                # 最初のオンカーブ点を先頭に回転して処理しやすくする
                start_idx = next((i for i, f in enumerate(flags) if f), 0)
                rot_pts = pts[start_idx:] + pts[:start_idx]
                rot_flags = flags[start_idx:] + flags[:start_idx]

                pen.moveTo((round(rot_pts[0].x), round(rot_pts[0].y)))

                i = 1
                while i < n:
                    if rot_flags[i]:
                        # オンカーブ単独 → lineTo
                        pen.lineTo((round(rot_pts[i].x), round(rot_pts[i].y)))
                        i += 1
                    else:
                        # オフカーブ連続を収集してから qCurveTo
                        off_pts: list[tuple[int, int]] = []
                        while i < n and not rot_flags[i]:
                            off_pts.append((round(rot_pts[i].x), round(rot_pts[i].y)))
                            i += 1
                        # 次のオンカーブ（輪郭末尾に達したら始点で閉じる）
                        if i < n:
                            on_pt = (round(rot_pts[i].x), round(rot_pts[i].y))
                            i += 1
                        else:
                            on_pt = (round(rot_pts[0].x), round(rot_pts[0].y))
                        pen.qCurveTo(*off_pts, on_pt)

                pen.closePath()

        return pen.glyph()

    def _build_kern_table(self, font: "TTFont") -> None:
        """kern テーブルを追加する（オプション）。"""
        flat_pairs = self.kerning.export_flat_pairs()
        if not flat_pairs:
            return

        # フォントに存在するグリフ名のセット
        glyph_names = set(font.getGlyphOrder())

        # 両グリフが存在するペアのみ含める
        valid_pairs = {
            (pair.left, pair.right): pair.value
            for pair in flat_pairs
            if pair.left in glyph_names and pair.right in glyph_names
        }
        if not valid_pairs:
            return

        kern = font["kern"] = ttLib.newTable("kern")
        kern.version = 0

        subtable = ttLib.tables._k_e_r_n.KernTable_format_0()
        subtable.version    = 0
        subtable.coverage   = 0x0001
        subtable.tupleIndex = 0
        subtable.kernTable  = valid_pairs
        kern.kernTables = [subtable]

    # ──────────────────────────────
    # ユーティリティ
    # ──────────────────────────────

    @staticmethod
    def _check_fonttools() -> None:
        if not FONTTOOLS_AVAILABLE:
            raise ImportError(
                "fonttools が見つかりません。\n"
                "pip install 'fonttools[woff]' を実行してください。"
            )

    def __repr__(self) -> str:
        return (
            f"FontAssembler("
            f"family={self.metadata.family_name!r}, "
            f"glyphs={self.glyph_count})"
        )


def _make_panose():
    """PANOSE オブジェクトのフォールバック生成。"""
    class Panose:
        bFamilyType = bSerifStyle = bWeight = bProportion = 0
        bContrast = bStrokeVariation = bArmStyle = bLetterForm = 0
        bMidline = bXHeight = 0
    return Panose()