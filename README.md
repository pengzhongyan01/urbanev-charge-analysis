# UrbanEV 城市充电桩数据分析系统

> 《基于 Hadoop 与 Spring Boot 的城市充电桩使用行为分析与充电需求预测系统的设计与实现》
> Java Web 后端开发技术 · 2405 班 · 第 06 组
> **交付：11/29　·　老师截止：12/5　·　答辩：12/8**

---

## 一、给每个成员：先看这三条

### 1️⃣ 每天开工第一件事

```bash
bash scripts/sync.sh
```

这一个命令会：拉取最新代码 → **告诉你谁的契约变了** → 检查你的环境和契约是否一致。

### 2️⃣ 有问题不要问人，先看契约

所有"字段叫什么""指标怎么算""接口返回什么"的问题，
**答案都在 `docs/contracts/` 里**。

```
docs/contracts/
├── README.md                  ← 契约机制说明（先读这个）
├── 01-数据字典.md              ← C 维护：11 个 CSV 的字段说明
├── 02-指标定义表.md            ← E 维护：12 项指标的口径
├── 03-接口规范.md              ← D 维护：API 路径与出入参
└── 04-数仓表结构规范.md        ← B 维护：四层建表 DDL
```

**契约文件才是交接物，聊天记录不是。** 别人的口径变了，你 pull 一下就看到了。

### 3️⃣ 完成的定义

> **有产物 + 能运行 + 有凭据。**

没有截图、没有文件、跑不出结果的，都叫"没做完"。

---

## 二、技术架构

```
UrbanEV 数据集（GitHub + Google Drive）
  275 交通分区 × 8760 小时 × {occupancy, duration, volume, volume-11kW, e_price, s_price}
  + {inf, poi, adj, distance} 维表 + {weather_airport, weather_central}
        │  Flume 批量采集
        ▼
  HDFS（按月分区）
        │  MapReduce 清洗校验
        ▼
  Hive 四层数仓
    ODS  原始贴源
    DWD  清洗后明细事实表（一行 = 分区 × 小时）
    DWS  轻度汇总（按天、滚动均值、峰谷标识）
    ADS  应用指标（一张表 = 前端一个图表）
        │  Sqoop
        ▼
  MySQL
        │  Spring Boot + MyBatis-Plus + Redis
        ▼
  ECharts 大屏（原生 JS，不用 Vue/React）
```

---

## 三、分工

| 岗位 | 技术层 | 核心交付物 | 报告署名 |
|---|---|---|---|
| **A**<br>彭忠燕 | 数据接入 + 部署集成 | Flume 配置、Docker Compose 编排、冒烟测试、RUNBOOK、**答辩 PPT 全部** | 第一、二、四章 + 统稿 |
| **B**<br>苏静 | 数仓 + 分布式计算 | Hive 四层、MR 清洗、Spark 计算 ADS、Sqoop | 第三章 3.1-3.4 |
| **C**<br>贺欢欢 | 可视化呈现 | 数据字典、地图底图、5 个图表、报告图片、演示视频、图表素材包 | 第三章 3.6 + 附录 |
| **D**<br>杨珊珊 | 后端服务 | Spring Boot 全套 API、MySQL、Redis、接口文档 | 第三章 3.5 + 第四章 |
| **E**<br>姬婷婷 | 分析与模型 | 指标定义表、三个创新指标、预测模型、布点建议 | **第五章** |

### 答辩 PPT 的分工

**PPT 全部由 A 制作**（结构、排版、配图、演讲稿），但**内容由主讲人自己提供**：

| 页 | 主讲 | 需要提供 |
|---|---|---|
| 1、2、4、11 | 彭忠燕 | 五人姓名、专业 |
| 3、10 | 杨珊珊 | 用例图草稿、测试用例表、缓存对比数据 |
| 5、6 | 苏静 | 清洗前后对比表、四层 count 截图、血缘图 |
| 7 | 贺欢欢 | 演示脚本、演示视频、各页高清截图 |
| 8、9 | **姬婷婷** | **公式、配好的图、2-3 句结论、预测曲线、MAPE** |

