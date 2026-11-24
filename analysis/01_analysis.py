# -*- coding: utf-8 -*-
"""
01_analysis.py —— E 组（分析与模型层）主分析脚本，覆盖 E01~E10
=================================================================
口径唯一依据：仓库 docs/contracts/02-指标定义表.md v1.1（姬婷婷维护）
             + docs/contracts/01-数据字典.md v1.0

数据源：02_数据/真实CSV(待B组ADS导出)/ 下 UrbanEV 原始宽表（time + 275 分区列）
        若为空则回退 02_数据/样例数据/ 合成数据

关键口径（与合同一致，勿改）：
  创新点① 失衡指数 I(z,t) = 需求份额 − 运力份额
          demand_share = volume(z,t)/Σvolume(·,t)；supply_share = charge_count(z)/Σcharge_count
  创新点② 电价弹性 σ_price(z)=STDDEV_POP(e_price)；σ>0.05 → TOU，否则 FLAT
          ELASTICITY = 高峰(17-19时)平均占用率 − 低谷(0-6时)平均占用率，越小越平
  创新点③ 需求预测 基础值=同星期同小时历史均值；γ=近7天均值/全期均值；predict=基础值×γ
          前 174 天训练（≤2023-02-21），最后 7 天验证（02-22~02-28），报 MAPE
  布点建议  新增桩数 = CEIL(峰值失衡 × 现有桩数 × 0.3)，按峰值失衡降序给优先级
  创新点④ 聚类 7 维特征、k=4、固定种子 42、肘部法 k=2~6、与失衡指数互证

输出：
  02_数据/分析结果/ads_*.csv        ← 对应 uev_ads 落地表（给 D 组取数）
  02_数据/分析结果/分析结论摘要.json ← 16 处【待 E 填】的计算结果
  03_图表/*.png                    ← ≥2200px 宽
  02_数据/模型产物/forecast_model.pkl + 数据指纹.json
"""
import os
import json
import math
import hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import joblib

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, ".."))

# 数据目录探测：与 scripts/find_data.sh 同口径，避免写死个人绝对路径
_CANDS = [
    os.environ.get("UEV_DATA_DIR"),
    os.path.join(ROOT, "data", "raw"),
    os.path.join(ROOT, "..", "数据", "UrbanEV"),
    os.path.join(ROOT, "..", "..", "数据", "UrbanEV"),
    os.path.join(ROOT, "02_数据", "真实CSV(待B组ADS导出)"),
]
_FOUND = next((p for p in _CANDS if p and os.path.isfile(os.path.join(p, "occupancy.csv"))), None)
REAL_DIR = _FOUND or os.path.join(ROOT, "data", "raw")
SAMPLE_DIR = os.path.join(ROOT, "02_数据", "样例数据")

OUT_DIR = os.path.join(BASE, "output")          # 产物一律落在 analysis/output，不进 Git
FIG_DIR = os.path.join(OUT_DIR, "figs")
RES_DIR = os.path.join(OUT_DIR, "ads")
EDA_DIR = os.path.join(OUT_DIR, "eda")
MODEL_DIR = os.path.join(OUT_DIR, "model")
for d in (FIG_DIR, RES_DIR, EDA_DIR, MODEL_DIR):
    os.makedirs(d, exist_ok=True)

FIG_DPI = 260                     # 9in × 260 ≈ 2340px，满足 ≥2200px
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

DATA_DIR = REAL_DIR if os.path.exists(os.path.join(REAL_DIR, "occupancy.csv")) else SAMPLE_DIR
IS_REAL = DATA_DIR == REAL_DIR
DATA_TAG = "真实 UrbanEV 数据" if IS_REAL else "样例合成数据（占位）"
print(f"[数据] {DATA_DIR}\n[来源] {DATA_TAG}")

TH_TOU = 0.05
PEAK_H = [17, 18, 19]
VALLEY_H = [0, 1, 2, 3, 4, 5, 6]
SEED = 42
TRAIN_END = "2023-02-21"
VALID_START = "2023-02-22"
GAMMA_START = "2023-02-15"
EXP_COEF = 0.3


def wide(name):
    """读宽表：time + 275 个分区列（列名即 zone_id 字符串）"""
    df = pd.read_csv(os.path.join(DATA_DIR, name))
    tcol = "time" if "time" in df.columns else df.columns[0]
    df[tcol] = pd.to_datetime(df[tcol])
    df = df.set_index(tcol)
    df.columns = [str(c) for c in df.columns]
    return df.sort_index()


occupancy = wide("occupancy.csv")
duration = wide("duration.csv")
volume = wide("volume.csv")
volume11 = wide("volume-11kW.csv")
e_price = wide("e_price.csv")
s_price = wide("s_price.csv")

inf = pd.read_csv(os.path.join(DATA_DIR, "inf.csv"), dtype={"TAZID": str}).set_index("TAZID")
zones = list(volume.columns)
inf = inf.reindex(zones)
charge_count = inf["charge_count"].astype(float)
area_m2 = inf["area"].astype(float)

city_demand_h = volume.groupby(volume.index.hour).mean()
city_occ_h = occupancy.groupby(occupancy.index.hour).mean()

# ==================================================================
# M1-M12 基础指标计算结果（E03 的 12 处回填）
# ==================================================================
di = duration.div(charge_count, axis=1)
baseline_h = duration.sum(axis=1) / charge_count.sum()
avg_occ = occupancy.mean()
max_occ = occupancy.max()
total_vol = volume.sum()
avg_dur = duration.mean()
pvg = occupancy.max(axis=0) - occupancy.min(axis=0)
occ_std = occupancy.std(ddof=0)
pile_density = charge_count / area_m2 * 1e6
vol_dev = ((volume - volume11) / volume.replace(0, np.nan)).mean()
price_gap = e_price.max() - e_price.min()
price_std = e_price.std(ddof=0)

