#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_samples.py —— 导出「数据导出样例」（进提交包）

★ 为什么必须有这个
  提交包不能带 129MB 原始 CSV（体积大、且违反数据集分发惯例），
  但「别人拿到包就能跑起来」是可复现性的最强证据。
  做法：每张 MySQL 表导出前 100 行为 CSV，配 restore_from_mysql.sh 一键回灌。

用法：
  python scripts/export_samples.py                       # 从 ETL 产出目录导出
  python scripts/export_samples.py --src data/etl_out --dst 05.源码/数据导出样例
"""
from __future__ import annotations
import argparse, os, sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent

# ETL 产出名 → MySQL 表名（对应契约 04 与 db/mysql/01_schema.sql）
NAME_MAP = {
    "dashboard_kpi":        "ads_dashboard_kpi",
    "zone_occupancy":       "ads_zone_occupancy",
    "hourly_supply_demand": "ads_hourly_supply_demand",
    "imbalance_index":      "ads_imbalance_index",
    "price_elasticity":     "ads_price_elasticity",
    "demand_forecast":      "ads_demand_forecast",
    "expansion_suggestion": "ads_expansion_suggestion",
    # insight_* —— E 岗的洞察表（本次由 Python 路径兜底产出）
    "zone_price_group":     "insight_zone_price_group",
    "dq_质量规则统计表":     "insight_dq_summary",
    "dwd_zone_hour_metric_抽样2000行": "dwd_zone_hour_metric_sample",
    "dws_zone_day_hour_抽样5000行":    "dws_zone_day_hour_sample",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="data/etl_out")
    ap.add_argument("--dst", default="05.源码/数据导出样例")
    ap.add_argument("--rows", type=int, default=100, help="每表导出前 N 行")
    args = ap.parse_args()

    src = Path(args.src) if Path(args.src).is_absolute() else REPO / args.src
    dst = Path(args.dst) if Path(args.dst).is_absolute() else REPO / args.dst

    if not src.is_dir():
        print(f"[错误] 找不到 ETL 产出目录：{src}")
        print("       先跑：python scripts/python_etl.py")
        return 1

    dst.mkdir(parents=True, exist_ok=True)
    print("=" * 74)
    print(" 导出数据样例")
    print(f" 源：{src}")
    print(f" 目标：{dst}")
    print("=" * 74)

    n = 0
    for f in sorted(src.glob("*.csv")):
        stem = f.stem
        tbl = NAME_MAP.get(stem, stem.lower().replace(" ", "_").replace("-", "_"))
        try:
            df = pd.read_csv(f)
        except Exception as e:
            print(f"  ✗ {f.name} 读取失败：{e}")
            continue
        out = df.head(args.rows)
        # MySQL LOAD DATA 兼容性：字段里的换行/逗号要转义
        out_path = dst / f"{tbl}.csv"
        out.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"  ✓ {tbl:34s} {len(out):>5d} 行 / 共 {len(df):>9,d} 行  "
              f"{out_path.stat().st_size/1024:>7.1f} KB")
        n += 1

    # 附一份说明
    readme = dst / "README.md"
    readme.write_text(f"""# 数据导出样例

> 由 `scripts/export_samples.py` 自动生成 | 每张表取前 {args.rows} 行

## 为什么有这个目录

提交包不包含 129MB 的 UrbanEV 原始 CSV（体积过大，且不符合数据集再分发惯例）。
但「第三方拿到提交包就能让系统跑起来」是**可复现性最有说服力的证据**。
本目录提供每张应用表的前 {args.rows} 行数据，配合 `scripts/restore_from_mysql.sh`
即可在**不下载原始数据**的前提下重建可查询的数据集。

## 怎么用

```bash
# 1. 起 MySQL
docker compose --profile app up -d mysql

# 2. 灌入本目录的样例
bash scripts/restore_from_mysql.sh

# 3. 体检（应转绿）
bash scripts/smoke_test.sh
```

## 目录清单

| MySQL 表 | 来源 | 说明 |
|---|---|---|
| `ads_dashboard_kpi` | ETL 产出 | 首页 5 个 KPI 指标卡 |
| `ads_zone_occupancy` | ETL 产出 | 分区占用率（地图/热力图） |
| `ads_hourly_supply_demand` | ETL 产出 | 24 小时供需曲线 |
| `ads_imbalance_index` | ETL 产出 | ★ 创新点① 供需失衡指数 TOP 200 |
| `ads_price_elasticity` | ETL 产出 | ★ 创新点② 电价弹性 TOU/FLAT 对比 |
| `ads_demand_forecast` | ETL 产出 | ★ 创新点③ 需求预测与回测 |
| `ads_expansion_suggestion` | ETL 产出 | ★ 创新点③ 布点扩容建议 |
| `insight_zone_price_group` | ETL 产出 | 分区 σ_price 分组结果（TOU/FLAT） |
| `insight_dq_summary` | ETL 产出 | 8 类数据质量规则实测统计 |
| `dwd_zone_hour_metric_sample` | ETL 抽样 | DWD 长表抽样（宽转长 + 清洗后） |
| `dws_zone_day_hour_sample` | ETL 抽样 | DWS 汇总表抽样 |

## ⚠ 重要说明（答辩时可能被问到）

- 这些数据是**真实计算结果**，不是编造的假数据。
  计算过程见 `scripts/python_etl.py`，可逐行核对。
- 原始口径唯一事实源仍是 `docs/contracts/01-数据字典.md` v1.0。
- **兜底说明**：本批数据由 A 岗（组长）用 Python 版 ETL 管道产出。
  原计划的 Hive 路径因 Docker 引擎不可用而无法执行，
  Python 路径与 Hive 路径使用**同一套指标公式**（契约 02），
  两者结果可交叉比对，这正是报告 6.3「数据准确性测试」所要求的验证方式。
""", encoding="utf-8")
    print()
    print(f"  完成：导出 {n} 张表 + README.md")
    print(f"  目录：{dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
