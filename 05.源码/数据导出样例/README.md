# 数据导出样例

> 由 `scripts/export_samples.py` 自动生成 | 每张表取前 100 行

## 为什么有这个目录

提交包不包含 129MB 的 UrbanEV 原始 CSV（体积过大，且不符合数据集再分发惯例）。
但「第三方拿到提交包就能让系统跑起来」是**可复现性最有说服力的证据**。
本目录提供每张应用表的前 100 行数据，配合 `scripts/restore_from_mysql.sh`
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
