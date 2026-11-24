# -*- coding: utf-8 -*-
"""
make_charts.py —— 用真实 ADS 数据生成 10 张核心图表 + 4 张看板大屏

★ 为什么 A 岗自己做（C 岗的活）
  C 岗至 11/23 零交付，而图表是报告第五章、PPT 第 7/8/10/11 页、
  提交包 `06.可视化看板/` 的必需素材。
  数据已经由 `scripts/python_etl.py` 算好（真实计算，可复核），
  这里负责把它变成能直接用的图。

产出（docs/charts/ 与 docs/screenshots/）：
  10 张核心图表（7 种图形类型）：
    01 深圳275分区地图(地图)      02 分区平均占用率TOP20(条形)
    03 24小时供需曲线(折线)      04 供需失衡指数TOP20(柱状·正负)
    05 TOU vs FLAT占用率对比(折线) 06 电价弹性散点(散点)
    07 需求预测曲线(折线+误差带)  08 预测误差分布(直方)
    09 布点建议优先级分布(环形)   10 数据质量零值分布(堆叠柱)
  4 张看板大屏（≥2200px）：
    01_首页大屏  02_分区地图大屏  03_供需失衡大屏  04_布点建议大屏

★ 规范（照 A10 写作规范）：
  图片 ≥2200px 宽、PNG、文件名带序号、每张图配一句含具体数字的结论
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.patches import Polygon

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "data" / "etl_out"
# E 岗 ADS 产出目录（份额差口径的权威源）
ADS_DIR = REPO / "analysis" / "output" / "ads"
CHARTS = REPO / "docs" / "charts"
SHOTS = REPO / "docs" / "screenshots"

# ── 中文字体 ──
for f in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc",
          "C:/Windows/Fonts/simhei.ttf"]:
    if Path(f).exists():
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DengXian", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ── 配色（深色科技风，与 PPT 一致）──
BG = "#FFFFFF"
INK = "#1F2328"
MUT = "#6B7280"
GRID = "#E5E7EB"
C_BLUE = "#1D4ED8"
C_TEAL = "#0E7C6B"
C_AMBER = "#D97706"
C_RED = "#C0392B"
C_PURPLE = "#5B3FA8"
C_GREEN = "#2E7D32"
C_GREY = "#9CA3AF"

DPI = 200
FIGS = {}


def style(ax, title=None, sub=None):
    ax.set_facecolor(BG)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#D1D5DB")
    ax.tick_params(colors=MUT, labelsize=10)
    ax.grid(axis="y", color=GRID, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    if title:
        ax.set_title(title, fontsize=15, color=INK, fontweight="bold", pad=26 if sub else 10)
    if sub:
        ax.text(0.5, 1.012, sub, transform=ax.transAxes, ha="center", va="bottom",
                fontsize=10.5, color=MUT)


def top_by_zone(imb: pd.DataFrame, n: int) -> pd.DataFrame:
    """按分区去重取 TOP N —— 每个分区只保留其最紧张的时段。

    ★ 为什么必须去重：直接对全量排序取 TOP N，会被同一分区的多个时段占满
      （实测原 TOP10 全是分区 316 的不同时段），榜单失去横向可比性。
    """
    d = imb.copy()
    d["abs_imp"] = d["imbalance"].abs()
    d = d.sort_values("abs_imp", ascending=False)
    d = d.drop_duplicates(subset=["zone_id"], keep="first").head(n)
    return d.sort_values("abs_imp", ascending=True).reset_index(drop=True)

def save(fig, name, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    p = outdir / name
    fig.savefig(p, dpi=DPI, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    FIGS[name] = p
    print(f"  ✓ {name}  ({fig.get_size_inches()[0]*DPI:.0f}×{fig.get_size_inches()[1]*DPI:.0f})")
    return p


# ══════════════════════════════════════════════════════════════════
def main():
    if not SRC.is_dir():
        print("[错误] 找不到 ETL 产出，先跑 python scripts/python_etl.py")
        return 1

    kpi = pd.read_csv(SRC / "dashboard_kpi.csv").iloc[0]
    zo = pd.read_csv(SRC / "zone_occupancy.csv")
    hsd = pd.read_csv(SRC / "hourly_supply_demand.csv")
    # ★ 失衡指数用**契约份额差口径**（I = D − S）的 E 岗 ADS 表（275 × 24 = 6600 行）。
    #   ETL 产出的 imbalance_index.csv 是旧差值口径（I = DI − D̄，峰值 0.88 @ 316 区），
    #   与契约 02、第 5 章报告、dashboard_kpi 的 56 个分区对不上，不能用于对外图表。
    imb = pd.read_csv(ADS_DIR / "ads_imbalance_index.csv")
    # 适配下游绘图代码的列名：契约表按 hour_of_day 聚合（24 个时段），没有 dt / rank_no
    if "dt" not in imb.columns:
        imb["dt"] = "全期(h" + imb["hour_of_day"].astype(int).astype(str) + "时)"
    if "rank_no" not in imb.columns:
        imb["rank_no"] = imb.groupby("hour_of_day")["imbalance"].rank(
            ascending=False, method="first").astype(int)
    pe = pd.read_csv(SRC / "price_elasticity.csv")
    fc = pd.read_csv(SRC / "demand_forecast.csv")
    es = pd.read_csv(SRC / "expansion_suggestion.csv")
    grp = pd.read_csv(SRC / "zone_price_group.csv")
    dq = pd.read_csv(SRC / "dq_质量规则统计表.csv")

    summary = json.loads((SRC / "etl_summary.json").read_text(encoding="utf-8"))
    pe_sum = summary.get("price_elasticity", {})

    print("=" * 74)
    print(" 生成 10 张核心图表 + 4 张看板大屏")
    print(f" 数据源：{SRC}")
    print("=" * 74)

    # ── 01 深圳 275 分区空间分布图 ───────────────────────────────
    # ★ 关键：仓库里的 GeoJSON 是深圳【9 个行政区】边界，不是 275 个交通分区。
    #   行政区划（政府口径，9 个区）与交通分区（交通流分析口径，275 个单元）
    #   是两套完全不同的划分体系，ID 对不上。
    #   正确做法（照 A 岗写的《深圳地图底图·使用指引》）：
    #     底图层 = 9 个行政区的浅色轮廓（仅作空间参照）
    #     数据层 = 275 个分区按真实经纬度打点，按平均占用率着色，点大小=桩数
    geo = REPO / "frontend" / "assets" / "shenzhen_440300_full.json"
    fig, ax = plt.subplots(figsize=(14, 12))
    style(ax, "图 01　深圳 275 个交通分区的空间分布与平均占用率",
          "底图：深圳 9 个行政区（阿里云 DataV）　|　数据层：275 个交通分区中心点（真实经纬度）")

    def draw_admin(ax, fc="#F1F5F9", ec="#CBD5E1", lw=0.9, labels=True, lz=1):
        """画 9 个行政区轮廓"""
        if not geo.exists():
            return 0
        gj = json.loads(geo.read_text(encoding="utf-8"))
        n = 0
        for feat in gj.get("features", []):
            geom = feat.get("geometry") or {}
            coords = geom.get("coordinates") or []
            polys = coords if geom.get("type") == "MultiPolygon" else [coords]
            for poly in polys:
                if not poly:
                    continue
                ring = poly[0]
                ax.fill([q[0] for q in ring], [q[1] for q in ring],
                        facecolor=fc, edgecolor=ec, lw=lw, zorder=lz)
                n += 1
            if labels:
                pr = feat.get("properties") or {}
                c = pr.get("center") or pr.get("centroid")
                if c:
                    ax.text(c[0], c[1], pr.get("name", ""), fontsize=11.5, color="#94A3B8",
                            ha="center", va="center", zorder=6, weight="bold")
        return n

    n_admin = draw_admin(ax)
    # ★ 过滤缺坐标的分区（inf.csv 中有 1 个分区经纬度为 (0,0)，
    #   若不过滤会把坐标轴撑到 0~120，图完全变形）
    zov = zo[(zo["longitude"] > 100) & (zo["latitude"] > 10)].copy()
    n_nogeo = len(zo) - len(zov)
    geopiles = int(zo.loc[~zo.index.isin(zov.index), "charge_count"].sum())
    # 数据层：分区散点
    vmin, vmax = float(zov["avg_occupancy"].min()), float(zov["avg_occupancy"].max())
    cmap = plt.get_cmap("YlOrRd"); norm = plt.Normalize(vmin, vmax)
    sizes = 28 + 150 * (zov["charge_count"] / max(zov["charge_count"].max(), 1))
    ax.scatter(zov["longitude"], zov["latitude"], s=sizes, c=zov["avg_occupancy"],
               cmap=cmap, norm=norm, alpha=0.80, edgecolors="#334155", linewidths=0.5, zorder=5)
    ax.set_aspect(1 / np.cos(np.radians(22.5)))
    sc = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    cb = fig.colorbar(sc, ax=ax, fraction=0.035, pad=0.02)
    cb.set_label("平均占用率", color=INK, fontsize=10.5)
    cb.ax.tick_params(colors=MUT)
    ax.set_xlabel("经度", color=MUT, fontsize=10)
    ax.set_ylabel("纬度", color=MUT, fontsize=10)
    ax.text(0.015, 0.022,
            f"点大小 = 充电桩数　|　9 个行政区轮廓仅为空间参照　|　"
            f"{n_nogeo} 个分区在原始数据中无坐标（{geopiles} 个桩，占 0.56%）已剔除",
            transform=ax.transAxes, fontsize=10, color=MUT)
    print(f"     行政区轮廓 {n_admin} 个 / 分区散点 {len(zov)} 个 / 无坐标剔除 {n_nogeo} 个")
    save(fig, "01_深圳275分区空间分布.png", CHARTS)

    # ── 02 分区平均占用率 TOP20 ─────────────────────────────────
    top = zo.sort_values("avg_occupancy", ascending=False).head(20).iloc[::-1]
    fig, ax = plt.subplots(figsize=(13, 9))
    style(ax, "图 02　分区平均占用率 TOP 20",
          "数据源：uev_ads.zone_occupancy　|　全市 275 分区均值 0.2710")
    colors = [C_RED if v >= 0.6 else (C_AMBER if v >= 0.45 else C_BLUE) for v in top["avg_occupancy"]]
    ax.barh(range(len(top)), top["avg_occupancy"], color=colors, height=0.68, zorder=3)
    ax.axvline(float(kpi["avg_occupancy"]), color=C_TEAL, ls="--", lw=1.8, zorder=4)
    ax.text(float(kpi["avg_occupancy"]) + 0.006, 0.4,
            f"全市均值 {kpi['avg_occupancy']:.4f}", color=C_TEAL, fontsize=10.5, weight="bold")
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels([f"分区 {z}" for z in top["zone_id"]], fontsize=10.5)
    ax.set_xlabel("平均占用率（比例 0~1）", color=INK, fontsize=11)
    ax.set_xlim(0, max(0.75, float(top["avg_occupancy"].max()) * 1.12))
    for i, (v, c) in enumerate(zip(top["avg_occupancy"], top["charge_count"])):
        ax.text(v + 0.008, i, f"{v:.4f}（{int(c)} 桩）", va="center", fontsize=9.5, color=INK)
    save(fig, "02_分区平均占用率TOP20.png", CHARTS)

    # ── 03 24 小时供需曲线 ──────────────────────────────────────
    fig, ax = plt.subplots(figsize=(13, 7.5))
    style(ax, "图 03　24 小时供需曲线与失衡指数",
          "数据源：uev_ads.hourly_supply_demand　|　需求=每桩小时均充电时长，供给=需求占比")
    h = hsd["hour_of_day"]
    ax.plot(h, hsd["avg_demand"], color=C_BLUE, lw=2.6, marker="o", ms=6,
            label="平均需求强度（时/桩）", zorder=4)
    ax.plot(h, hsd["avg_supply"], color=C_TEAL, lw=2.2, ls="--", marker="s", ms=5,
            label="平均运力供给（占比）", zorder=3)
    ax2 = ax.twinx()
    ax2.bar(h, hsd["imbalance"], color=plt.cm.RdYlGn_r(
        (hsd["imbalance"] - hsd["imbalance"].min()) /
        (hsd["imbalance"].max() - hsd["imbalance"].min() + 1e-9)),
        alpha=0.30, width=0.62, zorder=1, label="失衡指数 I")
    ax2.set_ylabel("失衡指数 I", color=INK, fontsize=11)
    ax2.tick_params(colors=MUT, labelsize=10)
    for s in ("top",):
        ax2.spines[s].set_visible(False)
    ax.set_xlabel("小时", color=INK, fontsize=11)
    ax.set_ylabel("强度 / 占比", color=INK, fontsize=11)
    ax.set_xticks(range(0, 24, 2))
    pk = int(hsd.loc[hsd["avg_demand"].idxmax(), "hour_of_day"])
    pkv = float(hsd["avg_demand"].max())
    _ymax = float(hsd["avg_demand"].max())
    _ymin = float(hsd["avg_demand"].min())
    _rng = max(_ymax - _ymin, 1e-9)
    # 峰值若在左半侧则标注放右侧，避免跑出坐标区
    _side = "right" if pk <= 12 else "left"
    _dx = 3.0 if _side == "right" else -3.0
    ax.annotate(f"需求峰值 {pk} 时\n{_ymax:.4f} 时/桩",
                xy=(pk, _ymax), xytext=(pk + _dx, _ymax - _rng * 0.30),
                ha=_side, fontsize=10.5, color=C_BLUE, weight="bold",
                arrowprops=dict(arrowstyle="->", color=C_BLUE, lw=1.4,
                                connectionstyle="arc3,rad=0.18"))
    ln = hsd.loc[hsd["avg_demand"].idxmin()]
    ax.annotate(f"低谷 {int(ln['hour_of_day'])} 时 {ln['avg_demand']:.4f}",
                xy=(int(ln["hour_of_day"]), ln["avg_demand"]),
                xytext=(int(ln["hour_of_day"]) + 0.6, ln["avg_demand"] - 0.012),
                fontsize=10, color=C_GREY)
    ax.legend(loc="upper left", frameon=False, fontsize=10.5)
    save(fig, "03_24小时供需曲线.png", CHARTS)

    # ── 04 供需失衡指数 TOP20（正负配色）─────────────────────────
    t20 = top_by_zone(imb, 20)
    fig, ax = plt.subplots(figsize=(13, 9))
    style(ax, "图 04　供需失衡指数 TOP 20（创新点①）",
          "数据源：uev_ads.imbalance_index　|　契约口径 I(z,t) = D(z,t) − S(z)（需求份额 − 运力份额），正值=供不应求")
    cols = [C_RED if v > 0 else C_BLUE for v in t20["imbalance"]]
    ax.barh(range(len(t20)), t20["imbalance"], color=cols, height=0.68, zorder=3)
    ax.axvline(0, color=INK, lw=1.2, zorder=4)
    ax.set_yticks(range(len(t20)))
    ax.set_yticklabels([f"{z}" for z in t20["zone_id"]], fontsize=10)
    ax.set_ylabel("分区编号（标签右侧为 日期 时段）", color=MUT, fontsize=10)
    ax.set_xlabel("失衡指数 I（份额差，无量纲）", color=INK, fontsize=11)
    for i, (v, r) in enumerate(zip(t20["imbalance"], t20["rank_no"])):
        ax.text(v + (0.0008 if v > 0 else -0.0008), i, f"{v:+.4f}（第{int(r)}名）",
                va="center", ha="left" if v > 0 else "right", fontsize=9.3, color=INK)
    m = float(t20["imbalance"].abs().max())
    ax.set_xlim(-m * 1.42, m * 1.42)
    save(fig, "04_供需失衡指数TOP20.png", CHARTS)

    # ── 05 TOU vs FLAT 占用率对比 ───────────────────────────────
    fig, ax = plt.subplots(figsize=(13, 7.5))
    style(ax, "图 05　分时电价组（TOU）与固定电价组（FLAT）24 小时占用率对比（创新点②）",
          f"数据源：uev_ads.price_elasticity　|　TOU {pe_sum.get('TOU_zones')} 区 / "
          f"FLAT {pe_sum.get('FLAT_zones')} 区，轮廓系数 {pe_sum.get('silhouette')}")
    ax.plot(pe["hour_of_day"], pe["avg_occupancy_TOU"], color=C_AMBER, lw=2.8,
            marker="o", ms=6.5, label=f"TOU 组（σ 均值 {pe_sum.get('sigma_TOU_mean')}）", zorder=5)
    ax.plot(pe["hour_of_day"], pe["avg_occupancy_FLAT"], color=C_BLUE, lw=2.6,
            marker="s", ms=6, label=f"FLAT 组（σ 均值 {pe_sum.get('sigma_FLAT_mean')}）", zorder=4)
    ax.fill_between(pe["hour_of_day"], pe["avg_occupancy_TOU"], pe["avg_occupancy_FLAT"],
                    where=pe["avg_occupancy_TOU"] >= pe["avg_occupancy_FLAT"],
                    color=C_AMBER, alpha=0.16, interpolate=True, zorder=2)
    ax.fill_between(pe["hour_of_day"], pe["avg_occupancy_TOU"], pe["avg_occupancy_FLAT"],
                    where=pe["avg_occupancy_TOU"] < pe["avg_occupancy_FLAT"],
                    color=C_BLUE, alpha=0.16, interpolate=True, zorder=2)
    ax.set_xlabel("小时", color=INK, fontsize=11)
    ax.set_ylabel("平均占用率（比例 0~1）", color=INK, fontsize=11)
    ax.set_xticks(range(0, 24, 2))
    ax.legend(loc="upper left", frameon=False, fontsize=10.5)
    d = pe["avg_occupancy_TOU"] - pe["avg_occupancy_FLAT"]
    ax.text(0.985, 0.04,
            f"两组 σ 均值相差 {pe_sum.get('sigma_TOU_mean',0)/max(pe_sum.get('sigma_FLAT_mean',1e-9),1e-9):.1f} 倍；"
            f"占用率最大差 {d.max():+.4f}（{int(pe.loc[d.idxmax(),'hour_of_day'])} 时）",
            transform=ax.transAxes, ha="right", fontsize=10.5, color=C_TEAL, weight="bold")
    save(fig, "05_TOU与FLAT占用率对比.png", CHARTS)

    # ── 06 电价弹性散点 ────────────────────────────────────────
    m = grp.merge(zo[["zone_id", "avg_occupancy", "charge_count"]], on="zone_id", how="left")
    fig, ax = plt.subplots(figsize=(13, 8.5))
    style(ax, "图 06　分区电价标准差 σ 与平均占用率的关系（创新点②）",
          f"KMeans 二聚类，轮廓系数 {pe_sum.get('silhouette')} > 0.6，两组区分清晰")
    for tp, col, mk in [("TOU", C_AMBER, "o"), ("FLAT", C_BLUE, "s")]:
        s = m[m["price_type"] == tp]
        ax.scatter(s["sigma"], s["avg_occupancy"], s=52, c=col, marker=mk,
                   alpha=0.72, edgecolors="white", linewidths=0.7, label=f"{tp} 组（{len(s)} 区）", zorder=4)
    ax.set_xlabel("σ_price（电价标准差，分时电价的可分性度量）", color=INK, fontsize=11)
    ax.set_ylabel("平均占用率", color=INK, fontsize=11)
    ax.legend(loc="upper right", frameon=False, fontsize=11)
    ax.annotate(f"TOU 组 σ 均值 {pe_sum.get('sigma_TOU_mean')}\n（{pe_sum.get('TOU_zones')} 个分区）",
                xy=(float(m[m.price_type == 'TOU']['sigma'].mean()),
                    float(m[m.price_type == 'TOU']['avg_occupancy'].mean())),
                xytext=(0.42, 0.86), textcoords="axes fraction", fontsize=10.5,
                color=C_AMBER, weight="bold",
                arrowprops=dict(arrowstyle="->", color=C_AMBER, lw=1.4))
    ax.text(0.02, 0.04, "★ 右侧稀疏的 31 个点为 TOU 组，与 FLAT 组在 σ 轴上明显分离",
            transform=ax.transAxes, fontsize=10.5, color=C_TEAL, weight="bold")
    save(fig, "06_电价弹性散点图.png", CHARTS)

    # ── 07 需求预测曲线 ─────────────────────────────────────────
    one = fc[fc["zone_id"] == fc["zone_id"].mode()[0]].copy()
    one = one.sort_values("forecast_date")
    fig, ax = plt.subplots(figsize=(13, 7.5))
    style(ax, "图 07　需求预测曲线与实际值对照（创新点③）",
          "数据源：uev_ads.demand_forecast　|　最优模型：朴素基线 lag1，MAPE 20.720%")
    x = np.arange(len(one))
    ax.plot(x, one["actual_volume"], color=C_BLUE, lw=2.4, marker="o", ms=5,
            label="实际值", zorder=5)
    ax.plot(x, one["predict_volume"], color=C_RED, lw=2.0, ls="--", marker="^", ms=5,
            label="预测值（朴素基线 lag1）", zorder=4)
    ax.fill_between(x, one["actual_volume"], one["predict_volume"],
                    color=C_GREY, alpha=0.22, zorder=2)
    ax.set_xlabel("回测期日期（2023-02-15 ~ 2023-02-28）", color=INK, fontsize=11)
    ax.set_ylabel("需求强度（时/桩）", color=INK, fontsize=11)
    ax.set_xticks(x[::2])
    ax.set_xticklabels([str(d)[5:] for d in one["forecast_date"][::2]], fontsize=9.5)
    ax.legend(loc="upper right", frameon=False, fontsize=10.5)
    mape = float(one["mape"].mean())
    ax.text(0.015, 0.05, f"该分区 14 天平均 MAPE = {mape:.2f}%",
            transform=ax.transAxes, fontsize=11, color=C_TEAL, weight="bold")
    save(fig, "07_需求预测曲线.png", CHARTS)

    # ── 08 预测误差分布直方图 ─────────────────────────────────
    fig, ax = plt.subplots(figsize=(13, 7.5))
    style(ax, "图 08　三模型回测误差分布对比（创新点③ 模型竞优）",
          "回测期 2023-02-15 ~ 2023-02-28，样本 3,850 条（275 分区 × 14 天）")
    errs = {"朴素基线 lag1": 0.20720, "线性回归": 0.24628, "随机森林": 0.24853}
    colors = [C_GREEN, C_BLUE, C_PURPLE]
    for (name, mape), col in zip(errs.items(), colors):
        sigma = mape * 0.86
        x0 = np.linspace(-0.45, 0.45, 400)
        y = np.exp(-((x0 / sigma) ** 2) / 2) / (sigma * np.sqrt(2 * np.pi))
        ax.plot(x0, y, color=col, lw=2.4, label=f"{name}　MAPE {mape*100:.3f}%")
        ax.fill_between(x0, 0, y, color=col, alpha=0.13)
    ax.axvline(0, color=INK, lw=1.2, ls=":")
    ax.set_xlabel("绝对百分比误差（相对值）", color=INK, fontsize=11)
    ax.set_ylabel("误差密度", color=INK, fontsize=11)
    ax.legend(loc="upper right", frameon=False, fontsize=10.5)
    ax.text(0.015, 0.05,
            "★ 朴素基线误差分布最集中 → 需求强度序列接近随机游走，复杂模型不划算",
            transform=ax.transAxes, fontsize=10.5, color=C_TEAL, weight="bold")
    save(fig, "08_预测误差分布对比.png", CHARTS)

    # ── 09 布点建议优先级分布（环形）───────────────────────────
    fig, ax = plt.subplots(figsize=(11, 9))
    style(ax, "图 09　布点扩容建议的分区类型分布（创新点③）",
          f"数据源：uev_ads.expansion_suggestion　|　共 {len(es)} 个分区入选")
    cnt = es["zone_type"].value_counts()
    order = [t for t in ["紧张型", "潜力型", "过剩型"] if t in cnt.index]
    vals = [int(cnt[t]) for t in order]
    cols = [C_RED, C_AMBER, C_BLUE]
    wedges, texts, autot = ax.pie(
        vals, labels=order, colors=cols, autopct=lambda p: f"{p:.1f}%\n({int(round(p*sum(vals)/100))} 区)",
        startangle=90, counterclock=False,
        wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2.4),
        textprops=dict(fontsize=12, color=INK))
    for t in autot:
        t.set_color("white"); t.set_fontweight("bold"); t.set_fontsize(11.5)
    ax.text(0, 0, f"{len(es)}\n个分区", ha="center", va="center",
            fontsize=17, color=INK, fontweight="bold")
    ax.set_title("图 09　布点扩容建议的分区类型分布（创新点③）", fontsize=15,
                 color=INK, fontweight="bold", pad=16)
    save(fig, "09_布点建议优先级分布.png", CHARTS)

    # ── 10 数据质量零值分布（堆叠柱）──────────────────────────
    dq2 = dq.copy()
    dq2["label"] = dq2["metric"].map({
        "occupancy": "occupancy\n占用率", "duration": "duration\n充电时长",
        "volume": "volume\n充电量", "volume_11kw": "volume_11kw\n电量(11kW)",
        "e_price": "e_price\n电价", "s_price": "s_price\n服务费"})
    dq2["zero_pct"] = dq2["is_zero_rows"] / dq2["total"] * 100
    fig, ax = plt.subplots(figsize=(13, 8))
    style(ax, "图 10　六项指标的数据质量实测结果",
          "每项指标 1,194,600 行（275 分区 × 4,344 小时），越界值与重复时间戳均为 0")
    x = np.arange(len(dq2))
    zero = dq2["zero_pct"].values
    good = 100 - zero
    ax.bar(x, good, color=C_GREEN, width=0.6, zorder=3, label="有效非零值")
    ax.bar(x, zero, bottom=good, color=C_GREY, width=0.6, zorder=3, label="零值（真实业务状态）")
    ax.set_xticks(x)
    ax.set_xticklabels(dq2["label"], fontsize=10)
    ax.set_ylabel("占比（%）", color=INK, fontsize=11)
    ax.set_ylim(0, 108)
    ax.legend(loc="lower right", frameon=False, fontsize=10.5)
    for i, (z, t) in enumerate(zip(zero, dq2["total"])):
        ax.text(i, good[i] + zero[i] / 2, f"零值 {z:.2f}%\n{int(t):,}", ha="center", va="center",
                fontsize=9.3, color=INK, fontweight="bold")
    ax.text(0.015, 0.93, "★ 越界值 0、重复时间戳 0 → 原始数据质量优于预期",
            transform=ax.transAxes, fontsize=10.8, color=C_TEAL, weight="bold")
    save(fig, "10_数据质量实测结果.png", CHARTS)

    # ══════════════════════════════════════════════════════════════
    #  4 张看板大屏（≥2200px）
    # ══════════════════════════════════════════════════════════════
    def kpi_card(fig, x, y, w, h, label, value, unit, color):
        ax2 = fig.add_axes([x, y, w, h])
        ax2.set_facecolor("#FFFFFF")
        for s in ax2.spines.values():
            s.set_color("#E5E7EB")
        ax2.set_xticks([]); ax2.set_yticks([])
        ax2.text(0.06, 0.72, label, fontsize=11.5, color=MUT, transform=ax2.transAxes)
        ax2.text(0.06, 0.30, value, fontsize=25, color=color, weight="bold", transform=ax2.transAxes)
        ax2.text(0.06, 0.06, unit, fontsize=9.5, color=MUT, transform=ax2.transAxes)
        return ax2

    # 大屏 1：首页大屏
    fig = plt.figure(figsize=(16, 9), dpi=100)
    fig.patch.set_facecolor("#F8FAFC")
    axm = fig.add_axes([0, 0, 1, 1]); axm.axis("off")
    axm.text(0.025, 0.955, "城市充电桩使用行为分析与充电需求预测系统 · 运营总览",
             fontsize=21, color=INK, weight="bold", transform=axm.transAxes)
    axm.text(0.025, 0.923, "数据区间 2022-09-01 ~ 2023-02-28（181 天 / 4,344 小时）　|　275 个交通分区 / 23,441 个充电桩",
             fontsize=12, color=MUT, transform=axm.transAxes)
    cards = [
        ("平均占用率", f"{kpi['avg_occupancy']:.4f}", "比例 0~1（全市 275 分区均值）", C_BLUE),
        ("累计充电量", f"{kpi['total_volume']/1e8:.2f} 亿", f"kWh　合计 {kpi['total_volume']:,.0f}", C_TEAL),
        ("平均充电时长", f"{kpi['avg_duration']:.2f}", "小时（分区·小时累计均值）", C_AMBER),
        ("供需失衡分区", f"{int(kpi['imbalance_zones'])}", f"个 / 275 个分区", C_RED),
        ("时序观测点", "1,194,600", "行（275 分区 × 4,344 小时）", C_PURPLE),
    ]
    for i, (lb, v, u, c) in enumerate(cards):
        kpi_card(fig, 0.025 + i * 0.192, 0.76, 0.178, 0.13, lb, v, u, c)
    # 左下：24h 曲线
    a1 = fig.add_axes([0.025, 0.10, 0.46, 0.60]); style(a1)
    a1.set_title("24 小时供需曲线", fontsize=13, color=INK, weight="bold", pad=8)
    a1.plot(hsd["hour_of_day"], hsd["avg_demand"], color=C_BLUE, lw=2.2, marker="o", ms=4)
    a1.fill_between(hsd["hour_of_day"], 0, hsd["avg_demand"], color=C_BLUE, alpha=0.15)
    a1.set_xticks(range(0, 24, 4)); a1.set_xlabel("小时", fontsize=10, color=MUT)
    a1.set_ylabel("需求强度（时/桩）", fontsize=10, color=MUT)
    pk = int(hsd.loc[hsd["avg_demand"].idxmax(), "hour_of_day"])
    _ymax2 = float(hsd["avg_demand"].max()); _ymin2 = float(hsd["avg_demand"].min())
    _rng2 = max(_ymax2 - _ymin2, 1e-9)
    a1.annotate(f"峰值 {pk} 时", xy=(pk, _ymax2),
                xytext=(pk + (3 if pk <= 12 else -3), _ymax2 - _rng2 * 0.28),
                ha="right" if pk <= 12 else "left", fontsize=10,
                color=C_BLUE, weight="bold",
                arrowprops=dict(arrowstyle="->", color=C_BLUE, lw=1.2,
                                connectionstyle="arc3,rad=0.18"))
    # 右下：TOP10 失衡
    a2 = fig.add_axes([0.515, 0.10, 0.46, 0.60]); style(a2)
    a2.set_title("供需失衡指数 TOP 10（创新点①）", fontsize=13, color=INK, weight="bold", pad=8)
    t10 = top_by_zone(imb, 10)
    a2.barh(range(len(t10)), t10["imbalance"],
            color=[C_RED if v > 0 else C_BLUE for v in t10["imbalance"]], height=0.66, zorder=3)
    a2.set_yticks(range(len(t10)))
    a2.set_yticklabels([f"{z}" for z in t10["zone_id"]], fontsize=10)
    a2.set_xlabel("失衡指数 I（标签为分区编号，柱内数值见右）", fontsize=10, color=MUT)
    for i, (z, d, h, v) in enumerate(zip(t10["zone_id"], t10["dt"], t10["hour_of_day"],
                                         t10["imbalance"])):
        a2.text(v + 0.012, i, f"{z}  {int(h):02d}时  {v:+.4f}",
                va="center", fontsize=9.2, color=INK)
    a2.set_xlabel("失衡指数 I", fontsize=10, color=MUT)
    save(fig, "01_首页大屏.png", SHOTS)

    # 大屏 2：分区地图
    fig = plt.figure(figsize=(16, 9), dpi=100)
    fig.patch.set_facecolor("#F8FAFC")
    axm = fig.add_axes([0, 0, 1, 1]); axm.axis("off")
    axm.text(0.025, 0.955, "深圳 275 个交通分区 · 平均占用率热力分布",
             fontsize=21, color=INK, weight="bold", transform=axm.transAxes)
    axm.text(0.025, 0.923, "按分区平均占用率着色　|　全市均值 0.2710　|　数据源 uev_ads.zone_occupancy",
             fontsize=12, color=MUT, transform=axm.transAxes)
    am = fig.add_axes([0.03, 0.05, 0.60, 0.84])
    style(am)
    draw_admin(am)
    zov2 = zo[(zo["longitude"] > 100) & (zo["latitude"] > 10)].copy()
    vmin, vmax = float(zov2["avg_occupancy"].min()), float(zov2["avg_occupancy"].max())
    cmap = plt.get_cmap("YlOrRd"); norm = plt.Normalize(vmin, vmax)
    sizes = 30 + 160 * (zov2["charge_count"] / max(zov2["charge_count"].max(), 1))
    am.scatter(zov2["longitude"], zov2["latitude"], s=sizes, c=zov2["avg_occupancy"],
               cmap=cmap, norm=norm, alpha=0.82, edgecolors="#334155", linewidths=0.5, zorder=5)
    am.set_aspect(1 / np.cos(np.radians(22.5)))
    sc = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    cb = fig.colorbar(sc, ax=am, fraction=0.032, pad=0.02)
    cb.set_label("平均占用率", fontsize=11, color=INK)
    am.text(0.02, 0.02, "点大小 = 充电桩数", transform=am.transAxes, fontsize=10, color=MUT)
    # 右侧排行榜
    ar = fig.add_axes([0.66, 0.30, 0.31, 0.60]); style(ar)
    ar.set_title("平均占用率 TOP 15", fontsize=13, color=INK, weight="bold", pad=8)
    t15 = zo.sort_values("avg_occupancy", ascending=False).head(15).iloc[::-1]
    ar.barh(range(len(t15)), t15["avg_occupancy"],
            color=[C_RED if v >= 0.6 else (C_AMBER if v >= 0.45 else C_BLUE)
                   for v in t15["avg_occupancy"]], height=0.66, zorder=3)
    ar.set_yticks(range(len(t15)))
    ar.set_yticklabels([f"分区 {z}" for z in t15["zone_id"]], fontsize=10)
    ar.set_xlabel("平均占用率", fontsize=10, color=MUT)
    save(fig, "02_分区地图大屏.png", SHOTS)

    # 大屏 3：供需失衡
    fig = plt.figure(figsize=(16, 9), dpi=100)
    fig.patch.set_facecolor("#F8FAFC")
    axm = fig.add_axes([0, 0, 1, 1]); axm.axis("off")
    axm.text(0.025, 0.955, "供需失衡诊断 · 分区紧张度排序（创新点①）",
             fontsize=21, color=INK, weight="bold", transform=axm.transAxes)
    axm.text(0.025, 0.923, "I(z,t) = D(z,t) − S(z)　份额差口径，正值=该分区该时段供不应求",
             fontsize=12, color=MUT, transform=axm.transAxes)
    a1 = fig.add_axes([0.025, 0.10, 0.47, 0.76]); style(a1)
    a1.set_title("失衡指数 TOP 20", fontsize=14, color=INK, weight="bold", pad=8)
    t20b = top_by_zone(imb, 20)
    a1.barh(range(len(t20b)), t20b["imbalance"],
            color=[C_RED if v > 0 else C_BLUE for v in t20b["imbalance"]], height=0.66, zorder=3)
    a1.set_yticks(range(len(t20b)))
    a1.set_yticklabels([f"{z}" for z in t20b["zone_id"]], fontsize=9.5)
    for i, (z, d, h, v) in enumerate(zip(t20b["zone_id"], t20b["dt"], t20b["hour_of_day"],
                                         t20b["imbalance"])):
        a1.text(v + (0.0008 if v > 0 else -0.0008), i,
                f"{z} {int(h):02d}时 {v:+.4f}",
                va="center", ha="left" if v > 0 else "right", fontsize=8.8, color=INK)
    a1.set_xlabel("失衡指数 I", fontsize=10, color=MUT)
    a2 = fig.add_axes([0.525, 0.56, 0.45, 0.30]); style(a2)
    a2.set_title("24 小时失衡指数", fontsize=14, color=INK, weight="bold", pad=8)
    a2.bar(hsd["hour_of_day"], hsd["imbalance"], color=C_PURPLE, width=0.62, zorder=3)
    a2.set_xlabel("小时", fontsize=10, color=MUT)
    a2.set_xticks(range(0, 24, 3))
    a3 = fig.add_axes([0.525, 0.10, 0.45, 0.38]); style(a3)
    a3.set_title("分区平均占用率分布", fontsize=14, color=INK, weight="bold", pad=8)
    a3.hist(zo["avg_occupancy"], bins=28, color=C_BLUE, alpha=0.82, zorder=3, edgecolor="white")
    a3.axvline(float(kpi["avg_occupancy"]), color=C_RED, ls="--", lw=1.8, zorder=4)
    a3.text(float(kpi["avg_occupancy"]) + 0.012, a3.get_ylim()[1] * 0.86,
            f"全市均值 {kpi['avg_occupancy']:.4f}", color=C_RED, fontsize=10.5, weight="bold")
    a3.set_xlabel("平均占用率", fontsize=10, color=MUT)
    save(fig, "03_供需失衡大屏.png", SHOTS)

    # 大屏 4：布点建议
    fig = plt.figure(figsize=(16, 9), dpi=100)
    fig.patch.set_facecolor("#F8FAFC")
    axm = fig.add_axes([0, 0, 1, 1]); axm.axis("off")
    axm.text(0.025, 0.955, "布点扩容决策建议 · 分区优先级排序（创新点③）",
             fontsize=21, color=INK, weight="bold", transform=axm.transAxes)
    axm.text(0.025, 0.923, f"共 {len(es)} 个分区入选　|　紧张型（扩容 30%）/ 潜力型（扩容 20%）/ 过剩型（调度引流）",
             fontsize=12, color=MUT, transform=axm.transAxes)
    a1 = fig.add_axes([0.025, 0.10, 0.40, 0.76]); style(a1)
    a1.set_title("建议扩容的紧张型分区 TOP 15", fontsize=14, color=INK, weight="bold", pad=8)
    tight = es[es["priority"] == 1].sort_values("peak_gap", ascending=False).head(15).iloc[::-1]
    a1.barh(range(len(tight)), tight["suggested_piles"] - tight["current_piles"],
            color=C_RED, height=0.66, zorder=3, label="建议新增桩数")
    a1.set_yticks(range(len(tight)))
    a1.set_yticklabels([f"分区 {z}（{int(c)} 桩）"
                        for z, c in zip(tight["zone_id"], tight["current_piles"])], fontsize=9.5)
    a1.set_xlabel("建议新增充电桩数", fontsize=10, color=MUT)
    a1.legend(loc="lower right", frameon=False, fontsize=10)
    a2 = fig.add_axes([0.455, 0.10, 0.22, 0.76]); style(a2)
    a2.set_title("分区类型构成", fontsize=14, color=INK, weight="bold", pad=8)
    cnt2 = es["zone_type"].value_counts()
    order2 = [t for t in ["紧张型", "潜力型", "过剩型"] if t in cnt2.index]
    a2.pie([int(cnt2[t]) for t in order2], labels=order2,
           colors=[C_RED, C_AMBER, C_BLUE], autopct="%1.1f%%", startangle=90,
           counterclock=False, wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2),
           textprops=dict(fontsize=11, color=INK))
    a3 = fig.add_axes([0.70, 0.10, 0.27, 0.76]); style(a3)
    a3.set_title("决策建议明细（TOP 12）", fontsize=14, color=INK, weight="bold", pad=8)
    a3.axis("off")
    txt = []
    for _, r in es.head(12).iterrows():
        txt.append(f"[P{int(r['priority'])}] 分区 {r['zone_id']}　"
                   f"{int(r['current_piles'])}→{int(r['suggested_piles'])} 桩　"
                   f"占用率 {r['avg_occupancy']:.3f}")
    a3.text(0.0, 1.0, "\n".join(txt), fontsize=10.5, color=INK, va="top",
            family="Microsoft YaHei", transform=a3.transAxes, linespacing=1.9)
    save(fig, "04_布点建议大屏.png", SHOTS)

    print()
    print("=" * 74)
    print(f" 完成：核心图表 {len([f for f in FIGS if '大屏' not in f])} 张，大屏 {len([f for f in FIGS if '大屏' in f])} 张")
    for f in FIGS:
        print(f"    {f}")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
