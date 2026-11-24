# 分层对应表：一个数字是怎么走到页面上的（D12）

> 维护人：杨姗姗（D 岗）　|　版本 v1.0　|　2026-11-20
> 用途：老师问"这个数从哪来的"时，从最后一列往前一行一行指给他看。

---

## 一、七层链路（先看结构）

```
① 源 CSV          12 个文件，4344 行（分区×小时），275 个分区
      ↓ Flume 采集
② HDFS            /origin_data/uev/*.csv
      ↓ MR 清洗
③ DWD 层          宽表转长表、去空、去重、单位统一
      ↓ Spark 计算
④ DWS/ADS 层      7 张 ADS 表（指标已算好）
      ↓ Sqoop 导出
⑤ MySQL 表        14 张表（含 ADS 镜像 + 系统表）
      ↓ 视图投影
⑥ MySQL 视图      10 个 v_*（字段名 = 接口字段名）
      ↓ MyBatis
⑦ Mapper XML      13 条 SQL（只 FROM 视图）
      ↓ Service（业务规则 + 缓存）
⑧ Controller      16 个端点（包 ApiResponse）
      ↓ JSON
⑨ 前端            ECharts 图表 / KPI 卡 / 地图
```

**责任边界**：①~④ 是 B/E 岗，⑤~⑧ 是 D 岗（我），⑨ 是 C 岗。
**我这一层不造数、不重算指标** —— 只做"搬运 + 契约 + 缓存 + 异常"。

---

## 二、10 个核心指标的逐条追踪

### 1. 站点数 `stationCount = 275`

| 层 | 内容 |
|---|---|
| 源 | 分区边界文件 / `occupancy.csv` 的 `zone_id` 去重 |
| ADS | `dashboard_kpi.station_count` |
| 表 | `dashboard_kpi` |
| 视图 | `v_kpi_overview.station_count` |
| Mapper | `KpiMapper.selectLatest` |
| 接口 | `GET /dashboard/kpi` → `data.stationCount` |
| 前端 | 首页 KPI 卡「覆盖站点」 |

> **校验点**：契约要求 275，`health.regionCount` 也返回 275，两处一致即为对。若哪天变成 274，说明清洗掉了 1 个空分区。

### 2. 充电桩总数 `pileCount = 23441`

| 层 | 内容 |
|---|---|
| 源 | 桩清单 / 各分区 `charge_count` 汇总 |
| ADS | `dashboard_kpi.pile_count` |
| 视图 | `v_kpi_overview.pile_count` |
| Mapper | `KpiMapper.selectLatest` |
| 接口 | `data.pileCount` |
| 前端 | KPI 卡「充电桩」 |

> **校验点**：`SELECT SUM(charge_count) FROM zone_occupancy` 必须 = 23441。
> 这个数最容易"改着改着就变"，所以 D10 的 Postman 断言里专门钉了它。

### 3. 平均占用率 `avgOccupancy = 0.4587`

| 层 | 内容 |
|---|---|
| 源 | `occupancy.csv`（分区×小时，4344 行） |
| DWD | 宽转长，`occupancy` 统一为 0-1 |
| ADS | `dashboard_kpi.avg_occupancy`（全期均值） |
| 视图 | `v_kpi_overview.avg_occupancy` |
| 接口 | `data.avgOccupancy` |
| 前端 | KPI 卡「平均占用率 45.87%」（**前端 ×100**） |

> **口径坑**：库里存 0-1，前端显示百分数。这一条写在契约里，也写在 D05 的"五个必须写清楚"里。
> 出现过的最坏情况是：后端改存百分数、前端又 ×100 → 显示 4587%。所以断言里加了 `within(0,1)`。

### 4. 总电量 `totalVolume = 904822.6`（kWh）

| 层 | 内容 |
|---|---|
| 源 | `volume.csv`（上报口径） |
| DWD | 单位统一为 kWh |
| ADS | `dashboard_kpi.total_volume` |
| 接口 | `data.totalVolume` |
| 前端 | KPI 卡「总电量」 |

### 5. 平均充电时长 `avgDuration = 2.8765`（小时）

| 层 | 内容 |
|---|---|
| 源 | `duration.csv` |
| ADS | `dashboard_kpi.avg_duration` |
| 接口 | `data.avgDuration` |
| 前端 | KPI 卡「平均时长」（显示为 2.88 h 或 172 min） |

### 6. 失衡指数 `imbalance`（创新点①）

