# -*- coding: utf-8 -*-
"""
把渲染好的插图写回报告 md（替换 ASCII 代码块）
==============================================
★ 处理两类：
  A. ASCII 框线图 → 渲染成 PNG 后，用 ![](...) 替换整个 ``` 代码块，
     但**保留**代码块里的关键说明文字（图题保留在 md，ASCII 原文删除）
  B. 纯描述性画法说明（无 ASCII，如 图 4-2）→ 直接插入仓库现成成品图

运行：python scripts/insert_figs_into_md.py
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(r"D:/一系列作业/java后端/大作业/urbanev-charge-analysis")
RPT = REPO / "docs" / "report"

# (md 文件, 图号, 图片路径, 是否删除 ASCII 代码块)
JOBS = [
    ("第2章_初稿.md", "2-1", "./images/01_系统整体技术架构六层分层图.png", True),
    ("第3-4章_初稿.md", "3-1", "./images/02_系统整体数据流分层结构图.png", True),
    ("第3-4章_初稿.md", "4-1", "./images/03_系统总体功能结构图.png", True),
    ("第3-4章_初稿.md", "4-2", "../charts/07_系统ER图.png", False),
    ("第6章_初稿.md", "6-1", "./images/05_四类测试策略递进关系图.png", True),
    ("第6章_初稿.md", "6-2", "./images/06_16个接口实现状态与返回码分布图.png", True),
    ("第6章_初稿.md", "6-3", "./images/07_数据准确性三方对账验证流程图.png", True),
    ("第6章_初稿.md", "6-4", "./images/08_六项指标数据质量实测结果图.png", True),
    ("第6章_初稿.md", "6-5", "./images/09_缓存命中与未命中对照测量流程图.png", True),
    ("第6章_初稿.md", "6-6", "./images/10_前端离线资源加载瀑布图.png", True),
]


def insert_one(fname: str, fig_no: str, img: str, drop_code: bool) -> bool:
    f = RPT / fname
    lines = f.read_text(encoding="utf-8").split("\n")
    pat = re.compile(r"^\*\*图 " + re.escape(fig_no) + r" (.+?)\*\*$")
    for i, l in enumerate(lines):
        m = pat.match(l.strip())
        if not m:
            continue
        title = m.group(1)
        # 已插过就跳过
        if any(f"![图 {fig_no} " in x for x in lines[i:i + 40]):
            return False

        j = i + 1
        # 找 ``` 代码块
        while j < len(lines) and lines[j].strip() != "```":
            j += 1
        code_end = -1
        if j < len(lines):
            k = j + 1
            while k < len(lines) and lines[k].strip() != "```":
                k += 1
            code_end = k

        img_line = f"\n![图 {fig_no} {title}]({img})\n"
        if drop_code and code_end > 0:
            # 删掉 ``` 代码块（含 ``` 围栏），换成图片
            new = lines[:j] + img_line.strip("\n").split("\n") + lines[code_end + 1:]
        else:
            # 保留说明文字，在其后插图
            ins_at = code_end + 1 if code_end > 0 else i + 1
            new = lines[:ins_at] + img_line.strip("\n").split("\n") + [""] + lines[ins_at:]
        f.write_text("\n".join(new), encoding="utf-8")
        return True
    return False


def main() -> None:
    ok = 0
    for fname, fig_no, img, drop in JOBS:
        r = insert_one(fname, fig_no, img, drop)
        p = RPT / img if img.startswith("./") else (REPO / "docs" / img)
        exists = p.exists()
        print(f"{'✓' if r else '·'} 图 {fig_no:4s} {fname:18s} 图片存在={exists}  {img.split('/')[-1]}")
        if r and exists:
            ok += 1
    print(f"\n共写入 {ok} 张")


if __name__ == "__main__":
    main()