每人工作量 0.5~2 小时，但**每个人在 PPT 上都有署名和主讲**。

素材统一交到 `docs/ppt/`，模板见 `docs/ppt/README.md`。

**交期**：苏静 11/26 · 姬婷婷 11/27 · 贺欢欢与杨珊珊 11/28 · 彭忠燕 11/29 做 PPT 并打包。

---

## 四、三个不可延误的节点

| 时间 | 交付 | 从 → 到 |
|---|---|---|
| **11/20** | `01-数据字典.md` | C → 全组 |
| **11/25** | `02-指标定义表.md` + `04-数仓表结构规范.md` | E → B　B → D |
| **11/26** | `03-接口规范.md` 首版 | E + D → C |

---

## 五、Git 使用规范

### 分支模型

```
main              ← 受保护，只有 A 能合并。始终是可运行的完整状态
develop           ← 集成分支，日常合并到这里
feat/<岗位>-<模块>  ← 个人开发分支
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
- 截图、SQL、Notebook、图表产出物**都要提交**

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

**为什么必须走 PR**：
契约一改，下游全部要跟着改。如果有人偷偷改了 master，别人 pull 下来直接崩。
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
bash scripts/sync.sh          # 拉最新 + 看契约变更 + 自检
  ↓
git switch -c feat/<你的分支>  # 从最新 main 切分支
  ↓
写代码
  ↓
bash scripts/check-contracts.sh  # 提交前自检，契约和实现一致吗
  ↓
git commit -m "[岗位] 模块 - 描述"
git push origin feat/<你的分支>
  ↓
在群里提 PR 或直接报进度（带截图）
  ↓
继续（每天 21:00 群里打卡一行）
```

### 每日打卡格式

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
| Redis | 6+ |
| Python | 3.8+（Pandas / NumPy / Matplotlib / Seaborn） |
| Node.js | 16+（可选，仅用于前端本地起服务） |

### 数据获取

```bash
# 1. 代码
git clone <仓库地址>
cd urbanev-charge-analysis

# 2. 数据（不进 Git，体积大）
mkdir -p data/dataset
# 方式一：GitHub 仓库里的 1 小时粒度数据（推荐，够用）
git clone --depth 1 https://github.com/whewhewhenew/UrbanEV.git /tmp/UrbanEV
cp -r /tmp/UrbanEV/data/dataset/* data/dataset/

# 方式二：5 分钟粒度数据（可选，加分项）
pip install gdown
gdown --folder https://drive.google.com/drive/folders/1VUgdb8uNgmtvO93BHBK_OrSxjndrF-48
```

> ⚠️ Google Drive 可能慢。**只用 1 小时粒度也完全够做全套功能**，5 分钟粒度是加分项不是必需。

---

## 九、目录结构

```
urbanev-charge-analysis/
├── README.md
├── RUNBOOK.md                      ★ 运行说明（A 维护）
├── docs/
│   ├── contracts/                  ★★ 契约目录（唯一事实来源）
│   │   ├── README.md
│   │   ├── 01-数据字典.md
│   │   ├── 02-指标定义表.md
│   │   ├── 03-接口规范.md
│   │   ├── 04-数仓表结构规范.md
│   │   └── CHANGELOG.md
│   ├── screenshots/                所有截图（编号命名）
│   └── images/                     报告用图表
├── hadoop/
│   ├── flume/flume-env.conf        ★ A
│   ├── hive/01_ods.sql ~ 04_ads.sql ★ B
│   ├── mr/CleanMapper.java 等      ★ B
│   └── spark/AdsCompute.py         ★ B
├── db/mysql/                       MySQL 建表 + 种子数据
├── backend/                        Spring Boot 工程 ★ D
├── frontend/                       静态页面 ★ C
│   ├── index.html demand.html imbalance.html
│   ├── price.html forecast.html advice.html
│   ├── js/common.js
│   └── assets/shenzhen.geojson
├── notebooks/                      E 的分析 Notebook
├── scripts/
│   ├── sync.sh                     ★ 每人每天跑
│   ├── check-contracts.sh          ★ 提交前自检
│   ├── smoke_test.sh               ★ A 维护，端到端检测
│   ├── start_all.sh / stop_all.sh  ★ A 维护
├── data/                           数据（.gitignore）
```

