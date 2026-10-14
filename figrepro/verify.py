# -*- coding: utf-8 -*-
"""
figrepro.verify -- 把复刻结果与原图**逐像素**比对。

这一步是"复刻得像不像"的唯一客观判据。做法是先按墨迹重叠自动求出平移量
（复刻图由 standalone/savefig 裁边，通常与输出原点差几十到一百多像素），
再在整幅图上算平均绝对灰度差、给出偏差最大的分块位置。

经验值（同为 Times 系字体、几何对齐到 1 px 以内时）：

* 平均差 < 12  几乎只差字体光栅化与虚线相位，肉眼与打印不可分辨
* 平均差 20–40 通常意味着某处整体偏移、字号偏差或嵌图被降采样
* 平均差 > 60   一般是有元素缺失或位置整体错位
"""

from __future__ import annotations

import io

import numpy as np
from PIL import Image


def render_pdf(pdf_path, dpi=None, out_path=None, page=0, width_px=None,
               zoom=None, mm_per_px=None):
    """把 PDF 渲染成位图。

    与原图比对时，请给 ``mm_per_px``（= :attr:`Figure.mm_per_px`）或等价的
    ``zoom``：这样渲染结果里**一个源图像素正好占一个输出像素**，两张图只差一个
    平移，比对才有意义。

    .. warning::
        不要用 ``width_px`` 去渲染 ``standalone`` 的 TikZ 页面——它已按内容裁过
        边（通常比画布窄十几毫米），拉宽到参考图宽度会整体放大百分之一以上，
        边缘处就错开几十像素了。
    """
    import pymupdf
    doc = pymupdf.open(pdf_path)
    p = doc[page]
    if zoom is None and mm_per_px:
        zoom = 25.4 / (mm_per_px * 72.0)      # 输出像素 / PDF 点
    if zoom is not None:
        pix = p.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
    elif width_px:
        z = float(width_px) / p.rect.width
        pix = p.get_pixmap(matrix=pymupdf.Matrix(z, z))
    else:
        pix = p.get_pixmap(dpi=int(round(dpi)))
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    if out_path:
        img.save(out_path)
    return img


def _profile_topk(a_counts, b_counts, search, k=6):
    """一维投影互相关的 top-k 平移候选（按分数降序）。

    单峰不一定可靠：容器上下边框的墨迹投影很像，投影互相关可能把"下边框对上
    上边框"当成最优解。所以这里只负责**提出候选**，最终由二维墨迹重叠定胜负。
    """
    a = a_counts - a_counts.mean()
    b = b_counts - b_counts.mean()
    scored = []
    for s in range(-search, search + 1):
        i0, i1 = max(0, s), min(len(a), len(b) + s)
        if i1 - i0 < 50:
            continue
        x, y = a[i0:i1], b[i0 - s:i1 - s]
        scored.append((float((x * y).sum()), s))
    scored.sort(reverse=True)
    out, used = [], set()
    for v, s in scored:                      # 候选之间至少隔 4 px，避免同一个峰
        if any(abs(s - u) < 4 for u in used):
            continue
        used.add(s)
        out.append(s)
        if len(out) >= k:
            break
    return out


def align_offset(ref, test, search=220, coarse=4, strip=None):
    """求 test 相对 ref 的平移量 (dx, dy)。

    一维投影互相关提候选（毫秒级），再用二维墨迹重叠在候选组合里定胜负，
    最后在全分辨率上精修 ±3 px。直接在二维上穷举会慢几个数量级。
    """
    A = np.asarray(ref.convert("L")) < 128
    B = np.asarray(test.convert("L")) < 128

    cand_y = _profile_topk(A.sum(axis=1), B.sum(axis=1), search)
    cand_x = _profile_topk(A.sum(axis=0), B.sum(axis=0), search)

    def ov(dx, dy):
        ax0, ax1 = max(0, dx), min(A.shape[1], dx + B.shape[1])
        ay0, ay1 = max(0, dy), min(A.shape[0], dy + B.shape[0])
        if ax1 - ax0 < 50 or ay1 - ay0 < 50:
            return -1
        a = A[ay0:ay1, ax0:ax1]
        b = B[ay0 - dy:ay1 - dy, ax0 - dx:ax1 - dx]
        return int(np.logical_and(a, b).sum())

    best = (-1, 0, 0)
    for dy in cand_y:
        for dx in cand_x:
            s = ov(dx, dy)
            if s > best[0]:
                best = (s, dx, dy)
    _, dx, dy = best
    for ddy in range(dy - 3, dy + 4):
        for ddx in range(dx - 3, dx + 4):
            s = ov(ddx, ddy)
            if s > best[0]:
                best = (s, ddx, ddy)
    return best[1], best[2], best[0]


def paste_aligned(test, size, dx, dy):
    """按 (dx, dy) 把 test 贴到 size 大小的白底画布上（与原图同坐标系）。"""
    c = Image.new("RGB", size, "white")
    c.paste(test, (dx, dy))
    return c


def compare(ref_img, test_img, out_dir=None, tag="cmp", search=220):
    """完整校验：自动对齐 → 平均差 → 最差分块 → 对照图。"""
    dx, dy, ov = align_offset(ref_img, test_img, search=search)
    aligned = paste_aligned(test_img, ref_img.size, dx, dy)
    A = np.asarray(ref_img.convert("L")).astype(int)
    B = np.asarray(aligned.convert("L")).astype(int)
    d = np.abs(A - B)
    res = dict(offset=(dx, dy), overlap=ov, mean_abs_diff=round(float(d.mean()), 2))

    bs = 200
    blocks = sorted(((float(d[y:y + bs, x:x + bs].mean()), y, x)
                     for y in range(0, d.shape[0] - bs, bs)
                     for x in range(0, d.shape[1] - bs, bs)), reverse=True)
    res["worst_blocks"] = [(round(m, 1), y, x) for m, y, x in blocks[:8]]

    if out_dir:
        import os
        os.makedirs(out_dir, exist_ok=True)
        aligned.save(os.path.join(out_dir, tag + "_aligned.png"))
        W = 1500
        a = ref_img.resize((W, int(W * ref_img.height / ref_img.width)))
        b = aligned.resize((W, int(W * aligned.height / aligned.width)))
        sheet = Image.new("RGB", (W, a.height + b.height + 16), "red")
        sheet.paste(a, (0, 0))
        sheet.paste(b, (0, a.height + 16))
        sheet.save(os.path.join(out_dir, tag + "_side_by_side.png"))
    return res