poi_path = os.path.join(DATA_DIR, "poi.csv")
if os.path.exists(poi_path):
    poi = pd.read_csv(poi_path)
    lon = inf["longitude"].astype(float).values
    lat = inf["latitude"].astype(float).values
    xy_zone = np.c_[lon * 102.6, lat * 110.9]      # 近似等距投影
    tree = cKDTree(xy_zone)
    _, idx = tree.query(np.c_[poi["longitude"].values * 102.6,
                              poi["latitude"].values * 110.9], workers=-1)
    poi_total = pd.Series(np.bincount(idx, minlength=len(zones)), index=zones).astype(float)
    poi_types = poi["primary_types"].value_counts().to_dict() if "primary_types" in poi.columns else {}
else:
    poi_total = pd.Series(np.nan, index=zones)
    poi_types = {}
poi_density = poi_total / area_m2 * 1e6

m1_m12 = {
    "M1 分区小时充电需求强度": {
        "公式": "DI(z,t)=duration_h(z,t)/charge_count(z)",
        "全市均值(小时/桩·时)": round(float(di.stack().mean()), 4),
        "峰值(小时/桩·时)": round(float(di.max().max()), 4),
        "均值最高5个分区": [(z, round(float(di[z].mean()), 4)) for z in di.mean().nlargest(5).index],
    },
    "M2 全市同期需求强度基准": {
        "公式": "D̄(t)=Σduration/Σcharge_count",
        "24小时基准曲线": {int(h): round(float(v), 4) for h, v in
                          baseline_h.groupby(baseline_h.index.hour).mean().items()},
        "基准最高时段": int(baseline_h.groupby(baseline_h.index.hour).mean().idxmax()),
    },
    "M3 分区平均占用率": {
        "公式": "AVG(occupancy(z,·))",
        "全市均值": round(float(avg_occ.mean()), 4),
        "最高5个分区": [(z, round(float(v), 4)) for z, v in avg_occ.nlargest(5).items()],
        "最低5个分区": [(z, round(float(v), 4)) for z, v in avg_occ.nsmallest(5).items()],
    },
    "M4 分区峰值占用率": {
        "公式": "MAX(occupancy(z,·))",
        "全市最高": round(float(max_occ.max()), 4),
        "达到0.9以上的分区数": int((max_occ >= 0.9).sum()),
    },
    "M5 累计充电量": {
        "公式": "Σ volume(z,t)",
        "全市合计(kWh)": round(float(total_vol.sum()), 1),
        "最高5个分区(kWh)": [(z, round(float(v), 1)) for z, v in total_vol.nlargest(5).items()],
    },
    "M6 平均充电时长": {
        "公式": "AVG(duration_h(z,t))",
        "全市均值(小时)": round(float(avg_dur.mean()), 4),
    },
    "M7 日内峰谷占用率差": {
        "公式": "MAX(occupancy)−MIN(occupancy)",
        "分区均值": round(float(pvg.mean()), 4),
        "波动最大5个分区": [(z, round(float(v), 4)) for z, v in pvg.nlargest(5).items()],
    },
    "M8 占用率波动率": {
        "公式": "STDDEV_POP(occupancy)",
        "分区均值": round(float(occ_std.mean()), 4),
        "波动最大5个分区": [(z, round(float(v), 4)) for z, v in occ_std.nlargest(5).items()],
    },
    "M9 分区POI密度": {
        "公式": "poi_total(z)/area(z)×10⁶",
        "POI总数": int(poi_total.sum()) if poi_total.notna().any() else None,
        "POI类别分布": poi_types,
        "密度最高5个分区(个/km²)": [(z, round(float(v), 1)) for z, v in poi_density.nlargest(5).items()],
    },
    "M10 充电桩密度": {
        "公式": "charge_count(z)/area(z)×10⁶",
        "全市均值(个/km²)": round(float(pile_density.mean()), 2),
        "最高5个分区": [(z, round(float(v), 2)) for z, v in pile_density.nlargest(5).items()],
    },
    "M11 双口径电量偏差率": {
        "公式": "(volume−volume_11kw)/volume",
        "全市加权偏差%": round(abs(float(volume.sum().sum() - volume11.sum().sum()))
                              / float(volume.sum().sum()) * 100, 2),
        "分区平均偏差%": round(float(vol_dev.mean()) * 100, 2),
        "偏差最大5个分区%": [(z, round(float(v), 2)) for z, v in (vol_dev * 100).nlargest(5).items()],
    },
    "M12 峰谷电价差": {
        "公式": "MAX(e_price)−MIN(e_price)",
        "全市平均(元/kWh)": round(float(price_gap.mean()), 4),
        "有分时电价的区数(价差>0)": int((price_gap > 1e-6).sum()),
        "价差最大5个分区": [(z, round(float(v), 4)) for z, v in price_gap.nlargest(5).items()],
    },
}

# ==================================================================
# 创新点① 峰谷供需失衡指数（份额差）
# ==================================================================
demand_share = city_demand_h.div(city_demand_h.sum(axis=1), axis=0)
supply_share = charge_count / charge_count.sum()
imb_h = demand_share.sub(supply_share, axis=1)

rows = []
for h in imb_h.index:
    for z in zones:
        rows.append([z, int(h), round(float(demand_share.at[h, z]), 6),
                     round(float(supply_share[z]), 6), round(float(imb_h.at[h, z]), 6)])
