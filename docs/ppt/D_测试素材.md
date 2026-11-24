# D 岗答辩素材 · 后端服务（杨姗姗）

> 对应《PPT逐页脚本》第 **3** 页（系统架构·后端层）、第 **10** 页（功能测试与缓存优化）、第 **11** 页（分工表）。
> 数据全部取自 2026-11-21 本机实测（后端 `--server.port=18080`，MySQL 3307，库 `uev_charge`）。
> 配图已放在 `docs/ppt/images/`，文件名以 `10_` 开头。

---

## 一、第 3 页用：后端一句话 + 分层

**一句话**：
> 后端用 Spring Boot 2.7 搭 REST 服务，Controller–Service–Mapper 三层，MySQL 8 存 14 张表、Redis 做热点缓存，对外暴露 16 个接口给大屏和 Postman 调用；统一 `Result` 响应体、全局异常处理、JWT 鉴权。

**分层表（可直接贴 PPT）**

| 层 | 技术 | 职责 |
|---|---|---|
| 接入层 | Spring MVC + JWT Filter | 路由、鉴权、参数校验、统一响应 |
| 业务层 | Service | 供需指数、分区详情、预测、布点建议等业务编排 |
| 数据层 | MyBatis-Plus + MySQL 8 | 14 张表（4 维表 + 6 明细 + 4 ADS）读写 |
| 缓存层 | Redis / Caffeine | KPI、分区列表、字典等热点结果缓存 |

**16 个接口按 6 组归类（口播时按组讲，不要逐个念）**

| 组 | 接口 | 说明 |
|---|---|---|
| 基础与鉴权 | `GET /health`、`POST /auth/login`、`GET /auth/me` | 健康检查、JWT 登录、当前用户 |
| 总览看板 | `GET /stats/kpi`、`GET /zones`、`GET /zones/occupancy` | KPI 卡片、分区列表、占用率 |
| 分区明细 | `GET /zones/{id}`、`GET /zones/{id}/hourly` | 单分区画像、24 小时曲线 |
| 分析模型 | `/analysis/imbalance`、`/analysis/price`、`/analysis/forecast`、`/analysis/suggestions`、`/analysis/volume-deviation` | 失衡指数、电价可分性、需求预测、布点建议、双口径电量偏差 |
| 基础数据 | `GET /meta/poi`、`GET /meta/dictionary` | POI 密度、数据字典 |
| 运维 | `GET /ops/cache-stats` | 命中率与加速比 |

---

## 二、第 10 页用：16 条接口实测（Postman，2026-11-21）

**结论一行**：16/16 全部 200 OK，无一条失败；最慢的是登录（397 ms，含 BCrypt 校验 + 签发 JWT），其余全部 ≤ 90 ms。

| # | 接口 | 耗时 | 响应体积 | 关键返回 |
|---|---|---|---|---|
| 01 | health | 12 ms | 503 B | status=DEGRADED，regionCount=275，mysql=UP，redis=DOWN |
| 02 | login | 397 ms | 623 B | JWT 签发成功，expiresIn=28800 |
| 03 | me | 71 ms | 440 B | admin / 系统管理员 / ADMIN |
| 04 | kpi | 90 ms | 9.11 KB | 275 分区 / 23441 桩 / 0.4587 / 904822.6 kWh / 2.8765 / 23 |
| 05 | zones | 46 ms | 36.48 KB | total=275 |
| 06 | occupancy | 22 ms | 36.46 KB | 275 条占用率 |
| 07 | zone_detail | 20 ms | 685 B | zoneId=140，poiTotal=2252，chargeCount=310 |
| 08 | hourly | 18 ms | 3.17 KB | 24 点曲线 |
| 09 | imbalance | 17 ms | 1.81 KB | limit=10，rankNo=1 |
| 10 | price | 27 ms | 4.01 KB | TOU / FLAT 对比 |
| 11 | forecast | 37 ms | 17.29 KB | MAPE=5.92（%） |
| 12 | suggestions | 23 ms | 3.01 KB | currentPiles=83 → suggestedPiles=10 |
| 13 | volume_dev | 31 ms | 19.81 KB | deviation=0.2784 |
| 14 | poi | 25 ms | 24.79 KB | poiTotal=1627，poiDensity=17.64 |
| 15 | dictionary | 12 ms | 2.33 KB | occupancy.csv，4344 行 |
| 16 | cache_stats | 5 ms | 464 B | hitAvg=0.005，missAvg=14.272，speedup=2667.596 |

