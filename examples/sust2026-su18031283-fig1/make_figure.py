# -*- coding: utf-8 -*-
"""
示例：复刻 Sustainability 2026, 18, 1283 的 Figure 1 "Research framework"。

    Fan/Zhang-type coupling-coordination paper——
    "Mapping the Coupling Coordination between Digital Economy and Carbon
     Emissions: Spatiotemporal Patterns and Spatial Markov Transitions"
    MDPI Sustainability 2026, 18, 1283, doi:10.3390/su18031283

这份脚本就是**唯一的图形描述**：同一个 Figure 对象分别交给 matplotlib 后端和
TikZ 后端，得到两版成品。所有坐标都是原图的像素坐标（5811 x 3837，y 向下），
可以直接拿原图量核对。

运行：
    python make_figure.py            # 只出图
    python build.py                  # 出图 + 编译 TikZ + 与原图逐像素校验
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))

from figrepro import Figure                                    # noqa: E402

REF_PX = (5811, 3837)          # 原图像素尺寸（从 PDF 里提取的整图）
WIDTH_MM = 170.0               # 成品物理宽（期刊双栏）

# 由原图量出的字号：em 高度（像素）。cap height ≈ 0.662 em
FS_TITLE = 160.0               # Indicator Selection / Measurement Model / ...
FS_PANEL = 126.7               # 三个面板小标题
FS_DEI = 142.2                 # DEI / CEI（粗斜体）
FS_BOX = 114.4                 # CRITIC / Markov Transition Matrix / ...
FS_COUP = 111.1                # Coupling Coordination Degree Model
FS_GREEN = 81.6                # Domains / IPv4 / CE / PCCE / ...


def build():
    f = Figure(REF_PX[0], REF_PX[1], WIDTH_MM)
    A = lambda p: os.path.join(HERE, "assets", p)              # noqa: E731

    # ---------------------------------------------------------- 调色板
    f.color("greenF", "#F0F8EB")   # 左容器填充
    f.color("greenB", "#C9E5B4")   # 指标小框
    f.color("creamF", "#FEF7F1")   # 中容器填充
    f.color("creamB", "#FCE7D6")   # 权重方法 / CCD 小框
    f.color("cyanF", "#EAF9F9")    # 下方大容器
    f.color("cyanB", "#D4F4F1")    # 面板内小框
    f.color("orangF", "#EF822F")   # 橙色大箭头
    f.color("greenA", "#75BC42")   # 绿色箭头

    # ==================================================== 第一行：标题
    f.text(150, 128, "Indicator Selection", FS_TITLE, anchor="w")
    f.text(2018, 130, "Measurement Model", FS_TITLE, anchor="w")

    # ============================ 第一行左：指标选取（DEI / CEI 两个子面板）
    f.rbox(34, 190, 1549, 1673, r=115, fill="greenF", lw=12)
    f.rbox(114, 417, 688, 1618, r=70, fill="greenF", lw=8)
    f.rbox(868, 417, 1443, 1618, r=70, fill="greenF", lw=8)
    f.text(403.5, 359, "DEI", FS_DEI, style="italic")
    f.text(1165, 361, "CEI", FS_DEI, style="italic")

    # DEI：五个槽位（第四个是省略号），x 190..629，高 177，节距 217.5
    for y0, lab, base in [(475, "Domains", 590), (693, "IPv4", 808),
                          (910, "IAP", 1025), (1127, None, None),
                          (1357, "DFFD", 1472)]:
        f.dbox(190, y0, 629, y0 + 177, fill="greenB", lw=12, r=14)
        if lab:
            f.text(409, base, lab, FS_GREEN)
    f.dots(1235, 372.5, 408.5, 444.5, r=11.5)

    # CEI：四个槽位，x 944..1383，节距 294.3
    for y0, lab, base in [(469, "CE", 585), (763, "PCCE", 879),
                          (1058, "CED", 1174), (1352, "ECI", 1468)]:
        f.dbox(944, y0, 1383, y0 + 177, fill="greenB", lw=12, r=14)
        f.text(1163, base, lab, FS_GREEN)

    # 连接两个容器的绿色箭头
    f.poly([(1605, 885), (1770, 885), (1770, 833), (1865, 932),
            (1770, 1031), (1770, 977), (1605, 977)], fill="greenA", lw=8.5)

    # ==================================== 第一行右：测度模型（权重 + 地图 + CCD）
    f.rbox(1951, 195, 5778, 1678, r=115, fill="creamF", lw=12)

    for lab, y0, base in [("CRITIC", 359, 511), ("Spearman", 814, 963),
                          ("EWM", 1269, 1421)]:
        f.dbox(2031, y0, 2669, y0 + 227, fill="creamB", lw=12, r=14)
        f.text(2350, base, lab, FS_BOX)

    # 把三种赋权方法括起来的右向花括号，尖端指向地图框
    f.brace(x_end=2805, x_body=2831.5, x_tip=2900, y_top=458, y_bot=1397, lw=8)
    f.line([(2897, 926), (2982, 926)], lw=8)

    # 两个地图框：栅格内容从原图裁切后嵌入
    f.frame(3058, 235, 4327, 1183, fill="white", lw=12)
    f.frame(4384, 235, 5654, 1183, fill="white", lw=12)
    f.image(A("panel_dei_maps.png"), 3070, 247, 4315, 1171)
    f.image(A("panel_cei_maps.png"), 4396, 247, 5642, 1171)

    # 汇合到 CCD 模型的支架
    f.line([(3692, 1183), (3692, 1266.5), (5018, 1266.5), (5018, 1183)], lw=8)
    f.arrow_down(4354.5, 1266.5, 1351, lw=8, w_head=44, h_head=40)

    f.dbox(3319, 1351, 5391, 1614, fill="creamB", lw=12, r=14)
    f.text(4354, 1520, "Coupling Coordination Degree Model", FS_COUP)

    # ============================================== 三个橙色大箭头（换行）
    for cx in (2896.5, 3898.5, 4899.0):
        f.poly([(cx - 45.5, 1750), (cx + 45.5, 1750), (cx + 45.5, 1929),
                (cx + 80.5, 1929), (cx, 2002), (cx - 80.5, 1929),
                (cx - 45.5, 1929)], fill="orangF", lw=8)

    # ==================================================== 第二行：时空演化分析
    f.text(106, 2015, "Spatio-temporal Evolution Analysis", FS_TITLE, anchor="w")
    f.rbox(34, 2085, 5778, 3819, r=138, fill="cyanF", lw=12)

    f.frame(175, 2396, 1648, 3630, fill="white", lw=12)      # 面板 1
    f.frame(1796, 2396, 3858, 3630, fill=None, lw=12)        # 面板 2
    f.frame(3986, 2396, 5653, 3630, fill="white", lw=12)     # 面板 3

    f.text(1000.5, 2336, "Global and Local Moran's I", FS_PANEL)
    f.text(2828.5, 2336, "Spatial Markov", FS_PANEL)
    f.text(4818.0, 2336, "Kernel Density Estimation", FS_PANEL)

    f.image(A("panel_moran_map.png"), 187, 2408, 1636, 3618)
    f.image(A("panel_kde_3d.png"), 3998, 2408, 5641, 3618)

    # 面板 2：空间马尔可夫链流程
    f.dbox(2349, 2476, 3297, 2703, fill="cyanB", lw=12, r=14)
    f.text(2823, 2628, "Local Moran's I", FS_BOX)
    f.arrow_down(2824, 2703, 2811, lw=8, w_head=44, h_head=40)

    f.dbox(2249, 2811, 3404, 3123, fill="cyanB", lw=12, r=14)
    f.text(2826, 2938, "Markov Transition", FS_BOX)
    f.text(2826, 3072, "Matrix", FS_BOX)

    f.line([(2826, 3123), (2826, 3175)], lw=8)                # 一分为二
    f.line([(2314, 3175), (3306, 3175)], lw=8)
    f.arrow_down(2314, 3175, 3229, lw=8, w_head=42, h_head=42)
    f.arrow_down(3306, 3175, 3229, lw=8, w_head=42, h_head=42)

    f.dbox(1867, 3229, 2761, 3541, fill="cyanB", lw=12, r=14)
    f.text(2314.0, 3355, "Temporal", FS_BOX)
    f.text(2314.0, 3488, "heterogeneity", FS_BOX)

    f.dbox(2859, 3229, 3753, 3541, fill="cyanB", lw=12, r=14)
    f.text(3306.0, 3355, "Spatial", FS_BOX)
    f.text(3306.0, 3488, "heterogeneity", FS_BOX)
    return f


def render(out_dir=None):
    out = out_dir or os.path.join(HERE, "out")
    os.makedirs(out, exist_ok=True)
    f = build()
    pdf = f.save_matplotlib(os.path.join(out, "fig1_matplotlib.pdf"))
    png = f.save_matplotlib(os.path.join(out, "fig1_matplotlib.png"), png_dpi=300)
    tex = f.save_tikz(os.path.join(out, "fig1_tikz.tex"),
                      cjk_font=None)          # 需要中文时传 "SimSun"
    # TikZ 版按文件名引用嵌图，把 assets 里的图拷到 out/ 旁边
    import shutil
    for n in ("panel_dei_maps.png", "panel_cei_maps.png",
              "panel_moran_map.png", "panel_kde_3d.png"):
        shutil.copyfile(os.path.join(HERE, "assets", n), os.path.join(out, n))
    return f, dict(pdf=pdf, png=png, tex=tex)


if __name__ == "__main__":
    f, paths = render()
    print("画布: %.0f x %.0f px -> %.1f x %.1f mm (native dpi %.1f)"
          % (f.width_px, f.height_px, f.width_mm, f.height_mm, f.native_dpi))
    for k, v in paths.items():
        print("  %-4s %s" % (k, v))
