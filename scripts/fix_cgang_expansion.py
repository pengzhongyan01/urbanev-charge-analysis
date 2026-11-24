# -*- coding: utf-8 -*-
"""
重绘 C 岗图表 09（布点建议优先级分布）→ 契约口径
================================================
★ C 岗原图用「全市 275 分区、峰值压到 0.75」规则，算出 103 个分区需加桩、+1917 桩；
  契约 02 规定的是：
      建议新增桩数 = ⌈ 峰值失衡指数 I_max(z) × charge_count(z) × 0.3 ⌉
      适用范围     = 56 个「峰值失衡 > 0」的分区
  → 契约口径：56 个分区、现有桩 5,103、建议新增 93 个桩（+1.82%）
  本脚本按契约口径重绘，并同步替换她交付目录里的 expansion_suggestion.csv。

运行：python scripts/fix_cgang_expansion.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

REPO = Path(__file__).resolve().parent.parent
CG = REPO / "docs" / "C岗：图表-贺欢欢交付"
ADS = REPO / "analysis" / "output" / "ads" / "ads_expansion_suggestion.csv"
DATA_CSV = CG / "_全量数据" / "expansion_suggestion.csv"
CHART09 = CG / "C05_十个核心图表" / "09_布点建议优先级分布.png"
URBANEV = Path(r"D:/一系列作业/java后端/大作业/数据/UrbanEV")

BG, BG2, GRID = "#0a1628", "#112240", "#1e3a5f"
CYAN, ORANGE = "#00d4ff", "#ff6b35"
TXT, TXT2, TXT3 = "#e8f1ff", "#94a3b8", "#8fa8c8"


def main() -> None:
    df = pd.read_csv(ADS)
    df["zone_id"] = df["zone_id"].astype(str)
    df = df.sort_values("priority").reset_index(drop=True)

    n_zones = len(df)
    cur = int(df["current_piles"].sum())
    add = int(df["add_piles"].sum())
    pct = add / cur * 100

    inf = pd.read_csv(URBANEV / "inf.csv", dtype={"TAZID": str}).set_index("TAZID")
    inf.index = inf.index.astype(str)
    df["longitude"] = df["zone_id"].map(inf["longitude"])
    df["latitude"] = df["zone_id"].map(inf["latitude"])

    # ── 1. 同步数据文件（契约口径 + 她的字段名）────────────────────
    out = df[["zone_id", "longitude", "latitude", "current_piles", "add_piles",
              "suggested_piles", "priority", "peak_gap", "peak_hour",
              "avg_occupancy", "reason"]].copy()
    out["zone_type"] = "P1-持续紧张"
    out.to_csv(DATA_CSV, index=False, encoding="utf-8-sig")
    print(f"✓ 已更新 expansion_suggestion.csv（{len(out)} 行，契约口径）")
    print(f"  需加桩分区 {n_zones} 个，现有桩 {cur}，建议新增 {add} 个（+{pct:.2f}%）")

    # ── 2. 重绘图 09 ────────────────────────────────────────────────
    top = df.head(15).iloc[::-1]      # 画出来是 TOP1 在最上
    fig = plt.figure(figsize=(14.5, 9.2), dpi=160, facecolor=BG)
    ax = fig.add_axes([0.095, 0.115, 0.875, 0.585])
    ax.set_facecolor(BG2)

    x = np.arange(len(top))
    w = 0.38
    b1 = ax.bar(x - w / 2, top["current_piles"], w, color=CYAN, label="现有桩数", zorder=3)
    b2 = ax.bar(x + w / 2, top["add_piles"], w, color=ORANGE, label="建议新增", zorder=3)

    for i, (c, a_, z, h) in enumerate(zip(top["current_piles"], top["add_piles"],
                                          top["zone_id"], top["peak_hour"])):
        if a_ > 0:
            ax.text(i + w / 2, c + 6, f"+{int(a_)}", ha="center", fontsize=10, color=ORANGE)
        ax.text(i - w / 2, c + 6, f"{int(c)}", ha="center", fontsize=9.5, color=TXT2)

    ax.set_xticks(x)
    ax.set_xticklabels([f"{z}\n{h:02d}时" for z, h in zip(top["zone_id"], top["peak_hour"])],
                       fontsize=10, color=TXT)
    ax.set_ylabel("桩数", fontsize=12, color=TXT2)
    ax.set_xlabel("分区 ID（下行标注峰值失衡时段）", fontsize=12, color=TXT2)
    ax.set_title("布点扩容建议 TOP15（现有桩数 vs 建议新增）",
                 fontsize=17, color=TXT, weight="bold", pad=14)
    ax.tick_params(colors=TXT2, labelsize=10)
    for sp in ax.spines.values():
        sp.set_color(GRID)
    ax.grid(axis="y", color=GRID, linestyle="--", alpha=0.6, zorder=0)
    leg = ax.legend(fontsize=11, facecolor=BG2, edgecolor=GRID, loc="upper right")
    for t in leg.get_texts():
        t.set_color(TXT)

    # ── 3. 顶部橙色结论带 ──────────────────────────────────────────
    concl1 = (f"1.全市 {n_zones} 个分区存在供需缺口，需新增 {add} 个桩（现有 {cur} 个，+{pct:.2f}%），"
              f"扩容后各分区桩数均多于现有。")
    concl2 = (f"2.优先扩容 TOP5：595 区（274→285，第 8 时）、1167 区（446→458，第 17 时）、"
              f"844 区（91→94）、775 区（52→54）、1026 区（77→79）。")

    fig.patches.append(plt.Rectangle(
        (0.010, 0.855), 0.980, 0.135, transform=fig.transFigure,
        facecolor="#132038", edgecolor=ORANGE, linewidth=1.6, zorder=5))
    fig.patches.append(plt.Rectangle(
        (0.020, 0.933), 0.028, 0.028, transform=fig.transFigure,
        facecolor=ORANGE, edgecolor="none", zorder=6))
    fig.text(0.033, 0.940, "结论", fontsize=10, color="#0a1628",
             weight="bold", va="center", zorder=7)
    fig.text(0.058, 0.940, concl1, fontsize=11.5, color=TXT, va="center", zorder=7)
    fig.text(0.058, 0.895, concl2, fontsize=11.5, color=TXT, va="center", zorder=7)
    fig.text(0.058, 0.836,
             "补充：契约规则 建议新增桩数 = 向上取整( 峰值失衡指数 I_max(z) × charge_count(z) × 0.3 )；"
             "适用范围为峰值失衡 > 0 的 56 个分区。",
             fontsize=10, color=TXT3, va="center", zorder=7)

    fig.savefig(CHART09, facecolor=BG, dpi=160)
    plt.close(fig)
    from PIL import Image
    w, h = Image.open(CHART09).size
    print(f"✓ 已重绘 {CHART09.name}（{w}×{h}）")


if __name__ == "__main__":
    main()
