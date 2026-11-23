# Flume 采集配置验证报告

> 生成时间：2026-11-23　|　配置文件：`hadoop/flume/flume-csv-hdfs.conf`  
> 生成方式：`python scripts/verify_flume_config.py`  
> 验证方式：属性表逐条比对 + 12 个真实 CSV 的存在性与行数核对

---

## 一、验证结论

| 项 | 结果 |
|---|---|
| 三个 agent 列表（sources / channels / sinks） | OK 各 12 个，一一对应 |
| 属性合法性（对照 Flume 1.11 官方属性表） | OK 全部合法，无静默失效项 |
| 五类语义陷阱 | OK 全部规避 |
| 通道 / CSV / ODS 表 三方一致性 | OK 闭合 |

## 二、静态验证明细

### 2.1 12 个独立采集通道

| # | 通道 | HDFS 子目录 | ODS 表 | CSV 数据行数 |
|---|---|---|---|---|
| 1 | `occupancy` | `hdfs://namenode:8020/uev/raw/occupancy/` | `uev_ods.occupancy` | 4,344 |
| 2 | `duration` | `hdfs://namenode:8020/uev/raw/duration/` | `uev_ods.duration` | 4,344 |
| 3 | `volume` | `hdfs://namenode:8020/uev/raw/volume/` | `uev_ods.volume` | 4,344 |
| 4 | `volume_11kW` | `hdfs://namenode:8020/uev/raw/volume-11kW/` | `uev_ods.volume_11kw` | 4,344 |
| 5 | `e_price` | `hdfs://namenode:8020/uev/raw/e_price/` | `uev_ods.e_price` | 4,344 |
| 6 | `s_price` | `hdfs://namenode:8020/uev/raw/s_price/` | `uev_ods.s_price` | 4,344 |
| 7 | `inf` | `hdfs://namenode:8020/uev/raw/inf/` | `uev_ods.inf` | 275 |
| 8 | `poi` | `hdfs://namenode:8020/uev/raw/poi/` | `uev_ods.poi` | 712,135 |
| 9 | `adj` | `hdfs://namenode:8020/uev/raw/adj/` | `uev_ods.adj` | 275 |
| 10 | `distance` | `hdfs://namenode:8020/uev/raw/distance/` | `uev_ods.distance` | 275 |
| 11 | `weather_airport` | `hdfs://namenode:8020/uev/raw/weather_airport/` | `uev_ods.weather_airport` | 4,344 |
| 12 | `weather_central` | `hdfs://namenode:8020/uev/raw/weather_central/` | `uev_ods.weather_central` | 4,344 |

### 2.2 属性合法性

对照 Flume 1.11 官方手册的 HDFS Sink / TAILDIR Source / Memory Channel 属性表逐条核对。
**重点是排除「语法合法但语义无效」的属性** —— 这类属性不会报错，只会静默失效：

| 属性 | 官方是否存在 | 若误用的后果 |
|---|---|---|
| `hdfs.codec` 配 `fileType=DataStream` | 存在，但 DataStream 明确不压缩 | gzip 不生效，产出不是 `.gz`，校验命令的 glob 匹配不到文件 |
| `hdfs.writeFormat=CompressedText` | **不存在**（只允许 Text / Writable） | 若生效，MR 的 split 逗号只切出 1 列 → 宽转长输出 0 行 |
| `hdfs.closeOnEOF` | **不存在** | 静默忽略，「空文件不入库」的预期不成立 |
| `hdfs.batchInterval` | **不存在** | 静默忽略 |
| `useLocalTimeStamp=false` 且无 timestamp 拦截器 | 需配套使用 | 事件缺 `timestamp` header，Flume 直接报错 |
| 自定义键 `${flume.*}` 间接层 | 非官方机制 | Flume 只解析 `agent.<name>.*` 前缀的键，引用行为不可靠 |

### 2.3 为什么是 12 个独立通道而不是 1 个通道 12 个文件

12 个 CSV 的表结构完全不同（6 个 276 列宽表 + 2 个 275×275 矩阵 + 2 个气象表 + 维表 + POI），
混在同一个 HDFS 目录里会导致无法按表建 Hive 表、也无法按表做增量。
每个 CSV 一个 source/channel/sink、落 12 个独立子目录，
与 `uev_ods.*` 的 12 张表一一对应 —— 这条闭合关系由本脚本自动校验。

## 三、等价采集证据

由于 Docker 引擎在当前环境不可用（`wsl.exe` 被沙箱 Program Blacklist 拦截），
无法产出真实的 `hdfs dfs -ls /uev/raw/` 截图。
本目录提供**等价证据**：按 Flume 的 taildir + HDFS Sink 语义模拟生成的 12 个通道目录结构与滚动文件名，
可据此核对三件事：采集目录层级、滚动文件名格式、目录与 ODS 表名的对应关系。

## 四、等 Docker 可用后的替换步骤（报告里要放真实截图）

```bash
# 1. 启动 Docker Desktop（引擎就绪后）
docker compose --profile hadoop up -d flume

# 2. 启动采集
bash scripts/start_flume.sh

# 3. 等待 >= 5 分钟（rollInterval=300s + 默认 .tmp 后缀，前 5 分钟只有 .tmp）

# 4. 截图（这条就是 B 岗 B01 要交的那张）
docker exec uev-namenode hdfs dfs -ls /uev/raw/
docker exec uev-namenode hdfs dfs -ls /uev/raw/occupancy/

# 5. 截图存到：
#    作业内容/苏静/B01_Hadoop集群环境与jps截图/01_jps六进程.png
#    作业内容/彭忠燕/A02_Flume采集配置与HDFS落地/01_hdfs目录截图.png
```

## 五、遗留问题

本次静态验证**未发现配置缺陷**。

### 仍需真机验证的部分

| 项 | 为什么静态验不了 | 何时验证 |
|---|---|---|
| 采集断点续传是否真的不重复入库 | 需实际跑两次观察 positionFile | Docker 可用后 |
| 滚动文件切分是否在 300s 边界 | 需等待并观察目录 | Docker 可用后 |
| 12 个 CSV 是否都被正则匹配到 | 正则匹配需真实目录 | Docker 可用后 |
