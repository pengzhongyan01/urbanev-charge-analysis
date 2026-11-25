# -*- coding: utf-8 -*-
"""
用 PowerPoint COM 导出 PPT 预览图（答辩前自查用）
=================================================
运行：python scripts/ppt_preview.py [输出目录]
"""
from __future__ import annotations

import sys
from pathlib import Path

import win32com.client

REPO = Path(r"D:/一系列作业/java后端/大作业/urbanev-charge-analysis")
PPTX = REPO / "docs" / "ppt" / "第02组_城市充电桩数据分析系统_答辩PPT.pptx"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else (REPO / "docs" / "ppt" / "_preview")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    app = win32com.client.Dispatch("PowerPoint.Application")
    pres = app.Presentations.Open(str(PPTX), WithWindow=False)
    for i, slide in enumerate(pres.Slides, 1):
        p = OUT / f"slide{i:02d}.png"
        slide.Export(str(p), "PNG", 1920, 1080)
    pres.Close()
    app.Quit()
    print(f"✓ 导出 {i} 页 → {OUT}")


if __name__ == "__main__":
    main()