ads_imb = pd.DataFrame(rows, columns=["zone_id", "hour_of_day", "demand_share", "supply_share", "imbalance"])
ads_imb["rank_no"] = ads_imb.groupby("hour_of_day")["imbalance"].rank(ascending=False, method="first").astype(int)
ads_imb = ads_imb.sort_values(["hour_of_day", "rank_no"])
ads_imb.to_csv(os.path.join(RES_DIR, "ads_imbalance_index.csv"), index=False, encoding="utf-8-sig")

peak_imb = imb_h.loc[PEAK_H].mean().sort_values(ascending=False)
max_imb_zone = imb_h.max().sort_values(ascending=False)
imb_summary = {
    "落表": "uev_ads.imbalance_index",
    "行数": len(ads_imb),
    "验收①275×24=6600行": len(ads_imb) == len(zones) * 24,
    "I最小值": round(float(imb_h.min().min()), 5),
    "I最大值": round(float(imb_h.max().max()), 5),
    "验收②范围在[-1,1]且正负都有": bool(imb_h.min().min() >= -1 and imb_h.max().max() <= 1
                                       and bool((imb_h > 0).any().any()) and bool((imb_h < 0).any().any())),
    "正值占比%": round(float((imb_h > 0).mean().mean() * 100), 2),
    "晚高峰17-19时TOP10": [(z, round(float(v), 4)) for z, v in peak_imb.head(10).items()],
    "全时段峰值失衡TOP10": [(z, round(float(v), 4)) for z, v in max_imb_zone.head(10).items()],
    "供不应求分区数(I峰值>0)": int((max_imb_zone > 0).sum()),
    "TOP10桩数": [int(charge_count[z]) for z in peak_imb.head(10).index],
}
print("[创新点①] I∈[%.4f, %.4f]，正值占比 %.1f%%，落表 %d 行" %
      (imb_summary["I最小值"], imb_summary["I最大值"], imb_summary["正值占比%"], len(ads_imb)))

fig, ax = plt.subplots(figsize=(10, 5.2))
top10 = peak_imb.head(10).iloc[::-1]
bars = ax.barh([f"分区{z}（{int(charge_count[z])}桩）" for z in top10.index], top10.values, color="#c0392b")
ax.axvline(0, color="#333", lw=0.8)
for b, v in zip(bars, top10.values):
    ax.text(v + 0.0012, b.get_y() + b.get_height() / 2, f"{v:.3f}", va="center", fontsize=9)
ax.set_xlabel("晚高峰（17—19 时）平均失衡指数 I = 需求份额 − 运力份额")
ax.set_title("晚高峰（17—19 时）供需失衡指数 TOP10 分区")
plt.tight_layout(); fig.savefig(os.path.join(FIG_DIR, "02_失衡指数_TOP10.png"), dpi=FIG_DPI); plt.close(fig)

fig, ax = plt.subplots(figsize=(10, 5.2))
hours = list(range(24))
occ24 = city_occ_h.mean(axis=1).reindex(hours) * 100
base24 = baseline_h.groupby(baseline_h.index.hour).mean().reindex(hours)
ax.plot(hours, occ24, marker="o", color="#c0392b", lw=2, label="全市平均占用率（左轴）")
ax.fill_between(hours, occ24, color="#c0392b", alpha=0.10)
ax.set_xlabel("小时"); ax.set_ylabel("全市平均占用率（%）"); ax.set_xticks(hours)
ax.set_ylim(0, float(occ24.max()) * 1.28)
ax2 = ax.twinx()
ax2.plot(hours, base24, ls="--", marker="s", color="#2c3e50", lw=1.5,
         label="单桩需求强度基准（右轴）")
ax2.set_ylabel("单桩需求强度（小时/桩·时）")
hmax, hmin = int(base24.idxmax()), int(base24.idxmin())
ax2.annotate("最高 %d 时 %.4f" % (hmax, base24[hmax]), xy=(hmax, base24[hmax]),
             xytext=(hmax + 2.0, base24[hmax] + 0.008), fontsize=9,
             arrowprops=dict(arrowstyle="->", color="#2c3e50", lw=0.8))
ax2.annotate("最低 %d 时 %.4f" % (hmin, base24[hmin]), xy=(hmin, base24[hmin]),
             xytext=(hmin + 1.5, base24[hmin] - 0.012), fontsize=9,
             arrowprops=dict(arrowstyle="->", color="#2c3e50", lw=0.8))
lines = ax.get_lines() + ax2.get_lines()
ax.legend(lines, [l.get_label() for l in lines], loc="upper center",
          fontsize=9, frameon=False, ncol=2)
ax.grid(alpha=0.25, ls=":")
ax.set_title("全市 24 小时平均占用率与单桩需求强度基准")
plt.tight_layout(); fig.savefig(os.path.join(FIG_DIR, "01_24小时供需曲线.png"), dpi=FIG_DPI); plt.close(fig)

# ==================================================================
# 创新点② 分时电价弹性（TOU vs FLAT）
# ==================================================================
is_tou = price_std > TH_TOU
grp = pd.Series(np.where(is_tou, "TOU", "FLAT"), index=zones)

occ_city_tou = city_occ_h.loc[:, is_tou[is_tou].index].mean(axis=1)
occ_city_flat = city_occ_h.loc[:, is_tou[~is_tou].index].mean(axis=1)
peak_t, valley_t = float(occ_city_tou.loc[PEAK_H].mean()), float(occ_city_tou.loc[VALLEY_H].mean())
peak_f, valley_f = float(occ_city_flat.loc[PEAK_H].mean()), float(occ_city_flat.loc[VALLEY_H].mean())
elast_t, elast_f = peak_t - valley_t, peak_f - valley_f
direction_ok = bool(elast_t < elast_f)

