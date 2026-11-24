# UrbanEV 城市充电桩数据分析系统

> 《基于 Hadoop 与 Spring Boot 的城市充电桩使用行为分析与充电需求预测系统的设计与实现》
> Java Web 后端开发技术 · 2405 班 · **第 02 组**
> **内部封版 11/29　·　交付老师 12/5　·　答辩 12/1**

基于深圳 **275 个交通分区 / 23,441 个充电桩 / 4,344 小时**（2022-09-01 ~ 2023-02-28，181 天逐小时）的真实公开数据，
用 **Flume → HDFS → Hive 四层数仓 → MapReduce/Spark → Sqoop → MySQL** 搭一条离线数仓链路，
算出 **4 个业务创新指标**，再用 **Spring Boot + Redis + ECharts** 做成能回答
"**哪个分区什么时候桩不够用、该在哪建桩、怎么用分时电价引导错峰**" 的决策看板。

---

## 一、给每个成员：先看这三条

### 1️⃣ 每天开工第一件事

```bash
bash scripts/sync.sh
```

拉取最新代码 → **告诉你谁的契约变了** → 检查你的环境和契约是否一致。

### 2️⃣ 有问题不要问人，先看契约

所有"字段叫什么""指标怎么算""接口返回什么"的问题，**答案都在 `docs/contracts/` 里**。

```
docs/contracts/
├── README.md                  ← 契约机制说明（先读这个）
├── 01-数据字典.md              ← C 维护：12 个 CSV 的字段说明与 9 个已知坑（v1.0 实测版）
├── 02-指标定义表.md            ← E 维护：12 基础指标 + 4 创新指标 + 三方联调对照表（v1.1）
├── 03-接口规范.md              ← D 维护：11 个 API 的完整出入参 + 缓存策略（v1.0）
├── 04-数仓表结构规范.md        ← B 维护：16 张表的完整 DDL + 建表 9 步检查清单（v1.0）
└── CHANGELOG.md               ← 谁改了什么、影响谁
```

**契约文件才是交接物，聊天记录不是。** 别人的口径变了，你 pull 一下就看到了。

### 3️⃣ 完成的定义

> **有产物 + 能运行 + 有凭据。**
> 没有截图、没有文件、跑不出结果的，都叫"没做完"。

---

## 二、技术架构

```
UrbanEV 数据集（GitHub 直链，CC0 协议）
  275 交通分区 × 4,344 小时 × 6 项指标（宽表：time + 275 列）
  + inf（分区坐标/桩数）、poi（71 万条）、adj、distance 维表
  + weather_airport / weather_central 两个气象站
        │  Flume taildir 增量采集
        ▼
  HDFS  /uev/raw/
        │  MapReduce ① WideToLong（宽表转长）② DataQualityCheck（质量清洗）③ PoiZoneJoin（空间连接）
        ▼
  Hive 四层数仓
    ODS  uev_ods.*        贴源宽表（276 列原貌，SerDe 自动建表）
    DWD  uev_dwd.*        长表（一行 = 分区×小时×指标）+ 分区维度表 + 质检统计表
    DWS  uev_dws.*        分区 × 日 × 小时 汇总
    ADS  uev_ads.*        7 张应用指标表（一表 = 一图表）
        │  Sqoop export
        ▼
  MySQL  uev_charge
    ads_*       7 张  ← B（Sqoop 导出）
    insight_*   5 张  ← E（pandas 直算 + pymysql 直插）
    sys_*       3 张  ← D（用户/角色/日志）
    v_*         4 张  ← B 建视图（D 的接口只读视图）
        │  Spring Boot 3.2.5 + MyBatis-Plus + Redis
        ▼
  ECharts 5 大屏（原生 JS，不用 Vue/React）
```

### ★ 两条路径在 MySQL 汇合

| 路径 | 负责人 | 说明 |
|---|---|---|
| **离线数仓管道** | B | ODS→DWD→DWS→ADS，Sqoop 导出 `ads_*` |
| **探索性分析** | E | pandas 直接从 CSV 算，直插 `insight_*` |

> **E 为什么不走 Hive/Sqoop？** E 的交付是 11/26，而 B 的 Sqoop 是 11/27，走 Hive 会时间倒挂；
> 且创新点④聚类本来就要写自己的 Spark MLlib 代码。改成直插后**两边并行，E 完全不被 B 卡住**。
> 代价是要做一致性校验：**同一个指标，MySQL 值必须等于 Hive 直查值**（报告 6.3 节）。

---

## 三、分工

