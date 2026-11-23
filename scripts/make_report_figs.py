# -*- coding: utf-8 -*-
"""
make_report_figs.py —— 补画报告需要的 3 张结构图

图 4-2 系统 E-R 图
图 5-1 Flume 12 通道采集拓扑图
图 5-5 后端 16 个接口的调用关系与缓存分层图

用法：python scripts/make_report_figs.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "docs" / "charts"

for f in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/simhei.ttf"]:
    if Path(f).exists():
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DengXian", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

INK, MUT = "#1F2328", "#6B7280"
BLUE, TEAL, AMBER, RED, PURPLE, GREY, GREEN = "#1D4ED8", "#0E7C6B", "#D97706", "#C0392B", "#5B3FA8", "#9CA3AF", "#2E7D32"
DPI = 200


def box(ax, x, y, w, h, text, fc, ec, tc="#FFFFFF", fs=9.5, weight="bold", lw=1.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.006,rounding_size=0.010",
                                fc=fc, ec=ec, lw=lw, zorder=3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=tc, fontweight=weight, zorder=4, linespacing=1.4)


def arrow(ax, p1, p2, color="#94A3B8", rad=0.0, ls="-", lw=1.1, style="arc3,rad=0"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=10,
                                 color=color, lw=lw, linestyle=ls, zorder=2,
                                 connectionstyle=style))


# ══════════════════════════════════════════════════════════════════
def make_er():
    """图 4-2 系统 E-R 图：三类实体 + 关系"""
    fig, ax = plt.subplots(figsize=(15, 9.5))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.5, 0.975, "图 4-2　系统 E-R 图", ha="center", fontsize=17,
            color=INK, fontweight="bold", transform=ax.transAxes)
    ax.text(0.5, 0.944, "三类实体（分区维表 / 指标事实表 / 系统实体）与主要关系",
            ha="center", fontsize=11, color=MUT, transform=ax.transAxes)

    # ---- 实体一：分区维表 ----
    box(ax, 0.045, 0.62, 0.215, 0.235, "", "#FFFFFF", BLUE, "#FFFFFF", lw=1.6)
    ax.text(0.152, 0.828, "分区维表", fontsize=12.5, color=BLUE, fontweight="bold", ha="center")
    fields = [("zone_id", "PK"), ("longitude", ""), ("latitude", ""),
              ("charge_count", ""), ("area / perimeter", ""), ("poi_total", ""),
              ("price_sigma", ""), ("is_tou_zone", "")]
    for i, (f, k) in enumerate(fields):
        y = 0.788 - i * 0.0225
        ax.text(0.062, y, f, fontsize=8.8, color=INK, family="Consolas", va="center")
        if k:
            ax.text(0.245, y, k, fontsize=8.2, color=RED, weight="bold", va="center", ha="right")

    # ---- 实体二：DWS 指标事实表（字段收敛，避免溢出）----
    box(ax, 0.395, 0.545, 0.225, 0.28, "", "#FFFFFF", TEAL, "#FFFFFF", lw=1.6)
    ax.text(0.5075, 0.800, "DWS 指标事实表", fontsize=12.5, color=TEAL,
            fontweight="bold", ha="center")
    facts = [
        ("zone_day_hour", "PK/FK"), ("  zone_id / dt / hour_of_day", "PK"),
        ("  occupancy / duration_h", ""), ("  volume_kwh", ""),
        ("  e_price / s_price", ""),
        ("zone_day", "PK/FK"), ("  day_avg_occupancy", ""),
        ("  peak_trough_gap", ""), ("  stddev_occupancy", ""),
        ("zone_hour_profile", "PK/FK"), ("  rolling7_mean", ""),
        ("hourly_supply_demand", "PK"), ("  demand / supply / gap", ""),
    ]
    for i, (f, k) in enumerate(facts):
        y = 0.762 - i * 0.0182
        ax.text(0.408, y, f, fontsize=7.9, color=INK, family="Consolas", va="center")
        if k:
            ax.text(0.610, y, k, fontsize=7.4, color=RED, weight="bold", va="center", ha="right")

    # ---- 实体三：系统实体 ----
    box(ax, 0.735, 0.62, 0.215, 0.235, "", "#FFFFFF", PURPLE, "#FFFFFF", lw=1.6)
    ax.text(0.8425, 0.828, "系统实体", fontsize=12.5, color=PURPLE, fontweight="bold", ha="center")
    sysf = [("sys_user", "PK"), ("  username", ""), ("  password_hash", ""),
            ("  role", ""), ("sys_role", "PK"), ("  role_name", ""),
            ("sys_query_log", "PK"), ("  query_text", ""), ("  elapsed_ms", "")]
    for i, (f, k) in enumerate(sysf):
        y = 0.788 - i * 0.0225
        ax.text(0.752, y, f, fontsize=8.8, color=INK, family="Consolas", va="center")
        if k:
            ax.text(0.935, y, k, fontsize=8.2, color=RED, weight="bold", va="center", ha="right")

    # ---- 关系 ----
    # 1:N  分区维表 → 指标事实表
    arrow(ax, (0.260, 0.720), (0.395, 0.700), color=BLUE, lw=1.5)
    ax.text(0.3275, 0.790, "1 : N", fontsize=11.5, color=BLUE, weight="bold", ha="center")
    ax.text(0.3275, 0.752, "一个分区对应\n多条时段记录", fontsize=8.4,
            color=MUT, ha="center", linespacing=1.4)

    # 1:1  指标事实表 → ADS 应用表
    box(ax, 0.400, 0.330, 0.215, 0.165, "", "#FFFFFF", AMBER, "#FFFFFF", lw=1.5)
    ax.text(0.5075, 0.468, "ADS 应用表（7 张）", fontsize=11, color=AMBER,
            fontweight="bold", ha="center")
    for i, t in enumerate(["dashboard_kpi", "zone_occupancy", "hourly_supply_demand",
                           "imbalance_index", "price_elasticity", "demand_forecast",
                           "expansion_suggestion"]):
        ax.text(0.412, 0.444 - i * 0.0158, t, fontsize=7.6, color=INK,
                family="Consolas", va="center")
    arrow(ax, (0.5075, 0.545), (0.5075, 0.495), color=AMBER, lw=1.6)
    ax.text(0.522, 0.518, "1 : 1　一表 = 一图表", fontsize=9.4, color=AMBER, weight="bold")

    # 视图层
    box(ax, 0.700, 0.320, 0.265, 0.150, "", "#FEF3C7", AMBER, "#92400E", lw=1.4)
    ax.text(0.8325, 0.442, "视图层 v_*（4 张）", fontsize=10.5, color="#92400E",
            fontweight="bold", ha="center")
    for i, t in enumerate(["v_zone_daily", "v_zone_imbalance",
                           "v_forecast", "v_advice"]):
        ax.text(0.712, 0.414 - i * 0.0215, t, fontsize=8.4, color=INK,
                family="Consolas", va="center")
    ax.text(0.712, 0.334, "ADS(7) + INSIGHT(5) 联查", fontsize=8.4, color=MUT, va="center")

    # 1:N  系统实体 ← 指标事实表（被查询）
    arrow(ax, (0.620, 0.790), (0.735, 0.790), color=PURPLE, lw=1.4)
    ax.text(0.6775, 0.812, "1 : N", fontsize=11, color=PURPLE, weight="bold", ha="center")
    ax.text(0.6775, 0.762, "用户查询\n记录日志", fontsize=8.4, color=MUT, ha="center",
            linespacing=1.4)

    # ADS → 视图
    arrow(ax, (0.615, 0.395), (0.700, 0.395), color=AMBER, lw=1.4)

    # 图例
    ax.text(0.045, 0.075, "PK 主键　FK 外键　PK/FK 复合主键且含外键", fontsize=10, color=MUT)
    ax.text(0.045, 0.045,
            "★ 三类实体：分区维表（维度基准）· 指标事实表（度量主体）· 系统实体（权限与日志）",
            fontsize=10.4, color=RED, weight="bold")
    out = OUT / "07_系统ER图.png"
    fig.savefig(out, dpi=DPI, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {out.name}")


# ══════════════════════════════════════════════════════════════════
def make_flume():
    """图 5-1 Flume 12 通道采集拓扑图"""
    fig, ax = plt.subplots(figsize=(15, 8.5))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.5, 0.972, "图 5-1　Flume 12 通道增量采集拓扑图", ha="center", fontsize=17,
            color=INK, fontweight="bold", transform=ax.transAxes)
    ax.text(0.5, 0.940,
            "每类 CSV 一个独立 source / channel / sink —— 12 个通道各落一个 HDFS 子目录，与 12 张 ODS 表一一对应",
            ha="center", fontsize=11, color=MUT, transform=ax.transAxes)

    # 源
    box(ax, 0.035, 0.40, 0.145, 0.235, "", "#FFFFFF", TEAL, "#FFFFFF", lw=1.5)
    ax.text(0.1075, 0.608, "本地数据目录", fontsize=11.5, color=TEAL, fontweight="bold", ha="center")
    ax.text(0.1075, 0.578, "data/UrbanEV/", fontsize=9.4, color=MUT, ha="center",
            family="Consolas")
    srcs = [("occupancy.csv", "276 列宽表"), ("duration.csv", "276 列宽表"),
            ("volume.csv", "276 列宽表"), ("volume-11kW.csv", "276 列宽表"),
            ("e_price.csv", "276 列宽表"), ("s_price.csv", "276 列宽表"),
            ("inf.csv", "6 列维表"), ("poi.csv", "4 列 · 712,135 行"),
            ("adj.csv", "275×275 矩阵"), ("distance.csv", "275×275 矩阵"),
            ("weather_airport.csv", "7 列气象"), ("weather_central.csv", "7 列气象")]
    for i, (n, d) in enumerate(srcs):
        y = 0.548 - i * 0.0272
        ax.text(0.048, y, n, fontsize=8.2, color=INK, family="Consolas", va="center")
        ax.text(0.172, y, d, fontsize=7.4, color=MUT, va="center", ha="right")

    # Flume agent
    box(ax, 0.255, 0.335, 0.155, 0.335, "", "#F5F9FF", BLUE, "#FFFFFF", lw=1.8)
    ax.text(0.3325, 0.638, "Flume Agent", fontsize=12.5, color=BLUE,
            fontweight="bold", ha="center")
    ax.text(0.3325, 0.610, "uev-agent", fontsize=9, color=MUT, ha="center", family="Consolas")
    for i, (t, c) in enumerate([("12 × TAILDIR Source", TEAL),
                                ("12 × Memory Channel", AMBER),
                                ("12 × HDFS Sink", PURPLE)]):
        y = 0.545 - i * 0.078
        box(ax, 0.272, y, 0.121, 0.058, t, "#FFFFFF", c, c, 8.4, "normal")
    ax.text(0.3325, 0.362, "断点续传 positionFile\nfileHeader · gzip · 300s 滚动",
            fontsize=7.8, color=MUT, ha="center", va="center", linespacing=1.5)

    # HDFS
    box(ax, 0.485, 0.30, 0.175, 0.405, "", "#FFFFFF", PURPLE, "#FFFFFF", lw=1.6)
    ax.text(0.5725, 0.672, "HDFS", fontsize=12.5, color=PURPLE, fontweight="bold", ha="center")
    ax.text(0.5725, 0.645, "/uev/raw/", fontsize=9.4, color=MUT, ha="center", family="Consolas")
    dirs = ["occupancy/", "duration/", "volume/", "volume-11kW/", "e_price/", "s_price/",
            "inf/", "poi/", "adj/", "distance/", "weather_airport/", "weather_central/"]
    for i, d in enumerate(dirs):
        col = 0 if i < 6 else 1
        row = i % 6
        x = 0.497 + col * 0.084
        y = 0.600 - row * 0.030
        ax.text(x, y, d, fontsize=7.6, color=INK, family="Consolas", va="center")
    ax.text(0.5725, 0.325, "12 个独立子目录", fontsize=8.8, color=PURPLE, weight="bold", ha="center")

    # ODS
    box(ax, 0.735, 0.395, 0.145, 0.21, "", "#FFFFFF", GREEN, "#FFFFFF", lw=1.6)
    ax.text(0.8075, 0.578, "Hive ODS", fontsize=12, color=GREEN, fontweight="bold", ha="center")
    ax.text(0.8075, 0.552, "uev_ods.*", fontsize=9, color=MUT, ha="center", family="Consolas")
    ax.text(0.8075, 0.516, "12 张 EXTERNAL 表", fontsize=9.2, color=INK, ha="center")
    ax.text(0.8075, 0.488, "LOCATION 逐一对应", fontsize=9.2, color=INK, ha="center")
    ax.text(0.8075, 0.460, "skip.header.lines.count=1", fontsize=8, color=MUT, ha="center",
            family="Consolas")
    ax.text(0.8075, 0.428, "ROW FORMAT DELIMITED", fontsize=8, color=MUT, ha="center",
            family="Consolas")

    # 连线
    arrow(ax, (0.180, 0.517), (0.255, 0.517), color=TEAL, lw=1.8)
    ax.text(0.217, 0.538, "taildir\n增量监控", fontsize=8.2, color=TEAL, ha="center",
            linespacing=1.4)
    arrow(ax, (0.410, 0.517), (0.485, 0.517), color=BLUE, lw=1.8)
    ax.text(0.447, 0.538, "memory\nchannel", fontsize=8.2, color=BLUE, ha="center",
            linespacing=1.4)
    arrow(ax, (0.660, 0.517), (0.735, 0.517), color=PURPLE, lw=1.8)
    ax.text(0.697, 0.538, "HDFS Sink\n滚动写入", fontsize=8.2, color=PURPLE, ha="center",
            linespacing=1.4)

    # 底部要点
    ax.text(0.035, 0.115,
            "★ 为什么是 12 个独立通道而不是 1 个通道 12 个文件",
            fontsize=11.5, color=RED, fontweight="bold", transform=ax.transAxes)
    ax.text(0.035, 0.055,
            "12 个 CSV 的表结构完全不同（6 个 276 列宽表 + 2 个 275×275 矩阵 + 2 个气象表 + 维表 + POI）。\n"
            "混在同一目录将无法按表建 Hive 表、也无法按表做增量；独立通道使「采集目录 → ODS 表」一一对应、可校验、可追溯。",
            fontsize=9.8, color=INK, transform=ax.transAxes, linespacing=1.7)
    out = OUT / "08_Flume采集拓扑图.png"
    fig.savefig(out, dpi=DPI, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {out.name}")


# ══════════════════════════════════════════════════════════════════
def make_api():
    """图 5-5 后端 16 个接口调用关系与缓存分层图"""
    fig, ax = plt.subplots(figsize=(15, 8.5))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.5, 0.972, "图 5-5　后端 16 个接口的调用关系与缓存分层", ha="center", fontsize=17,
            color=INK, fontweight="bold", transform=ax.transAxes)
    ax.text(0.5, 0.940,
            "前端 6 个页面 → Controller → Service → MyBatis Mapper → MySQL 视图层　｜　Redis 缓存热点聚合结果",
            ha="center", fontsize=11, color=MUT, transform=ax.transAxes)

    # 前端页面
    box(ax, 0.030, 0.44, 0.115, 0.235, "", "#FFFFFF", GREY, "#FFFFFF", lw=1.4)
    ax.text(0.0875, 0.648, "前端页面（6 个）", fontsize=10.8, color="#374151",
            fontweight="bold", ha="center")
    for i, p in enumerate(["首页运营大屏", "分区详情页", "供需失衡诊断",
                           "电价弹性分析", "需求预测页", "布点建议看板"]):
        ax.text(0.040, 0.612 - i * 0.030, p, fontsize=8.6, color=INK, va="center")

    # Controller
    box(ax, 0.195, 0.40, 0.145, 0.315, "", "#F5F9FF", BLUE, "#FFFFFF", lw=1.7)
    ax.text(0.2675, 0.688, "Controller 层", fontsize=11.5, color=BLUE,
            fontweight="bold", ha="center")
    ax.text(0.2675, 0.662, "16 个 REST 接口", fontsize=9, color=MUT, ha="center")
    for i, t in enumerate(["/api/health", "/api/dashboard/kpi", "/api/zones/occupancy",
                           "/api/zones/{id}/detail", "/api/charts/hourly", "/api/charts/imbalance",
                           "/api/charts/price-elasticity", "/api/charts/forecast",
                           "/api/charts/forecast-evaluate", "/api/charts/suggestions",
                           "/api/charts/volume-deviation", "/api/charts/poi-correlation",
                           "/api/charts/clusters", "/api/weather/list", "/api/dictionary",
                           "POST /api/advice/export"]):
        col = 0 if i < 8 else 1
        row = i % 8
        ax.text(0.203 + col * 0.070, 0.632 - row * 0.0295, t, fontsize=6.9,
                color=INK, family="Consolas", va="center")

    # Service
    box(ax, 0.395, 0.44, 0.135, 0.235, "", "#FFFFFF", TEAL, "#FFFFFF", lw=1.7)
    ax.text(0.4625, 0.648, "Service 层", fontsize=11.5, color=TEAL,
            fontweight="bold", ha="center")
    for i, t in enumerate(["参数校验与分页", "指标计算编排", "缓存读写策略",
                           "异常降级处理", "导出文件生成"]):
        ax.text(0.405, 0.612 - i * 0.032, "· " + t, fontsize=8.4, color=INK, va="center")

    # Mapper
    box(ax, 0.580, 0.44, 0.135, 0.235, "", "#FFFFFF", PURPLE, "#FFFFFF", lw=1.7)
    ax.text(0.6475, 0.648, "Mapper 层", fontsize=11.5, color=PURPLE,
            fontweight="bold", ha="center")
    for i, t in enumerate(["MyBatis 参数化查询", "防 SQL 注入", "@Transactional 批量写",
                           "分页插件", "视图联查"]):
        ax.text(0.590, 0.612 - i * 0.032, "· " + t, fontsize=8.4, color=INK, va="center")

    # MySQL
    box(ax, 0.765, 0.365, 0.205, 0.385, "", "#FFFFFF", GREEN, "#FFFFFF", lw=1.8)
    ax.text(0.8675, 0.722, "MySQL 8.0　uev_charge", fontsize=12, color=GREEN,
            fontweight="bold", ha="center")
    for i, (t, c) in enumerate([("ads_*　7 张　（B 岗 Sqoop 导出）", GREEN),
                                 ("insight_*　5 张　（E 岗 pymysql 直插）", TEAL),
                                 ("sys_*　3 张　（用户/角色/日志）", PURPLE)]):
        y = 0.672 - i * 0.042
        box(ax, 0.782, y - 0.019, 0.171, 0.034, t, "#FFFFFF", c, c, 8.0, "normal")
    box(ax, 0.782, 0.520, 0.171, 0.034, "v_*　4 张视图（联查层）", "#FEF3C7", AMBER, "#92400E", 8.0, "normal")
    ax.text(0.8675, 0.470, "★ 两条计算路径在此汇合", fontsize=9, color=RED,
            weight="bold", ha="center")
    ax.text(0.8675, 0.440, "ads 与 insight 由视图层联结", fontsize=8.4, color=MUT, ha="center")
    ax.text(0.8675, 0.400, "D 的接口只读视图，", fontsize=8.4, color=MUT, ha="center")
    ax.text(0.8675, 0.382, "ADS 改字段不用改接口", fontsize=8.4, color=MUT, ha="center")

    # Redis
    box(ax, 0.395, 0.245, 0.32, 0.135, "", "#FFF7F7", RED, "#FFFFFF", lw=1.7)
    ax.text(0.555, 0.352, "Redis 7 缓存层", fontsize=11.5, color=RED,
            fontweight="bold", ha="center")
    ax.text(0.555, 0.318, "缓存首页聚合 KPI 与热点图表结果　|　TTL 设定，数据更新即失效",
            fontsize=8.8, color=INK, ha="center")
    ax.text(0.555, 0.282, "缓存命中 → 直接返回　　未命中 → 查库并回填（记录命中率）",
            fontsize=8.8, color=MUT, ha="center")

    # 降级
    box(ax, 0.765, 0.245, 0.205, 0.100, "", "#FFFFFF", AMBER, "#FFFFFF", lw=1.6)
    ax.text(0.8675, 0.318, "异常降级", fontsize=10.5, color=AMBER, fontweight="bold", ha="center")
    ax.text(0.8675, 0.278, "参数非法返回友好提示\n不抛 500（实测 status=DEGRADED）",
            fontsize=8.2, color=INK, ha="center", linespacing=1.5)

    # 连线
    arrow(ax, (0.145, 0.557), (0.195, 0.557), color=GREY, lw=1.7)
    ax.text(0.170, 0.578, "HTTP", fontsize=8, color=MUT, ha="center")
    arrow(ax, (0.340, 0.557), (0.395, 0.557), color=BLUE, lw=1.7)
    arrow(ax, (0.530, 0.557), (0.580, 0.557), color=TEAL, lw=1.7)
    arrow(ax, (0.715, 0.557), (0.765, 0.557), color=PURPLE, lw=1.7)
    # Service ↔ Redis
    arrow(ax, (0.4625, 0.440), (0.4625, 0.380), color=RED, lw=1.5, ls="--")
    ax.text(0.474, 0.410, "缓存读写", fontsize=8.4, color=RED, va="center")
    # Service ↔ 降级
    arrow(ax, (0.530, 0.470), (0.765, 0.300), color=AMBER, lw=1.4, ls="--",
          style="arc3,rad=-0.22")

    # 图例
    ax.text(0.030, 0.115, "分层依据：Controller 只做参数校验与路由，Service 负责编排与缓存策略，"
                          "Mapper 只做数据访问", fontsize=9.8, color=INK, transform=ax.transAxes)
    ax.text(0.030, 0.070,
            "★ 三条工程化硬指标：参数化查询防 SQL 注入　|　@Transactional 保证批量写原子性　|　"
            "连接池 + 重试 + 异常降级兜底", fontsize=10.2, color=RED, weight="bold",
            transform=ax.transAxes)
    out = OUT / "09_接口调用关系与缓存分层图.png"
    fig.savefig(out, dpi=DPI, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {out.name}")


if __name__ == "__main__":
    print("补画报告结构图")
    make_er()
    make_flume()
    make_api()
    print("完成")
