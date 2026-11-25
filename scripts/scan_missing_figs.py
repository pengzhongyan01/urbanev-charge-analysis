# -*- coding: utf-8 -*-
"""
盘点报告第 2/3/4/6 章「有图题无图」的清单
========================================
★ 检查逻辑：`**图 X-N 标题**` 是图题；`![...]` 是实际插图。
  有图题但上下都没有 ![] 的，就是「图在号在，图没了」。

运行：python scripts/scan_missing_figs.py
"""
import re
from pathlib import Path

REPO = Path(r"D:/一系列作业/java后端/大作业/urbanev-charge-analysis")
RPT = REPO / "docs" / "report"

FILES = ["第1-2章_初稿.md", "第2章_初稿.md", "第3-4章_初稿.md",
         "第6章_初稿.md", "第7章_初稿.md"]

for fname in FILES:
    f = RPT / fname
    if not f.exists():
        continue
    lines = f.read_text(encoding="utf-8").split("\n")
    print(f"\n════ {fname} ════")
    for i, l in enumerate(lines):
        m = re.match(r"^\*\*图 (\d+)-(\d+) (.+?)\*\*$", l.strip())
        if not m:
            continue
        ch, no, title = int(m.group(1)), int(m.group(2)), m.group(3)
        # 向下 40 行内找插图
        has = False
        for j in range(i + 1, min(i + 45, len(lines))):
            if "![图" in lines[j]:
                has = True
                break
            if re.match(r"^\*\*图 \d+-\d+ ", lines[j].strip()):
                break
        if not has:
            # 画法说明里的关键词，用于匹配成品图
            ctx = " ".join(lines[i + 1:i + 12])
            print(f"  行{i:5d}  图 {ch}-{no}  {title}")
            print(f"           画法说明: {ctx.strip()[:150]}")