| 岗位 | 技术层 | 核心交付物 | 报告署名 |
|---|---|---|---|
| **A**<br>彭忠燕 | 数据接入 + 部署集成 | Flume 配置、Docker Compose 编排、冒烟测试、RUNBOOK、**答辩 PPT 全部** | 第一、二、四章 + 统稿 |
| **B**<br>苏静 | 数仓 + 分布式计算 | Hive 四层、MR 清洗、Spark 计算 ADS、Sqoop、**4 张 MySQL 视图** | 第三章 + 第五章 |
| **C**<br>贺欢欢 | 可视化呈现 | 数据字典、地图底图、**10 张图表 / 6 个页面**、演示视频、图表素材包 | 第三章 3.6 + 附录 |
| **D**<br>杨姗姗 | 后端服务 | Spring Boot **16 个 API**、MySQL、Redis、接口文档、测试用例表 | 第三章 3.5 + 第六章 |
| **E**<br>姬婷婷 | 分析与模型 | **指标定义表**、**4 个创新指标**、模型竞优与误差评估、聚类画像、布点建议 | **第五章** |

### 答辩 PPT 的分工（15 页）

**PPT 全部由 A 制作**（结构、排版、配图、演讲稿），但**内容由主讲人自己提供**：

| 页 | 主讲 | 需要提供 |
|---|---|---|
| 1、2、3、4、6、13、14、15 | 彭忠燕 | 五人姓名、专业、架构图 |
| 5、12 | 杨姗姗 | 用例图草稿、测试用例表、缓存对比数据 |
| 7、8 | 苏静 | 清洗前后对比表、四层 count 截图、血缘图 |
| 11 | 贺欢欢 | 演示脚本、演示视频、各页高清截图 |
| 9、10 | **姬婷婷** | **公式、配好的图、2-3 句结论、预测曲线、MAPE、聚类地图** |

每人工作量 0.5~2 小时，但**每个人在 PPT 上都有署名和主讲**。

---

## 四、五个硬节点（错过一个，后面全崩）

| 截止 | 交付 | 从 → 到 |
|---|---|---|
| **11/21** | `B02` 数据质量规则清单（≥8 类异常） | B → 全组 |
| **11/21** | `E02` σ_price 可分性验证（分时电价能否分两组） | E → 全组 |
| **11/24** | `D05` 16 个接口的 mock JSON 契约 | C + D → C |
| **11/25** | `E03`《指标定义表》定稿（回填 16 处） | **E → B → D → C（全链总源头）** |
| **11/27** | `B05` 四层数仓跑通 + Sqoop 导出 | B → D |

> ⚠️ 依赖链：`E 指标表(11/25) → B DWS/ADS(11/27) → D 真数据联调(11/27) → C 换真数据(11/28) → A 报告+PPT(11/29)`
> **E 的指标表晚一天，B/D/C 同时晚一天。**

---

## 五、Git 使用规范

### 分支模型

```
main                ← 受保护，只有 A 能合并。始终是可运行的完整状态
develop             ← 集成分支，日常合并到这里
feat/<岗位>-<模块>   ← 个人开发分支
contract/<主题>-v<n> ← 契约变更分支（提 PR 到 main，A 评审）
```

### 分支命名

```
feat/A-flume-collect        A 的 Flume 采集
feat/B-hive-ods             B 的 ODS 建表
feat/C-frontend-map         C 的地图底图
feat/D-api-heatmap          D 的热力图接口
feat/E-metric-definition    E 的指标定义表
contract/metric-v2          指标定义表升版
```

### 提交信息格式

```
[岗位] 模块 - 简要描述

[B] 数仓 - 新增 DWD 层建表语句与分区配置
[C] 前端 - 完成深圳275分区地图底图与区域编号校验
[E] 指标 - 供需失衡指数口径改为同类型分区同期基准
[D] 后端 - 热力图接口支持按日期筛选
[A] 部署 - 补充 smoke_test.sh 端到端检测脚本
```

### 提交频率

- **每天至少一次提交**，不要攒到最后
- 提交必须能跑通，不提交编译不过的代码
- 截图、SQL、图表产出物**都要提交**

### ★ 双端同步（GitHub + Gitee）

本仓库同时推送到两个远端：

| 远端 | 地址 | 作用 |
|---|---|---|
| `origin` | `git@github.com:pengzhongyan01/urbanev-charge-analysis.git` | 主仓库，国际访问 |
| `gitee` | `git@gitee.com:peng-zhongyan/urbanev-charge-analysis.git` | 镜像，国内访问快、不易超时 |

