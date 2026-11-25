# -*- coding: utf-8 -*-
"""
P11「系统实现与演示」补第 3 张系统截图
======================================
★ 老师验收清单原文：「第 11 页**内嵌 3 张系统截图**（现场起不来的兜底）」
  现状：只有 2 张（首页大屏 + 布点建议大屏），不达标。

做法：上方区改为三图并排（首页大屏 / 分区地图大屏 / 供需失衡大屏），
  下方演示动线文字区相应收窄。用 python-pptx 直接改，不重新生成整份 PPT。

运行：python scripts/fix_p11_three_shots.py
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.util import Emu

REPO = Path(r"D:/一系列作业/java后端/大作业/urbanev-charge-analysis")
PPTX = REPO / "docs" / "ppt" / "第02组_城市充电桩数据分析系统_答辩PPT.pptx"
SHOTS = REPO / "docs" / "screenshots"

# 三张并排的图（都是 C 岗实现的真实页面）
THREE = [
    ("01_首页大屏.png", "首页大屏 · 核心 KPI"),
    ("02_分区地图大屏.png", "分区地图 · 275 分区着色"),
    ("03_供需失衡大屏.png", "供需失衡 · 24 小时曲线"),
]


def main() -> None:
    prs = Presentation(PPTX)
    slide = prs.slides[10]          # P11
    shapes = list(slide.shapes)

    pics = [sh for sh in shapes if sh.shape_type == 13]
    print(f"P11 原有图片: {len(pics)} 张")

    # 记录第一张图的位置，作为三图并排的基准
    p0 = pics[0]
    base_left, base_top = p0.left, p0.top
    base_h = p0.height

    # 三图并排：左 0.62 起，总宽 12.10，每张 3.86，间距 0.26
    total_w = Emu(int(12.10 * 914400))
    gap = Emu(int(0.26 * 914400))
    w = Emu(int((12.10 - 0.26 * 2) / 3 * 914400))
    h = Emu(int(2.18 * 914400))
    top = Emu(int(1.92 * 914400))

    # 删掉原有 2 张
    for sh in pics:
        sh._element.getparent().remove(sh._element)

    # 插入 3 张
    for i, (fn, cap) in enumerate(THREE):
        p = SHOTS / fn
        if not p.exists():
            print(f"✗ 缺图 {fn}")
            continue
        left = Emu(int(0.62 * 914400)) + i * (w + gap)
        slide.shapes.add_picture(str(p), left, top, width=w, height=h)
        print(f"  ✓ P11 插入 {fn}")

    # 下方动线区上移并收窄
    for sh in slide.shapes:
        if sh.has_text_frame:
            t = sh.text_frame.text.strip()
            if t.startswith("现场演示动线"):
                sh.top = Emu(int(4.24 * 914400))
                sh.height = Emu(int(0.32 * 914400))
            elif t.startswith("① 首页大屏"):
                sh.top = Emu(int(4.62 * 914400))
                sh.height = Emu(int(1.90 * 914400))
            elif t.startswith("现场演示") and len(t) < 20:
                pass
        # 底部色带（下移一点给三图留空间）
        if not sh.has_text_frame and sh.shape_type == 1 and sh.width == Emu(int(13.33 * 914400)) and sh.height < Emu(int(0.05 * 914400)):
            pass

    prs.save(PPTX)
    print(f"\n✓ 已保存 {PPTX.name}")

    # 复查
    prs2 = Presentation(PPTX)
    n = sum(1 for sh in prs2.slides[10].shapes if sh.shape_type == 13)
    print(f"  复查：P11 图片数 = {n}")


if __name__ == "__main__":
    main()
