# -*- coding: utf-8 -*-
"""
修正 PPT 中的组员姓名：杨珊珊 → 杨姗姗
========================================
★ 2026-11-20 全仓做过一次姓名统一（杨珊珊 → 杨姗姗），但 PPT 是那次之后
  用另一条路径生成的，把旧名字带回来了。
  封面（P1）、尾页（P15）、分工页（P13）都有。

运行：python scripts/fix_ppt_name.py
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation

REPO = Path(r"D:/一系列作业/java后端/大作业/urbanev-charge-analysis")
PPTX = REPO / "docs" / "ppt" / "第02组_城市充电桩数据分析系统_答辩PPT.pptx"

OLD, NEW = "杨珊珊", "杨姗姗"


def fix_text(shape) -> int:
    n = 0
    if not shape.has_text_frame:
        return 0
    for para in shape.text_frame.paragraphs:
        for run in para.runs:
            if OLD in run.text:
                run.text = run.text.replace(OLD, NEW)
                n += 1
    return n


def main() -> None:
    prs = Presentation(PPTX)
    total = 0
    for i, s in enumerate(prs.slides, 1):
        cnt = 0
        for sh in s.shapes:
            cnt += fix_text(sh)
            if sh.has_table:
                for r in sh.table.rows:
                    for c in r.cells:
                        cnt += fix_text(c)
        if cnt:
            print(f"  P{i}: 修正 {cnt} 处")
            total += cnt
    prs.save(PPTX)
    print(f"\n✓ 共修正 {total} 处：{OLD} → {NEW}")

    # 复查
    prs2 = Presentation(PPTX)
    xml = "".join(s._element.xml for s in prs2.slides)
    print(f"  复查：仍含「{OLD}」 = {'是（未清干净）' if OLD in xml else '否'}")
    print(f"  复查：含「{NEW}」 = {'是' if NEW in xml else '否'}")


if __name__ == "__main__":
    main()