**日常用法**（组长）：

```bash
bash scripts/sync_dual.sh push      # 本地 → 两端同时推（先 Gitee 后 GitHub）
bash scripts/sync_dual.sh status    # 看两端各自领先/落后几个提交
bash scripts/sync_dual.sh pull      # 从 GitHub 拉
bash scripts/sync_dual.sh pull-gitee  # 只从 Gitee 拉
```

**组员只需要认一个远端**，推荐 Gitee（国内快）：

```bash
git remote set-url origin git@gitee.com:peng-zhongyan/urbanev-charge-analysis.git
git clone git@gitee.com:peng-zhongyan/urbanev-charge-analysis.git
```

> ★ **脚本的两个安全设计**：
> 1. 推送前自动 fetch 检查分叉，有分叉直接中止并提示，**绝不自动 --force**
> 2. 先推 Gitee 再推 GitHub —— GitHub 超时/被墙时，至少 Gitee 这一端是新的

---

## 六、契约变更流程（唯一硬规矩）

```
1. git switch -c contract/指标定义-v2
2. 修改 docs/contracts/02-指标定义表.md
   —— 记得改版本号 + 追加变更记录
3. git commit -m "[契约] 指标定义表 v2 - 供需失衡指数口径调整"
4. git push origin contract/指标定义-v2
5. 在群里提 PR，@ 组长，说明改了什么、为什么改、影响谁
6. A 评审通过 → 合并 main → 其他人 pull 即生效
```

**为什么必须走 PR**：契约一改，下游全部要跟着改。如果有人偷偷改了 main，别人 pull 下来直接崩。
走 PR 意味着**改动是可见的、可讨论的、可回滚的**。

**变更记录表是给下游看的**：
```
| v1.3 | 11-25 | E | 修正供需失衡指数的基准口径：全市同期 → 同类型分区同期 |
```
B pull 到 v1.3，看一眼就知道"我的实现要改" —— **不用再问 E**。

---

## 七、每日工作流

```
开工
  ↓
bash scripts/sync.sh              # 拉最新 + 看契约变更 + 自检
  ↓
git switch -c feat/<你的分支>      # 从最新 main 切分支
  ↓
写代码
  ↓
bash scripts/check-contracts.sh   # 提交前自检：契约和实现一致吗
  ↓
git commit -m "[岗位] 模块 - 描述"
git push origin feat/<你的分支>
  ↓
在群里提 PR 或直接报进度（带截图）
  ↓
继续（每天 21:00 群里打卡一行）
```

**每日打卡格式**
```
姓名 | 今天完成了什么（带截图） | 明天做什么 | 卡在哪
```
没有截图的"完成了"不算数。

---

## 八、本地环境

### 必需

| 软件 | 版本 |
|---|---|
| JDK | 17 |
| Maven | 3.6+ |
| Docker Desktop | 最新 |
| MySQL | 8.0 |
| Redis | 7+ |
| Python | 3.8+（Pandas / NumPy / Matplotlib） |
| Node.js | 16+（可选，仅用于前端本地起服务） |

### 代码与数据获取

```bash
# 1. 代码
git clone git@github.com:pengzhongyan01/urbanev-charge-analysis.git
# 国内访问推荐用 Gitee 镜像（速度更快）：
git clone git@gitee.com:peng-zhongyan/urbanev-charge-analysis.git
cd urbanev-charge-analysis

# 2. 数据（不进 Git，体积大）—— 一条命令搞定
bash scripts/download_data.sh              # 12 个 CSV，129MB，含重试与镜像加速
bash scripts/download_data.sh --only=timeseries   # 只下 6 个时序表 + inf（≈96MB）
bash scripts/verify_data.sh                # 校验，期望"通过 36 失败 0"
```

> **数据位置说明**：所有脚本通过 `scripts/find_data.sh` 自动探测，按以下优先级：
> 1. 环境变量 `UEV_DATA_DIR`
> 2. 仓库内 `data/raw/`
> 3. 仓库同级 `../数据/UrbanEV/`（★组长本机）
> 4. 更上层的 `../../数据/UrbanEV/` 等
>
> 也就是说 **放哪都能找到**，不用改任何配置。
> 5 分钟粒度数据在 Google Drive，国内慢且可能失效，**建议放弃** —— 1 小时粒度已足够做全套功能。

---

## 九、目录结构

