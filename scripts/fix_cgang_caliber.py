# -*- coding: utf-8 -*-
"""
C 岗图表口径对齐（组长 A 岗执行）
=================================
★ 背景：C 岗（贺欢欢）2026-11-24 推交的 `docs/C岗：图表-贺欢欢交付/` 里，
  图表 04（供需失衡指数）与 09（布点建议）用的是 **ETL 旧差值口径**
  （I = DI − D̄，值域 [0.65, 0.88]，316 区霸榜），
  与契约 02 的 **份额差口径**（I = D − S，值域 [−0.0129, 0.1225]，595 区峰值）矛盾。
  根因：她读的 `imbalance_index.csv` 来自 ETL，而 ETL 的该表尚未修正。
  ★ 今天 ETL 已修正（scripts/python_etl.py），但她交付目录里冻结的是旧副本。

本脚本做两件事：
  1. 把她交付目录 `_全量数据/imbalance_index.csv` 换成契约份额差口径
     （并补 dt / demand / supply / 经纬度列，保持她的字段结构不变）
  2. 重绘图 04（供需失衡指数 TOP15），沿用她的深色大屏风格 + 顶部橙色结论带

运行：python scripts/fix_cgang_caliber.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

# 中文字体（缺字体时中文会渲染成方框）
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

REPO = Path(__file__).resolve().parent.parent
CG = REPO / "docs" / "C岗：图表-贺欢欢交付"
DATA_CSV = CG / "_全量数据" / "imbalance_index.csv"
ADS = REPO / "analysis" / "output" / "ads" / "ads_imbalance_index.csv"
URBANEV = Path(r"D:/一系列作业/java后端/大作业/数据/UrbanEV")
CHART04 = CG / "C05_十个核心图表" / "04_供需失衡指数_分区TOP15.png"

# ── C 岗配色（深色大屏：主色 #00d4ff，强调色 #ff6b35）────────────────────
BG = "#0a1628"
BG2 = "#112240"
GRID = "#1e3a5f"
CYAN = "#00d4ff"
ORANGE = "#ff6b35"
TXT = "#e8f1ff"
TXT2 = "#94a3b8"
TXT3 = "#8fa8c8"


def main() -> None:
    # ── 1. 读取契约口径 ADS 表（份额差 275 × 24 = 6600 行）────────────
    ads = pd.read_csv(ADS)
    ads["zone_id"] = ads["zone_id"].astype(str)

    # 补经纬度
    inf = pd.read_csv(URBANEV / "inf.csv", dtype={"TAZID": str}).set_index("TAZID")
    inf.index = inf.index.astype(str)
    ads["longitude"] = ads["zone_id"].map(inf["longitude"])
    ads["latitude"] = ads["zone_id"].map(inf["latitude"])

    # ── 2. 计算 demand / supply 的可读形态（保持她的字段结构）──────────
    # 她的原表：demand = 需求份额、supply = 桩数、imbalance = 差值
    # 契约口径下：demand_share / supply_share 已是份额，imbalance = D − S
    # ★ 若 ADS 表被上一次的运行覆盖过（写回时只留了 9 列），从原始 ADS 重建
    if "demand_share" not in ads.columns or "supply_share" not in ads.columns:
        ads = pd.read_csv(ADS)
        ads["zone_id"] = ads["zone_id"].astype(str)
        ads["longitude"] = ads["zone_id"].map(inf["longitude"])
        ads["latitude"] = ads["zone_id"].map(inf["latitude"])

    total_piles = float(inf["charge_count"].sum())
    ads["demand"] = ads["demand_share"].round(6)
    ads["supply"] = (ads["supply_share"] * total_piles).round(0).astype(int)
    ads["dt"] = "全期"

    out = ads[["zone_id", "longitude", "latitude", "dt", "hour_of_day",
               "demand", "supply", "imbalance", "rank_no",
               "demand_share", "supply_share"]].copy()
    # 全时段按分区取峰值（契约判据：分区全时段峰值失衡 > 0 即为供不应求）
    peak = out.loc[out.groupby("zone_id")["imbalance"].idxmax()].copy()
    peak = peak.sort_values("imbalance", ascending=False).reset_index(drop=True)

    n_pos = int((out.groupby("zone_id")["imbalance"].max() > 0).sum())
    print(f"契约口径：供不应求分区 {n_pos} / {out['zone_id'].nunique()}")
    print(f"峰值分区 {peak.iloc[0]['zone_id']}  值 {peak.iloc[0]['imbalance']:.4f}")

    # ── 3. 写回她的交付数据目录 ─────────────────────────────────────
    # 保留她原有的 9 列 + 补上 demand_share / supply_share（口径可追溯）
    out_full = ads[["zone_id", "longitude", "latitude", "dt", "hour_of_day",
                    "demand", "supply", "imbalance", "rank_no",
                    "demand_share", "supply_share"]].copy()
    out_full.to_csv(DATA_CSV, index=False, encoding="utf-8-sig")
    print(f"✓ 已更新 {DATA_CSV.name}（{len(out_full)} 行，份额差口径）")

    # ── 4. 重绘图 04 ─────────────────────────────────────────────────
    top = peak.head(15).sort_values("imbalance", ascending=True)

    # 桩数与 POI 数（供结论引用）
    poi = pd.read_csv(URBANEV / "poi.csv", dtype={"TAZID": str})
    poi_cols = [c for c in poi.columns if c.lower() != "tazid"]
    poi_cnt = poi.groupby("TAZID").size() if "TAZID" in poi.columns else None
    z1 = peak.iloc[0]["zone_id"]
    z1_piles = int(inf.loc[z1, "charge_count"])
    z1_poi = int(poi_cnt.get(z1, 0)) if poi_cnt is not None else 0
    n_pos = int((out.groupby("zone_id")["imbalance"].max() > 0).sum())

    concl1 = (f"1.失衡高度集中在 {n_pos} 个分区（全市 275 个分区中占 {n_pos/275*100:.1f}%），"
              f"这些分区某些小时的需求份额明显高于运力份额，需提前排班、预留移动充电车。")
    concl2 = (f"2.{z1} 区是「桩最多、需求份额最高」的典型——峰值失衡 {peak.iloc[0]['imbalance']:.4f}，"
              f"占全市需求份额的 {peak.iloc[0]['demand']*100:.2f}%，而运力份额仅 {peak.iloc[0]['supply_share']*100:.2f}%。")

    # ★ ≥2200px 宽（C 岗验收标准），160dpi 下 figsize 需 ≥13.75 英寸
    fig = plt.figure(figsize=(14.5, 9.2), dpi=160, facecolor=BG)
    ax = fig.add_axes([0.095, 0.115, 0.875, 0.585])
    ax.set_facecolor(BG2)

    # 正值柱：前 5 名用强调橙，其余用主青
    top_rank = top["rank_no"].to_numpy()
    colors = [ORANGE if r <= 3 else CYAN for r in top_rank]
    ax.barh(range(len(top)), top["imbalance"], color=colors, height=0.68, zorder=3)

    for i, (z, v, r) in enumerate(zip(top["zone_id"], top["imbalance"], top["rank_no"])):
        ax.text(v + 0.0035, i, f"{v:.4f}（{r}）", va="center", fontsize=11, color=TXT)

    ax.set_yticks(range(len(top)))
    ax.set_yticklabels([f"{z}" for z in top["zone_id"]], fontsize=11, color=TXT)
    ax.set_xlabel("失衡指数 I（份额差 D − S）", fontsize=12, color=TXT2)
    ax.set_ylabel("分区 ID", fontsize=12, color=TXT2)
    ax.set_title("供需失衡指数 · 分区 TOP15（全量 275 分区 × 24 时段）",
                 fontsize=17, color=TXT, weight="bold", pad=14)
    ax.tick_params(colors=TXT2, labelsize=10)
    for sp in ax.spines.values():
        sp.set_color(GRID)
    ax.grid(axis="x", color=GRID, linestyle="--", alpha=0.6, zorder=0)
    ax.axvline(0, color=TXT3, lw=1.2, zorder=4)

    m = float(top["imbalance"].max())
    ax.set_xlim(0, m * 1.32)

    # 顶部橙色结论带（沿用她的样式，下方留出「补充」行）
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

    # 「补充」行放在结论带下方，避免被遮挡
    fig.text(0.058, 0.836,
             "补充：契约口径 I = D(z,t) − S(z)，D 为需求份额、S 为运力份额；"
             "分区全时段峰值失衡 > 0 即判为供不应求分区（全市 56 个）。",
             fontsize=10, color=TXT3, va="center", zorder=7)

    fig.savefig(CHART04, facecolor=BG, dpi=160)
    plt.close(fig)
    from PIL import Image
    w, h = Image.open(CHART04).size
    print(f"✓ 已重绘 {CHART04.name}（{w}×{h}）")


if __name__ == "__main__":
    main()
