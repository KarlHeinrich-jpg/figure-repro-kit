# figure-repro-kit

Reproduce a **raster** research-framework / flowchart figure from a journal paper as
an editable, submission-ready **vector** figure.

One coordinate table, two backends: the same figure description renders to
**matplotlib** (PDF/PNG) *and* to **LaTeX/TikZ** (compiled with xelatex). Every
coordinate is given in the *source figure's pixel grid*, so every line and every glyph
can be audited against the original pixel by pixel.

- Demo reproduction: Figure 1 of [Sustainability 2026, 18, 1283](https://doi.org/10.3390/su18031283)
- Verification: mean absolute grey-level difference against the original —
  **10.2/255** (matplotlib) and **8.6/255** (TikZ); geometry aligned to within 1 px.
  What remains is font rasterisation and dash phase only.
- 中文说明见 [README.md](README.md)

---

## Why measure first, then draw

Figures in a published PDF are usually a single flat bitmap: blurry when zoomed,
impossible to re-word, and any reviewer request ("rename that indicator") means
redrawing. Rebuilding one by eye from a thumbnail reliably produces a global offset,
wrong stroke widths, undersized type and wrong dash rhythm — and you cannot see it on
screen, only in print.

This kit inverts the workflow: **quantify the original first, then draw from the
numbers**, and accept the result with a pixel-level diff.

```
extract      →  measure        →  write the spec  →  render both   →  verify
raster.py       measure.py        Figure(...)        canvas / tikz    verify.py
```

## Quick start

```bash
pip install pymupdf pillow numpy matplotlib      # the only dependencies
git clone <this-repo> && cd figure-repro-kit
```

### 1. Pull the original figure out of the PDF

```bash
python tools/extract_figure.py paper.pdf --page 4 --list      # what's on that page?
python tools/extract_figure.py paper.pdf --page 4 --out qa/reference.png
```

Journal layout engines frequently split a large figure into **several strips** and embed
them separately; the script re-assembles them by display position. Taking a single
embedded image gets you a narrow band, not the figure.

### 2. Measure the layout

```bash
python tools/measure_figure.py qa/reference.png --colors
python tools/measure_figure.py qa/reference.png --row 1000          # find verticals
python tools/measure_figure.py qa/reference.png --col 400           # find horizontals
python tools/measure_figure.py qa/reference.png --box 2031,359,2669,586
python tools/measure_figure.py qa/reference.png --dash-y 364 --range 2030,2680
python tools/measure_figure.py qa/reference.png --text 2270,2830,3390,3110
```

You get stroke **outer-edge** coordinates, stroke widths, dash on/off lengths, fill
colours, and per-line text bounding boxes with baselines.

### 3. Write the figure spec (the single source of truth)

```python
from figrepro import Figure

f = Figure(width_px=5811, height_px=3837, width_mm=170)   # 170 mm = journal double column
f.color("greenF", "#F0F8EB")

f.rbox(34, 190, 1549, 1673, r=115, fill="greenF", lw=12)   # coordinates = source pixels
f.dbox(2031, 359, 2669, 586, fill="creamB", lw=12, r=14, dash=(47, 38))
f.text(150, 128, "Indicator Selection", size_px=160, anchor="w")
f.arrow_down(2824, 2703, 2811, lw=8)
f.brace(x_end=2805, x_body=2831.5, x_tip=2900, y_top=458, y_bot=1397, lw=8)
f.image("assets/panel_dei_maps.png", 3070, 247, 4315, 1171)

f.save_matplotlib("out/fig1.pdf")
f.save_tikz("out/fig1.tex")          # same f, other backend
```

Conventions:

| Item | Convention |
|---|---|
| Coordinates | source-figure pixels, **y increases downwards** — auditable against the original |
| Rectangles | the **outer edge** of the stroke (not the centreline) |
| Text | the **baseline**, with the size given as **em height in px** — no point arithmetic |
| Lengths | stroke width, dash rhythm and corner radius all in px; conversion follows from the canvas width |

### 4. Render and compile

```bash
cd examples/sust2026-su18031283-fig1
python build.py            # render + xelatex + pixel-level verification
```

### 5. Accept with a pixel diff

```bash
python tools/verify.py qa/reference.png out/fig1_matplotlib.pdf --mm-per-px 0.029254
```

```
offset      (0, 0)
mean abs diff  10.19  (0-255)
worst blocks   (40 @ y=2800 x=2400), (36 @ y=2200 x=5200), ...
verdict        font rasterisation and dash phase only -- indistinguishable in print
```

| Mean diff | Meaning |
|---|---|
| < 12 | only font rasterisation and dash phase differ; indistinguishable on screen and in print |
| 12–45 | a global offset, a font-size error, or a downsampled embedded image — look at the worst blocks |
| > 45 | clearly wrong: missing elements or a globally misplaced item |

## What to redraw, what to embed

| Content | Approach |
|---|---|
| Frames, dashed boxes, arrows, braces, brackets | **redraw as vectors** (editable, scalable, crisp) |
| All text | **redraw as vectors** (size quantified from the original, fonts embedded) |
| Maps, 3-D surfaces, word clouds, heatmaps | **crop and embed** from the original (cut exactly at the frame's inner edge, keep native resolution) |

Embedded rasters are written into the PDF at **native resolution** (`Figure.native_dpi`).
matplotlib's default behaviour would downsample them to the figure dpi and print soft —
see [docs/pitfalls.md](docs/pitfalls.md).

> When reusing parts of someone else's published figure, check the licence. Open-access
> journals (MDPI, Frontiers, …) are usually CC BY: attribution is enough. The demo
> figure's provenance is listed under "Provenance & licence" below.

## Layout

```
figrepro/            the reusable package
  canvas.py            Figure spec + matplotlib backend
  tikz.py              TikZ backend for the same spec
  raster.py            extract / stitch / crop the original from a PDF
  measure.py           automatic measurement of strokes, fills, dashes, text
  verify.py            auto-alignment + pixel-diff report
tools/               three command-line tools
docs/workflow.md     the full workflow, with the decision rule at every step
docs/pitfalls.md     the 12 traps we hit, each with symptom and cause
examples/            a real journal framework figure, both backends + QA images
```

## Provenance & licence

* Code: MIT, see [LICENSE](LICENSE).
* The demo figure reproduces Figure 1 "Research framework" of *Sustainability*
  **2026**, *18*, 1283 (MDPI, CC BY 4.0), doi:10.3390/su18031283.
  `qa/reference.png` and `assets/panel_*.png` inside the example directory are
  extractions/crops of that figure and are used under the same CC BY 4.0 terms;
  see the example directory's README for the attribution.
