#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A06 · 系统架构图 + 数据流向图 生成器
用法：python scripts/generate_arch_diagrams.py
产物：docs/架构图/项目架构.png     （6 层带编号横带图 + 右侧技术栈栏）
      docs/架构图/数据流向.png     （6 阶段竖向泳道图 + 判定分支）
版式照抄参考作业 07.数据流向架构图/ 的结构与信息密度
"""
import os, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon, Rectangle
from matplotlib import font_manager

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "docs" / "架构图"
OUT.mkdir(parents=True, exist_ok=True)

# ── 中文字体 ─────────────────────────────
# 必须用 font.sans-serif 列表形式：单字体名时粗体字重回退会丢字符
_FONTS = ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc",
          "C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/Deng.ttf"]
_NAMES = []
for _f in _FONTS:
    if os.path.exists(_f):
        font_manager.fontManager.addfont(_f)
        _n = font_manager.FontProperties(fname=_f).get_name()
        if _n not in _NAMES:
            _NAMES.append(_n)
if not _NAMES:
    sys.exit("找不到中文字体")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = _NAMES + ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
FONT = _NAMES[0]

DPI = 150
INK = "#1A1C22"
MUT = "#6B6A64"

# ── 配色 ─────────────────────────────
L1 = "#16324F"; L2 = "#C87A0A"; L3 = "#C2410C"
L4 = "#0E7C6B"; L5 = "#1D4ED8"; L6 = "#5B3FA8"
PANEL_BG = "#F4F1EA"
SUB_BG = "#FFFFFF"


def rbox(ax, x, y, w, h, fc, ec, lw=1.2, r=0.008, alpha=1.0, z=2):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                       fc=fc, ec=ec, lw=lw, alpha=alpha, zorder=z)
    ax.add_patch(p)
    return p


def txt(ax, x, y, s, size=8, color=INK, weight="normal", ha="center",
        va="center", z=5, lh=1.45):
    ax.text(x, y, s, fontsize=size, color=color, fontweight=weight,
            ha=ha, va=va, zorder=z, linespacing=lh)


# ══════════════════════════════════════════════════════════════
#  图一 · 项目架构（6 层横带 + 右侧两栏）
# ══════════════════════════════════════════════════════════════
def build_arch():
    fig = plt.figure(figsize=(16, 9), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    txt(ax, 0.5, 0.975, "基于 Hadoop 与 Spring Boot 的城市充电桩数据分析系统技术架构",
        size=19, weight="bold")
    txt(ax, 0.5, 0.947, "《基于 Hadoop 与 Spring Boot 的城市充电桩使用行为分析与充电需求预测系统的设计与实现》　·　2405 班 · 第 02 组",
        size=9, color=MUT)

    # ── 右侧两栏 ──
    RX, RW = 0.728, 0.267
    # 核心技术栈
    rbox(ax, RX, 0.395, RW, 0.545, PANEL_BG, "#C9C4B8", 1.4, r=0.006, z=1)
    txt(ax, RX + RW/2, 0.918, "核心技术栈", size=11, weight="bold")
    stack = [
        ("编程语言", ["Java 17（后端）", "Python 3.13（分析）", "SQL（Hive / MySQL）", "JavaScript ES6（前端）"]),
        ("数据库 / 存储", ["MySQL 8.0（应用库）", "Hive 3.x（四层数仓）", "Redis 7.x（缓存）", "HDFS 3.3（原始数据）"]),
        ("核心第三方库", ["Spring Boot 3.2.5", "MyBatis-Plus 3.1.3", "ECharts 5.x", "Apache Spark 3.5（SQL / MLlib）", "Apache Flume 1.11", "Apache Sqoop 1.4.7", "Pandas / NumPy"]),
        ("外部服务", ["UrbanEV 开源数据集（CC0）", "GitHub 代码托管", "Maven 中央仓库"]),
    ]
    sy = 0.884
    for gname, items in stack:
        txt(ax, RX + 0.012, sy, gname, size=8.5, weight="bold", ha="left", va="top")
        sy -= 0.0255
        for it in items:
            txt(ax, RX + 0.022, sy, "·  " + it, size=7.6, color="#3A3A38", ha="left", va="top")
            sy -= 0.0192
        sy -= 0.006
    # 核心特色技术
    rbox(ax, RX, 0.030, RW, 0.350, PANEL_BG, "#C9C4B8", 1.4, r=0.006, z=1)
    txt(ax, RX + RW/2, 0.358, "核心特色技术", size=11, weight="bold")
    feats = [
        "契约驱动的协作机制（契约即交接物）",
        "Hive 四层数仓 + 宽转长 ETL 方案",
        "归一化的供需失衡指数（消除规模差异）",
        "基于价格时序的分时电价引导量化",
        "三模型横向竞优的统计预测方案",
        "Spark MLlib 分区聚类画像发现",
        "Docker 一键复现部署与冒烟测试",
    ]
    fy = 0.322
    for f in feats:
        txt(ax, RX + 0.016, fy, "√", size=9.5, color="#1E8A5F", weight="bold", ha="left")
        txt(ax, RX + 0.036, fy, f, size=7.9, color="#2C2C2A", ha="left")
        fy -= 0.0390

    # ── 六层 ──
    LAYERS = [
        (6, L6, "应用展示层", "（成果输出与交互）", 0.930, 0.140, "SHOW"),
        (5, L5, "计算分析层", "（创新算法与指标）", 0.778, 0.140, "ANALYZE"),
        (4, L4, "数据仓库层", "（Hive 四层 + MySQL）", 0.626, 0.140, "WAREHOUSE"),
        (3, L3, "ETL 数据处理层", "（采集-清洗-转换-装载）", 0.474, 0.140, "ETL"),
        (2, L2, "数据源层", "（多结构数据源）", 0.322, 0.140, "SOURCE"),
        (1, L1, "公共支撑层", "（全局基础支撑）", 0.170, 0.140, "BASE"),
    ]
    MX, MW = 0.098, 0.612          # 主区
    NUMW = 0.078                  # 编号块宽

    # 每层的子块内容
    CONTENT = {
        "SHOW": [
            ("ECharts 5 大屏（原生 JS）", ["分区需求热力图", "24h 供需曲线", "失衡指数 TOP10", "预测曲线 + 置信带"], L6),
            ("Spring Boot 服务端渲染", ["首页 KPI 指标卡", "电价弹性双曲线", "聚类结果着色地图", "布点建议看板"], L5),
            ("决策成果输出", ["分区诊断报告", "布点扩容建议清单", "Excel 明细导出", "演示视频 / 答辩大屏"], L4),
        ],
        "ANALYZE": [
            ("Spark SQL 指标计算", ["需求强度归一化 D(z,t)", "峰谷差 / 波动率", "POI 与桩密度", "7 日滚动均值"], L5),
            ("★ 四个创新指标", ["① 供需失衡指数 I=D−D均值", "② 分时电价弹性（σ 反推）", "③ 需求预测（MAPE/基线）", "④ 聚类画像 KMeans k=4"], L6),
            ("探索性分析（pandas）", ["三模型横向竞优", "MAE / RMSE / 误差区间", "数据指纹与模型持久化", "布点建议规则生成"], L4),
        ],
        "WAREHOUSE": [
            ("Hive 四层数仓", ["ODS 贴源宽表 276 列", "DWD 长表 + 维度 + 质检", "DWS 分区×日×时汇总", "ADS 7 张应用表"], L4),
            ("MySQL 应用库 uev_charge", ["ads_* 7 张（B · Sqoop）", "insight_* 5 张（E · 直插）", "sys_* 3 张（D）", "v_* 4 视图（B 建 D 读）"], L5),
            ("质量与一致性", ["8 类数据质量规则", "脏行带因子隔离表", "清洗前后对比表", "MySQL vs Hive 一致性校验"], L3),
        ],
        "ETL": [
            ("① Flume 采集（增量）", ["taildir 监听 12 个 CSV", "写入 HDFS /uev/raw/", "断点续传 + 校验和"], L3),
            ("② MapReduce 清洗", ["WideToLong 宽转长", "DataQualityCheck 质检", "PoiZoneJoin 空间连接", "先修复后丢弃，逐条记因"], L3),
            ("③ Spark 转换", ["ADS 层指标计算", "空间聚合与邻接展开", "KMeans 聚类计算", "Spark SQL 数十行替代 MR 数百行"], L5),
            ("④ Sqoop 装载", ["export 到 MySQL", "增量 checkpoint 水位", "行数校验与日志"], L3),
        ],
        "SOURCE": [
            ("UrbanEV 数据集（CC0 1.0）", ["6 个时序宽表", "4344 小时 × 275 分区", "inf 分区维表 275 行", "poi 兴趣点 71 万条", "adj / distance / weather 维表"], L2),
            ("数据获取与校验", ["GitHub 直链下载（重试+镜像）", "SHA256 校验 36 项", "find_data.sh 自动探测", "数据绝不进 Git"], L2),
        ],
        "BASE": [
            ("开发环境", ["JDK 17 / Maven 3.9", "Docker Desktop", "IDEA / VS Code", "Python 3.13 / Node 22"], L1),
            ("配置与安全", ["application.yml 分层配置", "密码环境变量注入", "JWT 鉴权与角色", "参数化查询防注入"], L1),
            ("运行与监控", ["Logback 日志", "Actuator 健康检查", "冒烟测试 7 项", "一键 start_all.sh"], L1),
            ("协作与质量", ["Git 分支模型", "契约驱动 + CHANGELOG", "提交记录带岗位标签", "交付物自动验收"], L1),
        ],
    }

    for num, color, name, sub, ytop, hh, key in LAYERS:
        # 编号块
        rbox(ax, 0.010, ytop - hh, NUMW, hh, color, color, 0, r=0.004, z=3)
        txt(ax, 0.010 + NUMW/2, ytop - hh*0.70, str(num), size=20, color="#FFFFFF", weight="bold")
        txt(ax, 0.010 + NUMW/2, ytop - hh*0.44, name, size=9.2, color="#FFFFFF", weight="bold")
        txt(ax, 0.010 + NUMW/2, ytop - hh*0.28, sub, size=6.8, color="#E8E6E1")
        # 层框
        rbox(ax, MX, ytop - hh, MW, hh, "#FFFFFF", color, 1.6, r=0.004, z=1)
        rbox(ax, MX, ytop - hh, MW, hh, color, color, 0, r=0.004, alpha=0.045, z=2)
        # 子块
        blocks = CONTENT[key]
        gap = 0.008
        inner_x = MX + 0.006
        inner_w = MW - 0.012
        bw = (inner_w - gap*(len(blocks)-1)) / len(blocks)
        for i, (btitle, items, bc) in enumerate(blocks):
            bx = inner_x + i*(bw+gap)
            rbox(ax, bx, ytop - hh + 0.007, bw, hh - 0.014, SUB_BG, bc, 1.1, r=0.004, z=3)
            rbox(ax, bx, ytop - hh + hh - 0.030, bw, 0.023, bc, bc, 0, r=0.004, alpha=0.16, z=4)
            txt(ax, bx + bw/2, ytop - hh + hh - 0.0185, btitle, size=8.2, weight="bold", color=bc, z=6)
            iy = ytop - hh + hh - 0.038
            for it in items:
                txt(ax, bx + 0.008, iy, "· " + it, size=7.0, color="#333331", ha="left", va="top", z=6)
                iy -= 0.0185
        # 层间箭头
        if num > 1:
            ax.add_patch(FancyArrowPatch((MX+0.030, ytop+0.0015), (MX+0.030, ytop+0.0115),
                                         arrowstyle="-|>", mutation_scale=11,
                                         color="#5F5E5A", lw=1.3, zorder=6))

    fig.savefig(OUT / "项目架构.png", dpi=DPI, facecolor="white")
    plt.close(fig)
    print("  ✓ 项目架构.png")


# ══════════════════════════════════════════════════════════════
#  图二 · 数据流向（6 阶段泳道 + 判定分支）
# ══════════════════════════════════════════════════════════════
def build_flow():
    fig = plt.figure(figsize=(13.5, 16), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    txt(ax, 0.5, 0.978, "城市充电桩数据分析系统 · 整体数据流向图",
        size=19, weight="bold")
    txt(ax, 0.5, 0.960, "数据获取 → 接入 → 清洗 → 建模 → 分析 → 服务 → 决策　　★ 黄色菱形为判定分支",
        size=9.5, color=MUT)

    X0, X1 = 0.045, 0.980
    SPAN = X1 - X0
    GAP = 0.007

    # ── 阶段定义：tag, name, color, 色带顶, 色带高, 排布 ──
    PH = [
        ("阶段 0", "数据准备", "#C87A0A", 0.945, 0.075, 1),
        ("阶段 1", "数据接入", "#2E7D32", 0.856, 0.074, 1),
        ("阶段 2", "ETL 处理与入库", "#C2410C", 0.768, 0.156, 2),
        ("阶段 3", "数据分析", "#1D4ED8", 0.598, 0.156, 2),
        ("阶段 4", "核心功能模块", "#5B3FA8", 0.428, 0.156, 2),
        ("阶段 5", "决策输出与应用", "#0E7C6B", 0.258, 0.158, 2),
    ]

    def box(x, y, w, h, title, lines, color, fs=7.3, ts=8.0):
        rbox(ax, x, y, w, h, "#FFFFFF", color, 1.3, r=0.005, z=3)
        rbox(ax, x, y + h - 0.015, w, 0.015, color, color, 0, r=0.005, alpha=0.18, z=4)
        txt(ax, x + w/2, y + h - 0.0075, title, size=ts, weight="bold", color=color, z=6)
        iy = y + h - 0.0205
        for ln in lines:
            txt(ax, x + 0.006, iy, "· " + ln, size=fs, color="#333331", ha="left", va="top", z=6)
            iy -= 0.0098

    def dia(x, y, w, h, label, color="#D97706"):
        pts = [(x, y+h/2), (x+w/2, y+h), (x+w, y+h/2), (x+w/2, y)]
        ax.add_patch(Polygon(pts, closed=True, fc="#FEF3C7", ec=color, lw=1.4, zorder=4))
        txt(ax, x+w/2, y+h/2, label, size=7.2, color="#92400E", weight="bold", z=6, lh=1.25)

    def arrow(x1, y1, x2, y2, label=None, color="#5F5E5A", rad=0.0, ls="-", lx=0.012):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                     mutation_scale=12, color=color, lw=1.4,
                                     connectionstyle=f"arc3,rad={rad}",
                                     linestyle=ls, zorder=7))
        if label:
            txt(ax, (x1+x2)/2 + lx, (y1+y2)/2, label, size=7.0, color="#92400E", ha="left", z=8)

    def row(ytop, idx, items, h=0.042, n_rows=1):
        """在阶段内放一排方框，返回 (y, 各框 x 列表)"""
        y = ytop - 0.026 - h - (idx * (h + 0.006))
        n = len(items)
        w = (SPAN - GAP*(n-1)) / n
        xs = []
        for i, (t, lines, c) in enumerate(items):
            bx = X0 + i*(w+GAP)
            box(bx, y, w, h, t, lines, c)
            xs.append((bx, w))
        return y, xs

    # ── 阶段 0 数据准备 ──
    ytop = PH[0][3]
    rbox(ax, X0-0.010, ytop-PH[0][4], SPAN+0.020, PH[0][4], PH[0][2], PH[0][2], 0, r=0.005, alpha=0.07, z=1)
    txt(ax, X0, ytop-0.017, "阶段 0　数据准备", size=10.5, weight="bold", color=PH[0][2], ha="left")
    y0, xs0 = row(ytop, 0, [
        ("UrbanEV 数据集获取", ["GitHub 直链下载 12 个 CSV", "CC0 协议 · 129MB · 不进 Git"], "#C87A0A"),
        ("SHA256 完整性校验", ["36 项校验", "通过 36 失败 0"], "#C87A0A"),
        ("结构解析与形态确认", ["宽表：time + 275 分区列", "4344 小时 · 181 天"], "#C87A0A"),
        ("维表关联键整理", ["inf 行序 ≠ 时序表列序", "四处 zone_id 强制对齐"], "#C87A0A"),
        ("分区与桩数核对", ["275 分区", "23,441 桩"], "#C87A0A"),
    ])
    for i in range(4):
        arrow(xs0[i][0]+xs0[i][1], y0+0.021, xs0[i+1][0], y0+0.021)

    # ── 阶段 1 数据接入 ──
    ytop = PH[1][3]
    rbox(ax, X0-0.010, ytop-PH[1][4], SPAN+0.020, PH[1][4], PH[1][2], PH[1][2], 0, r=0.005, alpha=0.07, z=1)
    txt(ax, X0, ytop-0.017, "阶段 1　数据接入", size=10.5, weight="bold", color=PH[1][2], ha="left")
    y1, xs1 = row(ytop, 0, [
        ("Flume taildir 增量采集", ["监听 12 个 CSV 变化", "断点续传 + checksum"], "#2E7D32"),
        ("HDFS 落地", ["/uev/raw/ 目录", "hdfs dfs -ls 校验"], "#2E7D32"),
        ("Hive ODS 贴源建表", ["SerDe 自动建表 276 列", "COUNT(*) = 4344"], "#2E7D32"),
        ("原始数据可回溯", ["ODS 保真", "任何环节可重放"], "#2E7D32"),
    ])
    for i in range(3):
        arrow(xs1[i][0]+xs1[i][1], y1+0.021, xs1[i+1][0], y1+0.021)
    arrow(xs0[0][0]+xs0[0][1]/2, y0, xs1[0][0]+xs1[0][1]/2, y1+0.042, color="#92400E")

    # ── 阶段 2 ETL ──
    ytop = PH[2][3]
    rbox(ax, X0-0.010, ytop-PH[2][4], SPAN+0.020, PH[2][4], PH[2][2], PH[2][2], 0, r=0.005, alpha=0.07, z=1)
    txt(ax, X0, ytop-0.017, "阶段 2　ETL 处理与入库", size=10.5, weight="bold", color=PH[2][2], ha="left")
    y2a, xa = row(ytop, 0, [
        ("MR · WideToLong 宽转长", ["stack() 炸成长表", "zone×hour×metric×value"], "#C2410C"),
        ("MR · DataQualityCheck", ["8 类异常逐条判定", "先修复后丢弃，记脏因子"], "#C2410C"),
        ("MR · PoiZoneJoin", ["71 万 POI 空间连接", "Haversine 最近分区"], "#C2410C"),
        ("DWD 行数校验", ["DWD < ODS", "证明清洗生效"], "#C2410C"),
        ("脏行隔离表", ["dq_zone_stat", "可追溯丢弃原因"], "#C2410C"),
    ])
    y2b, xb = row(ytop, 1, [
        ("Hive DWS 轻汇总", ["分区×日×时聚合", "7 日滚动均值 / 峰谷差"], "#C2410C"),
        ("Hive ADS 应用表", ["7 张 ADS，一表一图表", "Spark SQL 计算"], "#C2410C"),
        ("Sqoop export", ["导出 MySQL uev_charge", "ads_* 7 张"], "#C2410C"),
        ("MySQL 视图层", ["v_* 4 张视图", "ads + insight 联查"], "#C2410C"),
        ("增量 checkpoint", ["水位推进", "跳过已导出行"], "#C2410C"),
    ])
    for i in range(4):
        arrow(xa[i][0]+xa[i][1], y2a+0.021, xa[i+1][0], y2a+0.021)
        arrow(xb[i][0]+xb[i][1], y2b+0.021, xb[i+1][0], y2b+0.021)
    for i in range(5):
        arrow(xa[i][0]+xa[i][1]/2, y2a, xb[i][0]+xb[i][1]/2, y2b+0.042, color="#92400E")
    dia(X0+0.640, y2b-0.034, 0.150, 0.030, "DWD < ODS ？")
    arrow(xa[3][0]+xa[3][1]/2, y2a, X0+0.715, y2b-0.004, color="#D97706", rad=0.0)
    arrow(xs1[0][0]+xs1[0][1]/2, y1, X0+0.140, y2a+0.042, color="#92400E")

    # ── 阶段 3 数据分析 ──
    ytop = PH[3][3]
    rbox(ax, X0-0.010, ytop-PH[3][4], SPAN+0.020, PH[3][4], PH[3][2], PH[3][2], 0, r=0.005, alpha=0.07, z=1)
    txt(ax, X0, ytop-0.017, "阶段 3　数据分析", size=10.5, weight="bold", color=PH[3][2], ha="left")
    y3a, xc = row(ytop, 0, [
        ("E · pandas 直算", ["6 时序表 + inf", "与 B 并行，不被阻塞"], "#1D4ED8"),
        ("指标 M1–M12", ["需求强度 / 占用率", "峰谷差 / 波动率 / POI"], "#1D4ED8"),
        ("★ 创新点 ① ②", ["① 失衡指数 D−D均值", "② 电价弹性 σ 反推"], "#1D4ED8"),
        ("★ 创新点 ③ 预测", ["三模型横向竞优", "MAPE / MAE / RMSE + 基线"], "#1D4ED8"),
        ("★ 创新点 ④ 聚类", ["KMeans k=4", "肘部法选 k"], "#1D4ED8"),
    ])
    y3b, xd = row(ytop, 1, [
        ("模型持久化", ["参数 + 数据指纹", "数据未变不重算"], "#1D4ED8"),
        ("布点扩容建议", ["规则表 + 前 10 条", "优先级 + 文字理由"], "#1D4ED8"),
        ("insight_* 入库", ["E 用 pymysql 直插", "5 张洞察表"], "#1D4ED8"),
        ("一致性校验（报告 6.3）", ["MySQL 查询值 ≡ Hive 直查值 —— 两边口径必须完全一致"], "#1D4ED8"),
    ])
    for i in range(4):
        arrow(xc[i][0]+xc[i][1], y3a+0.021, xc[i+1][0], y3a+0.021)
    arrow(xc[0][0]+xc[0][1]/2, y3a, xd[0][0]+xd[0][1]/2, y3b+0.042, color="#92400E")
    arrow(xc[2][0]+xc[2][1]/2, y3a, xd[2][0]+xd[2][1]/2, y3b+0.042, color="#92400E")
    arrow(xc[3][0]+xc[3][1]/2, y3a, xd[3][0]+xd[3][1]/2, y3b+0.042, color="#92400E")
    dia(X0+0.300, y3b-0.034, 0.155, 0.030, "σ 能否分成两组？")
    arrow(xc[2][0]+xc[2][1]/2, y3a, X0+0.377, y3b-0.004, color="#D97706")
    arrow(xb[0][0]+xb[0][1]/2, y2b, xc[0][0]+xc[0][1]/2, y3a+0.042, color="#92400E")

    # ── 阶段 4 核心功能模块 ──
    ytop = PH[4][3]
    rbox(ax, X0-0.010, ytop-PH[4][4], SPAN+0.020, PH[4][4], PH[4][2], PH[4][2], 0, r=0.005, alpha=0.07, z=1)
    txt(ax, X0, ytop-0.017, "阶段 4　核心功能模块", size=10.5, weight="bold", color=PH[4][2], ha="left")
    y4a, xe = row(ytop, 0, [
        ("MySQL uev_charge", ["ads_* 7 + insight_* 5", "+ sys_* 3 + v_* 4 共 19 张"], "#5B3FA8"),
        ("Spring Boot 服务层", ["16 个 REST API", "DTO / Entity 分层"], "#5B3FA8"),
        ("Redis 缓存", ["首页聚合缓存 + TTL", "数据更新即失效"], "#5B3FA8"),
        ("ECharts 渲染", ["10 张图 / 7 种图形", "6 个功能页面"], "#5B3FA8"),
        ("筛选与导出", ["多条件联动", "Excel 导出"], "#5B3FA8"),
    ])
    y4b, xf = row(ytop, 1, [
        ("JWT 鉴权与角色", ["管理员 / 运营人员", "参数化查询防注入"], "#5B3FA8"),
        ("缓存命中策略", ["命中 → 直接返回　　未命中 → 查库并回填（记录命中率）"], "#5B3FA8"),
        ("异常降级", ["参数非法返回友好提示", "不抛 500"], "#5B3FA8"),
    ])
    for i in range(4):
        arrow(xe[i][0]+xe[i][1], y4a+0.021, xe[i+1][0], y4a+0.021)
    arrow(xe[0][0]+xe[0][1]/2, y4a, xf[0][0]+xf[0][1]/2, y4b+0.042, color="#92400E")
    arrow(xe[2][0]+xe[2][1]/2, y4a, xf[1][0]+xf[1][1]/2, y4b+0.042, color="#92400E")
    dia(X0+0.360, y4b-0.034, 0.160, 0.030, "接口返回有数据？")
    arrow(xe[1][0]+xe[1][1]/2, y4a, X0+0.440, y4b-0.004, color="#D97706")
    arrow(xc[2][0]+xc[2][1]/2, y3b, xe[0][0]+xe[0][1]/2, y4a+0.042, color="#92400E")

    # ── 阶段 5 决策输出与应用 ──
    ytop = PH[5][3]
    rbox(ax, X0-0.010, ytop-PH[5][4], SPAN+0.020, PH[5][4], PH[5][2], PH[5][2], 0, r=0.005, alpha=0.07, z=1)
    txt(ax, X0, ytop-0.017, "阶段 5　决策输出与应用", size=10.5, weight="bold", color=PH[5][2], ha="left")
    y5a, xg = row(ytop, 0, [
        ("首页运营大屏", ["5 个 KPI 指标卡", "275 分区着色地图", "分区诊断视图"], "#0E7C6B"),
        ("布点扩容决策", ["分区清单 + 建议数量", "优先级 + 预期效果", "CSV / Excel 导出"], "#0E7C6B"),
        ("运营策略结论", ["紧张型 → 优先扩容", "过剩型 → 调度引流", "潜力型 → 提前布局"], "#0E7C6B"),
        ("报告与答辩成果", ["七章报告 · 15 页 PPT", "RUNBOOK 一键复现", "实验报告与个人贡献"], "#0E7C6B"),
    ])
    y5b, xh = row(ytop, 1, [
        ("★ 端到端可复现：GitHub 拉代码 → download_data.sh 取数 → start_all.sh 一键起栈 → smoke_test.sh 体检 → 打开看板",
         ["他人无需 129MB 原始数据，亦可用 restore_from_mysql.sh + rebuild_ads.sh 重建 ADS 层"], "#0E7C6B"),
    ])
    for i in range(3):
        arrow(xg[i][0]+xg[i][1], y5a+0.021, xg[i+1][0], y5a+0.021)
    arrow(xf[0][0]+xf[0][1]/2, y4b, xg[0][0]+xg[0][1]/2, y5a+0.042, color="#92400E")
    arrow(xg[2][0]+xg[2][1]/2, y5a, xh[0][0]+xh[0][1]/2, y5b+0.042, color="#92400E")

    # 页脚
    txt(ax, 0.5, 0.055, "★ 全链路唯一出口：MySQL uev_charge　　两条路径并行 —— B 的离线数仓管道（ads_*）与 E 的探索性分析（insight_*）在此汇合，由 B 建的 4 张视图联结，D 的接口只读视图",
        size=9.5, color="#5F5E5A")

    fig.savefig(OUT / "数据流向.png", dpi=DPI, facecolor="white")
    plt.close(fig)
    print("  ✓ 数据流向.png")


if __name__ == "__main__":
    print("生成架构图 ...")
    build_arch()
    build_flow()
    print(f"输出目录：{OUT}")
