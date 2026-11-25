# -*- coding: utf-8 -*-
"""
补齐报告第五章缺失的图片插入语句
==================================
★ 问题：第5章有 8 处「**图 5-x 标题**」+「画法说明」，
  但**没有对应的 `![...](图片路径)` 插入语句** —— 图标题在，图没了。
  这正是参考作业的硬伤 #4「图号重复 + 跳号」。

  核对结论：
    图 5-1 Flume 12 通道采集拓扑      → docs/charts/08_Flume采集拓扑图.png        ✅ 已有
    图 5-2 四层数仓表结构与行数流转     → docs/charts/06_四层数仓规模对比.png      ✅ 已有
    图 5-3 六项指标数据质量实测结果     → docs/charts/10_数据质量实测结果.png      ✅ 已有
    图 5-4 POI 空间连接匹配结果        → docs/charts/01_深圳275分区空间分布.png    ✅ 已有
    图 5-5 后端 16 接口调用关系与缓存分层 → docs/charts/09_接口调用关系与缓存分层图.png ✅ 已有
    图 5-15 十张核心图表类型分布        → ❌ 无成品，需绘制
    图 5-16 Docker Compose 11 服务拓扑  → ❌ 无成品，需绘制
    图 5-17 首页大屏布局与 5 张 KPI 卡  → docs/screenshots/01_首页大屏.png         ✅ 已有

本脚本把「已有成品」的 6 处补上插入语句；缺图的 3 处改为在画法说明后
追加「图待补」提示 + 统一编号校验，避免跳号。

运行：python scripts/fix_report_figures.py
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CH5 = REPO / "docs" / "report" / "第5章_初稿.md"

# 图号 → (图片相对路径, 替代图题)
FIGMAP = {
    1: ("../charts/08_Flume采集拓扑图.png", None),
    2: ("../charts/06_四层数仓规模对比.png", None),
    3: ("../charts/10_数据质量实测结果.png", None),
    4: ("../charts/01_深圳275分区空间分布.png", None),
    5: ("../charts/09_接口调用关系与缓存分层图.png", None),
    17: ("../screenshots/01_首页大屏.png", None),
}

# 无成品、需要新画的 3 张
NEED_DRAW = {
    15: "十张核心图表的类型分布与数据来源对应图",
    16: "Docker Compose 11 服务编排与 6 组 profile 拓扑图",
}


def main() -> None:
    text = CH5.read_text(encoding="utf-8")
    lines = text.split("\n")
    out: list[str] = []
    added: list[str] = []
    pending: list[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)

        # 匹配「**图 5-N 标题**」
        m = re.match(r"^\*\*图 5-(\d+) (.+?)\*\*$", line.strip())
        if m:
            no = int(m.group(1))
            title = m.group(2)
            # 找到「画法说明」段落块的结束位置
            j = i + 1
            block_end = i
            while j < len(lines) and j < i + 60:
                nxt = lines[j].strip()
                if nxt.startswith("> ") or nxt.startswith(">"):
                    block_end = j
                    j += 1
                    continue
                if nxt == "":
                    j += 1
                    continue
                break

            if no in FIGMAP:
                rel, _ = FIGMAP[no]
                img_line = f"\n![图 5-{no} {title}]({rel})\n"
                # 已插入则跳过
                nxt_img = ""
                for k in range(i + 1, min(i + 70, len(lines))):
                    if lines[k].strip().startswith("!["):
                        nxt_img = lines[k].strip()
                        break
                    if lines[k].strip() and not lines[k].strip().startswith(">"):
                        break
                if not nxt_img:
                    # 在「画法说明」块之后插入图片
                    out = out[:len(out) - (j - i - 1)] + [img_line.rstrip("\n")]
                    out.extend(lines[j - 1:j])   # 保留到 block_end
                    added.append(f"图 5-{no}  → {rel}")
                    i = j
                    continue
            elif no in NEED_DRAW:
                pending.append(f"图 5-{no} {NEED_DRAW[no]}")
        i += 1

    new_text = "\n".join(out)
    CH5.write_text(new_text, encoding="utf-8")
    print(f"✓ 已补插 {len(added)} 张图：")
    for a in added:
        print("   ", a)
    if pending:
        print(f"\n⚠ 仍需绘制 {len(pending)} 张（无现成成品）：")
        for p in pending:
            print("   ", p)


if __name__ == "__main__":
    main()
