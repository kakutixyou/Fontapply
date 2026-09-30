"""
glyph_builder_full.py

A–Z を 3つの幾何学ファミリー関数 + パラメータ辞書で生成。
個別定義は一切なし。

ファミリー:
  build_from_stems()     — 縦棒・横棒の組み合わせ  (I H F E L T)
  build_from_bowl()      — 楕円ベースの曲線       (O Q C G D P B R U J)
  build_from_diagonals() — 斜線の組み合わせ        (A V W M N K X Y Z)

出力スキーマ（IPC / FastAPI で使う既存フォーマットと同じ）:
  { char, unicode, width, contours: [{ id, closed, points: [{ id, x, y, type,
    handle_in, handle_out }] }] }

座標系: em=1000u, baseline=0, cap-height=680u
"""

from __future__ import annotations
import math
from typing import Any

# ── 型エイリアス ──────────────────────────────────────────────────────────────
Pt      = dict[str, Any]
Contour = dict[str, Any]
GlyphDict = dict[str, Any]

# ── 共有定数 ──────────────────────────────────────────────────────────────────
CAP_H   = 680    # cap-height
STEM_W  = 88     # 標準縦棒幅
ARM_H   = 80     # 横棒の高さ
CROSS_Y = 340    # H, A などのクロスバー y 中心
KAPPA   = 0.5523 # ベジェ円弧近似定数


# ═══════════════════════════════════════════════════════════════════════════════
# 低レベルヘルパー
# ═══════════════════════════════════════════════════════════════════════════════

def corner(pid: str, x: float, y: float) -> Pt:
    return {"id": pid, "x": round(x, 1), "y": round(y, 1),
            "type": "corner", "handle_in": None, "handle_out": None}

def smooth(pid: str, x: float, y: float,
           hi: tuple | None = None, ho: tuple | None = None) -> Pt:
    return {
        "id": pid, "x": round(x, 1), "y": round(y, 1), "type": "smooth",
        "handle_in":  {"x": round(hi[0],1), "y": round(hi[1],1)} if hi else None,
        "handle_out": {"x": round(ho[0],1), "y": round(ho[1],1)} if ho else None,
    }

def make_contour(cid: str, points: list[Pt], closed: bool = True) -> Contour:
    return {"id": cid, "closed": closed, "points": points}

def make_glyph(char: str, width: int, contours: list[Contour]) -> GlyphDict:
    return {"char": char, "unicode": f"{ord(char):04X}",
            "width": width, "contours": contours}

def rect_contour(cid: str, x: float, y: float,
                 w: float, h: float) -> Contour:
    """矩形を時計回りコーナーポイントで生成（底辺=0=baseline）"""
    return make_contour(cid, [
        corner("p0", x,     y),
        corner("p1", x + w, y),
        corner("p2", x + w, y + h),
        corner("p3", x,     y + h),
    ])

def ellipse_contour(cid: str, cx: float, cy: float,
                    rx: float, ry: float) -> Contour:
    """4点ベジェ楕円（右→下→左→上）"""
    kx, ky = rx * KAPPA, ry * KAPPA
    return make_contour(cid, [
        smooth("p0", cx+rx, cy,    hi=(cx+rx, cy-ky), ho=(cx+rx, cy+ky)),
        smooth("p1", cx,    cy+ry, hi=(cx+kx, cy+ry), ho=(cx-kx, cy+ry)),
        smooth("p2", cx-rx, cy,    hi=(cx-rx, cy+ky), ho=(cx-rx, cy-ky)),
        smooth("p3", cx,    cy-ry, hi=(cx-kx, cy-ry), ho=(cx+kx, cy-ry)),
    ])

def half_bowl_right(cid: str, cx: float, cy: float,
                    rx: float, ry: float,
                    stem_x: float, y0: float, y1: float) -> Contour:
    """
    右半分の楕円ボウル + 左縦棒を繋ぐコンター。
    D, P, B, R の右側に使う。
    stem_x  : 縦棒の右辺x
    y0, y1  : ボウルが接続する上下のy（フォントユニット）
    """
    kx, ky = rx * KAPPA, ry * KAPPA
    return make_contour(cid, [
        corner("p0", stem_x, y1),
        smooth("p1", cx,     cy + ry, hi=(cx + kx, cy + ry), ho=(cx - kx, cy + ry)),
        smooth("p2", cx + rx, cy,     hi=(cx + rx, cy + ky), ho=(cx + rx, cy - ky)),
        smooth("p3", cx,     cy - ry, hi=(cx - kx, cy - ry), ho=(cx + kx, cy - ry)),
        corner("p4", stem_x, y0),
    ])


