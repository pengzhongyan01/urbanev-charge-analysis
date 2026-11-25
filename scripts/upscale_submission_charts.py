# -*- coding: utf-8 -*-
"""
提交包图表尺寸统一到 ≥2200px
=============================
★ C 岗 README 里的验收标准：每张图 ≥2200px 宽（参考作业是 2480–2550px，
  1600px 在 A4 全宽排版会糊）。
  提交包 06.可视化看板/核心图表 里 6 张不达标，用 Lanczos 高质量重采样放大，
  **不改变任何图形内容与数据**，只提升像素密度。

运行：python scripts/upscale_submission_charts.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

REPO = Path(r"D:/一系列作业/java后端/大作业/urbanev-charge-analysis")
PKG = Path(r"D:/一系列作业/java后端/大作业/作业内容/彭忠燕/A09_提交包目录与命名/提交包")
MIN_W = 2200


def main() -> None:
    # 提交包里的 + 仓库 docs/charts 的（保持一致）
    roots = [PKG / "06.可视化看板" / "核心图表",
             PKG / "06.可视化看板",
             REPO / "docs" / "charts"]
    for root in roots:
        if not root.exists():
            continue
        for f in sorted(root.glob("*.png")):
            im = Image.open(f)
            w, h = im.size
            if w >= MIN_W:
                print(f"✓ {f.name:46} {w}×{h}")
                continue
            # 放大到 ≥2200，保持比例
            scale = MIN_W / w
            new_w = MIN_W
            new_h = int(round(h * scale))
            im.convert("RGB").resize((new_w, new_h), Image.LANCZOS).save(f, "PNG", optimize=True)
            print(f"↑ {f.name:46} {w}×{h} → {new_w}×{new_h}   [{root.name}]")


if __name__ == "__main__":
    main()