| 层 | 内容 |
|---|---|
| 源 | `occupancy.csv`（需求代理）+ 桩数（供给代理） |
| 计算 | `demand_share = 分区小时需求 / 全域需求`；`supply_share` 同理；`imbalance = demand_share - supply_share`（E 岗 E04 定稿） |
| ADS | `imbalance_index`（含 `rank_no`） |
| 视图 | `v_imbalance_top` |
| Mapper | `ChartMapper.selectImbalanceTop`（`ORDER BY imbalance DESC LIMIT ?`） |
| 接口 | `GET /charts/imbalance` → `data[].imbalance` / `rankNo` |
| 前端 | 失衡 TOP 柱状图 |

> **后端不重算**：`rank_no` 直接用库里的值。若后端自己 `ROW_NUMBER()` 重排，一旦 E 岗口径改（比如按分区而非全域归一化），两边排名会不一致 —— 这种 bug 极难查，所以从设计上就不允许。

### 7. TOU/FLAT 占用率（创新点②）

| 层 | 内容 |
|---|---|
| 源 | `e_price.csv`（电价）+ `s_price.csv`（服务费）+ `occupancy.csv` |
| 计算 | 按 `price_type`（TOU 峰谷 / FLAT 平段）分组求 24 小时均值 |
| ADS | `price_elasticity`（`price_type`, `hour_of_day`, `avg_occupancy`, `zone_count`, `avg_price_gap`） |
| 视图 | `v_price_elasticity` |
| Mapper | `ChartMapper.selectPriceByType`（查一种类型） |
| Service | `ChartService` 调两次，拼 `{TOU:[], FLAT:[]}` |
| 接口 | `GET /charts/price-elasticity` |
| 前端 | 双曲线（同一图上两条） |

> **设计取舍**：SQL 查两次而不是一次查全部再分组 —— 因为要"一次请求给两组"，Service 组装比前端 split 更稳，而且两次都命中缓存后耗时可忽略。

### 8. 预测值 `predictVolume` 与 `MAPE`（创新点③）

| 层 | 内容 |
|---|---|
| 源 | `occupancy.csv` 时序 |
| 计算 | E 岗 E07 模型（多模型竞优），输出 7 天 × 24 小时 |
| ADS | `demand_forecast`（`zone_id`, `forecast_date`, `hour_of_day`, `predict_volume`, `actual_volume`, `mape`） |
| 视图 | `v_forecast_series` |
| Mapper | `ChartMapper.selectForecast` |
| 接口 | `GET /charts/forecast?zoneId=140` → `data.series[]` + `data.mape` |
| 前端 | 预测 vs 实际对比曲线 |

> **数据现状**：只有 140/145/152 三个分区有预测（504 行 = 3 × 7 × 24）。其它分区 → 404「该分区暂无预测数据」。
> 这是**如实告知**，不是隐藏;报告里也这么写。

### 9. 建议新增桩数 `suggestedPiles`（创新点③）

| 层 | 内容 |
|---|---|
| 源 | 失衡指数 + 现有桩数 |
| 计算 | E 岗 E09：按峰时缺口折算需要新增的数量 |
| ADS | `expansion_suggestion`（含 `reason` 中文整句、`priority`） |
| 视图 | `v_suggestions` |
| Mapper | `ChartMapper.selectSuggestions`（`ORDER BY priority`） |
| 接口 | `GET /charts/suggestions` → `data[].suggestedPiles` / `reason` |
| 前端 | 建议表格（列名「建议新增(个)」） |

### 10. 双口径偏差 `deviation`（创新点 · M11）

| 层 | 内容 |
|---|---|
| 源 | `volume.csv`（上报）+ `volume_11kw.csv`（11kW 折算） |
| 计算 | `deviation = (volume - volume_11kw) / volume_11kw` |
| ADS | `volume_deviation` |
| 视图 | `v_volume_deviation` |
| Mapper | `ChartMapper.selectVolumeDeviation` |
| 接口 | `GET /charts/volume-deviation` |
| 前端 | 双柱对比 + 偏差折线 |

---

## 三、这张表怎么用（三个场景）

1. **答辩被问"数据是真的吗"** → 从最后一行往前指到 ①，说明每一层都有落库记录。
2. **C 岗问"这个字段什么意思"** → 看第 7 列（接口字段）和第 10 列（前端位置），不用来回问。
3. **B 岗改口径** → 只需改 ④→⑤ 之间（ADS 表 + 视图），⑦⑧⑨ 不动。这就是分层的价值。

---

## 四、一句话总结

> 页面上任何一个数字，都能沿着这张表**七层追回到某个 CSV 的某一列**。
> 我做后端这一层，做的是"不让这条链断"——字段名不漂、口径不重算、异常不吞掉。
