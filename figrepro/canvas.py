# -*- coding: utf-8 -*-
"""
figrepro.canvas -- 后端无关的图形描述 + matplotlib 渲染后端。

图形描述 (:class:`Figure`) 只是一串图元调用；每个后端把同一串调用翻译成
自己的输出。坐标一律是**原图像素坐标**，y 轴向下。
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle, PathPatch
from matplotlib.path import Path
from matplotlib.lines import Line2D


# 字体度量：Times/宋体一类的衬线体，cap height ≈ 0.662 em，descender ≈ 0.217 em。
# 仅用于把"字高"换算成"字体磅值"时的经验常数。
CAP_RATIO = 0.662
DESC_RATIO = 0.217


class Figure:
    """后端无关的图形描述。

    Parameters
    ----------
    width_px, height_px : int
        原图（被复刻的位图）的像素尺寸，也是本图所有坐标的取值范围。
    width_mm : float
        成品物理宽度（mm）。期刊单栏约 90、双栏 170–190。
    """

    def __init__(self, width_px, height_px, width_mm):
        self.width_px = float(width_px)
        self.height_px = float(height_px)
        self.width_mm = float(width_mm)
        self.colors = {}
        self.items = []
        # 背景色，None 表示透明
        self.background = "white"

    # ---------------------------------------------------------------- 单位
    @property
    def mm_per_px(self):
        return self.width_mm / self.width_px

    @property
    def height_mm(self):
        return self.height_px * self.mm_per_px

    @property
    def native_dpi(self):
        """让 1 px 恰好等于 1 输出像素所需的 dpi（嵌图按原分辨率落盘的关键）。"""
        return self.width_px / (self.width_mm / 25.4)

    def pt(self, px):
        """把原图像素长度换算成磅。"""
        return px * self.mm_per_px * 72.0 / 25.4

    # -------------------------------------------------------------- 调色板
    def color(self, name, hex_value):
        self.colors[name] = hex_value
        return name

    def _c(self, name):
        """既接受调色板名，也接受 '#RRGGBB'。"""
        if name is None or name == "none":
            return None
        return self.colors.get(name, name)

    # ---------------------------------------------------------------- 图元
    def frame(self, x0, y0, x1, y1, fill=None, lw=1.0, z=2):
        """直角边框矩形。坐标是描边**外沿**。"""
        self.items.append(dict(kind="rect", x0=x0, y0=y0, x1=x1, y1=y1,
                               rc=0.0, fill=self._c(fill), lw=lw,
                               dash=False, z=z))

    def rbox(self, x0, y0, x1, y1, r, fill=None, lw=1.0, dash=False, z=2):
        """圆角矩形。坐标是描边**外沿**，``r`` 是外沿圆角半径。"""
        self.items.append(dict(kind="rect", x0=x0, y0=y0, x1=x1, y1=y1,
                               rc=r, fill=self._c(fill), lw=lw,
                               dash=dash, z=z))

    def dbox(self, x0, y0, x1, y1, fill=None, lw=1.0, r=0.0, dash=(47.0, 38.0), z=2):
        """虚线框。``dash`` 是 (实线段, 空线段)，单位原图像素。"""
        self.items.append(dict(kind="rect", x0=x0, y0=y0, x1=x1, y1=y1,
                               rc=r, fill=self._c(fill), lw=lw,
                               dash=dash, z=z))

    def line(self, pts, lw=1.0, z=6):
        """折线，坐标是描边中心线。"""
        self.items.append(dict(kind="line", pts=list(pts), lw=lw, z=z))

    def poly(self, pts, fill=None, lw=1.0, z=6):
        """闭合多边形（实心箭头等），坐标是描边中心线；``lw=0`` 表示不描边。"""
        self.items.append(dict(kind="poly", pts=list(pts),
                               fill=self._c(fill), lw=lw, z=z))

    def bezier(self, pts, codes, lw=1.0, z=6):
        """路径（花括号等）。``codes`` 用 'M' / 'L' / 'C' 简写。"""
        self.items.append(dict(kind="bezier", pts=list(pts), codes=list(codes),
                               lw=lw, z=z))

    def text(self, x, y, s, size_px, weight="bold", style="normal",
             anchor="c", color="#000000", z=8):
        """文本。``y`` 是**基线**位置（不是包围盒中心），
        ``size_px`` 是字体 em 高度（按原图像素给），避免手算磅值。
        ``anchor``: 'w' 左对齐 / 'c' 居中 / 'e' 右对齐。"""
        self.items.append(dict(kind="text", x=x, y=y, s=s, size_px=size_px,
                               weight=weight, style=style, anchor=anchor,
                               color=color, z=z))

    def image(self, path, x0, y0, x1, y1, z=4):
        """把栅格子图放进给定矩形（通常取外框内沿）。"""
        self.items.append(dict(kind="image", path=path, x0=x0, y0=y0,
                               x1=x1, y1=y1, z=z))

    def circle(self, cx, cy, r, fill="#000000", lw=0.0, z=8):
        """实心/空心圆（省略号、散点记号等）。"""
        self.items.append(dict(kind="circle", cx=cx, cy=cy, r=r,
                               fill=self._c(fill), lw=lw, z=z))

    def dots(self, y, *xs, r=None, gap=None, fill="#000000", z=8):
        """水平省略号。给中心点 + 半径，或给间距 ``gap`` 由半径推。"""
        r = r if r is not None else 11.5
        gap = gap if gap is not None else r * 3.13
        n = len(xs)
        c0 = sum(xs) / n if n else 0
        for i in range(n):
            self.circle(c0 + (i - (n - 1) / 2.0) * gap, y, r, fill=fill, z=z)

    # ------------------------------------------------------------ 复合图元
    def arrow_down(self, cx, y_from, y_tip, lw=8, w_head=None, h_head=40.0, z=6):
        """纯黑下箭头：竖线 + 实心三角头（原图常见样式）。"""
        h = h_head
        w = w_head if w_head is not None else lw * 5.5
        y_base = y_tip - h
        self.line([(cx, y_from), (cx, y_base + 2)], lw=lw, z=z)
        self.poly([(cx - w / 2, y_base), (cx + w / 2, y_base), (cx, y_tip)],
                  fill="#000000", lw=0, z=z)

    def brace(self, x_end, x_body, x_tip, y_top, y_bot, lw=8, z=6):
        """右向花括号 “}”：两端在 x_end，主体在 x_body，尖端指向 x_tip。"""
        ym = (y_top + y_bot) / 2.0
        k = (y_bot - y_top) * 0.16
        pts = [(x_end, y_top),
               (x_body - 26, y_top), (x_body, y_top + 55), (x_body, y_top + 150),
               (x_body, ym - k),
               (x_body, ym - 26), (x_body + 12, ym), (x_tip, ym),
               (x_body + 12, ym), (x_body, ym + 26), (x_body, ym + k),
               (x_body, y_bot - 150),
               (x_body, y_bot - 55), (x_body - 26, y_bot), (x_end, y_bot)]
        codes = list("MCCCL" "CCCCCC" "L" "CCC")
        self.bezier(pts, codes, lw=lw, z=z)

    # --------------------------------------------------------------- 渲染
    def save_matplotlib(self, path, dpi=None, png_dpi=300):
        """渲染成 PDF/PNG（按扩展名）。PDF 中嵌图按原分辨率落盘。"""
        be = MatplotlibBackend(self)
        return be.save(path, dpi=dpi, png_dpi=png_dpi)

    def save_tikz(self, path, **kw):
        """生成 TikZ/LaTeX 源码（需 xelatex 编译）。"""
        from .tikz import TikzBackend
        return TikzBackend(self).save(path, **kw)


class MatplotlibBackend:
    """把 :class:`Figure` 渲染成 matplotlib 图。"""

    def __init__(self, fig: Figure):
        self.f = fig
        plt.rcParams.update({
            "pdf.fonttype": 42,          # TrueType 子集，不要 Type 3
            "ps.fonttype": 42,
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif"],
            "text.hinting": "none",      # 关闭 hinting，保证量到的宽度=画出的宽度
            "lines.dash_capstyle": "butt",
            "figure.facecolor": fig.background or "none",
        })
        self.mpl = plt.figure(figsize=(fig.width_mm / 25.4, fig.height_mm / 25.4),
                              dpi=fig.native_dpi)
        self.ax = self.mpl.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, fig.width_px)
        self.ax.set_ylim(fig.height_px, 0)          # y 向下，和原图一致
        self.ax.set_aspect("equal")
        self.ax.axis("off")

    # ------------------------------------------------------------------ 画
    def draw(self):
        f, ax = self.f, self.ax
        for it in sorted(f.items, key=lambda d: d.get("z", 5)):
            getattr(self, "_" + it["kind"])(it)

    def _rect(self, it):
        lw = self.f.pt(it["lw"])
        ls = "solid"
        if it["dash"]:
            on, off = it["dash"]
            ls = (0, (self.f.pt(on), self.f.pt(off)))
        if it["rc"] > 0:
            h = it["lw"] / 2.0          # 坐标给的是描边外沿，路径要内缩半个线宽
            x0, y0, x1, y1 = (it["x0"] + h, it["y0"] + h,
                              it["x1"] - h, it["y1"] - h)
            r = max(it["rc"] - h, 0.0)
            # 注意：FancyBboxPatch 的 round 盒样式以给定矩形为外框，
            # 不要再自己减一次 r（这是最容易踩的坑）。
            p = FancyBboxPatch((x0, y0), x1 - x0, y1 - y0,
                               boxstyle=f"round,pad=0,rounding_size={r}",
                               mutation_scale=1, fc=it["fill"] or "none",
                               ec="black", lw=lw, ls=ls, zorder=it["z"])
        else:
            h = it["lw"] / 2.0 if it["lw"] else 0.0
            p = Rectangle((it["x0"] + h, it["y0"] + h),
                          (it["x1"] - it["x0"]) - 2 * h,
                          (it["y1"] - it["y0"]) - 2 * h,
                          fc=it["fill"] or "none", ec="black", lw=lw, ls=ls,
                          joinstyle="miter", zorder=it["z"])
        self.ax.add_patch(p)

    def _line(self, it):
        xy = list(zip(*it["pts"]))
        self.ax.add_line(Line2D(xy[0], xy[1], color="black",
                                lw=self.f.pt(it["lw"]), solid_capstyle="butt",
                                solid_joinstyle="miter", zorder=it["z"]))

    def _poly(self, it):
        self.ax.add_patch(Polygon(it["pts"], closed=True,
                                  fc=it["fill"] or "none",
                                  ec="black" if it["lw"] else "none",
                                  lw=self.f.pt(it["lw"]) if it["lw"] else 0.0,
                                  joinstyle="miter", zorder=it["z"]))

    def _bezier(self, it):
        m = {"M": Path.MOVETO, "L": Path.LINETO, "C": Path.CURVE4}
        p = Path(it["pts"], [m[c] for c in it["codes"]])
        self.ax.add_patch(PathPatch(p, fc="none", ec="black",
                                    lw=self.f.pt(it["lw"]), capstyle="butt",
                                    zorder=it["z"]))

    def _text(self, it):
        ha = {"w": "left", "c": "center", "e": "right"}[it["anchor"]]
        self.ax.text(it["x"], it["y"], it["s"], fontsize=self.f.pt(it["size_px"]),
                     ha=ha, va="baseline", color=it["color"],
                     weight=it["weight"], style=it["style"], zorder=it["z"])

    def _image(self, it):
        self.ax.imshow(plt.imread(it["path"]),
                       extent=(it["x0"], it["x1"], it["y1"], it["y0"]),
                       aspect="auto", interpolation="bilinear",
                       zorder=it["z"])

    def _circle(self, it):
        self.ax.add_patch(plt.Circle((it["cx"], it["cy"]), it["r"],
                                     fc=it["fill"] or "none",
                                     ec="black" if it["lw"] else "none",
                                     lw=self.f.pt(it["lw"]) if it["lw"] else 0.0,
                                     zorder=it["z"]))

    # ---------------------------------------------------------------- 存盘
    def save(self, path, dpi=None, png_dpi=300):
        self.draw()
        # 重新钉死坐标轴，防止 imshow 改动 limits/aspect
        self.ax.set_xlim(0, self.f.width_px)
        self.ax.set_ylim(self.f.height_px, 0)
        self.ax.set_aspect("equal")
        dpi = dpi or self.f.native_dpi
        if path.lower().endswith(".png"):
            self.mpl.savefig(path, dpi=png_dpi)
        else:
            # dpi 必须显式给足，否则嵌图会按 figure.dpi 被降采样，打印发虚
            self.mpl.savefig(path, dpi=dpi)
        plt.close(self.mpl)
        return path
