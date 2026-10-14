# -*- coding: utf-8 -*-
"""
figrepro.measure -- 从原图位图里量出版式参数。

复刻的准确性几乎完全取决于这一步：先把原图量化，再照着数字重画。
凭肉眼看缩略图估坐标，最后一定会出现整体偏移、线宽不对、字号偏小这类问题。

约定：所有返回值都是**原图像素坐标**，y 轴向下。描边位置给的是**外沿**。
"""

from __future__ import annotations

from collections import Counter

import numpy as np

INK = 128           # 灰度阈值：小于此值算"有墨"


# ---------------------------------------------------------------- 基础工具
def to_gray(img):
    """PIL 图 / numpy 数组 → 灰度 numpy 数组（H, W）。

    量测函数一律接受这两者，免得每处都写一遍 convert("L")。
    """
    if hasattr(img, "convert"):
        return np.asarray(img.convert("L")).astype(int)
    a = np.asarray(img)
    if a.ndim == 3:
        a = a[..., :3].mean(axis=2)
    return a.astype(int)


def to_rgb(img):
    """PIL 图 / numpy 数组 → RGB numpy 数组（H, W, 3）。"""
    if hasattr(img, "convert"):
        return np.asarray(img.convert("RGB")).astype(int)
    a = np.asarray(img)
    if a.ndim == 2:
        a = np.dstack([a] * 3)
    return a[..., :3].astype(int)


def dark(img, thr=INK):
    return to_gray(img) < thr


def runs(mask_1d, min_len=1):
    """把布尔序列压成 [(start, end_inclusive, length), ...]。"""
    out, s = [], None
    for i, v in enumerate(mask_1d):
        if v and s is None:
            s = i
        elif not v and s is not None:
            if i - s >= min_len:
                out.append((s, i - 1, i - s))
            s = None
    if s is not None:
        out.append((s, len(mask_1d) - 1, len(mask_1d) - s))
    return out


def row_runs(img, y, x0=0, x1=None, thr=INK, min_len=1):
    m = dark(img, thr)[y, x0:x1]
    return [(x0 + s, x0 + e, n) for s, e, n in runs(m, min_len)]


def col_runs(img, x, y0=0, y1=None, thr=INK, min_len=1):
    m = dark(img, thr)[y0:y1, x]
    return [(y0 + s, y0 + e, n) for s, e, n in runs(m, min_len)]


# ------------------------------------------------------------------ 调色板
def dominant_colors(img, n=12, step=37):
    """出现频率最高的若干颜色，用来直接读出填充色。"""
    a = to_rgb(img).reshape(-1, 3)
    c = Counter(map(tuple, a[::step]))
    return [("#%02X%02X%02X" % col, cnt) for col, cnt in c.most_common(n)]


def fill_bbox(img, region, color, tol=8):
    """某个填充色在 region 内的包围盒。

    .. warning::
        虚线框的填充会从缝隙里"漏"出去，包围盒比真实内沿大 5–7 px。
        要精确值请用 :func:`stroke_edge`。
    """
    x0, x1, y0, y1 = region
    a = to_rgb(img)[y0:y1, x0:x1]
    tgt = np.array(color)
    m = (np.abs(a - tgt).max(axis=2) < tol)
    ys, xs = np.where(m)
    if len(xs) == 0:
        return None
    return (x0 + xs.min(), x0 + xs.max(), y0 + ys.min(), y0 + ys.max())


# -------------------------------------------------------------- 描边位置
def _edge_median(img, expected, lo, hi, fixed_range, axis, tol=16, step=11,
                 thr=INK):
    vals = []
    for t in range(fixed_range[0], fixed_range[1], step):
        rs = (col_runs(img, t, lo, hi, thr) if axis == "v"
              else row_runs(img, t, lo, hi, thr))
        for s, e, _ in rs:
            if abs(s - expected) <= tol:
                vals.append(s)
    return int(np.median(vals)) if vals else None


def stroke_edge(img, expected, lo, hi, along, axis, step=11, tol=16, thr=INK):
    """描边的外沿坐标（对虚线也稳：在多条扫描线上取中位数）。

    Parameters
    ----------
    expected : float
        大致位置，用来在扫描线上挑出目标那一段。
    lo, hi : float
        扫描窗口（沿 ``axis`` 相反方向的取值范围）。
    along : (float, float)
        扫描线本身的取值范围。``axis='v'`` 时是在列上纵向扫（找水平边），
        ``along`` 给 x 区间；``axis='h'`` 时反之。
    """
    return _edge_median(img, expected, lo, hi, along, axis, tol=tol, step=step,
                        thr=thr)


