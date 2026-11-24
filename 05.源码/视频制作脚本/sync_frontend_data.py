# -*- coding: utf-8 -*-
"""
前端离线数据同步
================
把 ETL 产出的 dashboard_kpi.csv 同步到 frontend/data/，
保证「后端接口 / 前端离线兜底 / 视频画面」三处 KPI 口径完全一致。

★ 背景：ETL 曾用「|I| > 全市同时段标准差」判据算出 275（= 分区总数），
  而契约 02 与 E 岗 ADS 表用的是「峰值失衡 I > 0」→ 56 个分区。
  两者不一致会让答辩时屏幕数字与口头结论打架。
  现已统一到契约口径（56 / 275，峰值 595 区 0.1225）。

运行：python scripts/sync_frontend_data.py
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "data" / "etl_out"
DST = REPO / "frontend" / "data"

# 表名映射：ETL 产出 → 前端直读文件
MAP = {
    "dashboard_kpi.csv": "dashboard_kpi.csv",
    "demand_forecast.csv": "demand_forecast.csv",
    "expansion_suggestion.csv": "expansion_suggestion.csv",
    "hourly_supply_demand.csv": "hourly_supply_demand.csv",
    "price_elasticity.csv": "price_elasticity.csv",
    "zone_occupancy.csv": "zone_occupancy.csv",
    "zone_price_group.csv": "zone_price_group.csv",
}

# ★ imbalance_index.csv 例外：ETL 产出的这张表是**差值口径**（I = DI − D̄，
#   峰值 0.88 @ 316 区），与契约的**份额差口径**（I = D − S，峰值 0.1225 @ 595 区）
#   冲突。前端与报告必须用契约口径 → 该表从 E 岗 ADS 产出目录取，不被 ETL 覆盖。
ADS = REPO / "analysis" / "output" / "ads"
ADS_IMBALANCE = ADS / "ads_imbalance_index.csv"


def main() -> None:
    DST.mkdir(parents=True, exist_ok=True)

    # ── 1. dashboard_kpi：单独处理（前端多一列 peak_imbalance 也无妨）──
    kpi_src = SRC / "dashboard_kpi.csv"
    if kpi_src.exists():
        df = pd.read_csv(kpi_src)
        keep = [c for c in df.columns if c != "peak_imbalance"]
        df[keep].to_csv(DST / "dashboard_kpi.csv", index=False, encoding="utf-8-sig")
        row = df.iloc[0]
        print(f"✓ dashboard_kpi.csv  供不应求分区={int(row['imbalance_zones'])} / "
              f"{int(row['station_count'])}  峰值失衡={row['peak_imbalance']}")

    # ── 2. imbalance_index：契约份额差口径（E 岗 ADS 表），不被 ETL 覆盖 ──
    if ADS_IMBALANCE.exists():
        shutil.copy2(ADS_IMBALANCE, DST / "imbalance_index.csv")
        n = len(pd.read_csv(ADS_IMBALANCE))
        print(f"✓ {'imbalance_index.csv':28} {n:>6} 行   ← 份额差口径（E 岗 ADS）")
    else:
        print(f"  ⚠ 跳过 imbalance_index.csv（未找到 {ADS_IMBALANCE}）")

    # ── 3. 其余表：整表同步 ──────────────────────────────────────────
    for s_name, d_name in MAP.items():
        if s_name == "dashboard_kpi.csv":
            continue
        s = SRC / s_name
        if not s.exists():
            print(f"  跳过 {s_name}（ETL 未产出）")
            continue
        shutil.copy2(s, DST / d_name)
        n = len(pd.read_csv(s))
        print(f"✓ {d_name:28} {n:>6} 行")

    # ── 4. 一致性自检 ────────────────────────────────────────────────
    print("\n一致性自检：")
    k = pd.read_csv(DST / "dashboard_kpi.csv").iloc[0]
    imb = pd.read_csv(DST / "imbalance_index.csv")
    if "imbalance" in imb.columns:
        pk = imb.groupby("zone_id")["imbalance"].max()
        n_pos = int((pk > 0).sum())
        print(f"  KPI 声明供不应求分区     : {int(k['imbalance_zones'])}")
        print(f"  imbalance_index 实算分区数: {n_pos}")
        print(f"  imbalance_index 峰值     : {pk.max():.4f} @ {pk.idxmax()}")
        ok = (n_pos == int(k["imbalance_zones"]))
        print(f"  → {'✓ 一致' if ok else '✗ 不一致，需排查'}")
        if not ok:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
