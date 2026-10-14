# 踩过的坑

每一条都是这次复刻真实踩到的，附带症状、成因和正确做法。按"最费时间"排序。

---

## 1. `FancyBboxPatch` 的圆角会二次内缩

```python
# 错：所有圆角框整体缩小 2r
FancyBboxPatch((x0 + r, y0 + r), w - 2*r, h - 2*r,
               boxstyle=f"round,pad=0,rounding_size={r}")
```

**症状**：一次性所有圆角容器（外框、子面板）都变小了，且缩小的幅度正好等于两倍
圆角半径。文字位置却是对的，于是"文字跑到框外面"。

**成因**：`round` 盒样式本身就**以传入的矩形为外框**在四角内切圆角；常见的"先减
2r 再传"的写法是另一套 API（`pad` + 外扩）的遗留习惯，两者混用就多减了一次。

**正确**：

```python
FancyBboxPatch((x0, y0), x1 - x0, y1 - y0,
               boxstyle=f"round,pad=0,rounding_size={r}", mutation_scale=1)
```

（`mutation_scale=1` 表示 `rounding_size` 用数据单位而不是字号倍数。）

---

## 2. 描边沿路径居中，而量出来的坐标是外沿

**症状**：所有线框整体向外偏了半个线宽（比如 12 px 线框偏 6 px），叠加起来画面
"发胖"，叠图时能看到红绿两条平行边。

**成因**：matplotlib / TikZ / SVG 都是**沿路径居中描边**；而从原图量出来的是墨迹的
外沿。

**正确**：画之前把矩形内缩 `lw/2`（圆角半径同时减 `lw/2`）：

```python
h = lw / 2
Rectangle((x0 + h, y0 + h), (x1 - x0) - lw, (y1 - y0) - lw, lw=...)
```

`figrepro` 的两个后端都已经这样处理，传进去的 `x0,y0,x1,y1` 就是外沿。

---

## 3. 导 PDF 时嵌图被降采样

**症状**：矢量部分清晰锐利，但嵌进去的地图/三维图在放大或打印时发虚。PDF 里查
一下嵌图分辨率，发现只有几百像素宽。

**成因**：`savefig(pdf)` 的 `dpi` 默认是 `'figure'`，而 `plt.figure(figsize=...)`
的 `dpi` 默认是 100。于是所有嵌图按 100 dpi 光栅化后写进 PDF。

**正确**：给足 dpi，让嵌图按原分辨率落盘：

```python
fig = plt.figure(figsize=(W/DPI, H/DPI), dpi=DPI)
fig.savefig("out.pdf", dpi=DPI)          # DPI = 画布像素宽 / 画布英寸宽
```

`Figure.native_dpi` 就是这个值。

---

## 4. TikZ 的 `dash pattern` 不能从宏展开

```latex
\def\dsP{on 4pt off 3pt}
\draw[dash pattern=\dsP] ...     % ! Use of \tikz@scandashon doesn't match its definition
```

**正确**：定义成 style 再用：

```latex
\tikzset{boxdash/.style={dash pattern=on 4pt off 3pt}}
\draw[boxdash] ...
```

---

## 5. TikZ `standalone` 的页面是裁过边的

**症状**：TikZ 版怎么对齐都对不上，平均差三四十，最差分块集中在图像边缘。

**成因**：`standalone` 把页面裁到内容边界。画布宽 170 mm 的图，页面只有 168 mm
（左右各少 1 mm 空白）。若按"把页面渲染成参考图那么宽"来比对，整张图被放大
1.2%，边缘处就错开三十多像素，平移对齐根本无解。

**正确**：按"**一个源像素对应一个输出像素**"渲染：

```python
zoom = 25.4 / (mm_per_px * 72.0)          # 输出像素 / PDF 点
pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
```

这样 matplotlib 版（页面 = 整画布）与 TikZ 版（页面 = 裁边后的内容）都落在同一个
像素网格上，只差一个平移。`verify.render_pdf(..., mm_per_px=K)` 已经封装好。

