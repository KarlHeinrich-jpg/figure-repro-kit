#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从原图位图里量出版式参数（复刻准确性的关键一步）。

    # 1) 先看主要填充色
    python tools/measure_figure.py qa/reference.png --colors

    # 2) 扫一行/一列，找边和线：输出所有墨迹段 (起点, 终点, 长度)
    python tools/measure_figure.py qa/reference.png --row 1000
    python tools/measure_figure.py qa/reference.png --col 400

    # 3) 量一个框的四条外沿（对虚线也稳）
    python tools/measure_figure.py qa/reference.png --box 2031,359,2669,586

    # 4) 量虚线节奏（实线段/空线段长度）
    python tools/measure_figure.py qa/reference.png --dash-y 364

    # 5) 量某区域里的文字行（得到各行包围盒，据此推字号与基线）
    python tools/measure_figure.py qa/reference.png --text 2270,2830,3390,3110

    # 6) 一次量一批框，直接抄进 Figure 脚本
    python tools/measure_figure.py qa/reference.png --batch boxes.json
    #    boxes.json: {"CRITIC": [2031,359,2669,586], "EWM": [2031,1269,2669,1496]}
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PIL import Image                                             # noqa: E402
from figrepro import measure                                      # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--colors", action="store_true", help="列出主要填充色")
    g.add_argument("--row", type=int, help="扫描该行，输出墨迹段")
    g.add_argument("--col", type=int, help="扫描该列，输出墨迹段")
    g.add_argument("--box", help="量框的四条外沿 x0,y0,x1,y1")
    g.add_argument("--dash-y", type=int, help="沿该行量虚线节奏")
    g.add_argument("--dash-x", type=int, help="沿该列量虚线节奏")
    g.add_argument("--text", help="量文字行 x0,y0,x1,y1")
    g.add_argument("--batch", help="批量量框，参数是 JSON 文件")
    ap.add_argument("--top", type=int, default=16, help="--colors 输出几个")
    ap.add_argument("--range", dest="rng",
                    help="--dash-* 时限定扫描范围 A,B（强烈建议给）")
    a = ap.parse_args()

    img = Image.open(a.image)
    print("图像 %dx%d" % img.size)

    if a.colors:
        print("主要颜色（hex, 像素数）：")
        for hexv, n in measure.dominant_colors(img, n=a.top):
            print("   %s  %d" % (hexv, n))
    elif a.row is not None:
        print("行 y=%d 的墨迹段 (起, 止, 长)：" % a.row)
        for s, e, n in measure.row_runs(img, a.row):
            print("   (%d, %d, %d)" % (s, e, n))
    elif a.col is not None:
        print("列 x=%d 的墨迹段 (起, 止, 长)：" % a.col)
        for s, e, n in measure.col_runs(img, a.col):
            print("   (%d, %d, %d)" % (s, e, n))
    elif a.box:
        x0, y0, x1, y1 = json.loads("[" + a.box + "]")
        print(measure.report(img, {"box": (x0, y0, x1, y1)}))
    elif a.dash_y is not None or a.dash_x is not None:
        lo, hi = (json.loads("[" + a.rng + "]") if a.rng else (None, None))
        on, off = measure.dash_pattern(img, y=a.dash_y, x=a.dash_x, lo=lo, hi=hi)
        print("虚线节奏：实线 %s px，空档 %s px" % (on, off))
    elif a.text:
        x0, y0, x1, y1 = json.loads("[" + a.text + "]")
        print("文字行（y0, y1, 高, x0, x1）：")
        for ln in measure.text_lines(img, (x0, x1, y0, y1)):
            print("   y[%d,%d] h=%d  x[%d,%d]"
                  % (ln["y0"], ln["y1"], ln["h"], ln["x0"], ln["x1"]))
    elif a.batch:
        boxes = json.load(open(a.batch, encoding="utf-8"))
        print(measure.report(img, {k: tuple(v) for k, v in boxes.items()}))
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
