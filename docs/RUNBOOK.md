# RUNBOOK · 城市充电桩分析系统运行手册

> **维护人：A（彭忠燕）**　|　**交付：11/26**　|　**创建时间：2026-11-19**
> **目标**：拿到这份文档的人，**不需要问任何人**，能在 30 分钟内把整套系统跑起来。

---

## 目录

1. [系统概述](#一系统概述)
2. [环境要求](#二环境要求)
3. [30 分钟快速启动](#三30-分钟快速启动)
4. [完整部署流程](#四完整部署流程)
5. [数据获取](#五数据获取)
6. [数仓构建](#六数仓构建)
7. [应用部署](#七应用部署)
8. [验证与排错](#八验证与排错)
9. [附录](#九附录)

---

## 一、系统概述

### 1.1 技术栈

| 层 | 技术 | 版本 | 说明 |
|---|---|---|---|
| 存储 | HDFS | 3.3.x | 原始数据 + 数仓存储 |
| 计算 | MapReduce | 3.3.x | 宽表转长、数据质量检查、POI 空间连接 |
| 计算 | Spark SQL | 3.4+ | DWS/ADS 层聚合计算 |
| 数仓 | Hive | 4.0.x | 四层数仓（ODS/DWD/DWS/ADS） |
| 采集 | Flume | 1.11 | CSV → HDFS 增量采集 |
| 交换 | Sqoop | 1.4.7 | Hive ADS → MySQL |
| 存储 | MySQL | 8.0 | 业务库 `uev_charge` |
| 缓存 | Redis | 7.x | 首页聚合缓存 |
| 后端 | Spring Boot | 3.2.5 | REST API |
| 前端 | ECharts 5 + 原生 JS | — | 数据看板 |

### 1.2 目录结构

```
urbanev-charge-analysis/
├── backend/                 Spring Boot 后端
├── frontend/                前端静态页面 + Nginx
├── hadoop/
│   ├── flume/               Flume 采集配置
│   ├── hive/                Hive DDL 生成脚本
│   ├── mr/                  MapReduce Java 作业
│   └── spark/               Spark SQL 计算脚本
├── db/mysql/                MySQL 建表脚本（Docker 自动执行）
├── docs/
│   ├── contracts/           ★ 四份契约（数据字典/指标定义/接口规范/数仓规范）
│   ├── ppt/                 PPT 素材
│   └── screenshots/         报告截图
├── scripts/                 ★ 启停、下载、采集、体检脚本
├── data/raw/                原始 CSV（不在 Git 里）
├── docker-compose.yml       ★ 一键编排
└── RUNBOOK.md               本文件
```

### 1.3 端口一览

| 端口 | 服务 | 访问方式 |
|---|---|---|
| 80 | 前端 Nginx | http://localhost |
| 8080 | 后端 Spring Boot | http://localhost:8080/api |
| 3306 | MySQL | localhost:3306 |
| 6379 | Redis | localhost:6379 |
| 9870 | NameNode Web UI | http://localhost:9870 |
| 8088 | YARN Web UI | http://localhost:8088 |
| 10000 | HiveServer2 JDBC | jdbc:hive2://localhost:10000/default |
| 19888 | Flume 内部（容器内） | — |

### 1.4 默认账号

| 服务 | 用户名 | 密码 |
|---|---|---|
| MySQL | root | `uev123456` |
| MySQL 库 | — | 数据库名 `uev_charge` |
| Redis | — | `uev_redis_pass` |

> ⚠️ 这些是**课程作业用的弱密码**，仅限本地环境。生产环境必须改掉。

---

## 二、环境要求

### 2.1 最低配置

| 项 | 要求 | 说明 |
|---|---|---|
| 操作系统 | Windows 10/11 或 macOS / Linux | 本项目在 Windows 11 + WSL2 上验证 |
| 内存 | **8 GB 以上** | Hadoop + Spark + MySQL + 后端同时跑，至少 8G |
| 磁盘 | **20 GB 可用** | 镜像 6-8G + 数据 132MB + 数仓 2-3G |
| CPU | 4 核以上 | Spark 至少 4 核才不卡 |

### 2.2 方案 A：Docker（推荐）

安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)（Windows/Mac）或 Docker Engine（Linux）。

```bash
docker --version    # 需要 20.10+
docker compose version
```

### 2.3 方案 B：本机原生 Hadoop（无 Docker 时）

需要：
- JDK 17（或 JDK 8 + Hadoop 3.3）
- Hadoop 3.3.x（含 HDFS / YARN / MapReduce）
- Hive 4.0.x
- MySQL 8.0、Redis 7.x
- Maven 3.9+

```bash
export HADOOP_HOME=/opt/hadoop-3.3.6
export HIVE_HOME=/opt/apache-hive-4.0.0
export FLUME_HOME=/opt/apache-flume-1.11.0
export JAVA_HOME=/usr/lib/jvm/java-17
```

> 下载地址：
> - Hadoop：https://archive.apache.org/dist/hadoop/common/hadoop-3.3.6/
> - Hive：https://archive.apache.org/dist/hive/hive-4.0.0/
> - Flume：https://archive.apache.org/dist/flume/1.11.0/

---

## 三、30 分钟快速启动

> **给只想看效果的人**：跑完这一节就能打开看板。

```bash
# 1. 克隆仓库
git clone <你的仓库地址>
cd urbanev-charge-analysis

# 2. 下载数据（约 4 分钟，132MB）
bash scripts/download_data.sh

# 3. 一键启动（自动选择 full / app / native 模式）
bash scripts/start_all.sh

# 4. 打开浏览器
#    http://localhost
```

**如果第 3 步报错**，逐条对照 [第八章 排错](#八验证与排错)。

**如果只想看前端效果但没有后端数据**，前端会显示"数据加载失败"的占位提示，
但**版式、图表框架、筛选交互都能看到**——可以先做 PPT 版式。

---

## 四、完整部署流程

> **给要答辩演示的人**：需要完整的 Hadoop + 数仓 + 业务数据。

### 步骤 1：环境准备

```bash
git clone <你的仓库地址>
cd urbanev-charge-analysis
cp .env.example .env      # 按需修改端口和密码
```

### 步骤 2：拉取镜像（提前一天做，流量约 2GB）

```bash
docker compose --profile full pull
```

镜像清单：
- `mysql:8.0`（约 500MB）
- `redis:7-alpine`（约 40MB）
- `apache/hadoop:3.3.6`（约 1.1GB）
- `apache/hive:4.0.0`（约 500MB）
- `maven:3.9-eclipse-temurin-17`（约 800MB，构建用）
- `eclipse-temurin:17-jre-alpine`（约 200MB）

### 步骤 3：下载数据

```bash
bash scripts/download_data.sh
# 输出示例：
#   [1/3] 下载核心数据（1 小时粒度，12 个 CSV）...
#       ✓ occupancy.csv  (19MB)
#       ...
#   [3/3] 校验数据...
#   下载完成  共 12 个 CSV，总计 132M
```

> 💡 **国内网络慢**：脚本已内置重试和 `ghfast.top` 镜像加速。
> 若仍失败，用网盘分发（见第五章）。

### 步骤 4：启动基础服务

```bash
bash scripts/start_all.sh
```

**预期输出**：
```
[2/5] 选择启动模式...
    ✓ 检测到本地 Hadoop 镜像 → full 模式（Hadoop+Hive+应用全起）
[3/5] 启动服务...
[4/5] 等待服务就绪（最长 120 秒）...
    ✓ 后端已就绪
[5/5] 端到端体检...
```

### 步骤 5：初始化 Hive 数仓

```bash
# 5.1 生成 ODS 建表 DDL（275 列自动展开）
python3 hadoop/hive/gen_ddl.py > ddl_ods.sql

# 5.2 上传并执行
docker cp ddl_ods.sql uev-namenode:/tmp/
docker exec uev-namenode beeline -u jdbc:hive2://hive:10000 -f /tmp/ddl_ods.sql

# 5.3 验证
docker exec uev-namenode beeline -u jdbc:hive2://hive:10000 -e \
  "SELECT COUNT(*) FROM uev_ods.occupancy;"
# 期望输出：4344
```

### 步骤 6：Flume 采集 CSV 到 HDFS

```bash
bash scripts/start_flume.sh

# 等待 30 秒后验证
docker exec uev-namenode hdfs dfs -ls /uev/raw/
docker exec uev-namenode hdfs dfs -cat '/uev/raw/*.csv' | head -3
```

### 步骤 7：运行 MapReduce 作业

```bash
# 7.1 编译 MR 作业
docker exec uev-namenode bash -c '
  mkdir -p /opt/mr && cd /opt/mr
  cp -r /data/hadoop/mr/*.java .
  javac -cp $(hadoop classpath) *.java
  jar cf uev-mr.jar *.class'

# 7.2 宽表转长表
docker exec uev-namenode bash -c '
  hadoop jar /opt/mr/uev-mr.jar com.uev.mr.WideToLong \
    /uev/raw/ /uev/dwd/long/occupancy \
    -D uev.metric.name=occupancy'

# 7.3 数据质量检查
docker exec uev-namenode bash -c '
  hadoop jar /opt/mr/uev-mr.jar com.uev.mr.DataQualityCheck \
    /uev/raw/ /uev/dwd/dq/occupancy \
    -D uev.metric.name=occupancy -D uev.metric.min=0 -D uev.metric.max=1'

# 7.4 POI 空间连接
docker exec uev-namenode bash -c '
  hadoop jar /opt/mr/uev-mr.jar com.uev.mr.PoiZoneJoin \
    /uev/poi/poi.csv /uev/dwd/zone_poi_count \
    -D uev.zone.info.path=/uev/inf/inf.csv'
```

> 各指标重复执行步骤 7.2，把 `uev.metric.name` 换成
> `duration` / `volume` / `volume_11kw` / `e_price` / `s_price`。

### 步骤 8：计算 DWS / ADS 层

```bash
docker cp hadoop/spark/ads_metrics.sql uev-namenode:/tmp/
docker exec uev-namenode bash -c '
  spark-sql --master local[*] --conf spark.sql.hive.metastore.uris=thrift://hive:9083 \
    -f /tmp/ads_metrics.sql'
```

**验证**：
```bash
docker exec uev-namenode beeline -u jdbc:hive2://hive:10000 -e "
  SELECT 'imbalance', COUNT(*) FROM uev_ads.imbalance_index
  UNION ALL SELECT 'elasticity', COUNT(*) FROM uev_ads.price_elasticity
  UNION ALL SELECT 'forecast', COUNT(*) FROM uev_ads.demand_forecast
  UNION ALL SELECT 'suggestion', COUNT(*) FROM uev_ads.expansion_suggestion;"
```

### 步骤 9：Sqoop 导出到 MySQL

```bash
docker exec uev-namenode sqoop export \
  --connect jdbc:mysql://mysql:3306/uev_charge \
  --username root --password uev123456 \
  --table zone_occupancy \
  --hcatalog-table uev_ads.zone_occupancy \
  --hcatalog-database uev_ads \
  --hive-import -m 1 \
  --null-string '\\N' --null-non-string '\\N'
```

> 对每个 ADS 表重复一次。字段类型不一致时见 [第九章 附录 C](#九附录)。

### 步骤 10：启动应用层

```bash
docker compose --profile app up -d backend frontend
```

### 步骤 11：全链路验证

```bash
bash scripts/smoke_test.sh
```

**期望全绿**：
```
==============================================================
  UrbanEV 项目 · 端到端体检报告
==============================================================
  [1/6] 数据文件          ✓ 12 个 CSV
  [2/6] Hive 四层表        ✓ 全部有数据，DWD < ODS（清洗生效）
  [3/6] MySQL 业务表       ✓ 9 张表有数据
  [4/6] 后端接口           ✓ 全部 200
  [5/6] Redis 缓存         ✓ 连接正常
  [6/6] 契约一致性         ✓ 0 处冲突
==============================================================
  结果：6/6 通过
==============================================================
```

---

## 五、数据获取

### 5.1 数据来源

| 项 | 内容 |
|---|---|
| 数据集 | UrbanEV —— 深圳公共充电桩时空运行数据集 |
| 仓库 | https://github.com/whewhewhenew/UrbanEV |
| 论文 | arXiv:2309.05259 |
| 协议 | CC0 1.0 Universal |
| 作者 | Han Li（中山大学）、Haohao Qu（香港理工大学） |

### 5.2 自动下载（推荐）

```bash
bash scripts/download_data.sh           # 1 小时粒度（核心）
bash scripts/download_data.sh --5min    # 额外下载 5 分钟粒度（可选，42MB）
```

> **数据放在哪都行** —— 所有脚本通过 `scripts/find_data.sh` 自动探测：
> 1. 环境变量 `UEV_DATA_DIR`
> 2. 仓库内 `data/raw/`
> 3. 仓库同级 `../数据/UrbanEV/`
> 4. `../../数据/UrbanEV/` 及更上层
>
> 想指定其他位置：`export UEV_DATA_DIR=/你的/路径`

### 5.3 手动下载（备用）

从 https://github.com/whewhewhenew/UrbanEV/tree/main/data 下载以下 12 个文件，
放入 `data/raw/`（或 `../数据/UrbanEV/`，或任意路径后设 `UEV_DATA_DIR`）：

```
occupancy.csv  duration.csv  volume.csv  volume-11kW.csv
e_price.csv    s_price.csv   inf.csv     adj.csv
distance.csv   poi.csv       weather_airport.csv  weather_central.csv
```

### 5.4 数据校验

```bash
wc -l data/raw/*.csv
```

**期望行数**：

| 文件 | 行数 | 文件 | 行数 |
|---|---|---|---|
| occupancy.csv | 4344 | e_price.csv | 4344 |
| duration.csv | 4344 | s_price.csv | 4344 |
| volume.csv | 4344 | weather_airport.csv | 4344 |
| volume-11kW.csv | 3085 | weather_central.csv | 4344 |
| inf.csv | 275 | adj.csv | 275 |
| distance.csv | 275 | poi.csv | 712135 |

> ⚠️ `volume-11kW.csv` 只有 3085 行（比其他的少），这是官方数据本身的不完整，
> **不是下载失败**。计算时注意做时间对齐。

---

## 六、数仓构建

### 6.1 四层结构

| 层 | 表 | 说明 |
|---|---|---|
| ODS | `uev_ods.occupancy` 等 9 张 | 贴源，宽表原貌，275 列 |
| DWD | `uev_dwd.zone_hour_metric` | **宽转长 + 清洗**，一行 = 分区×小时×指标 |
| DWD | `uev_dwd.dim_zone_info` | 分区综合维度（含分时电价标识） |
| DWS | `uev_dws.zone_day_hour` | 分区×日×小时 事实表 |
| ADS | `uev_ads.*` 7 张 | 一张表 = 前端一个图表 |

完整 DDL 见 `docs/contracts/04-数仓表结构规范.md`。

### 6.2 快速重建（数据没变时）

```bash
# 只重跑 ADS 层（改了指标公式时用这个）
docker cp hadoop/spark/ads_metrics.sql uev-namenode:/tmp/
docker exec uev-namenode spark-sql --master local[*] -f /tmp/ads_metrics.sql

# 全量重建（改了 DWD 结构时用这个）
docker exec uev-namenode hdfs dfs -rm -r /uev/dwd
docker exec uev-namenode hdfs dfs -rm -r /uev/dws
# 然后重跑步骤 7、8
```

---

## 七、应用部署

### 7.1 后端

```bash
# 本机开发模式
cd backend
mvn clean package -DskipTests
java -jar target/uev-charge-analysis.jar

# Docker 模式
docker compose --profile app up -d backend
docker logs -f uev-backend
```

### 7.2 前端

```bash
# Docker 模式（推荐）
docker compose --profile app up -d frontend

# 本机模式
cd frontend
python3 -m http.server 8081
# 浏览器打开 http://localhost:8081
```

### 7.3 前后端联调

前端默认通过 Nginx 反向代理访问后端（`/api/` → `backend:8080`）。
本机开发时，在 `frontend/index.html` 的 `<head>` 里加一行：

```html
<script>window.__API_BASE__ = 'http://localhost:8080';</script>
```

---

## 八、验证与排错

### 8.1 体检脚本

```bash
bash scripts/smoke_test.sh
```

分 6 项检查，每项独立可定位。

### 8.2 常见问题

| 现象 | 原因 | 解决 |
|---|---|---|
| `docker compose` 提示找不到 | Docker 未安装或未启动 | 装 Docker Desktop 并启动守护进程 |
| 镜像拉取超时 | 国内网络 | 用镜像加速：`docker compose --profile full pull` 配 registry mirror |
| 内存不足，容器被 kill | 物理内存 < 8G | Docker Desktop → Settings → Resources 调到 8G+ |
| `start_all.sh` 提示数据目录为空 | 没下载数据 | `bash scripts/download_data.sh` |
| 后端 120 秒未就绪 | MySQL 初始化慢 / 编译失败 | `docker logs uev-backend` 看具体报错 |
| 前端显示"数据加载失败" | 后端没起或接口报错 | 打开 `http://localhost:8080/api/health` 看各组件状态 |
| Hive 建表报列数不匹配 | ODS 表列数与 CSV 不一致 | 重新跑 `gen_ddl.py` 生成 DDL |
| MR 作业报 `ClassNotFound` | jar 没打进去 | 确认 `jar cf uev-mr.jar *.class` 在正确目录 |
| Sqoop 导出报类型错 | MySQL 字段类型不匹配 | 见附录 C 的类型对照表 |
| 第二台电脑跑不起来 | 硬编码了绝对路径 | 检查 `application.yml` 和脚本里的路径 |

### 8.3 答辩现场应急

| 情况 | 应急方案 |
|---|---|
| Docker 起不来 | 提前导出 ADS 到 MySQL 静态数据，前端直连 MySQL |
| 集群挂了但 MySQL 还在 | `docker compose --profile app up -d` 只起应用层 |
| 前端 CDN 加载不了（ECharts） | ECharts 已本地化到 `frontend/js/echarts.min.js`，不依赖 CDN |
| 全挂了 | 播放 `docs/ppt/演示视频.mp4` 录屏 |

> 💡 **强烈建议 11/30 提前录一份 5-8 分钟的演示视频**，作为最后兜底。

---

## 九、附录

### 附录 A：常用运维命令

```bash
# 查看所有容器状态
docker compose --profile full ps

# 查看某个服务日志
docker logs -f uev-backend
docker logs -f uev-namenode

# 进入容器
docker exec -it uev-namenode bash
docker exec -it uev-mysql mysql -uroot -puev123456 uev_charge

# HDFS 操作
docker exec uev-namenode hdfs dfs -ls -R /uev
docker exec uev-namenode hdfs dfs -du -sh /uev/*

# Hive 查询
docker exec uev-namenode beeline -u jdbc:hive2://hive:10000

# MySQL 查询
docker exec uev-mysql mysql -uroot -puev123456 uev_charge -e "
  SELECT zone_id, avg_occupancy FROM zone_occupancy ORDER BY avg_occupancy DESC LIMIT 10;"

# 重启单个服务
docker compose --profile full restart backend

# 彻底重来
bash scripts/stop_all.sh --clean && bash scripts/start_all.sh
```

### 附录 B：契约与协作规范

| 契约 | 维护人 | 用途 |
|---|---|---|
| `docs/contracts/01-数据字典.md` | 贺欢欢 | 字段含义、join 键、已知坑 |
| `docs/contracts/02-指标定义表.md` | 姬婷婷 | 12 项指标公式与口径 |
| `docs/contracts/03-接口规范.md` | 杨珊珊 | API 路径、出入参 |
| `docs/contracts/04-数仓表结构规范.md` | 苏静 | 四层数仓 DDL |

**协作命令**：
```bash
bash scripts/sync.sh            # 拉最新 + 看谁的契约变了 + 检查一致性
bash scripts/check-contracts.sh  # 单独跑一致性检查
```

**提交规范**：`[岗位] 模块 - 简短说明`，例：`[B] MR清洗 - 修复分区ID类型转换`

### 附录 C：Sqoop 类型对照表

| Hive 类型 | MySQL 类型 | 说明 |
|---|---|---|
| STRING | VARCHAR(n) | 文本、ID、时间戳字符串 |
| INT | INT | 计数 |
| BIGINT | BIGINT | 大计数 |
| DOUBLE | DOUBLE | 浮点指标 |
| TIMESTAMP | **VARCHAR(30)** | ⚠️ 用字符串避免映射坑 |

### 附录 D：环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `MYSQL_HOST` | localhost | MySQL 主机 |
| `MYSQL_PORT` | 3306 | MySQL 端口 |
| `MYSQL_DB` | uev_charge | 数据库名 |
| `MYSQL_USER` | root | 用户名 |
| `MYSQL_PASSWORD` | uev123456 | 密码 |
| `REDIS_HOST` | localhost | Redis 主机 |
| `REDIS_PASSWORD` | uev_redis_pass | Redis 密码 |
| `HIVE_JDBC_URL` | jdbc:hive2://localhost:10000/default | Hive 连接串 |
| `DATA_START` | 2022-09-01 | 数据起始日 |
| `DATA_END` | 2023-02-28 | 数据结束日 |

### 附录 E：常见提问的答案

**Q：为什么用 Hadoop？数据量不大。**
> 本项目包含 275 个分区 × 6 项指标 × 4,344 小时的时序数据，
> 加上 71 万条 POI 记录，原始层约 120 万单元格，长表化后约 717 万行，
> 且需要"宽转长""空间连接""多指标聚合"三类重计算。
> 更重要的是，本方案通过 Flume→HDFS→MapReduce→Hive→Spark→Sqoop 的完整链路，
> 验证了 Hadoop 生态在时序分析场景下的工程可用性。

**Q：为什么不用 LSTM？**
> 出于工程可复现性与答辩现场可演示性的考虑，采用基于同周期移动平均的统计预测方法。
> 数据具有强周周期性，统计方法在分区级周同环比上足以达到可用精度（MAPE 见报告）。
> 深度学习序列模型列入后续工作展望。

**Q：数据是外国的还是中国的？**
> UrbanEV 是**中国深圳**的真实数据，由中山大学与香港理工大学联合发布，CC0 协议。
> 覆盖深圳 275 个交通分区、23,441 个充电桩、2022-09 至 2023-02 共 6 个月逐小时数据。

---

## 版本记录

| 版本 | 日期 | 修改人 | 内容 |
|---|---|---|---|
| v1.0 | 2026-11-19 | 彭忠燕 | 首次建立完整运行手册 |