ads_elast = pd.DataFrame({
    "price_type": ["TOU", "FLAT"],
    "zone_count": [int(is_tou.sum()), int((~is_tou).sum())],
    "peak_ratio": [round(peak_t, 4), round(peak_f, 4)],
    "valley_ratio": [round(valley_t, 4), round(valley_f, 4)],
    "elasticity": [round(elast_t, 4), round(elast_f, 4)],
    "avg_price_gap": [round(float(price_gap[is_tou].mean()), 4), round(float(price_gap[~is_tou].mean()), 4)],
    "avg_price_std": [round(float(price_std[is_tou].mean()), 4), round(float(price_std[~is_tou].mean()), 4)],
})
ads_elast.to_csv(os.path.join(RES_DIR, "ads_price_elasticity.csv"), index=False, encoding="utf-8-sig")

ads_elast_24 = pd.DataFrame({
    "hour_of_day": list(range(24)),
    "TOU_avg_occupancy": [round(float(v), 4) for v in occ_city_tou.values],
    "FLAT_avg_occupancy": [round(float(v), 4) for v in occ_city_flat.values],
})
ads_elast_24.to_csv(os.path.join(RES_DIR, "ads_price_elasticity_24h.csv"), index=False, encoding="utf-8-sig")

elast_summary = {
    "落表": "uev_ads.price_elasticity",
    "阈值σ_price": TH_TOU,
    "TOU分区数": int(is_tou.sum()),
    "FLAT分区数": int((~is_tou).sum()),
    "TOU_peak_ratio": round(peak_t, 4),
    "TOU_valley_ratio": round(valley_t, 4),
    "TOU_elasticity": round(elast_t, 4),
    "FLAT_peak_ratio": round(peak_f, 4),
    "FLAT_valley_ratio": round(valley_f, 4),
    "FLAT_elasticity": round(elast_f, 4),
    "验收①两组均非空": bool(is_tou.any() and (~is_tou).any()),
    "验收②TOU弹性小于FLAT": direction_ok,
    "峰谷压平幅度(FLAT−TOU)": round(elast_f - elast_t, 4),
    "峰谷电价差TOU均值": round(float(price_gap[is_tou].mean()), 4),
    "峰谷电价差FLAT均值": round(float(price_gap[~is_tou].mean()), 4),
    "口径声明": "观测性关联，不作因果推断",
}
print("[创新点②] TOU %d 个 / FLAT %d 个；TOU弹性 %.4f，FLAT弹性 %.4f → 方向%s" %
      (int(is_tou.sum()), int((~is_tou).sum()), elast_t, elast_f, "正确" if direction_ok else "异常"))

fig, ax = plt.subplots(figsize=(9, 4.8))
ax.hist(price_std.values, bins=30, color="#2980b9", alpha=0.85, edgecolor="white")
ax.axvline(TH_TOU, color="#c0392b", ls="--", lw=1.6, label=f"阈值 σ={TH_TOU}")
ax.set_xlabel("σ_price（元/kWh）"); ax.set_ylabel("分区数"); ax.legend()
ax.set_title(f"分区电价标准差分布（阈值 σ=0.05；TOU {int(is_tou.sum())} 个 / FLAT {int((~is_tou).sum())} 个）")
plt.tight_layout(); fig.savefig(os.path.join(FIG_DIR, "03_电价标准差_可分性.png"), dpi=FIG_DPI); plt.close(fig)

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(range(24), occ_city_tou.values * 100, marker="o", lw=2, color="#c0392b",
        label=f"TOU 区（{int(is_tou.sum())} 个）")
ax.plot(range(24), occ_city_flat.values * 100, marker="s", lw=2, color="#2980b9",
        label=f"FLAT 区（{int((~is_tou).sum())} 个）")
ax.axvspan(16.5, 19.5, color="#c0392b", alpha=0.08)
ax.axvspan(-0.5, 6.5, color="#27ae60", alpha=0.08)
ax.set_xlabel("小时"); ax.set_ylabel("平均占用率（%）"); ax.set_xticks(range(0, 24)); ax.legend()
ax.set_title(f"分时电价区与固定电价区 24 小时占用率对比（弹性差 {elast_f - elast_t:+.3f}）")
plt.tight_layout(); fig.savefig(os.path.join(FIG_DIR, "04_TOU_FLAT_占用率对比.png"), dpi=FIG_DPI); plt.close(fig)

# ==================================================================
# 创新点③ 需求预测
# ==================================================================
vol_long = volume.stack().rename("v").reset_index()
vol_long.columns = ["time", "zone", "v"]
vol_long["dt"] = vol_long["time"].dt.strftime("%Y-%m-%d")
vol_long["dow"] = vol_long["time"].dt.day_of_week
vol_long["hod"] = vol_long["time"].dt.hour

tr = vol_long[vol_long["dt"] <= TRAIN_END]
va = vol_long[vol_long["dt"] >= VALID_START]

base = tr.groupby(["zone", "dow", "hod"])["v"].mean().rename("base")
gamma = (tr[tr["dt"] >= GAMMA_START].groupby("zone")["v"].mean()
         / tr.groupby("zone")["v"].mean()).replace([np.inf, -np.inf], np.nan).fillna(1.0)

va2 = va.merge(base.reset_index(), on=["zone", "dow", "hod"], how="left")
va2["gamma"] = va2["zone"].map(gamma).fillna(1.0)
va2["predict"] = va2["base"] * va2["gamma"]
va2 = va2.dropna(subset=["predict"])
va2["ape"] = np.where(va2["v"] > 0, (va2["predict"] - va2["v"]).abs() / va2["v"], np.nan)

