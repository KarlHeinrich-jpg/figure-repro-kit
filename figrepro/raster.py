# -*- coding: utf-8 -*-
"""
figrepro.raster -- 从 PDF 里把图"捞"出来。

期刊 PDF 里的插图常被排版工具**切成好几条**分别嵌入（同一 xref 家族、按显示位置
上下拼接）。直接取单张图会得到一条窄带，所以这里按显示矩形的 y 坐标排序后拼回整图。
"""

from __future__ import annotations

import io

import numpy as np
from PIL import Image


def page_images(pdf_path, page_index):
    """列出某页所有嵌入图，按显示位置从上到下、从左到右排序。

    Returns
    -------
    list[dict]
        每项含 ``xref`` / ``size`` / ``rect``（页面坐标，points）。
    """
    import pymupdf
    doc = pymupdf.open(pdf_path)
    page = doc[page_index]
    out = []
    for im in page.get_images(full=True):
        xref = im[0]
        for r in page.get_image_rects(xref):
            out.append(dict(xref=xref, size=(im[2], im[3]), rect=r))
    out.sort(key=lambda d: (round(d["rect"].y0, 1), round(d["rect"].x0, 1)))
    return out


def extract_figure(pdf_path, page_index, out_path=None, image_index=None):
    """把某一页上的插图拼成一张整图。

    Parameters
    ----------
    image_index : int | None
        该页有多组插图时用序号选择（按 :func:`page_images` 的顺序取第一张的
        xref 家族）。None 表示该页只有一组。
    """
    import pymupdf
    doc = pymupdf.open(pdf_path)
    infos = page_images(pdf_path, page_index)
    if not infos:
        raise ValueError("第 %s 页没有嵌入图" % (page_index + 1))
    if image_index is None:
        base = infos[0]
    else:
        base = infos[image_index]
    # 只保留和基准图同宽（同一张图被切成的条带）
    strips = [d for d in infos
              if abs(d["size"][0] - base["size"][0]) <= 2
              and abs(d["rect"].x0 - base["rect"].x0) < 1.0
              and abs(d["rect"].x1 - base["rect"].x1) < 1.0]
    tiles = []
    for d in strips:
        pix = pymupdf.Pixmap(doc, d["xref"])
        if pix.n > 4:
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
        tiles.append(Image.open(io.BytesIO(pix.tobytes("png"))))
    w = max(t.width for t in tiles)
    h = sum(t.height for t in tiles)
    sheet = Image.new("RGB", (w, h), "white")
    y = 0
    for t in tiles:
        sheet.paste(t, (0, y))
        y += t.height
    if out_path:
        sheet.save(out_path)
    return sheet


def render_page(pdf_path, page_index, dpi=200, out_path=None):
    """把整页渲染成位图（比逐张取图更适合已经压平的矢量图）。"""
    import pymupdf
    doc = pymupdf.open(pdf_path)
    pix = doc[page_index].get_pixmap(dpi=dpi)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    if out_path:
        img.save(out_path)
    return img


def crop(img, x0, y0, x1, y1, out_path=None):
    """裁切。给内沿坐标时正好得到不含边框的栅格内容。"""
    c = img.crop((int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))))
    if out_path:
        c.save(out_path)
    return c


def gray(img):
    return np.asarray(img.convert("L")).astype(int)
