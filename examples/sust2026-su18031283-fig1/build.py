# -*- coding: utf-8 -*-
"""
一键：出图 -> 编译 TikZ -> 与原图逐像素校验。

    python build.py

校验需要 qa/reference.png（从原论文 PDF 里提取的整图，见 README 的
"复现校验" 一节）。没有它时脚本仍会出图并编译 TikZ，只是跳过比对。
"""

import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))

import make_figure                                            # noqa: E402
from figrepro import verify                                   # noqa: E402

OUT = os.path.join(HERE, "out")
QA = os.path.join(HERE, "qa")
REF = os.path.join(QA, "reference.png")


def compile_tikz(tex, workdir):
    """用 xelatex 编译 standalone TikZ；找不到就跳过。"""
    exe = shutil.which("xelatex")
    if not exe:
        print("[skip] 没找到 xelatex，跳过 TikZ 编译")
        return None
    r = subprocess.run([exe, "-interaction=nonstopmode", "-halt-on-error",
                        os.path.basename(tex)],
                       cwd=workdir, capture_output=True, text=True)
    pdf = os.path.splitext(tex)[0] + ".pdf"
    if r.returncode != 0 or not os.path.exists(pdf):
        tail = "\n".join(r.stdout.splitlines()[-15:])
        print("[fail] xelatex 编译失败：\n" + tail)
        return None
    for ext in (".aux", ".log", ".out"):
        p = os.path.splitext(tex)[0] + ext
        if os.path.exists(p):
            os.remove(p)
    return pdf


def main():
    f, paths = make_figure.render()
    print("画布 %.0f x %.0f px -> %.1f x %.1f mm（native dpi %.1f）"
          % (f.width_px, f.height_px, f.width_mm, f.height_mm, f.native_dpi))
    for k in ("pdf", "png", "tex"):
        print("  出图 %-4s %s" % (k, os.path.relpath(paths[k], HERE)))

    tikz_pdf = compile_tikz(paths["tex"], OUT)
    if tikz_pdf:
        png = os.path.splitext(tikz_pdf)[0] + ".png"
        verify.render_pdf(tikz_pdf, out_path=png, mm_per_px=f.mm_per_px * 2.4)
        print("  出图 tikz %s" % os.path.relpath(tikz_pdf, HERE))

    if not os.path.exists(REF):
        print("\n[skip] 没有 %s，跳过与原图的逐像素校验。" % os.path.relpath(REF, HERE))
        return 0

    from PIL import Image
    ref = Image.open(REF).convert("RGB")
    print("\n与原图逐像素比对（参考图 %dx%d）：" % ref.size)
    rc = 0
    for tag, pdf in (("matplotlib", paths["pdf"]),
                     ("tikz", tikz_pdf)):
        if not pdf or not os.path.exists(pdf):
            continue
        img = verify.render_pdf(pdf, mm_per_px=f.mm_per_px)
        res = verify.compare(ref, img, out_dir=QA, tag="cmp_" + tag, search=260)
        ok = res["mean_abs_diff"] < 12
        rc = rc or (0 if ok else 1)
        print("  %-12s 平移=(%d,%d)  平均差=%.2f   %s"
              % (tag, res["offset"][0], res["offset"][1],
                 res["mean_abs_diff"], "OK" if ok else "偏差偏大"))
        print("               最差分块 %s" % (res["worst_blocks"][:4],))
    print("\n对照图已写入 %s" % os.path.relpath(QA, HERE))
    return rc


if __name__ == "__main__":
    sys.exit(main())
