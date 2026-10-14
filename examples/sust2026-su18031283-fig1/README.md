# 示例：复刻 Sustainability 2026, 18, 1283 的 Figure 1

被复刻的图：**Figure 1 "Research framework"**，出自

> Yang, X. et al. *Mapping the Coupling Coordination between Digital Economy and
> Carbon Emissions: Spatiotemporal Patterns and Spatial Markov Transitions.*
> **Sustainability 2026, 18, 1283.** doi:[10.3390/su18031283](https://doi.org/10.3390/su18031283)
> （MDPI，CC BY 4.0）

该图在原 PDF 里是一张 5811 × 3837 的位图（被排版切成 3 条嵌入）。
本目录把它复刻成矢量图：线框、虚线框、箭头、花括号、连接支架和全部文字都重画，
四块地图/三维核密度曲面按外框内沿从原图裁切后嵌入。

## 文件

| 文件 | 说明 |
|---|---|
| `make_figure.py` | **唯一的图形描述**（两版共用），坐标即原图像素 |
| `build.py` | 出图 → xelatex 编译 → 与原图逐像素比对 |
| `assets/panel_*.png` | 从原图裁切的四块栅格内容（CC BY 4.0，见仓库 LICENSE） |
| `qa/reference.png` | 从原论文提取的整图，作为比对基准（CC BY 4.0） |
| `qa/cmp_*.png` | 校验产物：对齐后的复刻图 + 上下对照图 |
| `out/` | 成品：`fig1_matplotlib.pdf/.png`、`fig1_tikz.tex/.pdf/.png` |

## 跑一遍

```bash
python build.py
```

预期输出：

```
画布 5811 x 3837 px -> 170.0 x 112.3 mm（native dpi 868.2）
  出图 pdf  out\fig1_matplotlib.pdf
  出图 png  out\fig1_matplotlib.png
  出图 tex  out\fig1_tikz.tex
  出图 tikz out\fig1_tikz.pdf

与原图逐像素比对（参考图 5811x3837）：
  matplotlib   平移=(0,0)   平均差=10.19   OK
  tikz         平移=(34,20) 平均差=8.58    OK
```

平移量不是 (0,0) 是正常的：matplotlib 版的 PDF 页面就是整个画布，所以偏移为 0；
TikZ 版由 `standalone` 按内容裁边，所以比画布少了左 34 px、上 20 px 的空白。
校验工具会自动求出这个偏移再比对。

## 版式参数（量测结果，直接支撑脚本里那些数字）

| 项目 | 实测值（原图像素） |
|---|---|
| 画布 | 5811 × 3837 |
| 容器描边 | 12 px ；子面板 8 px |
| 圆角半径 | 行 1 容器 115 / 行 2 容器 138 / 子面板 70 / 虚线框 14 |
| 虚线节奏 | 实线 47 px / 空档 38 px |
| 填充色 | `#F0F8EB` `#C9E5B4` `#FEF7F1` `#FCE7D6` `#EAF9F9` `#D4F4F1` `#EF822F` `#75BC42` |
| 字号（em 高） | 大标题 160 / 面板标题 126.7 / DEI·CEI 142.2 / 框内文字 114.4 / CCD 111.1 / 指标小框 81.6 |

## 换成自己的图

1. `cp -r examples/sust2026-su18031283-fig1 examples/<你的图>`，把 `qa/reference.png`
   换成你要复刻的图。
2. 用 `tools/measure_figure.py` 重新量一遍参数（见 `docs/workflow.md` 第 ② 步）。
3. 改 `make_figure.py` 里的坐标、文字和配色。结构类似的图，改十几行就能换一张。