```
urbanev-charge-analysis/
├── README.md
├── docker-compose.yml               ★ 一键编排（A 维护）
├── docs/
│   ├── RUNBOOK.md                  ★★ 运行手册（A 维护，别人照着能跑）
│   ├── 答辩备用说明_技术选型两段.md  ★★ 「为什么不用爬虫 / 不用 FineBI」话术
│   ├── 参考作业骨架提取.md           ★★ 参考作业的七章骨架与排版规格
│   ├── contracts/                  ★★ 契约目录（唯一事实来源）
│   │   ├── README.md
│   │   ├── 01-数据字典.md          v1.0 实测版
│   │   ├── 02-指标定义表.md        v1.1（12 基础 + 4 创新指标）
│   │   ├── 03-接口规范.md          v1.0（11 个接口）
│   │   ├── 04-数仓表结构规范.md    v1.0（16 张表完整 DDL）
│   │   └── CHANGELOG.md
│   ├── report/第1-2章_初稿.md      ★ 报告初稿（A 写）
│   ├── ppt/PPT逐页脚本.md          ★★ 15 页 PPT 逐页脚本 + 演示秒表
│   ├── ppt/images/                 ★ 图表素材
│   └── screenshots/                ★ 所有截图（编号命名）
├── hadoop/
│   ├── flume/flume-env.conf        ★ A
│   ├── flume/flume-csv-hdfs.conf   ★ A
│   ├── hive/gen_ddl.py             ★ 275 列宽表 DDL 自动生成（已实测可用）
│   ├── mr/WideToLong.java          ★ 宽表转长 MR 作业
│   ├── mr/DataQualityCheck.java    ★ 数据质量检查 MR 作业
│   ├── mr/PoiZoneJoin.java         ★ POI 空间连接 MR 作业
│   ├── spark/ads_metrics.sql       ★ ADS 层计算 SQL
│   ├── spark/zone_clustering.sql   ★ 聚类输入宽表 SQL
│   └── spark/ZoneClustering.scala  ★★ 创新点④ Spark MLlib KMeans
├── db/mysql/01_schema.sql          ★ MySQL 建表 + 索引 + 视图
├── backend/                        Spring Boot 工程 ★ D（骨架已就位）
│   ├── pom.xml / Dockerfile
│   └── src/main/java/com/uev/{common,config,controller}/
├── frontend/                       静态页面 ★ C（骨架已就位）
│   ├── index.html
│   ├── js/{common.js, app.js, echarts.min.js}   ★ echarts 已本地化
│   ├── css/style.css
│   ├── assets/shenzhen_440300_full.json  ★ 深圳行政区划底图（已下载）
│   └── assets/深圳地图底图_使用指引.md    ★ 贺欢欢看这个
├── scripts/
│   ├── sync.sh                     ★ 每人每天跑
│   ├── check-contracts.sh          ★ 提交前自检
│   ├── check-deliverables.sh       ★★ 交付物验收（机器可查部分自动判）
│   ├── smoke_test.sh               ★ 端到端体检
│   ├── verify_data.sh              ★ 数据完整性校验（36 项）
│   ├── find_data.sh                ★ 统一数据探测
│   ├── download_data.sh            ★ 数据下载（含镜像加速）
│   ├── start_all.sh / stop_all.sh  ★ 一键起停（profile 自动降级）
│   ├── start_native.sh / stop_native.sh
│   └── start_flume.sh              ★ Flume 采集启动
└── data/raw/                       数据（.gitignore，组员 clone 后放这里）
```

---

## 十、四个创新点

| # | 名称 | 方法 | 关键点 |
|---|---|---|---|
| ① | **峰谷供需失衡指数** | `I(z,t) = D(z,t) − D̄(t)`，归一化消除分区规模差异 | 份额差思想，可与②互相印证 |
| ② | **分时电价弹性分析** | 按 `e_price.csv` 时序标准差 σ 反推分时电价区 | ⚠️ 数据集**无**分时电价标识字段，这个判定方法是本组自推导 |
| ③ | **充电需求预测 + 布点建议** | 滑动平均 / 同星期同比 / 多元回归**三模型横向竞优** | MAPE + MAE + RMSE + 基线对比 + ±1.5σ 区间；不用 LSTM 是因为可解释性与可复现性优先 |
| ④ | **分区聚类画像** | Spark MLlib KMeans（k=4，seed=42） | **必须标准化**（否则桩密度主导距离计算）+ **肘部法选 k**；紧张型簇与①互相印证 |

---

## 十一、常见问题

