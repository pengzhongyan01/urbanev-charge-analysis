# -*- coding: utf-8 -*-
"""
全文图文一致性检查（按章编号）
==============================
★ 图号格式为「图 <章>-<序>」，逐章检查：
  - 插入了哪些图、正文引用了哪些图
  - 引用缺图（图有号无图）/ 重复插图 / 跳号

运行：python scripts/check_all_fig_refs.py
"""
import re
from pathlib import Path

REPO = Path(r"D:/一系列作业/java后端/大作业/urbanev-charge-analysis")
RPT = REPO / "docs" / "report"

FILES = [
    ("第1-2章_初稿.md", [1, 2]),
    ("第2章_初稿.md", [2]),
    ("第3-4章_初稿.md", [3, 4]),
    ("第5章_初稿.md", [5]),
    ("第6章_初稿.md", [6]),
    ("第7章_初稿.md", [7]),
]

total_bad = 0
for fname, chapters in FILES:
    f = RPT / fname
    if not f.exists():
        print(f"（缺文件 {fname}）")
        continue
    t = f.read_text(encoding="utf-8")
    lines = t.split("\n")
    print(f"\n════ {fname} ════")

    for ch in chapters:
        # 插入点
        ins = []
        for i, l in enumerate(lines):
            m = re.search(rf"!\[图 {ch}-(\d+) ", l)
            if m:
                ins.append((i, int(m.group(1))))
        ins_nums = [n for _, n in ins]
        # 正文引用（排除图片语法内的）
        refs = []
        for l in lines:
            if l.strip().startswith("!["):
                continue
            for m in re.finditer(rf"(?<!\!)\b图 {ch}-(\d+)\b", l):
                refs.append(int(m.group(1)))
        refs_u = sorted(set(refs))
        dup = sorted({n for n in ins_nums if ins_nums.count(n) > 1})
        miss = [r for r in refs_u if r not in ins_nums]
        maxn = max(ins_nums) if ins_nums else 0
        gap = [i for i in range(1, maxn + 1) if i not in ins_nums]
        flag = "" if not (dup or miss or gap) else "   ★"
        print(f"  第{ch}章: 插图{len(ins_nums)}张 编号{ins_nums}")
        print(f"        引用{refs_u}  重复{dup or '无'}  缺图{miss or '无'}  跳号{gap or '无'}{flag}")
        total_bad += len(dup) + len(miss) + len(gap)

print(f"\n════ 全报告问题总数: {total_bad} ════")
