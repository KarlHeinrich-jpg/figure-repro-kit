#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
把复刻结果与原图逐像素比对。

    python tools/verify.py qa/reference.png out/fig1_matplotlib.pdf \
                            --mm-per-px 0.029254 --out-dir qa --tag mpl

``--mm-per-px`` 是 Figure 的 mm_per_px（= width_mm / width_px）。给上它，
渲染结果里一个源图像素正好占一个输出像素，两张图只差一个平移。
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PIL import Image                                             # noqa: E402
from figrepro import verify                                       # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reference", help="原图（PNG）")
    ap.add_argument("pdf", help="复刻结果（PDF）")
    ap.add_argument("--mm-per-px", type=float, default=None,
                    help="Figure.mm_per_px；不给则用 --dpi 渲染")
    ap.add_argument("--dpi", type=float, default=None)
    ap.add_argument("--search", type=int, default=260, help="平移搜索范围（像素）")
    ap.add_argument("--out-dir", default=None, help="写出对照图")
    ap.add_argument("--tag", default="cmp")
    a = ap.parse_args()

    ref = Image.open(a.reference).convert("RGB")
    test = verify.render_pdf(a.pdf, dpi=a.dpi, mm_per_px=a.mm_per_px,
                             zoom=None if a.mm_per_px else None)
    res = verify.compare(ref, test, out_dir=a.out_dir, tag=a.tag, search=a.search)

    print("参考图      %dx%d" % ref.size)
    print("复刻渲染    %dx%d" % test.size)
    print("平移        (%d, %d)" % res["offset"])
    print("墨迹重叠    %d px" % res["overlap"])
    print("平均绝对差  %.2f  (0-255)" % res["mean_abs_diff"])
    print("最差分块    " + ", ".join("(%.0f @ y=%d x=%d)" % b
                                     for b in res["worst_blocks"][:5]))
    v = res["mean_abs_diff"]
    verdict = ("几乎只差字体光栅化与虚线相位，肉眼不可分辨" if v < 12 else
               "存在整体偏移 / 字号偏差 / 嵌图被降采样，建议查最差分块" if v < 45 else
               "明显不对：可能有元素缺失或位置整体错位")
    print("判读        %s" % verdict)
    if a.out_dir:
        print("对照图      %s" % a.out_dir)
    return 0 if v < 45 else 1


if __name__ == "__main__":
    sys.exit(main())
