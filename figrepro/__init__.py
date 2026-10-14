# -*- coding: utf-8 -*-
"""
figrepro -- 把一张已发表的位图式框架图/流程图复刻成矢量图。

设计要点
--------
1. **一套坐标，两个后端。**  所有图元都用"原图像素坐标"(x 向右, y 向下)描述，
   同一个图形描述既能渲染成 matplotlib，也能生成 TikZ/LaTeX 源码。
   两版因此永远不会脱节——这是手写两份代码最大的坑。

2. **长度全部以原图像素为单位。**  画布给定 ``width_px`` 和成品物理宽度
   ``width_mm`` 后，1 px = ``width_mm/width_px`` mm，字号、线宽、虚线节奏
   一律按这个比例换算，不再手算磅值（这类换算错一次就会全线偏小）。

3. **栅格内容原样嵌入。**  地图、三维曲面这类无法矢量重画的内容，
   用 :mod:`figrepro.raster` 从原图按外框内沿裁切后嵌入；其余线框、箭头、
   花括号、文字全部重画为矢量。

典型用法
--------
>>> from figrepro import Figure
>>> fig = Figure(width_px=5811, height_px=3837, width_mm=170)
>>> fig.color("greenF", "#F0F8EB")
>>> fig.rbox(34, 190, 1549, 1673, r=115, fill="greenF", lw=12)
>>> fig.text(150, 128, "Indicator Selection", size_px=160, weight="bold")
>>> fig.save_matplotlib("out/fig.pdf")
>>> fig.save_tikz("out/fig.tex")
"""

from .canvas import Figure, MatplotlibBackend          # noqa: F401
from .tikz import TikzBackend                          # noqa: F401
from . import raster, measure, verify                  # noqa: F401

__version__ = "0.1.0"
__all__ = ["Figure", "MatplotlibBackend", "TikzBackend",
           "raster", "measure", "verify"]