# ═══════════════════════════════════════════════════════════════════════════════
# ファミリー 1: 縦棒・横棒ベース (I H F E L T K)
# ═══════════════════════════════════════════════════════════════════════════════

def build_from_stems(
    char: str,
    width: int,
    *,
    left_stem:  bool = True,
    right_stem: bool = False,
    top_arm:    bool = False,    # 最上部の横棒
    mid_arm:    bool = False,    # 中間横棒
    bot_arm:    bool = False,    # 最下部の横棒（L の底辺など）
    top_full:   bool = False,    # 幅いっぱいの上横棒 (T, F, E, H)
    bot_full:   bool = False,    # 幅いっぱいの下横棒
    mid_full:   bool = False,    # 幅いっぱいの中横棒 (H)
    mid_y:      float = CROSS_Y, # 中横棒の中心y
    lsb:        int   = 80,
    stem_w:     int   = STEM_W,
    arm_h:      int   = ARM_H,
    arm_len:    int   = 0,       # 0=auto (width-lsb*2-stem_w まで)
    # K 専用: 右側対角線 2本
    k_diag:     bool  = False,
) -> GlyphDict:
    contours: list[Contour] = []
    cid = 0

    rsb = width - lsb - stem_w
    if not right_stem:
        rsb_x = width - lsb
    else:
        rsb_x = width - lsb - stem_w

    arm_right = arm_len if arm_len > 0 else (width - lsb)

    # 左縦棒
    if left_stem:
        contours.append(rect_contour(f"c{cid}", lsb, 0, stem_w, CAP_H)); cid += 1

    # 右縦棒（H など）
    if right_stem:
        contours.append(rect_contour(f"c{cid}", width - lsb - stem_w, 0, stem_w, CAP_H)); cid += 1

    # 上横棒（幅いっぱい: T F E H）
    if top_full:
        contours.append(rect_contour(f"c{cid}", lsb, CAP_H - arm_h, width - lsb*2, arm_h)); cid += 1

    # 上腕（片方だけ: F E）
    if top_arm:
        contours.append(rect_contour(f"c{cid}", lsb + stem_w, CAP_H - arm_h, arm_right - lsb - stem_w, arm_h)); cid += 1

    # 中横棒（幅いっぱい: H）
    if mid_full:
        cb_h = arm_h * 0.9
        contours.append(rect_contour(f"c{cid}", lsb + stem_w,
                                     mid_y - cb_h/2, width - (lsb+stem_w)*2, cb_h)); cid += 1

    # 中腕（F E など）
    if mid_arm:
        cb_h = arm_h * 0.85
        contours.append(rect_contour(f"c{cid}", lsb + stem_w,
                                     mid_y - cb_h/2, arm_right - lsb - stem_w, cb_h)); cid += 1

    # 底辺横棒（L）
    if bot_full:
        contours.append(rect_contour(f"c{cid}", lsb, 0, width - lsb*2, arm_h)); cid += 1

    if bot_arm:
        contours.append(rect_contour(f"c{cid}", lsb, 0, arm_right - lsb, arm_h)); cid += 1

    # K 専用: 右上と右下の対角バー
    if k_diag:
        sw = stem_w * 0.85
        # 上の斜め腕 (stem 右辺 → 右上角)
        rx0 = lsb + stem_w
        rx1 = width - lsb
        # 上腕
        contours.append(make_contour(f"c{cid}", [
            corner("p0", rx0, mid_y),
            corner("p1", rx0 + (rx1-rx0)*0.06, mid_y),
            corner("p2", rx1, CAP_H),
            corner("p3", rx1 - sw, CAP_H),
        ])); cid += 1
        # 下腕
        contours.append(make_contour(f"c{cid}", [
            corner("p0", rx0, mid_y),
            corner("p1", rx1, 0),
            corner("p2", rx1 - sw, 0),
            corner("p3", rx0 + sw*0.3, mid_y),
        ])); cid += 1

    return make_glyph(char, width, contours)


# ═══════════════════════════════════════════════════════════════════════════════
# ファミリー 2: 楕円・ボウルベース (O Q C G D P B R U J)
# ═══════════════════════════════════════════════════════════════════════════════