zone_mape = va2.groupby("zone")["ape"].mean() * 100
mape_overall = float(zone_mape.mean())
mape_main = mape_overall                      # 主方案（基础值×γ）的分区 MAPE，留档对比
mape_fb = None
fallback_note = f"主方案分区 MAPE {mape_overall:.2f}%，未超过 25%，按合同沿用主方案"
if mape_overall > 25:
    last7 = tr[tr["dt"] >= GAMMA_START]
    fb = last7.groupby(["zone", "hod"])["v"].mean().rename("fb")
    va2 = va2.merge(fb.reset_index(), on=["zone", "hod"], how="left")
    va2["predict"] = va2["fb"]
    va2 = va2.dropna(subset=["predict"])
    va2["ape"] = np.where(va2["v"] > 0, (va2["predict"] - va2["v"]).abs() / va2["v"], np.nan)
    zone_mape = va2.groupby("zone")["ape"].mean() * 100
    mape_overall = float(zone_mape.mean())
    mape_fb = mape_overall
    fallback_note = (f"主方案分区 MAPE {mape_main:.2f}% 超过 25%，已按合同切换兜底方案"
                     f"（近 7 天同小时均值），兜底后 {mape_fb:.2f}%")

city_pred = va2.groupby("time")["predict"].sum()
city_act = va2.groupby("time")["v"].sum()
city_mape = float((city_pred - city_act).abs().div(city_act.replace(0, np.nan)).mean() * 100)
city_wape = float((city_pred - city_act).abs().sum() / city_act.sum() * 100)   # 全市口径稳健指标

# 小分母修正：小时级 MAPE 在低电量时段分母趋零会失真，补算两项稳健指标
va2["err_abs"] = (va2["predict"] - va2["v"]).abs()
zone_wape = (va2.groupby("zone")["err_abs"].sum() /
             va2.groupby("zone")["v"].sum().replace(0, np.nan)) * 100       # WAPE：绝对误差/总实际量
wape_overall = float(zone_wape.dropna().mean())
BIG = 5.0                                                                     # 只统计实际电量≥5kWh 的小时
sub = va2[va2["v"] >= BIG]
zone_mape_big = (sub.groupby("zone")["ape"].mean() * 100).dropna()
mape_big = float(zone_mape_big.mean()) if len(zone_mape_big) else None

# 日聚合口径（运营排班看日总量，比小时级更稳）
zd = va2.groupby(["zone", "dt"]).agg(p=("predict", "sum"), v=("v", "sum"))
zone_day_wape = ((zd["p"] - zd["v"]).abs() / zd["v"].replace(0, np.nan) * 100).dropna()
print("[创新点③] 分区WAPE %.2f%%；日聚合WAPE中位 %.2f%%；≥5kWh MAPE %.2f%%；全市MAPE %.2f%%" %
      (wape_overall, zone_day_wape.median(), mape_big if mape_big is not None else -1, city_mape))

ads_fc = (va2.groupby(["zone", "time"]).agg(predict_volume=("predict", "sum"),
                                            actual_volume=("v", "sum")).reset_index()
          .rename(columns={"time": "hour_ts"}))
ads_fc["mape"] = ads_fc["zone"].map(zone_mape).round(2)
ads_fc.to_csv(os.path.join(RES_DIR, "ads_demand_forecast.csv"), index=False, encoding="utf-8-sig")

f_summary = {
    "落表": "uev_ads.demand_forecast",
    "方法": "基础值=同星期同小时历史均值；γ=近7天均值/全期均值；predict=基础值×γ",
    "训练期": f"2022-09-01 ~ {TRAIN_END}",
    "验证期": f"{VALID_START} ~ 2023-02-28",
    "分区级MAPE%": round(mape_overall, 2),
    "主方案分区MAPE%(基础值×γ)": round(mape_main, 2),
    "兜底方案分区MAPE%(近7天同小时)": round(mape_fb, 2) if mape_fb is not None else None,
    "全市汇总MAPE%": round(city_mape, 2),
    "全市汇总WAPE%": round(city_wape, 2),
    "分区级WAPE%(主指标)": round(wape_overall, 2),
    "实际电量≥5kWh样本MAPE%": round(mape_big, 2) if mape_big is not None else None,
    "分区小时级WAPE中位数%": round(float(zone_wape.dropna().median()), 2),
    "分区小时级WAPE_15%以内占比%": round(float((zone_wape.dropna() < 15).mean() * 100), 1),
    "分区日聚合WAPE中位数%": round(float(zone_day_wape.median()), 2),
    "验收①全市口径小于15%": bool(city_mape < 15),
    "误差分层结论": "全市逐小时预测可用（MAPE %.2f%%、WAPE %.2f%%）；分区逐小时因电量分布尖峰、单区样本少，误差偏大，"
                 "报告按‘全市总量可用、分区日聚合次之、分区逐小时列入展望’分层表述" % (city_mape, city_wape),
    "低电量失真说明": "小时级 MAPE 在实际电量趋零时分母极小导致失真，故并列 WAPE 与全市汇总 MAPE",
    "验收②是否触发25%兜底": bool(mape_overall > 25),
    "兜底说明": fallback_note,
    "趋势因子γ范围": [round(float(gamma.min()), 4), round(float(gamma.max()), 4)],
    "γ均值": round(float(gamma.mean()), 4),
    "最难预测5个分区MAPE%": [(z, round(float(v), 2)) for z, v in zone_mape.nlargest(5).items()],
    "最容易预测5个分区MAPE%": [(z, round(float(v), 2)) for z, v in zone_mape.nsmallest(5).items()],
}
print("[创新点③] 分区级 MAPE %.2f%%（全市汇总 %.2f%%）" % (mape_overall, city_mape))

