# -*- coding: utf-8 -*-
"""
把报告里的 ASCII 艺术框线图渲染成规范插图
==========================================
★ 背景：报告第 2/3/4/6 章共 10 处「图 X-N」只写了 ASCII 字符画（代码块），
  没有真正的图片插入 —— 老师要求的是论文级插图，不是字符画。

本脚本：
  1. 从各章 md 中提取 `**图 X-N 标题**` 后的 ``` 代码块（ASCII 图）
  2. 用等宽字体逐字符绘制成 PNG（深色主题，与 C 岗看板风格一致）
  3. 把生成的图片插入回 md（替换代码块为 ![](...)）

运行：python scripts/render_ascii_figs.py
"""
from __future__ import annotations

import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
# 等宽 + 覆盖中文与框线字符（DejaVu Sans Mono 无中文字形，会渲染成方框）
from matplotlib import font_manager  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
FANG = FontProperties(fname=r"C:/Windows/Fonts/simfang.ttf")

REPO = Path(__file__).resolve().parent.parent
RPT = REPO / "docs" / "report"
IMGDIR = RPT / "images"
IMGDIR.mkdir(parents=True, exist_ok=True)

# 等宽字体（Cascadia Mono 有框线字符；中文用宋体混排会乱 → 统一用等宽宋体）
FONT = r"C:/Windows/Fonts/simsun.ttc"

BG = "#0a1628"
BG2 = "#112240"
TXT = "#e8f1ff"
TXT2 = "#94a3b8"
CYAN = "#00d4ff"
ORANGE = "#ff6b35"
GRID = "#1e3a5f"

# 需要渲染的图：(md 文件, 图号, 输出文件名)
TARGETS = [
    ("第2章_初稿.md", "2-1", "01_系统整体技术架构六层分层图.png"),
    ("第3-4章_初稿.md", "3-1", "02_系统整体数据流分层结构图.png"),
    ("第3-4章_初稿.md", "4-1", "03_系统总体功能结构图.png"),
    ("第3-4章_初稿.md", "4-2", "04_系统ER图.png"),
    ("第6章_初稿.md", "6-1", "05_四类测试策略递进关系图.png"),
    ("第6章_初稿.md", "6-2", "06_16个接口实现状态与返回码分布图.png"),
    ("第6章_初稿.md", "6-3", "07_数据准确性三方对账验证流程图.png"),
    ("第6章_初稿.md", "6-4", "08_六项指标数据质量实测结果图.png"),
    ("第6章_初稿.md", "6-5", "09_缓存命中与未命中对照测量流程图.png"),
    ("第6章_初稿.md", "6-6", "10_前端离线资源加载瀑布图.png"),
]


def extract_ascii(lines: list[str], fig_no: str) -> tuple[str, list[str], int]:
    """找到 **图 X-N 标题** 后的第一个 ``` 代码块，返回 (标题, 代码行, 块结束行号)"""
    pat = re.compile(r"^\*\*图 " + re.escape(fig_no) + r" (.+?)\*\*$")
    for i, l in enumerate(lines):
        m = pat.match(l.strip())
        if not m:
            continue
        title = m.group(1)
        # 往后找 ```
        j = i + 1
        while j < len(lines) and lines[j].strip() != "```":
            j += 1
        if j >= len(lines):
            return title, [], -1
        k = j + 1
        code = []
        while k < len(lines) and lines[k].strip() != "```":
            code.append(lines[k])
            k += 1
        return title, code, k
    return "", [], -1


def render_ascii(title: str, code: list[str], out_name: str) -> Path:
    """把 ASCII 图渲染成 PNG"""
    code = [c for c in code]
    n = len(code)
    # 计算最宽行（按显示宽度：中文算 2）
    def width(s: str) -> int:
        return sum(2 if ord(ch) > 0x2E80 else 1 for ch in s)
    maxw = max((width(c) for c in code), default=40)

    # 画布尺寸
    fs = 13.0
    colw = 0.088          # 每半角字符宽（figure 坐标）
    lineh = 1.0 / (n + 6)
    figw = min(30.0, max(12.0, maxw * colw * 0.62))
    figh = max(6.0, (n + 5) * 0.30)

    fig = plt.figure(figsize=(figw, figh), dpi=170, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    ax.axis("off"); ax.set_facecolor(BG)

    fig.text(0.5, 0.975, title, ha="center", va="top", fontsize=15,
             color=TXT, weight="bold")

    top = 92.0
    bottom = 3.0
    avail = top - bottom
    lh = avail / max(n, 1)

    for i, ln in enumerate(code):
        y = top - i * lh
        # 颜色：框线字符用青，正文用浅色，箭头/标题用橙
        if not ln.strip():
            continue
        if re.search(r"[┌┐└┘├┤┬┴┼─│▼▲◀▶]", ln):
            col = CYAN
        elif re.match(r"^\s*[①②③④⑤⑥⑦⑧⑨⑩]", ln) or "──▶" in ln or "▼" in ln:
            col = ORANGE
        elif re.match(r"^\s*[A-Z]\d?\.|^\s*[└├│]", ln):
            col = TXT
        else:
            col = TXT2
        ax.text(1.5, y, ln.replace("─", "-"), fontsize=fs, color=col,
                fontproperties=FANG, va="top", ha="left", zorder=5)

    # 外框
    ax.add_patch(FancyBboxPatch((0.6, 1.2), 98.8, 97.0,
                                boxstyle="round,pad=0.2", facecolor=BG2,
                                edgecolor=GRID, lw=1.0, zorder=1))
    p = IMGDIR / out_name
    fig.savefig(p, facecolor=BG, dpi=170)
    plt.close(fig)
    return p


def main() -> None:
    made = []
    for fname, fig_no, out_name in TARGETS:
        f = RPT / fname
        if not f.exists():
            print(f"✗ 缺 {fname}")
            continue
        lines = f.read_text(encoding="utf-8").split("\n")
        title, code, end = extract_ascii(lines, fig_no)
        if not code:
            print(f"✗ {fname} 图 {fig_no} 没找到 ASCII 代码块")
            continue
        p = render_ascii(title, code, out_name)
        made.append((fname, fig_no, title, out_name, end, lines))
        print(f"✓ 图 {fig_no}  {title[:30]}  → {out_name}  ({len(code)} 行)")

    print(f"\n共渲染 {len(made)} 张。接下来需要把 md 里的代码块换成图片引用。")


if __name__ == "__main__":
    main()
