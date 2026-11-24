# 接口 mock 契约（D05 · 硬节点③）

> 维护人：杨姗姗（D 岗）　|　联调方：贺欢欢（C 岗）　|　版本 v1.0　|　2026-11-20
> 数据来源：**本机 18080 端口真实后端跑出的响应快照**，非手写假数据
> 契约上游：`docs/contracts/03-接口规范.md`

---

## 一、这 16 份 mock 是什么、怎么用

```
mock/
├── 01_health.json        GET  /api/health                     健康检查
├── 02_login.json         POST /api/auth/login                 登录
├── 03_me.json            GET  /api/auth/me                    当前用户
├── 04_kpi.json           GET  /api/dashboard/kpi               首页 KPI
├── 05_zones.json         GET  /api/zones                       分区列表
├── 06_occupancy.json     GET  /api/zones/occupancy             地图散点
├── 07_zone_detail.json   GET  /api/zones/{zoneId}              分区详情
├── 08_hourly.json        GET  /api/charts/hourly               24h 供需曲线
├── 09_imbalance.json     GET  /api/charts/imbalance            失衡 TOP
├── 10_price.json         GET  /api/charts/price-elasticity     电价弹性双曲线
├── 11_forecast.json      GET  /api/charts/forecast             预测曲线
├── 12_suggestions.json   GET  /api/charts/suggestions          布点建议
├── 13_volume_dev.json    GET  /api/charts/volume-deviation     双口径电量偏差
├── 14_poi.json           GET  /api/charts/poi-correlation      POI 关联
├── 15_dictionary.json    GET  /api/dictionary                  数据字典
└── 16_cache_stats.json   GET  /api/system/cache-stats          缓存统计
```

**C 岗用法（两种，任选）**

1. **静态托管法（最省事）**：把 `mock/` 目录丢到一个静态服务下（VS Code 的 Live Server 即可），
   前端 `apiGet('/api/dashboard/kpi')` 改成 `fetch('mock/04_kpi.json')` —— 一行改动，页面就能画出来。
2. **Mock Server 法**：用 Postman 的 Mock Server 或 `json-server`，把 16 份按路径映射。
   好处是不改前端代码，只改 `baseUrl`。

> **建议用第 1 种**：改一个 `baseUrl` 常量（`common.js` 里已有），16 个接口全覆盖，零部署成本。

---

## 二、16 个接口 mock 明细（前端照这张表画）

| # | 接口 | 方法 | 关键参数 | data 形状 | 关键字段 | 单位/口径 |
|---|---|---|---|---|---|---|
| 1 | `/api/health` | GET | — | object | `status`, `components{mysql,redis}`, `version` | status=UP；redis 未装为 DOWN |
| 2 | `/api/auth/login` | POST | body: username, password | object | `token`, `tokenType`, `expiresIn`, `user{username,realName,roleCode}` | expiresIn 秒 |
| 3 | `/api/auth/me` | GET | Header: Authorization | object | `username`, `realName`, `roleCode` | — |
| 4 | `/api/dashboard/kpi` | GET | — | object | `stationCount`, `pileCount`, `avgOccupancy`, `totalVolume`, `avgDuration`, `imbalanceZones`, `regions[]{zoneId,pileCount}` | 占用率 0-1；电量 kWh；时长 小时 |
| 5 | `/api/zones` | GET | limit | object | `total`(275), `zones[]{zoneId,longitude,latitude,avgOccupancy,maxOccupancy,chargeCount,poiTotal}` | 经纬度 WGS84；占用率 0-1 |
| 6 | `/api/zones/occupancy` | GET | — | array | 同上，扁平数组（给地图散点直接吃） | 同上 |
| 7 | `/api/zones/{zoneId}` | GET | 路径参数 zoneId | object | `zone{...}`, `peakHours[]{hourOfDay,avgOccupancy}` | peakHours 取 TOP5 |
| 8 | `/api/charts/hourly` | GET | hourRange | array | `hourOfDay`, `avgOccupancy`, `avgDemand`, `avgSupply`, `gap`, `imbalance` | 份额 0-1 |
| 9 | `/api/charts/imbalance` | GET | limit(≤100) | array | `zoneId`, `hourOfDay`, `demandShare`, `supplyShare`, `imbalance`, `rankNo` | 份额 0-1 |
| 10 | `/api/charts/price-elasticity` | GET | priceType | object | `TOU[]`, `FLAT[]`（各 24 点：`hourOfDay`,`avgOccupancy`） | 两条曲线一组 |
| 11 | `/api/charts/forecast` | GET | zoneId | object | `zoneId`, `mape`, `series[]{forecastDate,hourOfDay,predictVolume,actualVolume}` | MAPE 百分数 |
| 12 | `/api/charts/suggestions` | GET | limit | array | `zoneId`, `currentPiles`, `suggestedPiles`, `priority`, `reason`(中文整句), `avgOccupancy`, `peakGap` | **suggestedPiles 是"新增数"不是总数** |
| 13 | `/api/charts/volume-deviation` | GET | — | array | `zoneId`, `volume`, `volume11kw`, `deviation` | deviation 为比例 |
| 14 | `/api/charts/poi-correlation` | GET | — | array | `zoneId`, `poiTotal`, `poiDensity`, `pileDensity`, `avgOccupancy` | 密度为每平方公里 |
| 15 | `/api/dictionary` | GET | — | array | `fileName`, `metricName`, `unit`, `rowCount`, `grain`, `description` | 12 个 CSV 的口径说明 |
| 16 | `/api/system/cache-stats` | GET | — | object | `type`, `hitCount`, `missCount`, `hitRate`, `hitAvgMs`, `missAvgMs`, `speedup`, `localEntries` | 耗时单位 ms |