def build_from_bowl(
    char: str,
    width: int,
    *,
    closed: bool    = True,   # O=True, C/G=False
    has_stem: bool  = False,  # D P B R = True
    stem_side: str  = "left", # 縦棒の側 (always left for caps)
    double_bowl: bool = False, # B = 上下2つのボウル
    has_tail: bool  = False,  # Q の尾
    has_bar:  bool  = False,  # G の内部バー
    open_angle: float = 30,   # C/G/S の開口角度 (degrees from right)
    lsb: int = 60,
    stem_w: int = STEM_W,
) -> GlyphDict:
    contours: list[Contour] = []
    cid = 0

    cx = width / 2
    cy = CAP_H / 2  # = 340

    if not has_stem:
        # 純粋な楕円 (O)
        rx = width/2 - lsb
        ry = CAP_H/2

        if closed:
            # 外楕円
            contours.append(ellipse_contour(f"c{cid}", cx, cy, rx, ry)); cid += 1
            # 内楕円 (カウンター)
            inner = stem_w
            contours.append(ellipse_contour(f"c{cid}", cx, cy, rx - inner, ry - inner)); cid += 1

        else:
            # C / G: 右側を切り取った楕円
            ang = math.radians(open_angle)
            rx_o, ry_o = rx, ry
            cut_y_top = cy - ry_o * math.sin(math.pi/2 - ang)
            cut_y_bot = cy + ry_o * math.sin(math.pi/2 - ang)
            cut_x     = cx + rx_o * math.cos(ang)

            # 外輪郭（右を開口）
            k_rx, k_ry = rx_o * KAPPA, ry_o * KAPPA
            pts = [
                corner("p0", cut_x, cut_y_top),
                smooth("p1", cx, cy - ry_o, hi=(cx+k_rx, cy-ry_o), ho=(cx-k_rx, cy-ry_o)),
                smooth("p2", cx - rx_o, cy, hi=(cx-rx_o, cy+k_ry), ho=(cx-rx_o, cy-k_ry)),
                smooth("p3", cx, cy + ry_o, hi=(cx-k_rx, cy+ry_o), ho=(cx+k_rx, cy+ry_o)),
                corner("p4", cut_x, cut_y_bot),
            ]

            if has_bar:  # G: 内部バー（右開口部に突き出す水平線）
                bar_y = cy + 20
                bar_w = rx_o * 0.4
                contours.append(make_contour(f"c{cid}", pts, closed=False)); cid += 1
                contours.append(rect_contour(f"c{cid}", cx, bar_y - ARM_H*0.4,
                                             bar_w, ARM_H * 0.8)); cid += 1
            else:
                contours.append(make_contour(f"c{cid}", pts, closed=False)); cid += 1

        if has_tail:  # Q: 右下への尾
            tail_pts = [
                corner("t0", cx + 40,       cy + ry - 40),
                corner("t1", width - lsb,   0),
                corner("t2", width - lsb + stem_w*0.6, 0),
                corner("t3", cx + 40 + stem_w*0.7, cy + ry - 40 + stem_w*0.7),
            ]
            contours.append(make_contour(f"c{cid}", tail_pts)); cid += 1

    else:
        # 縦棒 + 右ボウル (D, P, B, R)
        stem_x = lsb + stem_w   # 縦棒の右辺x

        # 縦棒
        contours.append(rect_contour(f"c{cid}", lsb, 0, stem_w, CAP_H)); cid += 1

        if not double_bowl:
            # D / P / R: 1つのボウル
            if char in ("D",):
                # D: 全高ボウル
                bowl_cx = stem_x + (width - stem_x - lsb*0.5) / 2
                bowl_rx = width - stem_x - lsb*0.5 - (bowl_cx - stem_x)
                bowl_cy = cy
                bowl_ry = CAP_H / 2
            else:
                # P, R: 上半分ボウル
                bowl_cx = stem_x + (width - stem_x - lsb) / 2
                bowl_rx = (width - stem_x - lsb) / 2
                bowl_cy = CAP_H * 0.7
                bowl_ry = CAP_H * 0.3

            kx = bowl_rx * KAPPA
            ky = bowl_ry * KAPPA
            top_y = bowl_cy + bowl_ry
            bot_y = bowl_cy - bowl_ry

            pts = [
                corner("p0", stem_x, bot_y),
                corner("p1", stem_x, top_y),
                smooth("p2", bowl_cx, top_y, hi=(stem_x + kx, top_y), ho=(bowl_cx + kx*0.5, top_y)),
                smooth("p3", bowl_cx + bowl_rx, bowl_cy,
                       hi=(bowl_cx + bowl_rx, bowl_cy + ky), ho=(bowl_cx + bowl_rx, bowl_cy - ky)),
                smooth("p4", bowl_cx, bot_y, hi=(bowl_cx + kx*0.5, bot_y), ho=(stem_x + kx, bot_y)),
            ]
            contours.append(make_contour(f"c{cid}", pts)); cid += 1

            # R: 右下への脚
            if char == "R":
                leg = [
                    corner("r0", stem_x + STEM_W*0.2, CROSS_Y - STEM_W*0.4),
                    corner("r1", width - lsb,           0),
                    corner("r2", width - lsb - STEM_W*0.75, 0),
                    corner("r3", stem_x,                CROSS_Y + STEM_W*0.2),
                ]
                contours.append(make_contour(f"c{cid}", leg)); cid += 1

        else:
            # B: 上下2つのボウル
            for i, (y_bot, y_top) in enumerate([(0, CAP_H//2 + 10), (CAP_H//2 - 10, CAP_H)]):
                bcy = (y_bot + y_top) / 2
                bry = (y_top - y_bot) / 2
                brx = (width - stem_x - lsb) * (0.85 if i == 0 else 0.78)
                bcx = stem_x + brx
                kx = brx * KAPPA
                ky = bry * KAPPA
                pts = [
                    corner(f"p{i*5+0}", stem_x, y_bot),
                    corner(f"p{i*5+1}", stem_x, y_top),
                    smooth(f"p{i*5+2}", bcx, y_top, hi=(stem_x+kx, y_top), ho=(bcx+kx*0.4, y_top)),
                    smooth(f"p{i*5+3}", bcx + brx, bcy,
                           hi=(bcx+brx, bcy+ky), ho=(bcx+brx, bcy-ky)),
                    smooth(f"p{i*5+4}", bcx, y_bot, hi=(bcx+kx*0.4, y_bot), ho=(stem_x+kx, y_bot)),
                ]
                contours.append(make_contour(f"c{cid}", pts)); cid += 1

    return make_glyph(char, width, contours)


# ═══════════════════════════════════════════════════════════════════════════════
# ファミリー 3: 対角線ベース (A V W M N X Y Z)
# ═══════════════════════════════════════════════════════════════════════════════

def build_from_diagonals(
    char: str,
    width: int,
    *,
    shape: str,       # 'A' 'V' 'W' 'M' 'N' 'X' 'Y' 'Z'
    lsb: int = 60,
    stem_w: int = STEM_W,
) -> GlyphDict:
    contours: list[Contour] = []
    cid = 0
    sw = stem_w
    H = CAP_H
    L, R = lsb, width - lsb

    if shape == "V":
        # V: 2本の斜め辺が底点で合わさる
        tip_x = width / 2
        pts = [
            corner("p0", L,            H),
            corner("p1", L + sw,       H),
            corner("p2", tip_x + sw/2, sw * 0.5),
            corner("p3", tip_x - sw/2, sw * 0.5),
            corner("p4", R - sw,       H),
            corner("p5", R,            H),
        ]
        contours.append(make_contour(f"c{cid}", pts)); cid += 1

    elif shape == "A":
        # A: 逆 V + クロスバー
        tip_x = width / 2
        tip_y = H
        pts = [
            corner("p0", L,            0),
            corner("p1", tip_x - sw/2, tip_y),
            corner("p2", tip_x + sw/2, tip_y),
            corner("p3", R,            0),
            corner("p4", R - sw,       0),
            corner("p5", tip_x + sw*0.3, sw),
            corner("p6", tip_x - sw*0.3, sw),
            corner("p7", L + sw,       0),
        ]
        contours.append(make_contour(f"c{cid}", pts)); cid += 1
        # クロスバー
        cb_y = H * 0.42
        cb_x0 = L + sw + (tip_x - sw/2 - L - sw) * (cb_y / H) * 0.95
        cb_x1 = R - sw - (R - sw - (tip_x + sw/2)) * (cb_y / H) * 0.95
        contours.append(rect_contour(f"c{cid}", cb_x0, cb_y - sw*0.4,
                                     cb_x1 - cb_x0, sw * 0.8)); cid += 1

    elif shape == "W":
        # W: 4本の斜め辺
        q = width / 4
        pts = [
            corner("p0", L,           H),
            corner("p1", L + sw,      H),
            corner("p2", q*1.5,       sw*0.6),
            corner("p3", q*2,         H * 0.55),
            corner("p4", q*2.5,       sw*0.6),
            corner("p5", R - sw,      H),
            corner("p6", R,           H),
            corner("p7", q*2.5 + sw*0.5, sw*0.6 + sw*0.5),
            corner("p8", q*2,         H * 0.55 + sw*0.5),
            corner("p9", q*1.5 - sw*0.5, sw*0.6 + sw*0.5),
        ]
        contours.append(make_contour(f"c{cid}", pts)); cid += 1

    elif shape == "M":
        # M: 外2本縦棒 + 内側V谷
        cx = width / 2
        # 左縦棒
        contours.append(rect_contour(f"c{cid}", L, 0, sw, H)); cid += 1
        # 右縦棒
        contours.append(rect_contour(f"c{cid}", R - sw, 0, sw, H)); cid += 1
        # 中央V(実体=三角の塗り)
        valley_y = H * 0.45
        pts = [
            corner("p0", L + sw,     H),
            corner("p1", cx - sw*0.3, valley_y),
            corner("p2", cx + sw*0.3, valley_y),
            corner("p3", R - sw,     H),
        ]
        contours.append(make_contour(f"c{cid}", pts)); cid += 1

    elif shape == "N":
        # N: 左縦棒 + 右縦棒 + 対角バー
        contours.append(rect_contour(f"c{cid}", L, 0, sw, H)); cid += 1
        contours.append(rect_contour(f"c{cid}", R - sw, 0, sw, H)); cid += 1
        diag = [
            corner("p0", L + sw,  H),
            corner("p1", L + sw*2, H),
            corner("p2", R - sw,  0),
            corner("p3", R - sw*2, 0),
        ]
        contours.append(make_contour(f"c{cid}", diag)); cid += 1

    elif shape == "X":
        # X: 2本の対角バーが中央で交差
        # 左上→右下
        contours.append(make_contour(f"c{cid}", [
            corner("p0", L,         H),
            corner("p1", L + sw,    H),
            corner("p2", R,         0),
            corner("p3", R - sw,    0),
        ])); cid += 1
        # 右上→左下
        contours.append(make_contour(f"c{cid}", [
            corner("p0", R - sw,    H),
            corner("p1", R,         H),
            corner("p2", L + sw,    0),
            corner("p3", L,         0),
        ])); cid += 1

    elif shape == "Y":
        # Y: 上2本の斜め + 下縦棒
        cx = width / 2
        mid_y = H * 0.45
        contours.append(make_contour(f"c{cid}", [
            corner("p0", L,          H),
            corner("p1", L + sw,     H),
            corner("p2", cx + sw*0.5, mid_y),
            corner("p3", cx - sw*0.5, mid_y),
        ])); cid += 1
        contours.append(make_contour(f"c{cid}", [
            corner("p0", R - sw,     H),
            corner("p1", R,          H),
            corner("p2", cx + sw*0.5, mid_y),
            corner("p3", cx - sw*0.5, mid_y),
        ])); cid += 1
        # 下縦棒
        contours.append(rect_contour(f"c{cid}", cx - sw/2, 0, sw, mid_y)); cid += 1

    elif shape == "Z":
        # Z: 上横棒 + 対角 + 下横棒
        contours.append(rect_contour(f"c{cid}", L, H - ARM_H, R - L, ARM_H)); cid += 1
        contours.append(rect_contour(f"c{cid}", L, 0, R - L, ARM_H)); cid += 1
        contours.append(make_contour(f"c{cid}", [
            corner("p0", L,       H - ARM_H),
            corner("p1", R,       H - ARM_H),
            corner("p2", L + sw,  ARM_H),
            corner("p3", L,       ARM_H),
        ])); cid += 1

    return make_glyph(char, width, contours)
# ↑ここから上は計算をしまくっています!

# ═══════════════════════════════════════════════════════════════════════════════
# パラメータ辞書 ── ここだけ編集すれば全グリフが変わる
# ═══════════════════════════════════════════════════════════════════════════════

# (builder_fn, kwargs)
_SPECS: dict[str, tuple] = {
# ═══════════════════════════════════════════════════════════════════════════════
# パラメータ辞書 ── ここだけ編集すれば全グリフが変わる
# ═══════════════════════════════════════════════════════════════════════════════

    # ── ファミリー 1: 大文字アルファベット (A–Z) ──
    "0041": (build_from_diagonals, dict(char="A", width=660, shape="A")),
    "0042": (build_from_bowl,      dict(char="B", width=620, has_stem=True, double_bowl=True)),
    "0043": (build_from_bowl,      dict(char="C", width=580, closed=False, open_angle=28)),
    "0044": (build_from_bowl,      dict(char="D", width=620, has_stem=True)),
    "0045": (build_from_stems,     dict(char="E", width=560, top_full=True, mid_arm=True, bot_full=True, mid_y=CROSS_Y)),
    "0046": (build_from_stems,     dict(char="F", width=520, top_full=True, mid_arm=True)),
    "0047": (build_from_bowl,      dict(char="G", width=620, closed=False, open_angle=20, has_bar=True)),
    "0048": (build_from_stems,     dict(char="H", width=700, right_stem=True, mid_full=True)),
    "0049": (build_from_stems,     dict(char="I", width=280)),
    "004A": (build_from_bowl,      dict(char="J", width=400, closed=False, open_angle=60, has_stem=False)),
    "004B": (build_from_stems,     dict(char="K", width=640, k_diag=True)),
    "004C": (build_from_stems,     dict(char="L", width=480, bot_full=True)),
    "004D": (build_from_diagonals, dict(char="M", width=780, shape="M")),
    "004E": (build_from_diagonals, dict(char="N", width=700, shape="N")),
    "004F": (build_from_bowl,      dict(char="O", width=660, closed=True, lsb=70)),
    "0050": (build_from_bowl,      dict(char="P", width=580, has_stem=True)),
    "0051": (build_from_bowl,      dict(char="Q", width=660, closed=True, has_tail=True, lsb=70)),
    "0052": (build_from_bowl,      dict(char="R", width=620, has_stem=True)),
    "0053": (build_from_bowl,      dict(char="S", width=540, closed=False, open_angle=35)),
    "0054": (build_from_stems,     dict(char="T", width=620, top_full=True)),
    "0055": (build_from_bowl,      dict(char="U", width=620, closed=False, open_angle=75, lsb=80)),
    "0056": (build_from_diagonals, dict(char="V", width=620, shape="V")),
    "0057": (build_from_diagonals, dict(char="W", width=840, shape="W")),
    "0058": (build_from_diagonals, dict(char="X", width=640, shape="X")),
    "0059": (build_from_diagonals, dict(char="Y", width=620, shape="Y")),
    "005A": (build_from_diagonals, dict(char="Z", width=580, shape="Z")),

    # ── ファミリー 2: 数字 (0–9) ──
    "0030": (build_from_bowl,      dict(char="0", width=620, closed=True, lsb=70)), # Oを流用
    "0031": (build_from_stems,     dict(char="1", width=360, left_stem=True, lsb=140)),
    "0032": (build_from_diagonals, dict(char="2", width=580, shape="Z")), # Zを流用
    "0033": (build_from_bowl,      dict(char="3", width=560, closed=False, double_bowl=True)), # Bを流用
    "0034": (build_from_diagonals, dict(char="4", width=620, shape="X")), # 交差形状としてXを流用
    "0035": (build_from_stems,     dict(char="5", width=560, top_full=True, mid_arm=True, bot_full=True, mid_y=CROSS_Y)), # Eを流用
    "0036": (build_from_bowl,      dict(char="6", width=600, closed=True)), # Oベース
    "0037": (build_from_diagonals, dict(char="7", width=580, shape="Z")), # Zを流用
    "0038": (build_from_bowl,      dict(char="8", width=620, closed=True, double_bowl=True)), # Bを流用
    "0039": (build_from_bowl,      dict(char="9", width=600, closed=True)), # Oベース

    # ── ファミリー 3: 小文字アルファベット (a–z) ──
    # ※ 一旦は大文字の描画ロジックを流用し、幅(width)を少し狭めて仮置きしています
    "0061": (build_from_bowl,      dict(char="a", width=580, has_stem=True)), # Dの流用
    "0062": (build_from_bowl,      dict(char="b", width=580, has_stem=True, double_bowl=True)), # Bの流用
    "0063": (build_from_bowl,      dict(char="c", width=540, closed=False, open_angle=28)), # Cの流用
    "0064": (build_from_bowl,      dict(char="d", width=580, has_stem=True)), # Dの流用
    "0065": (build_from_stems,     dict(char="e", width=520, top_full=True, mid_arm=True, bot_full=True, mid_y=CROSS_Y)), # Eの流用
    "0066": (build_from_stems,     dict(char="f", width=480, top_full=True, mid_arm=True)), # Fの流用
    "0067": (build_from_bowl,      dict(char="g", width=580, closed=False, open_angle=20, has_bar=True)), # Gの流用
    "0068": (build_from_stems,     dict(char="h", width=620, right_stem=True, mid_full=True)), # Hの流用
    "0069": (build_from_stems,     dict(char="i", width=260)), # Iの流用
    "006A": (build_from_bowl,      dict(char="j", width=360, closed=False, open_angle=60, has_stem=False)), # Jの流用
    "006B": (build_from_stems,     dict(char="k", width=580, k_diag=True)), # Kの流用
    "006C": (build_from_stems,     dict(char="l", width=260)), # Iの流用
    "006D": (build_from_diagonals, dict(char="m", width=740, shape="M")), # Mの流用
    "006E": (build_from_diagonals, dict(char="n", width=620, shape="N")), # Nの流用
    "006F": (build_from_bowl,      dict(char="o", width=580, closed=True, lsb=70)), # Oの流用
    "0070": (build_from_bowl,      dict(char="p", width=580, has_stem=True)), # Pの流用
    "0071": (build_from_bowl,      dict(char="q", width=580, closed=True, has_tail=True, lsb=70)), # Qの流用
    "0072": (build_from_bowl,      dict(char="r", width=560, has_stem=True)), # Rの流用
    "0073": (build_from_bowl,      dict(char="s", width=500, closed=False, open_angle=35)), # Sの流用
    "0074": (build_from_stems,     dict(char="t", width=540, top_full=True)), # Tの流用
    "0075": (build_from_bowl,      dict(char="u", width=560, closed=False, open_angle=75, lsb=80)), # Uの流用
    "0076": (build_from_diagonals, dict(char="v", width=560, shape="V")), # Vの流用
    "0077": (build_from_diagonals, dict(char="w", width=780, shape="W")), # Wの流用
    "0078": (build_from_diagonals, dict(char="x", width=580, shape="X")), # Xの流用
    "0079": (build_from_diagonals, dict(char="y", width=560, shape="Y")), # Yの流用
    "007A": (build_from_diagonals, dict(char="z", width=520, shape="Z")), # Zの流用

    # ── 記号・その他 ──
    "002E": (build_from_stems,     dict(char=".", width=240, bot_full=True, lsb=80, stem_w=80, arm_h=80)),
    "0020": (lambda c, w, **kw: make_glyph(c, w, []), dict(char=" ", width=240)),
}


# ═══════════════════════════════════════════════════════════════════════════════
# 公開 API
# ═══════════════════════════════════════════════════════════════════════════════

# python_backend/core/glyph_builder_full.py

# python_backend/core/glyph_builder_full.py

def build_glyph(unicode_hex: str) -> GlyphDict | None:
    key = unicode_hex.upper().zfill(4)
    print(f"   ---> [ビルダー] 辞書(_SPECS)からキー '{key}' を探します...")
    
    spec = _SPECS.get(key)
    if spec is None:
        print(f"   ---> [ビルダー] ⚠️ 辞書に '{key}' が登録されていません！")
        return None
        
    print(f"   ---> [ビルダー]  辞書に '{key}' を発見！座標を計算します。")
    fn, kwargs = spec
    return fn(**kwargs)


def get_supported_unicodes() -> list[str]:
    return list(_SPECS.keys())


# ═══════════════════════════════════════════════════════════════════════════════
# 動作確認
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import json

    ok, fail = 0, 0
    for u in get_supported_unicodes():
        g = build_glyph(u)
        if g is None:
            print(f"FAIL U+{u}"); fail += 1; continue
        n_c = len(g["contours"])
        n_p = sum(len(c["points"]) for c in g["contours"])
        print(f"U+{u} '{g['char']}'  w={g['width']:4d}  contours={n_c}  points={n_p:3d}")
        ok += 1

    print(f"\n{ok} OK / {fail} FAIL")
    print("\nA sample:")
    print(json.dumps(build_glyph("0041"), indent=2))