def stroke_width(img, x, y, axis="v", thr=INK):
    """某点处描边的厚度（像素）。"""
    rs = col_runs(img, x, y - 40, y + 40, thr) if axis == "v" \
        else row_runs(img, y, x - 40, x + 40, thr)
    for s, e, n in rs:
        if s <= y <= e or s <= x <= e:
            return n
    return None


# ---------------------------------------------------------------- 虚线节奏
def dash_pattern(img, y=None, x=None, lo=None, hi=None, thr=INK):
    """量出虚线的 (实线段, 空线段) 平均长度。

    给 ``y`` 时沿该行扫（量水平虚线），给 ``x`` 时沿该列扫。

    .. note::
        一定要用 ``lo`` / ``hi`` 把范围收在被测的那条边上——整行扫过去会扫到
        其它框的竖直边框（每条 8-12 px），中位数会被带偏成边框宽度。
    """
    rs = (row_runs(img, y, lo, hi, thr) if y is not None
          else col_runs(img, x, lo, hi, thr))
    ons = [n for s, e, n in rs if 4 <= n <= 200]
    gaps = [rs[i + 1][0] - rs[i][1] - 1 for i in range(len(rs) - 1)
            if 2 <= rs[i + 1][0] - rs[i][1] - 1 <= 200]
    f = lambda v: round(float(np.median(v)), 1) if v else None
    return f(ons), f(gaps)


# ---------------------------------------------------------------- 文字度量
def text_lines(img, region, thr=INK):
    """区域内每一行文字的包围盒（基线请按 cap height 推）。"""
    x0, x1, y0, y1 = region
    m = dark(img, thr)[y0:y1, x0:x1]
    out = []
    for s, e, _ in runs(m.any(axis=1)):
        sub = m[s:e + 1]
        xs = np.where(sub.any(axis=0))[0]
        out.append(dict(y0=y0 + s, y1=y0 + e, h=e - s,
                        x0=x0 + int(xs.min()), x1=x0 + int(xs.max())))
    return out


def text_bbox(img, region, thr=INK):
    """区域内所有墨迹的包围盒。"""
    x0, x1, y0, y1 = region
    m = dark(img, thr)[y0:y1, x0:x1]
    ys, xs = np.where(m)
    if len(xs) == 0:
        return None
    return dict(x0=x0 + int(xs.min()), x1=x0 + int(xs.max()),
                y0=y0 + int(ys.min()), y1=y0 + int(ys.max()),
                w=int(xs.max() - xs.min()), h=int(ys.max() - ys.min()))


def size_pt_for_cap(cap_px, pt_per_px):
    """由 cap height（大写字母高，像素）反推字号（磅）。Times 系 cap ≈ 0.662 em。"""
    return cap_px / 0.662 * pt_per_px


def size_pt_for_ascdesc(h_px, pt_per_px):
    """由"上伸部到下降部"总高（像素）反推字号（磅），约 0.879 em。"""
    return h_px / 0.879 * pt_per_px


def baseline(cap_top=None, bottom=None, em_px=None, descender=False):
    """按 cap 顶边或包围盒底边推基线（y 向下）。"""
    if descender:
        return bottom - 0.217 * em_px
    if bottom is not None and descender is False:
        return bottom
    return cap_top + 0.662 * em_px


# ------------------------------------------------------------------ 报告
def report(img, boxes, colors=None):
    """对一组待测框输出"实测描边外沿"表，直接抄进 Figure 脚本。"""
    lines = []
    for name, (x0, y0, x1, y1) in boxes.items():
        cy, cx = (y0 + y1) // 2, (x0 + x1) // 2
        L = stroke_edge(img, x0, x0 - 60, x0 + 60, (y0, y1), "h")
        R = stroke_edge(img, x1, x1 - 60, x1 + 60, (y0, y1), "h")
        T = stroke_edge(img, y0, y0 - 60, y0 + 60, (x0, x1), "v")
        B = stroke_edge(img, y1, y1 - 60, y1 + 60, (x0, x1), "v")
        L, R = (L, (R + 12) if R is not None else None)
        T, B = (T, (B + 12) if B is not None else None)
        lines.append("%-16s x[%s,%s]  y[%s,%s]" % (name, L, R, T, B))
    if colors:
        for name, col in colors.items():
            bb = fill_bbox(img, col[1], col[0])
            lines.append("%-16s fill_bbox=%s" % (name, bb))
    return "\n".join(lines)