（表太长，PPT 上只放 01/02/04/11/16 五行 + 一句“其余 11 条全部 ≤ 46 ms，明细见报告 6.2”即可。）

---

## 三、缓存优化：两个数字，别混用

| 口径 | 来源 | 未缓存 | 缓存后 | 加速比 |
|---|---|---|---|---|
| 正文/报告用这个 | D07 基准脚本（同进程连续调用） | 1.952 ms | 0.003 ms | **650.733×** |
| 界面证据 | D10 Postman `cache_stats` 接口自报 | 14.272 ms（miss 均值） | 0.005 ms（hit 均值） | 2667.596× |

**口径说明（被追问时照着说）**：两个数是不同轮次采样的——前者是同进程微基准，后者是"跨请求真实链路"的命中/未命中均值，分母里含第一次 SQL 冷启动，所以看着更夸张。**答辩统一讲 650.733×**，2667.596× 只作为 Postman 截图里能看到的界面数字，不单独引用。

---

## 四、可当旁证的数据规模（第 3 / 10 页都能用）

275 个分区 · 23441 个充电桩 · 半年逐小时 23441×24×6 条 · 总电量 904822.6 kWh · 平均利用率 0.4587 · 峰谷比 23 · POI 1627 条 · 数据字典导出 4344 行。

---

## 五、配图（已提交到 `docs/ppt/images/`）

| 文件 | 内容 | 放哪页 |
|---|---|---|
| `10_接口实测_kpi.png` | Postman 调 `/stats/kpi`，200 OK、90 ms、9.11 KB，返回 275/23441/0.4587 | 第 10 页左 |
| `10_接口实测_zones.png` | Postman 调 `/zones`，200 OK、46 ms、36.48 KB、total=275 | 第 10 页右 |
| `10_缓存对比_cache_stats.png` | Postman 调 `/ops/cache-stats`，200 OK、5 ms，hitAvg/missAvg/speedup | 第 10 页下（配 650.733× 的说明） |

原图（16 张全量）在 `docs/screenshots/D10_postman/实测响应_*.png`，需要补图直接从这里取。

---

## 六、30 秒口播稿

**第 3 页（讲后端那一格，约 20 s）**
> "后端这块是 Spring Boot 三层结构，上面 16 个接口按六组对外——鉴权、总览、分区明细、分析模型、基础数据、运维。数据落 MySQL 14 张表，热点结果走 Redis，所有接口统一用 Result 包一层，异常由全局处理器兜住，前端拿到的永远是同一套结构。"

**第 10 页（讲测试与缓存，约 30 s）**
> "功能测试用 Postman 打了 16 条接口，全部 200，最慢是登录 397 毫秒——因为要跑 BCrypt 和签 JWT，其余都在 90 毫秒以内，KPI 这种 9 KB 的聚合查询 90 毫秒出。缓存这块做了对照实验：同一进程连续调，1.952 毫秒降到 0.003 毫秒，加速 650 倍；右边这张截图是 Postman 里 cache-stats 接口自己报的命中/未命中均值，加速比 2667 倍，那是跨请求真实链路的数，跟左边的同进程基准不是一回事，报告里统一用的是 650.733 倍。"

**被问"Redis 挂了怎么办"**（health 里 redis=DOWN 可能被追问）
> "接口设计成缓存不可用就回源 MySQL，health 里 redis=DOWN 是当时没起 Redis 的实况，不影响功能，只是没有缓存加速；生产上会配 Caffeine 本地二级缓存兜底。"

---

## 七、复现命令

```powershell
# 1) 起 MySQL（3307）+ 初始化
mysql --defaults-file=D:\uev_db\my.ini -uroot < db\mysql\01_schema.sql
mysql --defaults-file=D:\uev_db\my.ini -uroot uev_charge < db\mysql\02_seed_mock.sql

# 2) 起后端
java -jar backend\target\uev-charge-analysis.jar --server.port=18080

# 3) Postman：导入 docs\screenshots\D10_postman\UrbanEV_D岗_16接口.postman_collection.json
#    集合变量 baseUrl 已是 http://127.0.0.1:18080/api，先跑 02_login 再跑其余
```
