# figure-repro-kit

把期刊论文里的**位图式**研究框架图 / 流程图，复刻成可编辑、可投稿的矢量图。

一套坐标，两个后端：同一份图形描述同时输出 **matplotlib**（PDF/PNG）和
**LaTeX/TikZ**（xelatex 编译）。坐标直接用原图的像素坐标，所以画出来的每一根线、
每一个字都能和原图逐像素对账。

- 示例复刻：[Sustainability 2026, 18, 1283](https://doi.org/10.3390/su18031283) 的 Figure 1
- 校验结果：matplotlib 版与原图平均灰度差 **10.2/255**，TikZ 版 **8.6/255**
  （几何对齐到 1 px 以内，残余差异仅来自字体光栅化与虚线相位）
- English: [README.en.md](README.en.md)

---

## 为什么要"先量后画"

论文插图在 PDF 里往往是一整张位图：放大发虚、无法改字、审稿人要求改一个指标就得重做。
拿眼睛照着缩略图重画，几乎必然出现整体偏移、线宽不对、字号偏小、虚线节奏不对这些
问题——而且自己看不出来，印出来才发现。

这个工具包把流程倒过来：**先把原图量化，再照数字重画**，最后用逐像素比对验收。

```
提取原图  →  量出版式参数  →  写图形描述  →  两后端出图  →  逐像素校验
raster.py     measure.py      Figure(...)    canvas/tikz    verify.py
```

## 快速上手

```bash
pip install pymupdf pillow numpy matplotlib      # 只有这些依赖
git clone <this-repo> && cd figure-repro-kit
```

### 1. 把原图从 PDF 里捞出来

```bash
python tools/extract_figure.py paper.pdf --page 4 --list      # 先看这页有什么
python tools/extract_figure.py paper.pdf --page 4 --out qa/reference.png
```

期刊排版常把一张大图**切成几条**分别嵌入，脚本会按显示位置拼接回去——
直接取单张只会得到一条窄带。

### 2. 量出版式参数

```bash
python tools/measure_figure.py qa/reference.png --colors
python tools/measure_figure.py qa/reference.png --row 1000          # 找竖线
python tools/measure_figure.py qa/reference.png --col 400           # 找横线
python tools/measure_figure.py qa/reference.png --box 2031,359,2669,586
python tools/measure_figure.py qa/reference.png --dash-y 364 --range 2030,2680
python tools/measure_figure.py qa/reference.png --text 2270,2830,3390,3110
```

得到的就是"描边外沿坐标 / 线宽 / 虚线 on-off / 填充色 / 每行文字的包围盒与基线"。

### 3. 写图形描述（唯一的一份）

```python
from figrepro import Figure

f = Figure(width_px=5811, height_px=3837, width_mm=170)   # 170 mm = 期刊双栏
f.color("greenF", "#F0F8EB")

f.rbox(34, 190, 1549, 1673, r=115, fill="greenF", lw=12)   # 坐标即原图像素
f.dbox(2031, 359, 2669, 586, fill="creamB", lw=12, r=14, dash=(47, 38))
f.text(150, 128, "Indicator Selection", size_px=160, anchor="w")
f.arrow_down(2824, 2703, 2811, lw=8)
f.brace(x_end=2805, x_body=2831.5, x_tip=2900, y_top=458, y_bot=1397, lw=8)
f.image("assets/panel_dei_maps.png", 3070, 247, 4315, 1171)

f.save_matplotlib("out/fig1.pdf")
f.save_tikz("out/fig1.tex")          # 同一个 f，另一套后端
```

约定：

| 项 | 约定 |
|---|---|
| 坐标 | 原图像素，**y 向下**，和原图可以直接对账 |
| 矩形 | 给的是**描边外沿**（不是中心线） |
| 文字 | 给的是**基线**，字号给 **em 高度（px）**，不用手算磅值 |
| 长度 | 线宽、虚线节奏、圆角半径一律用 px；换算由画布宽度推出 |

### 4. 出图与编译

```bash
cd examples/sust2026-su18031283-fig1
python build.py            # 出图 + xelatex 编译 + 与原图逐像素校验
```

### 5. 逐像素验收

```bash
python tools/verify.py qa/reference.png out/fig1_matplotlib.pdf --mm-per-px 0.029254
```

```
平移        (0, 0)
平均绝对差  10.19  (0-255)
最差分块    (40 @ y=2800 x=2400), (36 @ y=2200 x=5200), ...
判读        几乎只差字体光栅化与虚线相位，肉眼不可分辨
```

经验阈值：

| 平均差 | 含义 |
|---|---|
| < 12 | 几乎只剩字体光栅化与虚线相位差异，肉眼与打印不可分辨 |
| 12–45 | 有整体偏移 / 字号偏差 / 嵌图被降采样，去查最差分块的位置 |
| > 45 | 明显不对：元素缺失或位置整体错位 |

## 什么该重画，什么该嵌

| 内容 | 做法 |
|---|---|
| 线框、虚线框、箭头、花括号、连接支架 | **重画矢量**（可改、可缩放、印刷锐利） |
| 文字 | **重画矢量**（字号按原图量化，字体自带） |
| 地图、三维曲面、词云、热力图 | **从原图裁切嵌入**（按外框内沿精确裁切，保持原分辨率） |

嵌入的栅格图会按原分辨率写进 PDF（`Figure.native_dpi`），不会被打成 100 dpi 的糊图——
这是 matplotlib 默认行为里最容易踩的一个坑，见 [docs/pitfalls.md](docs/pitfalls.md)。

> 复用他人已发表图的局部内容时请确认许可（MDPI / Frontiers 等开放获取期刊通常为
> CC BY，署明出处即可）。本仓库示例图的来源见下方"出处与许可"。

## 目录

```
figrepro/            可复用的包
  canvas.py            Figure 描述 + matplotlib 后端
  tikz.py              同一描述的 TikZ 后端
  raster.py            从 PDF 提取/拼接/裁切原图
  measure.py           描边、填充、虚线、文字的自动量测
  verify.py            自动对齐 + 逐像素差值报告
tools/               三个命令行工具
docs/workflow.md     完整工作流（含每一步的判断标准）
docs/pitfalls.md     踩过的坑清单（12 条，每条都有症状与成因）
examples/            示例：复刻一张真实的期刊框架图（两版成品 + 校验图）
```

## 出处与许可

* 代码：MIT，见 [LICENSE](LICENSE)。
* 示例图复刻自：*Sustainability* **2026**, *18*, 1283（MDPI，CC BY 4.0）的
  Figure 1 "Research framework"，doi:10.3390/su18031283。
  示例目录内的 `qa/reference.png` 与 `assets/panel_*.png` 是该图的提取/裁切结果，
  同样按 CC BY 4.0 使用，署名见示例目录的 README。