---

## 6. 字号换算把毫米当磅用

**症状**：TikZ 版的字全部只有应有大小的三分之一。

**成因**：缩放系数写成 `170 / (5811 * 72/800)`——分子是毫米、分母是磅，量纲不一致。

**正确**：两头都换成磅再比：

```python
S = (width_mm / 25.4 * 72.0) / (width_px * 72.0 / dpi)
```

**更根本的做法**：字号也用"原图像素"给（em 高），由画布宽度统一换算，从此不会
再出现量纲混用。`figrepro` 采用的就是这个约定。

---

## 7. 量虚线节奏必须限定范围

**症状**：明明是一段 48 px 实线 / 36 px 空档的虚线，量出来却是 12 / 36。

**成因**：整行扫过去，扫到别的框的竖直边框（每条 8–12 px），中位数被这些短线
带偏。

**正确**：把扫描范围收在被测的那条边上：`--dash-y 364 --range 2030,2680`。

---

## 8. 虚线框的填充会"漏"

**症状**：用填充色包围盒反推虚线框的边界，得到的位置比实际大 5–7 px，逐像素比对
时每条虚线框都差几个像素。

**成因**：填充色从虚线的空隙里透出去，包围盒因此被撑大。

**正确**：边界要用**描边**来量，而且在多条扫描线上取中位数（躲开虚线空档）：

```python
measure.stroke_edge(img, expected=475, lo=415, hi=535, along=(190, 629), axis="v")
```

---

## 9. `codes` 里三个连续 `C` 才是一段曲线

**症状**：生成 TikZ 时报 `IndexError`，或者曲线被拉得乱七八糟。

**成因**：matplotlib 的路径 codes 约定里，`CURVE4` 是**逐顶点**标注的，三个连续的
`CURVE4` 才构成一段三次贝塞尔。若把每个 `C` 都当成消耗三个点，索引会跑飞。

**正确**：按三个一组消费：

```python
while j < len(codes):
    if codes[j] == "C":
        emit(pts[i], pts[i+1], pts[i+2]); i += 3; j += 3
```

---

## 10. LaTeX 里 `\fbox` 是内置命令

**症状**：`! LaTeX Error: Command \fbox already defined.`

**成因**：自定义宏与 LaTeX 内核重名。同类的还有 `\frame`、`\box`、`\arc` 等。

**正确**：起名带前缀（`\pframe`），或改用 `\providecommand` / `\renewcommand` 前
先想清楚是否真要覆盖。

---

## 11. `pymupdf` 的 `set_dpi` 只收整数

**症状**：`TypeError: argument 2 of type 'int'`。

**成因**：`get_pixmap(dpi=868.2)` 内部把它转成整数 dpi 设置，浮点会报错。

**正确**：要么取整（会带来 0.1% 的尺度误差，跨整幅图几像素，够用了），要么用
`matrix=Matrix(z, z)` 给精确缩放（推荐，见第 5 条）。

---

## 12. 期刊会把一张图切成几条嵌入

**症状**：从 PDF 取图，拿到的是一条又扁又窄的带子，或者上下顺序错乱。

**成因**：排版引擎把宽图横向切片后分多个 image XObject 嵌入，每个还带各自的显示
矩形。

**正确**：按显示矩形的 y 坐标排序后拼接，并且只合并**同宽、同 x 范围**的那些
（用 xref 家族判断不可靠）。`raster.extract_figure()` 已实现。

---

## 附：字体与 hinting

`text.hinting` 关掉（`"none"`）。开了 hinting 后字形的推进宽度会被取整到整像素，
于是"量出来的行宽"和"画出来的行宽"不再一致，逐像素比对时文字会有系统性偏移。
`figrepro` 默认已关闭。

中文字体不要用 `\itshape` 或 matplotlib 的 `italic`——SimSun 没有斜体，会得到机械
倾斜的假斜体。要强调就用字号或粗细对比。
