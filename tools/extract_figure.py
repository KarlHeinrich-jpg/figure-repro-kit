#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从期刊 PDF 里把插图提取成整图（自动拼接被排版工具切开的条带）。

    python tools/extract_figure.py paper.pdf --page 4 --out qa/reference.png
    python tools/extract_figure.py paper.pdf --page 4 --list      # 先看看有什么

也可以渲染整页（矢量图或已经压平的页面用这个）：

    python tools/extract_figure.py paper.pdf --page 4 --render --dpi 600 --out page.png
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from figrepro import raster                                      # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--page", type=int, required=True, help="页码，从 1 开始")
    ap.add_argument("--out", help="输出 PNG 路径")
    ap.add_argument("--index", type=int, default=None,
                    help="该页有多组插图的序号（从 0 开始）")
    ap.add_argument("--list", action="store_true", help="只列出该页的嵌入图")
    ap.add_argument("--render", action="store_true", help="改为渲染整页")
    ap.add_argument("--dpi", type=int, default=300, help="--render 时的分辨率")
    a = ap.parse_args()

    page = a.page - 1
    if a.list:
        infos = raster.page_images(a.pdf, page)
        if not infos:
            print("该页没有嵌入图")
        for i, d in enumerate(infos):
            r = d["rect"]
            print("[%d] xref=%-6s %5dx%-5d  显示位置 x[%.0f,%.0f] y[%.0f,%.0f]"
                  % (i, d["xref"], d["size"][0], d["size"][1],
                     r.x0, r.x1, r.y0, r.y1))
        return 0

    if a.render:
        img = raster.render_page(a.pdf, page, dpi=a.dpi, out_path=a.out)
        print("渲染整页 %dx%d -> %s" % (img.width, img.height, a.out))
        return 0

    img = raster.extract_figure(a.pdf, page, out_path=a.out, image_index=a.index)
    print("拼接 %dx%d -> %s" % (img.width, img.height, a.out))
    print("提示：接下来用 tools/measure_figure.py 量出版式参数。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