fig, ax = plt.subplots(figsize=(11, 5.2))
ax.plot(city_act.index, city_act.values, label="实际充电量", color="#2c3e50", lw=1.8)
ax.plot(city_pred.index, city_pred.values, label="预测充电量", color="#e67e22", lw=1.8, ls="--")
ax.fill_between(city_act.index, city_pred.values * 0.85, city_pred.values * 1.15,
                color="#e67e22", alpha=0.12, label="±15% 带")
ax.set_ylabel("全市逐小时充电量 kWh")
ax.set_title("验证期（2023-02-22 至 02-28）全市汇总逐小时预测 vs 实际")
ax.legend(); plt.xticks(rotation=30, ha="right")
plt.tight_layout(); fig.savefig(os.path.join(FIG_DIR, "05_需求预测_曲线.png"), dpi=FIG_DPI); plt.close(fig)

# ==================================================================
# 布点扩容建议
# ==================================================================
peak_hour = imb_h.idxmax()
peak_val = imb_h.max()

sugg_rows = []
prio = 0
for z, gap in peak_val.sort_values(ascending=False).items():
    if gap <= 0:
        continue
    prio += 1
    cur = int(charge_count[z])
    add = int(math.ceil(gap * cur * EXP_COEF))
    sug = cur + add
    ph = int(peak_hour[z])
    reason = (f"该分区在 {ph} 时出现供需失衡（失衡指数 {gap:.3f}），现有 {cur} 个充电桩，"
              f"建议新增 {add} 个桩，扩容至 {sug} 个")
    sugg_rows.append([z, cur, add, sug, prio, round(float(gap), 4), ph,
                      round(float(avg_occ[z]), 4), round(float(pile_density[z]), 2),
                      str(grp[z]), reason])

ads_exp = pd.DataFrame(sugg_rows, columns=["zone_id", "current_piles", "add_piles", "suggested_piles",
                                           "priority", "peak_gap", "peak_hour", "avg_occupancy",
                                           "pile_density", "price_type", "reason"])
ads_exp.to_csv(os.path.join(RES_DIR, "ads_expansion_suggestion.csv"), index=False, encoding="utf-8-sig")

readable = ads_exp.rename(columns={"zone_id": "分区", "current_piles": "现有桩数", "add_piles": "建议新增桩数",
                                   "suggested_piles": "扩容后桩数", "priority": "优先级",
                                   "peak_gap": "峰值失衡指数", "peak_hour": "最紧张时段",
                                   "avg_occupancy": "平均占用率", "pile_density": "桩密度(个/km²)",
                                   "price_type": "电价类型", "reason": "依据（可直接进看板）"})
readable.to_csv(os.path.join(RES_DIR, "布点扩容建议清单.csv"), index=False, encoding="utf-8-sig")

exp_summary = {
    "落表": "uev_ads.expansion_suggestion",
    "建议条数(有缺口分区)": len(ads_exp),
    "分区总数": len(zones),
    "建议新增桩合计": int(ads_exp["add_piles"].sum()),
    "现有桩合计(这些分区)": int(ads_exp["current_piles"].sum()),
    "增量比例%": round(float(ads_exp["add_piles"].sum() / ads_exp["current_piles"].sum() * 100), 2),
    "验收②扩容后多于现有占比%": round(float((ads_exp["suggested_piles"] > ads_exp["current_piles"]).mean() * 100), 2),
    "TOP10建议": [(z, int(cur), int(add), int(ph)) for z, cur, add, ph in
                  zip(ads_exp["zone_id"].head(10), ads_exp["current_piles"].head(10),
                      ads_exp["add_piles"].head(10), ads_exp["peak_hour"].head(10))],
    "按电价类型分布": {k: int(v) for k, v in ads_exp.groupby("price_type")["add_piles"].sum().items()},
    "系数说明": "0.3 为保守规划系数，分期建设，避免一次扩容过大",
}
print("[布点建议] %d 条，新增桩合计 %d（占现有 %.1f%%）" %
      (len(ads_exp), exp_summary["建议新增桩合计"], exp_summary["增量比例%"]))

# ==================================================================
# 创新点④ 分区聚类画像
# ==================================================================
feat = pd.DataFrame({
    "avg_occupancy": avg_occ,
    "peak_valley_gap": pvg,
    "occupancy_std": occ_std,
    "avg_duration": avg_dur,
    "poi_density": poi_density,
    "pile_density": pile_density,
    "price_std": price_std,
}).reindex(zones)
feat = feat.fillna(feat.median())
print("[聚类] 特征表 %d 行，NULL %d 个" % (len(feat), int(feat.isna().sum().sum())))

scaler = StandardScaler()
X = scaler.fit_transform(feat)
wcss = {k: round(float(KMeans(n_clusters=k, random_state=SEED, n_init=10).fit(X).inertia_), 2)
        for k in range(2, 7)}
km = KMeans(n_clusters=4, random_state=SEED, n_init=10).fit(X)
feat["cluster"] = km.labels_
sil = float(silhouette_score(X, km.labels_))

feat["imbalance"] = max_imb_zone.reindex(zones).values
prof = feat.groupby("cluster").mean()
prof["分区数"] = feat.groupby("cluster").size()

names = {int(prof["imbalance"].idxmax()): "紧张型"}
rest = [c for c in prof.index if int(c) not in names]
names[int(prof.loc[rest, "poi_density"].idxmax())] = "潜力型"
rest = [c for c in rest if int(c) not in names]
names[int(prof.loc[rest, "avg_occupancy"].idxmin())] = "过剩型"
rest = [c for c in rest if int(c) not in names]
for c in rest:
    names[int(c)] = "稳定型"

