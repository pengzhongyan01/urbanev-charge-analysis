# -*- coding: utf-8 -*-
"""
make_extra_charts.py —— 补两张 PPT 专用图：需求分析用例图 + 四层数仓规模对比图

用法：python scripts/make_extra_charts.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "data" / "etl_out"
OUT = REPO / "docs" / "charts"

for f in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/simhei.ttf"]:
    if Path(f).exists():
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DengXian", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

INK, MUT, LINE = "#1F2328", "#6B7280", "#D1D5DB"
BLUE, TEAL, AMBER, RED, PURPLE, GREY = "#1D4ED8", "#0E7C6B", "#D97706", "#C0392B", "#5B3FA8", "#9CA3AF"
DPI = 200


def box(ax, x, y, w, h, text, fc, ec, tc="#FFFFFF", fs=10, weight="bold"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.012",
                                fc=fc, ec=ec, lw=1.1, zorder=3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=tc, fontweight=weight, zorder=4, linespacing=1.35)


def arrow(ax, p1, p2, color="#94A3B8", rad=0.0, ls="-"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=11,
                                 color=color, lw=1.2, linestyle=ls, zorder=2,
                                 connectionstyle=f"arc3,rad={rad}"))


def make_usecase():
    """需求分析用例图：3 类角色 + 14 个系统用例"""
    fig, ax = plt.subplots(figsize=(14, 9.5))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.5, 0.975, "图 5-1　系统用例图", ha="center", fontsize=17,
            color=INK, fontweight="bold", transform=ax.transAxes)
    ax.text(0.5, 0.943, "三类使用者 · 14 个系统用例 · 数据来源：docs/contracts/03-接口规范.md",
            ha="center", fontsize=11, color=MUT, transform=ax.transAxes)

    # 系统边界
    ax.add_patch(FancyBboxPatch((0.215, 0.075), 0.575, 0.815,
                                boxstyle="round,pad=0.006,rounding_size=0.012",
                                fc="#F8FAFC", ec=BLUE, lw=1.6, zorder=1))
    ax.text(0.502, 0.868, "城市充电桩数据分析系统", ha="center", fontsize=13,
            color=BLUE, fontweight="bold", zorder=4)

    # 角色（左侧）
    roles = [("城市运营管理者", 0.68, RED), ("充电站运营方", 0.40, AMBER),
             ("数据分析师 / 研究者", 0.12, PURPLE)]
    for name, y, c in roles:
        box(ax, 0.025, y - 0.052, 0.155, 0.104, name, c, c, "#FFFFFF", 11.5)

    # 用例（系统内部）—— ★ 14 个用例排成两列，每列 7 个
    UC_NAMES = [
        ("UC1 分区供需失衡诊断", RED), ("UC2 布点扩容建议生成", RED),
        ("UC3 充电需求预测与回测", PURPLE), ("UC4 电价引导效果评估", PURPLE),
        ("UC5 分区类型画像聚类", PURPLE), ("UC6 全市 KPI 概览", AMBER),
        ("UC7 分区占用率查询", AMBER), ("UC8 24 小时供需曲线", AMBER),
        ("UC9 筛选与条件联动", AMBER), ("UC10 数据导出（Excel）", AMBER),
        ("UC11 数据字典查询", PURPLE), ("UC12 气象关联分析", PURPLE),
        ("UC13 POI 密度与需求关联", PURPLE), ("UC14 用户登录与权限控制", AMBER),
    ]
    UH, VGAP = 0.058, 0.0165
    TOP_Y = 0.775
    ucs = []
    for i, (name, c) in enumerate(UC_NAMES):
        col = 0 if i < 7 else 1
        row = i % 7
        y = TOP_Y - row * (UH + VGAP)
        x = 0.248 + col * 0.268
        box(ax, x, y - UH, 0.252, UH, name, "#FFFFFF", c, c, 9.6, "normal")
        ucs.append((name, y - UH / 2, c, x, y - UH))

    # 关联线（角色 → 相关用例）
    role_uc = {
        "城市运营管理者": [0, 1, 5, 6, 7, 8],
        "充电站运营方": [5, 6, 7, 9, 13],
        "数据分析师 / 研究者": [2, 3, 4, 10, 11],
    }
    for rname, ry, rc in roles:
        for idx in role_uc[rname]:
            uname, uy, _c, ux, _uy = ucs[idx]
            arrow(ax, (0.180, ry), (ux, uy), color=rc, rad=0.05)

    # 登录前置（<<include>>）
    box(ax, 0.248, 0.088, 0.252, 0.052, "〈include〉用户登录与权限校验",
        "#FEF3C7", AMBER, "#92400E", 9.4, "normal")
    for idx in [5, 6, 7, 9]:
        uname, uy, _c, ux, _uy = ucs[idx]
        arrow(ax, (0.374, 0.140), (ux + 0.126, uy), color=AMBER, rad=0.10, ls="--")

    # 图例
    ax.text(0.025, 0.035, "◆ 关联（associate）　┈ include（包含）　—— 14 个系统用例全部由 REST 接口支撑",
            fontsize=10.5, color=MUT, transform=ax.transAxes)
    out = OUT / "05_需求分析用例图.png"
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=DPI, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {out.name}")


def make_warehouse():
    """四层数仓规模对比图（用 DWD/DWS 抽样 + 契约 04 的表清单）"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7.5),
                                   gridspec_kw={"width_ratios": [1.15, 1]})
    fig.patch.set_facecolor("white")

    # 左：四层流转（带实测行数）
    ax1.set_xlim(0, 1); ax1.set_ylim(0, 1); ax1.axis("off")
    ax1.text(0.5, 0.965, "图 8-1　四层数仓流转与实测规模", ha="center",
             fontsize=15.5, color=INK, fontweight="bold", transform=ax1.transAxes)
    layers = [
        ("ODS　贴源层", "12 张表（6 宽表 276 列 + 2 矩阵 275 列 + 维表 + POI + 2 气象）\n每宽表 4,344 行 × 275 分区 = 1,194,600 行", TEAL),
        ("DWD　明细层", "zone_hour_metric（宽转长后 6 指标 × 1,194,600 行 = 7,167,600 行）\ndim_zone_info（275 行）· dq_zone_stat（质检统计）", BLUE),
        ("DWS　汇总层", "zone_day_hour（分区 × 日 × 时）· zone_day（分区 × 日）\nzone_hour_profile（7 日滚动均值 / 峰谷差）", PURPLE),
        ("ADS　应用层", "7 张应用表，一表 = 一前端图表\ndashboard_kpi · zone_occupancy · hourly_supply_demand\nimbalance_index · price_elasticity · demand_forecast · expansion_suggestion", AMBER),
    ]
    ys = [0.80, 0.585, 0.37, 0.155]
    for (name, desc, c), y in zip(layers, ys):
        box(ax1, 0.055, y - 0.085, 0.89, 0.17, "", "#FFFFFF", c, "#FFFFFF", 10)
        ax1.text(0.085, y + 0.045, name, fontsize=12.5, color=c, fontweight="bold", va="center")
        ax1.text(0.085, y - 0.038, desc, fontsize=9.6, color=INK, va="center", linespacing=1.5)
    for i in range(len(ys) - 1):
        arrow(ax1, (0.50, ys[i] - 0.088), (0.50, ys[i + 1] + 0.088), color=GREY, rad=0.0)
    ax1.text(0.50, 0.035,
             "★ 关键校验：DWD 行数 > ODS 行数（宽转长必然放大），这是「宽表转长生效」的硬证据",
             ha="center", fontsize=10.3, color=RED, fontweight="bold", transform=ax1.transAxes)

    # 右：实测数据质量（6 指标）
    dq = pd.read_csv(SRC / "dq_质量规则统计表.csv")
    ax2.set_facecolor("white")
    for s in ("top", "right"):
        ax2.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax2.spines[s].set_color(LINE)
    ax2.grid(axis="y", color="#E5E7EB", lw=0.8, zorder=0)
    ax2.set_axisbelow(True)
    ax2.tick_params(colors=MUT, labelsize=10)
    ax2.set_title("六项指标清洗前后（实测）", fontsize=13, color=INK,
                  fontweight="bold", pad=12)
    x = np.arange(len(dq))
    total = dq["total"].values / 1e4          # 万行
    zero = dq["is_zero_rows"].values / 1e4
    ax2.bar(x, total - zero, color="#E5E7EB", width=0.62, zorder=3, label="有效非零值")
    ax2.bar(x, zero, bottom=total - zero, color=BLUE, width=0.62, zorder=3, label="零值行")
    ax2.set_xticks(x)
    ax2.set_xticklabels(["occupancy", "duration", "volume", "volume_11kw", "e_price", "s_price"],
                         fontsize=9.5, rotation=18)
    ax2.set_ylabel("行数（万）", fontsize=11, color=INK)
    ax2.legend(loc="upper right", frameon=False, fontsize=10)
    for i, (t, z) in enumerate(zip(total, zero)):
        ax2.text(i, t + 1.5, f"{t:.0f}万", ha="center", fontsize=9.3, color=INK)
    ax2.text(0.02, 0.93, "★ 每项 119.46 万行，越界值 0、重复时间戳 0",
             transform=ax2.transAxes, fontsize=10.2, color=RED, fontweight="bold")
    fig.tight_layout()
    out = OUT / "06_四层数仓规模对比.png"
    fig.savefig(out, dpi=DPI, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {out.name}")


if __name__ == "__main__":
    print("生成 PPT 补充图")
    make_usecase()
    make_warehouse()
    print("完成")