**Q：我要问某个人一个字段名，直接问不行吗？**
A：可以问，但**先查契约**。契约里没有的，说明这是个新需求 —— 那就该补充进契约文件，而不是停留在聊天里。

**Q：我改了 SQL 会不会影响别人？**
A：会影响。但只要符合契约定义、且指标口径没变，就不影响。如果改了指标口径，**必须提契约 PR**，让下游知道。

**Q：数据文件太大，进不了 Git 怎么办？**
A：数据本来就不该进 Git（已配置 .gitignore）。数据放本地 `data/` 或直接放 HDFS，仓库里只放**处理数据的代码和契约**。

**Q：我的代码在别人机器上跑不起来？**
A：这是严重问题。**12/1 答辩是腾讯会议、各自带电脑**，跑不起来 = 答辩演示翻车。
所有环境相关的东西必须收敛到 `scripts/start_all.sh` 和 `RUNBOOK.md`（A 负责），**不允许写死个人绝对路径**。

**Q：契约检查脚本报错了怎么办？**
A：说明你的实现和契约对不上。**以契约为准改代码**，或者如果确实是契约错了，提 PR 改契约。不能让两边不一致。

---

## 十二、答辩预设问答

1. 数据哪来的？→ UrbanEV，CC0 协议，GitHub 可查，论文 arXiv:2309.05259，深圳真实数据
2. 为什么用 Hadoop？→ 275 分区 × 4,344 小时 × 6 指标（长表化后约 717 万行）+ 71 万 POI，含宽转长/空间连接/多维聚合三类重计算
3. 创新点是什么？→ 供需失衡指数 + 分时电价弹性 + 需求预测与布点建议 + **分区聚类画像**
4. 为什么不用 LSTM？→ 可解释性与工程可复现性优先，深度学习列入展望
5. 为什么不用爬虫？→ 数据集 CC0 授权、真实运营数据、结果可复现；详见 `docs/答辩备用说明_技术选型两段.md`
6. 为什么不用 FineBI？→ 课程适配性 / 可扩展性 / 零授权成本；同上
7. 数据是分区级还是桩级？→ 官方清洗后为分区级 275 个，报告中已说明
8. 预测准不准？→ 给误差区间与三模型竞优对比，不追求单点精度
9. 怎么部署的？→ Docker + 一键脚本 + RUNBOOK，别人不下载 129MB 原始数据也能用还原脚本重建 ADS
10. 各模块谁做的？→ 报告逐章署名，仓库提交记录带岗位标签

---

## 十三、数据来源与引用

> 本系统选用 UrbanEV 开放数据集作为研究数据源。该数据集由中山大学 Li Han 与香港理工大学 Qu Haohao 等人构建并公开发布（https://github.com/whewhewhenew/UrbanEV），原始数据取自深圳市 1,682 个公共充电站、24,798 个充电桩在 2022 年 9 月至 2023 年 2 月的逐小时运行记录，并经异常值检测与零值校验后清洗为 275 个交通分区的分区级数据集（分区充电桩数合计 23,441 个），采用 CC0 1.0 Universal 协议开放授权，相关研究成果发表于 Scientific Data, 2025, 12:523（DOI: 10.1038/s41597-025-04874-4）。
>
> 经本组实测校验，该数据集各时序表共 4,344 个逐小时时点（2022-09-01 00:00 ~ 2023-02-28 23:00，181 天），单表结构为"时间戳列 + 275 个分区列"的**宽表**形式，并包含 71 万条兴趣点记录、三类充电指标（占用率、充电时长、充电电量两种口径）、电价与服务费时序。
>
> 选择该数据集的理由有三：其一，数据规模（275 分区 × 4,344 小时 × 6 项指标，长表化后约 717 万行，叠加 71 万条 POI）满足分布式计算对数据量的基本要求，使 Hadoop 与 Spark 生态组件的引入具有必要性；其二，数据同时包含充电占用率、充电时长、充电电量三类运行指标与电价、服务费、天气、时段四类动态影响因素，以及兴趣点、邻接关系等空间属性，为供需失衡分析、电价弹性分析等多维建模提供了充分特征；其三，数据来源于中国城市并以 CC0 协议开放，不存在版权与合规风险，便于结果复现。

**参考文献**
```
[1] Li H, Qu H, You L, et al. A physics-informed and attention-based graph learning
    approach for regional electric vehicle charging demand prediction. arXiv:2309.05259.
[2] Qu H, Kuang H, Li H, You L. ST-EVCDP: Spatio-temporal EV charging demand prediction.
    https://github.com/CMR0806/ST-EVCDP
```