feat["cluster_name"] = feat["cluster"].map(names)
prof["画像名称"] = [names[int(c)] for c in prof.index]
feat.reset_index().rename(columns={"index": "zone_id"}).to_csv(
    os.path.join(RES_DIR, "分区聚类画像.csv"), index=False, encoding="utf-8-sig")
prof.to_csv(os.path.join(RES_DIR, "ads_zone_cluster_profile.csv"), encoding="utf-8-sig")

tight_cluster = int(prof["imbalance"].idxmax())
mutual = {
    "紧张型簇编号": tight_cluster,
    "紧张型簇平均失衡": round(float(prof.loc[tight_cluster, "imbalance"]), 4),
    "其他簇平均失衡": round(float(prof.drop(index=tight_cluster)["imbalance"].mean()), 4),
    "互证成立": bool(prof.loc[tight_cluster, "imbalance"] == prof["imbalance"].max()),
}
cluster_summary = {
    "落表": "uev_ads.zone_cluster",
    "特征维度": 7,
    "特征列表": ["avg_occupancy", "peak_valley_gap", "occupancy_std", "avg_duration",
                "poi_density", "pile_density", "price_std"],
    "k": 4,
    "随机种子": SEED,
    "轮廓系数": round(sil, 4),
    "肘部法WCSS(k=2..6)": {int(k): v for k, v in wcss.items()},
    "各簇": {names[int(c)]: {"分区数": int(prof.loc[c, "分区数"]),
                            "平均占用率": round(float(prof.loc[c, "avg_occupancy"]), 4),
                            "平均失衡": round(float(prof.loc[c, "imbalance"]), 4),
                            "桩密度": round(float(prof.loc[c, "pile_density"]), 2),
                            "POI密度": round(float(prof.loc[c, "poi_density"]), 1),
                            "电价σ": round(float(prof.loc[c, "price_std"]), 4)} for c in prof.index},
    "簇规模最极端占比%": round(float(prof["分区数"].max() / prof["分区数"].sum() * 100), 1),
    "互证": mutual,
}
print("[聚类] 轮廓系数 %.3f；各簇 %s" %
      (sil, {names[int(c)]: int(prof.loc[c, "分区数"]) for c in prof.index}))

fig, ax = plt.subplots(figsize=(9, 4.8))
ks = list(wcss.keys()); vs = list(wcss.values())
ax.plot(ks, vs, marker="o", color="#8e44ad", lw=2)
for i in range(1, len(ks)):
    ax.annotate("%.0f" % (vs[i] - vs[i - 1]), xy=((ks[i] + ks[i - 1]) / 2, (vs[i] + vs[i - 1]) / 2),
                xytext=(0, 16), textcoords="offset points", ha="center", fontsize=8.5,
                color="#555", arrowprops=dict(arrowstyle="-", color="#aaa", lw=0.6))
ax.axvline(4, color="#c0392b", ls="--", label="选定 k=4")
ax.set_xlabel("簇数 k"); ax.set_ylabel("簇内平方和 WCSS"); ax.set_xticks(ks); ax.legend()
ax.set_title("肘部法：簇内平方和 WCSS 随簇数 k 的变化（标注为相邻 k 的单步降幅）")
plt.tight_layout(); fig.savefig(os.path.join(FIG_DIR, "08_肘部法_WCSS.png"), dpi=FIG_DPI); plt.close(fig)

colors = {"紧张型": "#c0392b", "过剩型": "#2980b9", "稳定型": "#27ae60", "潜力型": "#8e44ad"}
fig, ax = plt.subplots(figsize=(9, 6))
for nm, c in colors.items():
    m = feat["cluster_name"] == nm
    if m.any():
        ax.scatter(feat.loc[m, "avg_occupancy"] * 100, feat.loc[m, "imbalance"],
                   c=c, label=f"{nm}（{int(m.sum())}）", s=42, alpha=0.75)
ax.set_xlabel("平均占用率（%）"); ax.set_ylabel("峰值失衡指数")
ax.set_title(f"275 个分区聚类画像散点（轮廓系数 {sil:.3f}）"); ax.legend()
plt.tight_layout(); fig.savefig(os.path.join(FIG_DIR, "06_聚类_散点.png"), dpi=FIG_DPI); plt.close(fig)

rad_cols = ["avg_occupancy", "peak_valley_gap", "occupancy_std", "avg_duration",
            "poi_density", "pile_density", "price_std"]
rad_lab = ["平均占用率", "峰谷差", "占用率波动", "平均时长", "POI密度", "桩密度", "电价σ"]
rn = (prof[rad_cols] - prof[rad_cols].min()) / (prof[rad_cols].max() - prof[rad_cols].min()).replace(0, 1)
ang = np.linspace(0, 2 * np.pi, len(rad_cols), endpoint=False).tolist(); ang += ang[:1]
fig = plt.figure(figsize=(8.6, 7)); ax = plt.subplot(111, polar=True)
for c in prof.index:
    v = rn.loc[c].tolist(); v += v[:1]
    ax.plot(ang, v, color=colors[names[int(c)]], lw=1.8, label=names[int(c)])
    ax.fill(ang, v, color=colors[names[int(c)]], alpha=0.07)
ax.set_xticks(ang[:-1]); ax.set_xticklabels(rad_lab)
ax.set_title("四类分区画像 7 维特征雷达图"); ax.legend(loc="upper right", bbox_to_anchor=(1.28, 1.12))
plt.tight_layout(); fig.savefig(os.path.join(FIG_DIR, "07_聚类_雷达.png"), dpi=FIG_DPI); plt.close(fig)

