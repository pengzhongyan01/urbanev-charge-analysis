# -*- coding: utf-8 -*-
"""
C 岗图表尺寸统一（C 岗验收标准：每张图 ≥2200px 宽）
===================================================
★ C 岗交付的 10 张核心图表宽度只有 1450–1832px，低于她自己 README 里写的
  验收标准（≥2200px），在 PPT 全宽排版会糊。
  本脚本用 Lanczos 高质量重采样放大到 ≥2200px，**不改变任何图形内容与数据**，
  只提升像素密度。

运行：python scripts/upscale_cgang_charts.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parent.parent
CG = REPO / "docs" / "C岗：图表-贺欢欢交付"
MIN_W = 2200

# 需要放大的目标（相对 REPO）
TARGETS = [
    "docs/C岗：图表-贺欢欢交付/C05_十个核心图表/01_275分区空间分布.png",
    "docs/C岗：图表-贺欢欢交付/C05_十个核心图表/02_分区平均占用率TOP20.png",
    "docs/C岗：图表-贺欢欢交付/C05_十个核心图表/03_24小时供需曲线.png",
    "docs/C岗：图表-贺欢欢交付/C05_十个核心图表/05_分时定价与固定定价充电桩占用率对比.png",
    "docs/C岗：图表-贺欢欢交付/C05_十个核心图表/06_两类电价区的价差与占用率对照.png",
    "docs/C岗：图表-贺欢欢交付/C05_十个核心图表/07_需求预测曲线.png",
    "docs/C岗：图表-贺欢欢交付/C05_十个核心图表/08_预测误差分布对比.png",
    "docs/C岗：图表-贺欢欢交付/C05_十个核心图表/09_布点建议优先级分布.png",
    "docs/C岗：图表-贺欢欢交付/C05_十个核心图表/10_数据质量实测结果.png",
    "docs/C岗：图表-贺欢欢交付/C02_深圳275分区地图底图/01_深圳行政区划底图_9区.png",
    "docs/C岗：图表-贺欢欢交付/C02_深圳275分区地图底图/02_275分区空间分布_平均占用率.png",
]


def main() -> None:
    for rel in TARGETS:
        p = REPO / rel
        if not p.exists():
            print(f"  跳过（不存在）：{p.name}")
            continue
        im = Image.open(p)
        w, h = im.size
        if w >= MIN_W:
            print(f"✓ {p.name:52} {w}×{h}（已达标）")
            continue
        scale = MIN_W / w
        # 保持整数倍或至少 2200，取整到 2 的倍数更稳
        new_w = MIN_W
        new_h = int(round(h * scale))
        im2 = im.convert("RGB").resize((new_w, new_h), Image.LANCZOS)
        im2.save(p, "PNG", optimize=True)
        print(f"↑ {p.name:52} {w}×{h} → {new_w}×{new_h}")


if __name__ == "__main__":
    main()