> `POST /api/system/cache-stats/reset` 用于清空统计，无 mock 单独文件（响应复用第 16 份形状，`data` 为 null）。

---

## 三、五个"必须写清楚否则前端会画错"的口径

这是契约里最容易踩的坑，逐条钉死：

### 1. `avgOccupancy` 是 **0-1 的比例，不是百分数**
`0.4587` 表示 45.87%。前端要显示百分比请自己 `×100`。
封面上写"平均占用率 45.87%"，卡里必须 `(v*100).toFixed(2)`，否则会出现"占用率 0.46%"这种离谱显示。

### 2. `suggestedPiles` 是 **建议新增数量**，不是建议总数
`currentPiles=83, suggestedPiles=10` 的含义是"从 83 加到 93"，不是"加到 10"。
前端表格列名请写「建议新增(个)」，不要写「建议桩数」。

### 3. `imbalanceZones=23` 与 `/charts/imbalance` 的行数对齐
KPI 里的 23 是"存在失衡的分区数"，`/charts/imbalance?limit=23` 正好返回 23 行。
如果前端传 `limit=10` 只显示 10 行，KPI 仍然显示 23 —— 这是**正确**的，不要"修正"。

### 4. `reason` 是**完整中文句子**，直接放进表格/弹窗
例：`该分区在 18 时出现供需失衡（失衡指数 0.0029），现有 83 个充电桩，建议新增 10 个桩`
不要在前端再拼"建议："前缀，会变成"建议：该分区在 18 时…"重复。

### 5. `zoneId` 是 **字符串**，不是数字
`"140"` 而非 `140`。前端拼路径时直接字符串拼接，别做 `parseInt` 再转回来（会丢掉前导格式的一致性）。

---

## 四、mock 与最终实现的差异声明（诚实条款）

| 项 | mock 里的值 | 最终实现 |
|---|---|---|
| `timestamp` | 生成快照那一刻的毫秒数（如 1795160027232） | 每次请求实时生成，前端**不要**把 timestamp 写进 UI（它不是数据时间） |
| `token` | `******<脱敏…>******` | 真实 172 字符 JWT |
| `health.components.redis` | `DOWN` | 装了 Redis 才是 `UP`；本机未装 Redis，属设计性降级（见 D13） |
| `data` 中的行数 | 演示库真实数据（275 分区 / 23441 桩） | 与 mock 一致，因为 mock 就是从这套库跑出来的 |

> 换句话说：**除了 timestamp 会变、token 已脱敏，其它字段前端可以当成"就是这样"。**

---

## 五、变更流程（谁改了要通知谁）

1. **C 岗要加字段** → 群里说 → D 岗评估是否影响契约 03 → 若只是新增字段（不改名、不删字段）→ D 岗直接加，同时更新 mock 与本文件表格。
2. **B/E 岗改口径**（例如 avgOccupancy 改成百分数）→ **不允许单方面改**，必须回到契约 03 开会确认，因为会让 C 岗全部图表返工。
3. **任何人改 mock** → 必须同时改：本文件第二节表格 + D09 接口文档 + D10 Postman 集合，三处一致才算改完。

**一句话：mock 是 C 岗的施工图，改图要按流程，不能各画各的。**