---

## 十、常见问题

**Q：我要问某个人一个字段名，直接问不行吗？**
A：可以问，但**先查契约**。契约里没有的，说明这是个新需求 —— 那就该补充进契约文件，而不是停留在聊天里。

**Q：我改了 SQL 会不会影响别人？**
A：会影响。但只要符合契约定义、且指标口径没变，就不影响。如果改了指标口径，**必须提契约 PR**，让下游知道。

**Q：数据文件太大，进不了 Git 怎么办？**
A：数据本来就不该进 Git（已配置 .gitignore）。数据放本地 `data/` 或直接放 HDFS，仓库里只放**处理数据的代码和契约**。

**Q：我的代码在别人机器上跑不起来？**
A：这是严重问题。12/8 答辩是各自带电脑。跑不起来 = 答辩演示翻车。
所有环境相关的东西必须收敛到 `scripts/start_all.sh` 和 `RUNBOOK.md`（A 负责），**不允许写死个人绝对路径**。

**Q：契约检查脚本报错了怎么办？**
A：说明你的实现和契约对不上。**以契约为准改代码**，或者如果确实是契约错了，提 PR 改契约。不能让两边不一致。

---

## 十一、答辩预设问答

1. 数据哪来的？→ UrbanEV，CC0 协议，GitHub 可查，论文 arXiv:2309.05259
2. 为什么用 Hadoop？→ 275 分区 × 8760 小时 × 多指标时序聚合，单机是瓶颈
3. 创新点是什么？→ 供需失衡指数 + 分时电价弹性 + 布点扩容建议
4. 为什么不用 LSTM？→ 可解释性与工程可复现性优先，深度学习列入展望
5. 数据是分区级还是桩级？→ 官方清洗后为分区级 275 个，报告中已说明
6. 预测准不准？→ 给误差区间，不追求单点精度
7. 怎么部署的？→ Docker + 一键脚本，RUNBOOK 可复现
8. 各模块谁做的？→ 报告逐章署名

---

## 十二、数据来源与引用

> 本系统选用 UrbanEV 开放数据集作为研究数据源。该数据集由中山大学 Li Han 与香港理工大学 Qu Haohao 等人构建并公开发布（https://github.com/whewhewhenew/UrbanEV），原始数据取自深圳市 1,682 个公共充电站、24,798 个充电桩在 2022 年 9 月至 2023 年 2 月的逐小时运行记录，并经异常值检测与零值校验后清洗为 1,362 个充电站、17,532 个充电桩、275 个交通分区的数据集，采用 CC0 1.0 Universal 协议开放授权，相关研究成果发表于 arXiv:2309.05259。
>
> 选择该数据集的理由有三：其一，数据规模（275 分区 × 8760 小时的多指标时序记录）满足分布式计算对数据量的基本要求，使 Hadoop 与 Spark 生态组件的引入具有必要性；其二，数据同时包含充电占用率、充电时长、充电电量三类运行指标与电价、服务费、天气、时段四类动态影响因素，以及兴趣点、邻接关系等空间属性，为供需失衡分析、弹性分析等多维建模提供了充分特征；其三，数据来源于中国城市并以 CC0 协议开放，不存在版权与合规风险，便于结果复现。

**参考文献**
```
[1] Li H, Qu H, You L, et al. A physics-informed and attention-based graph learning
    approach for regional electric vehicle charging demand prediction. arXiv:2309.05259.
[2] Qu H, Kuang H, Li H, You L. ST-EVCDP: Spatio-temporal EV charging demand prediction.
    https://github.com/CMR0806/ST-EVCDP
```
