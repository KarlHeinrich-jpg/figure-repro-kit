---
name: figure-repro-kit
description: 把期刊论文里的位图式研究框架图/流程图/技术路线图复刻成可编辑的矢量图，同一份图形描述同时输出 matplotlib（PDF/PNG）与 LaTeX/TikZ，并用逐像素比对验收。触发词：复刻流程图、复刻论文图、框架图矢量化、重画论文插图、figure reproduction、redraw paper figure、matplotlib 画框架图、TikZ 框架图、改论文图里的字、图太糊想重画。
---

# figure-repro-kit — 论文插图复刻

把已发表论文里那张"放大就糊、想改一个字都不行"的框架图/流程图，复刻成可编辑的
矢量图（matplotlib 与 TikZ 两版，同一套坐标）。

## 什么时候用

* 要在自己的论文/汇报里重画一张别人（或自己旧作）的框架图，想改指标名、换配色、
  换语言。
* 期刊要求矢量图，手里的图只有位图。
* 想照着某张图的风格画一张**结构相同、内容不同**的新图。

不要用它去逐像素重画折线图、散点图、热力图——那些应该用原始数据重新绘图。
本工具针对的是**线框 + 文字 + 少量嵌入位图**这一类图。

## 核心不变式

1. **坐标即原图像素**（y 向下），画完可以拿原图直接对账。
2. **一套描述、两个后端**：`Figure` 对象交给 `save_matplotlib()` 或 `save_tikz()`。
   绝不手写两份代码——那是脱节的开始。
3. **长度一律用 px**（线宽、虚线节奏、圆角、字号 em 高），换算由 `width_mm/width_px`
   推出。不要手算磅值。
4. **矩形给描边外沿，文字给基线**。
5. **无法矢量重画的内容（地图、三维曲面）按外框内沿裁切后嵌入**，其余全部重画矢量。

## 五步流程

```bash
# 1) 提取原图（自动拼接被排版切成条带的插图）
python tools/extract_figure.py paper.pdf --page 4 --out qa/reference.png

# 2) 量化版式
python tools/measure_figure.py qa/reference.png --colors
python tools/measure_figure.py qa/reference.png --row 1000
python tools/measure_figure.py qa/reference.png --col 400
python tools/measure_figure.py qa/reference.png --box x0,y0,x1,y1
python tools/measure_figure.py qa/reference.png --dash-y Y --range X0,X1
python tools/measure_figure.py qa/reference.png --text x0,y0,x1,y1

# 3) 写 Figure 脚本（参考 examples/ 里的示例）
# 4) 出图
python examples/<case>/build.py

# 5) 逐像素验收
python tools/verify.py qa/reference.png out/fig.pdf --mm-per-px <K>
```

验收标准：平均绝对灰度差 **< 12** 为通过；12–45 去查最差分块；> 45 说明有元素
缺失或整体错位。几何应对齐到 1 px 以内。

## 字体

* 英文：Times New Roman（`\setmainfont` + matplotlib 的 `font.serif`）。
* 中文：SimSun；TikZ 里 `save_tikz(..., cjk_font="SimSun")` 会自动加
  `\setCJKmainfont{SimSun}[AutoFakeBold=2.5]`。SimSun 没有粗体，标题靠
  `AutoFakeBold` 或加一号字重。
* 必须用 **xelatex** 编译（fontspec）。
* 中文不要用 `\itshape` / 斜体（会得到假斜体）。

## 已知陷阱（详见 docs/pitfalls.md）

* `FancyBboxPatch` 的 `round` 盒样式**以给定矩形为外框**，再自己减一次圆角半径
  会让所有圆角框缩小。
* matplotlib 的描边**沿路径居中**；若坐标记的是外沿，路径要内缩半个线宽。
* `savefig` 不显式给 `dpi` 时，PDF 里的嵌图会按 figure dpi 降采样，印出来发虚。
* TikZ 的 `dash pattern` 必须定义成 `\tikzset` 的 style，直接展开宏会报
  `\tikz@scandashon doesn't match its definition`。
* TikZ `standalone` 的页面**按内容裁边**，不能按"目标宽度"去渲染比对，要按
  "每个源像素对应一个输出像素"的 zoom 渲染。
* 量虚线节奏必须限定扫描范围，否则会扫到别的框的竖直边框，把中位数带偏。
* 虚线框的填充会从缝隙漏出，包围盒比真实内沿大 5–7 px，边界要用描边中位数测。