# ==================================================================
# E08 双口径电量对比
# ==================================================================
v_sum, v11_sum = float(volume.sum().sum()), float(volume11.sum().sum())
dual = {"volume总电量kWh": round(v_sum, 1), "volume_11kw总电量kWh": round(v11_sum, 1),
        "偏差%": round(abs(v_sum - v11_sum) / v_sum * 100, 2)}
dual_zone = pd.DataFrame({"zone_id": zones,
                          "volume_kwh": [round(float(volume[z].sum()), 1) for z in zones],
                          "volume_11kw_kwh": [round(float(volume11[z].sum()), 1) for z in zones]})
dual_zone["deviation_pct"] = ((dual_zone.volume_kwh - dual_zone.volume_11kw_kwh)
                              / dual_zone.volume_kwh.replace(0, np.nan) * 100).round(2)
dual_zone.to_csv(os.path.join(RES_DIR, "双口径电量分区对比.csv"), index=False, encoding="utf-8-sig")

fig, ax = plt.subplots(figsize=(9.8, 5.4))
dz = dual_zone.dropna(subset=["deviation_pct"])
sc = ax.scatter(dz["volume_kwh"] / 1e6, dz["deviation_pct"], s=26,
                c=dz["deviation_pct"], cmap="YlOrRd", edgecolor="#7f8c8d", lw=0.4, alpha=0.9)
ax.axhline(dual["偏差%"], color="#c0392b", ls="--", lw=1.2,
           label="全市加权偏差 %.1f%%" % dual["偏差%"])
ax.set_xlabel("分区累计充电量（百万 kWh）")
ax.set_ylabel("双口径偏差率（%）")
ax.set_title("双口径电量偏差率与分区电量规模的关系")
# 标注电量最大的 3 个分区
top3 = dz.nlargest(3, "volume_kwh")
for _, r in top3.iterrows():
    ax.annotate(str(r["zone_id"]), xy=(r["volume_kwh"] / 1e6, r["deviation_pct"]),
                xytext=(4, 4), textcoords="offset points", fontsize=9, color="#7b241c")
ax.legend(loc="lower right", fontsize=9)
plt.tight_layout(); fig.savefig(os.path.join(FIG_DIR, "09_双口径_对比.png"), dpi=FIG_DPI); plt.close(fig)

# ==================================================================
# E01 探索性分析
# ==================================================================
eda = {
    "时间范围": f"{occupancy.index.min()} ~ {occupancy.index.max()}",
    "小时数": int(len(occupancy.index)),
    "分区数": len(zones),
    "桩数合计": int(charge_count.sum()),
    "桩数min/median/max": [int(charge_count.min()), int(charge_count.median()), int(charge_count.max())],
    "缺失率%": {n: round(float(df.isna().mean().mean() * 100), 3) for n, df in
                [("occupancy", occupancy), ("duration", duration), ("volume", volume),
                 ("volume-11kW", volume11), ("e_price", e_price), ("s_price", s_price)]},
    "占用率越界比例%": round(float(((occupancy < 0) | (occupancy > 1)).mean().mean() * 100), 3),
    "负值比例%": round(float((duration < 0).mean().mean() * 100), 3),
}
pd.DataFrame({"zone_id": zones, "pile_cnt": charge_count.astype(int).values}).to_csv(
    os.path.join(EDA_DIR, "分区桩数分布.csv"), index=False, encoding="utf-8-sig")
volume.groupby(volume.index.hour).mean().sum(axis=1).rename("avg_volume_kwh").to_csv(
    os.path.join(EDA_DIR, "全市时段电量分布.csv"), encoding="utf-8-sig")

# ==================================================================
# E10 模型持久化 + 数据指纹
# ==================================================================
joblib.dump({"method": "same_dow_hour_mean_with_trend_gamma", "base": base, "gamma": gamma,
             "kmeans": km, "scaler": scaler,
             "features": ["avg_occupancy", "peak_valley_gap", "occupancy_std", "avg_duration",
                          "poi_density", "pile_density", "price_std"],
             "seed": SEED, "trained_until": TRAIN_END},
            os.path.join(MODEL_DIR, "forecast_model.pkl"))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


finger = {f: sha256(os.path.join(DATA_DIR, f)) for f in
          ["occupancy.csv", "duration.csv", "volume.csv", "volume-11kW.csv",
           "e_price.csv", "s_price.csv", "inf.csv"] if os.path.exists(os.path.join(DATA_DIR, f))}
json.dump({"数据来源": DATA_TAG, "样本小时数": int(len(occupancy.index)), "分区数": len(zones),
           "桩数合计": int(charge_count.sum()), "输入文件SHA256": finger},
          open(os.path.join(MODEL_DIR, "数据指纹.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

# ==================================================================
# 汇总落盘（16 处【待 E 填】）
# ==================================================================
summary = {
    "数据来源": DATA_TAG,
    "口径依据": "docs/contracts/02-指标定义表.md v1.2",
    "E01 探索性分析": eda,
    "基础指标 M1-M12": m1_m12,
    "创新点① 失衡指数": imb_summary,
    "创新点② 电价弹性": elast_summary,
    "创新点③ 需求预测": f_summary,
    "创新点④ 聚类画像": cluster_summary,
    "布点扩容建议": exp_summary,
    "E08 双口径电量": dual,
}
json.dump(summary, open(os.path.join(RES_DIR, "分析结论摘要.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print(f"\n[完成] 图表 -> {FIG_DIR}；落地表 -> {RES_DIR}；模型 -> {MODEL_DIR}")
