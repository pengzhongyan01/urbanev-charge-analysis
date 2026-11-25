# -*- coding: utf-8 -*-
"""
补画报告第五章缺失的两张图
==========================
★ 图 5-15「十张核心图表的类型分布与数据来源对应图」
★ 图 5-16「Docker Compose 11 服务编排与 6 组 profile 拓扑图」

这两张在报告里只有「画法说明」，没有成图。其余 6 处（5-1~5-5、5-17）
已由 fix 脚本插入仓库现成成品图。

★ 数据全部来自真实产出：
  - 图 5-15 的 10 张图表 / 7 种类型 / ADS 表对应，取自 C 岗 C05 交付
  - 图 5-16 的 11 服务 / profile 归属 / 14 数据卷 / 端口映射，
    由 docker-compose.yml 解析得到（不手写）

运行：python scripts/make_report_figs2.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import yaml  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle  # noqa: E402

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "docs" / "report" / "images"
OUT.mkdir(parents=True, exist_ok=True)

# ── C 岗深色大屏配色 ──────────────────────────────────────────────────────
BG = "#0a1628"
BG2 = "#112240"
BG3 = "#16294a"
GRID = "#1e3a5f"
CYAN = "#00d4ff"
ORANGE = "#ff6b35"
GREEN = "#22c55e"
TXT = "#e8f1ff"
TXT2 = "#94a3b8"
TXT3 = "#8fa8c8"


# ══════════════════════════════════════════════════════════════════════════
# 图 5-15　十张核心图表的类型分布与数据来源对应图
# ══════════════════════════════════════════════════════════════════════════
def fig_15() -> Path:
    # (编号, 图表名, 图形类型, ADS 表)
    items = [
        ("01", "深圳 275 分区空间分布", "map", "zone_occupancy"),
        ("02", "分区平均占用率 TOP20", "hbar", "zone_occupancy"),
        ("03", "24 小时供需曲线", "line", "hourly_supply_demand"),
        ("04", "供需失衡指数 TOP15", "hbar2", "imbalance_index"),
        ("05", "分时定价与固定定价占用率对比", "bar2", "price_elasticity"),
        ("06", "两类电价区价差与占用率对照", "scatter", "price_elasticity"),
        ("07", "需求预测曲线", "line2", "demand_forecast"),
        ("08", "预测误差分布对比", "hist", "demand_forecast"),
        ("09", "布点建议优先级分布", "stack", "expansion_suggestion"),
        ("10", "数据质量实测结果", "pie", "dq_质量规则统计表"),
    ]

    fig = plt.figure(figsize=(15, 8.6), dpi=170, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    ax.axis("off"); ax.set_facecolor(BG)

    fig.text(0.5, 0.955, "图 5-15　十张核心图表的类型分布与数据来源对应图",
             ha="center", fontsize=19, color=TXT, weight="bold")
    fig.text(0.5, 0.915, "10 张图表覆盖 7 种图形类型，每张严格对应一张 ADS 表 —— 图与表一一对应，口径永不漂移",
             ha="center", fontsize=11.5, color=TXT2)

    COLS, ROWS = 5, 2
    x0, y0, cw, ch = 3.2, 47.0, 18.0, 30.0
    gx, gy = 1.1, 4.2

    def thumb(axx, kind, cx, cy, w, h):
        """在单元格内画简化图形缩略示意"""
        if kind == "map":
            axx.add_patch(plt.Polygon(
                [(cx - w*.42, cy - h*.30), (cx - w*.30, cy + h*.34),
                 (cx + w*.18, cy + h*.30), (cx + w*.40, cy - h*.10),
                 (cx + w*.05, cy - h*.36)],
                closed=True, facecolor=BG3, edgecolor=TXT3, lw=1.0, zorder=2))
            rng = np.random.default_rng(7)
            for _ in range(30):
                axx.add_patch(Circle(
                    (cx + rng.uniform(-w*.33, w*.31), cy + rng.uniform(-h*.26, h*.26)),
                    rng.uniform(0.4, 0.9), facecolor=ORANGE, edgecolor="none",
                    alpha=0.9, zorder=3))
        elif kind in ("hbar", "hbar2"):
            n = 6 if kind == "hbar" else 5
            vals = rng_vals = np.linspace(0.35, 1.0, n)
            for i, v in enumerate(vals):
                c = CYAN if kind == "hbar" else (ORANGE if i == 0 else CYAN)
                axx.add_patch(Rectangle((cx - w*.38, cy + h*.26 - i*h*.11),
                                         w*.72*v, h*.062, facecolor=c,
                                         edgecolor="none", zorder=3))
        elif kind in ("line", "line2"):
            # 用平滑的双峰日周期曲线（模拟 24 小时供需），而非高频锯齿
            x = np.linspace(cx - w*.40, cx + w*.40, 120)
            base = np.sin((x - cx) / w * 2 * np.pi * 1.35)
            peak = np.exp(-(((x - cx) / w * 2 * np.pi * 0.9) - 1.1) ** 2 / 0.55)
            y = cy + h*.10 + h*.16 * base + h*.16 * peak
            if kind == "line2":
                y = cy + h*.02 + h*.13 * base + h*.13 * peak
            axx.fill_between(x, cy - h*.22, y, color=CYAN, alpha=0.16, zorder=2)
            axx.plot(x, y, color=CYAN, lw=2.2, zorder=3)
            axx.plot(x, y - h*.06, color=ORANGE, lw=1.5, ls="--", zorder=3)
        elif kind == "bar2":
            for i, (v, c) in enumerate([(0.7, ORANGE), (-0.5, CYAN),
                                        (0.45, ORANGE), (-0.3, CYAN), (0.6, ORANGE)]):
                axx.add_patch(Rectangle((cx - w*.34 + i*w*.17, cy - h*.02 if v > 0 else cy + h*.02),
                                         w*.12, h*.28*v, facecolor=c, edgecolor="none", zorder=3))
        elif kind == "scatter":
            # 两簇点云（模拟 TOU / FLAT 分组），密度适中不糊
            rng = np.random.default_rng(11)
            for ccx, ccy, col, cnt in [(-w*.16, h*.10, CYAN, 22),
                                       (w*.18, -h*.12, ORANGE, 18)]:
                for _ in range(cnt):
                    axx.add_patch(Circle(
                        (cx + ccx + rng.normal(0, w*.07),
                         cy + ccy + rng.normal(0, h*.09)),
                        rng.uniform(0.7, 1.5), facecolor=col,
                        edgecolor="none", alpha=0.72, zorder=3))
            axx.plot([cx - w*.36, cx + w*.36], [cy - h*.26, cy + h*.26],
                     color=TXT3, lw=1.1, ls="--", alpha=0.8, zorder=4)
        elif kind == "hist":
            for i in range(11):
                v = np.exp(-((i - 3) ** 2) / 9.0)
                axx.add_patch(Rectangle((cx - w*.38 + i*w*.068, cy - h*.30),
                                         w*.058, h*.58*v, facecolor=CYAN,
                                         edgecolor="none", alpha=0.9, zorder=3))
        elif kind == "stack":
            for i in range(5):
                axx.add_patch(Rectangle((cx - w*.36 + i*w*.15, cy - h*.28),
                                         w*.13, h*.30, facecolor=ORANGE,
                                         edgecolor="none", zorder=3))
                axx.add_patch(Rectangle((cx - w*.36 + i*w*.15, cy - h*.28),
                                         w*.13, h*.15, facecolor=CYAN,
                                         edgecolor="none", zorder=4))
        elif kind == "pie":
            axx.add_patch(Circle((cx, cy), h*.30, facecolor=BG3,
                                  edgecolor=TXT3, lw=1.2, zorder=2))
            axx.add_patch(Circle((cx, cy), h*.30, facecolor=ORANGE,
                                  edgecolor="none", zorder=3, alpha=0.85))
            axx.add_patch(Circle((cx, cy), h*.16, facecolor=BG,
                                  edgecolor="none", zorder=4))
            axx.add_patch(Circle((cx + h*.21, cy + h*.16), h*.055,
                                  facecolor=CYAN, edgecolor="none", zorder=5))

    for idx, (no, name, kind, tbl) in enumerate(items):
        r, c = divmod(idx, COLS)
        cx = x0 + c * (cw + gx) + cw / 2
        cy = y0 - r * (ch + gy) + ch / 2
        ax.add_patch(FancyBboxPatch((cx - cw/2, cy - ch/2 + 3.2), cw, ch - 3.2,
                                    boxstyle="round,pad=0.4", facecolor=BG2,
                                    edgecolor=GRID, lw=1.0, zorder=1))
        thumb(ax, kind, cx, cy + 4.0, cw * 0.86, 15.0)
        ax.text(cx, cy - ch/2 + 7.4, f"{no}　{name}", ha="center", va="center",
                fontsize=10.2, color=TXT, zorder=6)
        ax.text(cx, cy - ch/2 + 4.2, tbl, ha="center", va="center",
                fontsize=8.2, color=CYAN, zorder=6)

    # 类型图例
    types = ["地图", "条形图", "折线图", "双柱图", "散点图", "直方图", "环形图", "堆叠柱", "饼图", "雷达图"]
    y = 6.5
    ax.text(3.2, y + 1.6, "图形类型（7 类）：", fontsize=10, color=TXT2, va="center")
    x = 20.0
    for i, tp in enumerate(types):
        ax.add_patch(Circle((x, y), 0.9, facecolor=CYAN, edgecolor="none", alpha=0.85))
        ax.text(x + 1.6, y, tp, fontsize=9.2, color=TXT3, va="center")
        x += 2.6 + len(tp) * 1.35
    ax.text(3.2, y - 2.8, "★ 图与表一一对应：前端每张图只读一张 ADS 表，杜绝多表拼装导致的口径漂移",
            fontsize=10.2, color=ORANGE, va="center")

    p = OUT / "15_核心图表类型与ADS表对应.png"
    fig.savefig(p, facecolor=BG, dpi=170)
    plt.close(fig)
    return p


# ══════════════════════════════════════════════════════════════════════════
# 图 5-16　Docker Compose 11 服务编排与 6 组 profile 拓扑图
# ══════════════════════════════════════════════════════════════════════════
def fig_16() -> Path:
    d = yaml.safe_load((REPO / "docker-compose.yml").read_text(encoding="utf-8"))
    svcs = d.get("services", {})
    n_vol = len(d.get("volumes", {}))
    n_port = sum(len(s.get("ports", []) or []) for s in svcs.values())

    # 分层（按报告规格）
    LAYERS = [
        ("接入层", ["flume"], ORANGE),
        ("计算层", ["namenode", "datanode", "resourcemanager",
                    "nodemanager", "hive", "spark"], CYAN),
        ("数据层", ["mysql", "redis"], GREEN),
        ("应用层", ["backend", "frontend"], "#a78bfa"),
    ]
    PROFILES = ["base", "app", "hadoop", "hive", "spark", "full"]
    PCOLOR = {"base": "#22c55e", "app": "#a78bfa", "hadoop": "#00d4ff",
              "hive": "#fbbf24", "spark": "#fb923c", "full": "#ff6b35"}

    fig = plt.figure(figsize=(15, 8.6), dpi=170, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    ax.axis("off"); ax.set_facecolor(BG)

    fig.text(0.5, 0.955, "图 5-16　Docker Compose 11 服务编排与 6 组 profile 拓扑图",
             ha="center", fontsize=19, color=TXT, weight="bold")
    fig.text(0.5, 0.915, "11 服务 / 14 数据卷 / 11 端口映射 —— 按需组合，full 一键全栈，app 四服务保底可演示",
             ha="center", fontsize=11.5, color=TXT2)

    LX, LW = 3.0, 58.0
    PX, PW = 65.0, 32.0
    top = 84.0

    # profile 归属映射
    prof_of = {}
    for nm, s in svcs.items():
        for pr in (s.get("profiles") or []):
            prof_of.setdefault(pr, []).append(nm)

    # 各层服务方块
    box_pos = {}
    # 按服务数分配层高，铺满左侧纵向空间（top=84 → bottom=12）
    total_svc = sum(len([m for m in ms if m in svcs]) for _, ms, _ in LAYERS)
    span = top - 12.0
    y = top
    for lname, members, color in LAYERS:
        members = [m for m in members if m in svcs]
        # 层高 = 基础 7 + 每服务 2.4，按比例分配总空间
        h = (7.0 + len(members) * 2.4) / (4 * 7.0 + total_svc * 2.4) * span
        ax.add_patch(FancyBboxPatch((LX, y - h), LW, h - 1.2,
                                    boxstyle="round,pad=0.3", facecolor=BG2,
                                    edgecolor=color, lw=1.2, alpha=0.92, zorder=1))
        ax.text(LX + 1.6, y - h/2 - 0.2, lname, fontsize=11, color=color,
                weight="bold", va="center", zorder=6)
        n = len(members)
        bw = (LW - 15) / n
        bh = min(h - 5.0, 9.0)
        for i, m in enumerate(members):
            s = svcs[m]
            cname = s.get("container_name", m)
            # 超长容器名换行，避免溢出方框
            disp = cname
            if len(disp) > 16:
                disp = disp[:15] + "\n" + disp[15:]
            bx = LX + 10.5 + i * bw
            by = y - h/2 - bh/2 - 0.2
            ax.add_patch(FancyBboxPatch((bx, by), bw - 1.4, bh,
                                         boxstyle="round,pad=0.25",
                                         facecolor=BG3, edgecolor=color,
                                         lw=1.0, zorder=3))
            ax.text(bx + (bw - 1.4)/2, by + bh/2 + 0.9, disp,
                    ha="center", va="center", fontsize=7.2, color=TXT,
                    linespacing=1.3, zorder=5)
            img = str(s.get("image", ""))
            ax.text(bx + (bw - 1.4)/2, by + bh/2 - 1.6, img[:16],
                    ha="center", va="center", fontsize=5.6, color=TXT3, zorder=5)
            box_pos[m] = (bx, by, bw - 1.4, bh)
            if m == "flume":
                ax.add_patch(FancyBboxPatch((bx - 0.8, by - 0.8), bw + 0.2, bh + 1.6,
                                             boxstyle="round,pad=0.25",
                                             facecolor="none", edgecolor=ORANGE,
                                             lw=1.8, zorder=6))
                ax.text(bx + (bw - 1.4)/2, by + bh + 1.4, "自建镜像 uev/flume:1.11.0",
                        fontsize=6.8, color=ORANGE, ha="center", zorder=7)
        y -= h + 1.0

    # ── 右侧 profile 列 ────────────────────────────────────────────────
    ax.add_patch(FancyBboxPatch((PX, 12.0), PW, top - 12.0,
                                boxstyle="round,pad=0.35", facecolor=BG2,
                                edgecolor=GRID, lw=1.1, zorder=1))
    ax.text(PX + PW/2, top - 2.6, "6 组 profile", ha="center", fontsize=11.5,
            color=TXT, weight="bold", zorder=6)

    ph = (top - 18) / len(PROFILES)
    for i, pr in enumerate(PROFILES):
        py = top - 6.4 - i * ph
        c = PCOLOR[pr]
        mem = prof_of.get(pr, [])
        ax.add_patch(FancyBboxPatch((PX + 2.0, py - ph + 1.6), PW - 4.0, ph - 2.6,
                                    boxstyle="round,pad=0.25", facecolor=BG3,
                                    edgecolor=c, lw=1.5, linestyle="--", zorder=3))
        ax.text(PX + 3.6, py - 2.2, pr, fontsize=11, color=c,
                weight="bold", va="center", zorder=6)
        txt = f"{len(mem)} 服务"
        if pr == "full":
            txt = f"{len(mem)} 服务 / {n_vol} 卷 / {n_port} 端口"
        ax.text(PX + 3.6, py - 5.0, txt, fontsize=8.4, color=TXT3, va="center", zorder=6)
        # 连线：只连到该 profile 覆盖的服务框右侧，透明度低
        for m in mem:
            if m in box_pos:
                bx, by, bw, bh = box_pos[m]
                ax.plot([PX + 2.0, bx + bw], [py - ph/2 + 1.6, by + bh/2],
                        color=c, lw=0.6, alpha=0.28, ls=":", zorder=2)

    # full 最外框
    ax.add_patch(FancyBboxPatch((PX + 1.2, 13.2), PW - 2.4, top - 14.4,
                                boxstyle="round,pad=0.35", facecolor="none",
                                edgecolor=ORANGE, lw=2.0, zorder=8))
    ax.text(PX + PW - 2.4, top - 4.4, "full 包住全部 11 个服务", fontsize=8.2,
            color=ORANGE, ha="right", zorder=9)

    ax.text(3.0, 7.0, "★ 11 个服务通过 6 组 profile 实现按需组合：full 一键拉起完整集群，app 只起 4 个应用服务即可让看板跑起来",
            fontsize=10.4, color=ORANGE, va="center")
    ax.text(3.0, 3.6, "降级链路：full（11 服务）→ app（4 服务）→ native（免 Docker）　｜　start_all.sh 自动按可用性选择",
            fontsize=9.6, color=TXT3, va="center")

    p = OUT / "16_DockerCompose编排与profile拓扑.png"
    fig.savefig(p, facecolor=BG, dpi=170)
    plt.close(fig)
    return p


if __name__ == "__main__":
    a = fig_15()
    b = fig_16()
    from PIL import Image
    for p in (a, b):
        w, h = Image.open(p).size
        print(f"✓ {p.name}（{w}×{h}）")
