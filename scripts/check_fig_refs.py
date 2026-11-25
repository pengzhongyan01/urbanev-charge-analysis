# -*- coding: utf-8 -*-
"""
核查报告第五章正文引用与实际图号是否对应
==========================================
★ 问题类型：正文写「图 5-N 把……」，其下插入的却是「图 5-M」，两者错位。
  判定方法：找到每个 `![图 5-M 标题]` 插入点，回看它**上面最近的**正文引用行，
  若引用行的编号 ≠ M，则为错位。

运行：python scripts/check_fig_refs.py
"""
import re
from pathlib import Path

REPO = Path(r"D:/一系列作业/java后端/大作业/urbanev-charge-analysis")
CH5 = REPO / "docs" / "report" / "第5章_初稿.md"

lines = CH5.read_text(encoding="utf-8").split("\n")

# 收集所有插入点：(行号, 图号, 标题)
inserts = []
for i, l in enumerate(lines):
    m = re.search(r"!\[图 5-(\d+) ([^\]]*)\]", l)
    if m:
        inserts.append((i, int(m.group(1)), m.group(2)))

print("════ 插入的图 ════")
for i, n, t in inserts:
    print(f"  行{i:5d}  图 5-{n:2d}  {t[:50]}")

# 对每个插入点，往上找最近的一句「图 5-X」正文引用
print("\n════ 正文引用 ↔ 实际插图 对照 ════")
bad = []
for i, n, t in inserts:
    ref = None
    ref_line = None
    for j in range(i - 1, max(i - 12, -1), -1):
        st = lines[j].strip()
        if st.startswith("!["):
            break
        m = re.search(r"(?<!!)\b图 5-(\d+)\b", st)
        if m:
            ref = int(m.group(1))
            ref_line = j
            break
    if ref is None:
        print(f"  图 5-{n:2d}  ←  上方无正文引用（可能是纯插图）")
        continue
    ok = (ref == n)
    if not ok:
        bad.append((ref, n, ref_line, i))
    print(f"  正文「图 5-{ref}」 → 实际插图「图 5-{n}」  {'' if ok else '  ★ 错位'}")

print(f"\n错位处: {len(bad)}")
for ref, n, j, i in bad:
    print(f"  行{j}: {lines[j].strip()[:88]}")
    print(f"      → 行{i}: {lines[i].strip()[:88]}")
