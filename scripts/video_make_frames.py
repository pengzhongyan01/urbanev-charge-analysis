# -*- coding: utf-8 -*-
"""
生成演示视频的全部画面帧
========================
★ 原则：画面里的每一张图都直接取自**仓库已有的成品图**，不另外绘制。
  图片来源优先级：
    1. C 岗（贺欢欢）交付的 10 张核心图表 + 6 个页面预览 —— `docs/C岗：图表-贺欢欢交付/`
    2. A/D/E 岗的架构图、图表、大屏截图 —— `docs/架构图`、`docs/charts`、`docs/screenshots`
  画面配色统一采用 C 岗的深色大屏风格（主色 #00d4ff / 强调 #ff6b35）。

运行：python scripts/video_make_frames.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from video_render import (  # noqa: E402
    OUT, ROOT, f_hei, f_msyh, render_bullets_page, render_code_page,
    render_cover, render_ending_page, render_formula_page, render_image_page,
    render_section_card, render_table_page, save,
)

MEMBERS = "彭忠燕 · 苏静 · 姬婷婷 · 杨姗姗 · 贺欢欢 · 彭忠燕（组长）"

# C 岗交付目录
CG = "docs/C岗：图表-贺欢欢交付"
CG_CHART = f"{CG}/C05_十个核心图表"
CG_PAGE = f"{CG}/C04_六个功能页面"


def main() -> None:
    frames: list[str] = []

    # ══ L01 封面 ══════════════════════════════════════════════════════
    save(render_cover(
        "城市充电桩数据分析系统",
        "基于 ETL 的 UrbanEV 数据智能分析系统的设计与实现",
        MEMBERS), "L01_cover.jpg")
    frames.append("L01_cover.jpg")

    # ══ L02 章节卡：系统总览 ═════════════════════════════════════════
    save(render_section_card("系统总览", "六阶段数据链路 · 四层数仓 · 16 个后端接口",
                              "第 02 组 · UrbanEV 充电桩数据分析"), "L02_sec_overview.jpg")
    frames.append("L02_sec_overview.jpg")

    # ── L03 项目整体技术架构 ─────────────────────────────────────────
    save(render_image_page(
        ["docs/架构图/项目架构.png"],
        "系统整体技术架构：六层分工与核心技术栈",
        caption="仓库图：docs/架构图/项目架构.png",
        annotations=[{
            "box": (0.03, 0.05, 0.72, 0.95),
            "label": "应用展示 6\n计算分析层 5\n数仓存储层 4\nETL 3\n数据源 2",
            "label_xy": (1430, 200),
            "arrow": ((0.755, 0.30), (0.72, 0.30)),
        }]), "L03_arch.jpg")
    frames.append("L03_arch.jpg")

    # ── L04 整体数据流向 ─────────────────────────────────────────────
    save(render_image_page(
        ["docs/架构图/数据流向.png"],
        "整体数据流向：数据准备 → 接入 → ETL → 分析 → 决策输出",
        caption="仓库图：docs/架构图/数据流向.png"), "L04_flow.jpg")
    frames.append("L04_flow.jpg")

    # ══ L05 章节卡：数据采集 ═════════════════════════════════════════
    save(render_section_card("数据采集", "Flume → Kafka → Sqoop → Hive 四层数仓",
                              "第 02 组 · UrbanEV 充电桩数据分析"), "L05_sec_collect.jpg")
    frames.append("L05_sec_collect.jpg")

    # ── L06 Flume 采集拓扑 ───────────────────────────────────────────
    save(render_image_page(
        ["docs/charts/08_Flume采集拓扑图.png"],
        "数据采集链路：Flume 12 通道增量采集拓扑",
        caption="仓库图：docs/charts/08_Flume采集拓扑图.png",
        annotations=[{
            "box": (0.30, 0.30, 0.62, 0.62),
            "label": "Flume 采集\n→ Kafka 削峰\n→ Sqoop 入 Hive",
            "label_xy": (1500, 380),
            "arrow": ((0.795, 0.46), (0.625, 0.46)),
        }]), "L06_flume.jpg")
    frames.append("L06_flume.jpg")

    # ── L07 四层数仓规模对比 ─────────────────────────────────────────
    save(render_image_page(
        ["docs/charts/06_四层数仓规模对比.png"],
        "四层数据仓库：ODS → DWD → DWS → ADS",
        caption="仓库图：docs/charts/06_四层数仓规模对比.png",
        annotations=[{
            "box": (0.55, 0.20, 0.98, 0.92),
            "label": "ADS 层直接服务\n前端 16 个接口",
            "label_xy": (1420, 250),
            "arrow": ((0.755, 0.42), (0.55, 0.42)),
        }]), "L07_dw.jpg")
    frames.append("L07_dw.jpg")

    # ── L08 数仓分层设计表 ───────────────────────────────────────────
    save(render_table_page(
        "数仓分层设计",
        ["层级", "粒度", "记录量", "作用"],
        [
            ["ODS", "原始指标 × 分区 × 小时", "12 张源表", "贴源存放，保留原始口径"],
            ["DWD", "分区 × 时间戳 × 指标", "长表，119 万行", "宽转长 + 8 条质量规则清洗"],
            ["DWS", "分区 × 日期 × 小时", "按周期汇总", "计算分区级派生指标"],
            ["ADS", "分区 / 分区×时段", "12 张结果表", "直接供接口与前端看板消费"],
        ],
        highlight_row=1,
        note="★ 高亮行为关键设计：宽表转长表是后续所有时空分析与 POI 空间连接的基础"), "L08_table.jpg")
    frames.append("L08_table.jpg")

    # ── L09 DWD 宽转长代码页（真实源码）──────────────────────────────
    save(render_code_page(
        "scripts/python_etl.py", 117, 133,
        annotations=[{
            "lines": (117, 123),
            "label": "宽转长入口\n字段严格对齐\nuev_dwd.zone_hour_metric",
            "anchor": "a",
        }],
        title="scripts/python_etl.py",
        subtitle="DWD 层 · 宽转长"), "L09_code_dwd.jpg")
    frames.append("L09_code_dwd.jpg")

    # ══ L10 章节卡：数据清洗 ═════════════════════════════════════════
    save(render_section_card("数据清洗", "宽转长 + 八条数据质量规则",
                              "核心环节：直接决定分析结论是否可信"), "L10_sec_clean.jpg")
    frames.append("L10_sec_clean.jpg")

    # ── L11 宽转长实现（真实源码）────────────────────────────────────
    save(render_code_page(
        "scripts/python_etl.py", 124, 138,
        annotations=[{
            "lines": (126, 129),
            "label": "行 = 分区\n列 = 时间\n→ 展开成长表",
            "anchor": "a",
        }],
        title="scripts/python_etl.py",
        subtitle="np.repeat / np.tile 构造长表"), "L11_code_long.jpg")
    frames.append("L11_code_long.jpg")

    # ── L12 质量规则：范围校验（真实源码）────────────────────────────
    save(render_code_page(
        "scripts/python_etl.py", 141, 157,
        annotations=[{
            "lines": (142, 150),
            "label": "按指标类型分别定义\n取值范围：占用率 ∈ [0,1]\n时长/电量/价格 ≥ 0",
            "anchor": "a",
        }, {
            "lines": (149, 149),
            "label": "先修复后丢弃\n避免脏值污染",
            "anchor": "a",
        }],
        title="scripts/python_etl.py",
        subtitle="数据质量规则 1–4：取值范围校验"), "L12_code_range.jpg")
    frames.append("L12_code_range.jpg")

    # ── L13 去重与零值标记（真实源码）────────────────────────────────
    save(render_code_page(
        "scripts/python_etl.py", 158, 169,
        annotations=[{
            "lines": (162, 165),
            "label": "同分区同时间同指标\n只保留首条",
            "anchor": "a",
        }],
        title="scripts/python_etl.py",
        subtitle="数据质量规则 5–8：去重 / 零值标记 / 时间戳校验"), "L13_code_dup.jpg")
    frames.append("L13_code_dup.jpg")

    # ── L14 数据质量实测（C 岗图 10）────────────────────────────────
    save(render_image_page(
        [f"{CG_CHART}/10_数据质量实测结果.png"],
        "数据质量 8 项体检：716.76 万行，越界/重复/空值均为 0",
        caption="C 岗贺欢欢交付：10_数据质量实测结果.png"), "L14_quality.jpg")
    frames.append("L14_quality.jpg")

    # ══ L15 章节卡：核心算法 ═════════════════════════════════════════
    save(render_section_card("核心算法", "供需失衡指数 · 电价弹性 · 四类分区画像",
                              "创新点一 / 创新点二 / 创新点三"), "L15_sec_algo.jpg")
    frames.append("L15_sec_algo.jpg")

    # ── L16 公式卡 ───────────────────────────────────────────────────
    save(render_formula_page(
        "创新点①　供需失衡指数（契约口径）",
        "I  =  D  -  S",
        [
            "D = 该分区充电需求占全市总需求的比例（需求份额）",
            "S = 该分区充电桩数占全市总桩数的比例（运力份额）",
            "采用份额差而非绝对差值，消除分区规模差异，公平可比",
        ],
        emphasis="I > 0 → 供不应求（需优先补点）　　I < 0 → 运力相对闲置",
        note="口径来源：docs/contracts/02-指标定义表.md　已由 scripts/verify_e_caliber.py 独立复算验证"),
        "L16_formula.jpg")
    frames.append("L16_formula.jpg")

    # ── L17 TOP-N 矩阵算法（真实源码）───────────────────────────────
    save(render_code_page(
        "scripts/python_etl.py", 319, 335,
        annotations=[{
            "lines": (320, 323),
            "label": "★ 矩阵上直接取 TOP-N\n避免 merge 键类型不一致\n膨胀到 3.2 亿行而 OOM",
            "anchor": "a",
        }, {
            "lines": (331, 333),
            "label": "argpartition 定位\nTOP 2000 扁平索引",
            "anchor": "a",
        }],
        title="scripts/python_etl.py",
        subtitle="创新点① 实现：imb_mat 矩阵上直接取 TOP-N"), "L17_code_topn.jpg")
    frames.append("L17_code_topn.jpg")

    # ── L18 失衡指数 TOP15（C 岗图 04）──────────────────────────────
    save(render_image_page(
        [f"{CG_CHART}/04_供需失衡指数_分区TOP15.png"],
        "创新点①　供需失衡指数 · 分区 TOP15（595 区峰值 0.1225）",
        caption="C 岗贺欢欢交付：04_供需失衡指数_分区TOP15.png"), "L18_imbalance.jpg")
    frames.append("L18_imbalance.jpg")

    # ── L19 分时/固定定价占用率对比（C 岗图 05）─────────────────────
    save(render_image_page(
        [f"{CG_CHART}/05_分时定价与固定定价充电桩占用率对比.png"],
        "创新点②　分时定价 vs 固定定价的占用率对比（34.4% vs 26.2%）",
        caption="C 岗贺欢欢交付：05_分时定价与固定定价充电桩占用率对比.png"), "L19_price.jpg")
    frames.append("L19_price.jpg")

    # ── L20 价差与占用率对照（C 岗图 06）────────────────────────────
    save(render_image_page(
        [f"{CG_CHART}/06_两类电价区的价差与占用率对照.png"],
        "创新点②　价差与占用率反向走 —— 价格弹性成立",
        caption="C 岗贺欢欢交付：06_两类电价区的价差与占用率对照.png"), "L20_elastic.jpg")
    frames.append("L20_elastic.jpg")

    # ── L21 四类分区画像：聚类散点 + 雷达 ───────────────────────────
    save(render_image_page(
        ["analysis/output/figs/06_聚类_散点.png", "analysis/output/figs/07_聚类_雷达.png"],
        "创新点③　7 维特征 KMeans 四类分区画像（k=4, seed=42）",
        caption="仓库图：analysis/output/figs/06、07",
        annotations=[{
            "box": (0.72, 0.06, 0.99, 0.30),
            "label": "紧张型 27 / 过剩型 128\n稳定型 79 / 潜力型 41",
            "label_xy": (1180, 400),
            "arrow": ((0.86, 0.42), (0.86, 0.32)),
        }]), "L21_cluster.jpg")
    frames.append("L21_cluster.jpg")

    # ── L22 需求预测曲线（C 岗图 07）────────────────────────────────
    save(render_image_page(
        [f"{CG_CHART}/07_需求预测曲线.png"],
        "创新点③　需求预测曲线（实际 vs 预测）",
        caption="C 岗贺欢欢交付：07_需求预测曲线.png"), "L22_forecast.jpg")
    frames.append("L22_forecast.jpg")

    # ── L23 预测误差分布（C 岗图 08）────────────────────────────────
    save(render_image_page(
        [f"{CG_CHART}/08_预测误差分布对比.png"],
        "创新点③　预测误差分布：中位 MAPE 9.9%，73% 样本低于 20%",
        caption="C 岗贺欢欢交付：08_预测误差分布对比.png"), "L23_error.jpg")
    frames.append("L23_error.jpg")

    # ── L24 布点建议优先级（C 岗图 09，契约口径）────────────────────
    save(render_image_page(
        [f"{CG_CHART}/09_布点建议优先级分布.png"],
        "创新点③　布点扩容建议：56 个分区需加桩，建议新增 93 个桩（+1.82%）",
        caption="C 岗贺欢欢交付：09_布点建议优先级分布.png"), "L24_expansion.jpg")
    frames.append("L24_expansion.jpg")

    # ══ L25 章节卡：后端服务 ═════════════════════════════════════════
    save(render_section_card("后端服务", "Spring Boot 3.2.5 + MyBatis + Redis",
                              "16 个接口，全部 Postman 实测通过"), "L25_sec_backend.jpg")
    frames.append("L25_sec_backend.jpg")

    # ── L26 缓存切面（真实源码）────────────────────────────────────
    save(render_code_page(
        "backend/src/main/java/com/uev/aspect/CacheAspect.java", 37, 65,
        annotations=[{
            "lines": (42, 51),
            "label": "① 先查缓存",
            "anchor": "a",
        }, {
            "lines": (53, 55),
            "label": "② 回源执行",
            "anchor": "a",
        }, {
            "lines": (57, 60),
            "label": "③ 回填缓存\n结果为空不缓存\n防止缓存穿透",
            "anchor": "a",
        }],
        title="aspect/CacheAspect.java",
        subtitle="AOP 缓存切面：读缓存 → 回源 → 写缓存"), "L26_code_cache.jpg")
    frames.append("L26_code_cache.jpg")

    # ── L27 缓存 key 设计（真实源码）────────────────────────────────
    save(render_code_page(
        "backend/src/main/java/com/uev/aspect/CacheAspect.java", 16, 30,
        annotations=[{
            "lines": (22, 24),
            "label": "QueryParams 含 5 个筛选字段\n→ 改筛选必换 key\n→ 不会拿到旧数据",
            "anchor": "a",
        }],
        title="aspect/CacheAspect.java",
        subtitle="缓存 key 设计：方法名 + 全部入参 MD5"), "L27_code_key.jpg")
    frames.append("L27_code_key.jpg")

    # ── L28 接口调用关系与缓存分层 ───────────────────────────────────
    save(render_image_page(
        ["docs/charts/09_接口调用关系与缓存分层图.png"],
        "后端 16 个接口的调用关系与缓存分层",
        caption="仓库图：docs/charts/09_接口调用关系与缓存分层图.png",
        annotations=[{
            "box": (0.27, 0.60, 0.75, 0.85),
            "label": "Redis 缓存层\n命中直接返回\n未命中查库回填",
            "label_xy": (1440, 560),
            "arrow": ((0.80, 0.72), (0.755, 0.72)),
        }]), "L28_apiarch.jpg")
    frames.append("L28_apiarch.jpg")

    # ── L29 接口清单表 ───────────────────────────────────────────────
    save(render_table_page(
        "后端接口清单（16 个 · 全部实测通过）",
        ["模块", "接口", "路径", "说明"],
        [
            ["认证", "登录 / 个人信息", "/api/auth/login · /me", "JWT 签发与校验"],
            ["看板", "核心 KPI / 分区列表 / 分区详情", "/api/dashboard/kpi · /zones", "首页大屏数据"],
            ["图表", "占用率 / 24 小时供需 / 失衡指数", "/api/chart/occupancy · hourly · imbalance", "六张分析图表"],
            ["图表", "电价弹性 / 需求预测", "/api/chart/price · forecast", "创新点②③"],
            ["建议", "扩容建议 / 电量偏差 / POI", "/api/suggestion/*", "布点决策支撑"],
            ["系统", "数据字典 / 缓存统计 / 健康检查", "/api/dict · /cache · /health", "可观测性"],
        ],
        note="证据：docs/screenshots/D10_postman/ 共 16 张 Postman 实测响应截图"), "L29_api.jpg")
    frames.append("L29_api.jpg")

    # ══ L30 章节卡：运行演示 ═════════════════════════════════════════
    save(render_section_card("运行演示", "可视化大屏 · 实时接口 · 缓存命中",
                              "以下均为真实运行结果"), "L30_sec_demo.jpg")
    frames.append("L30_sec_demo.jpg")

    # ── L31 首页总览（C 岗页面 P1）──────────────────────────────────
    save(render_image_page(
        [f"{CG_PAGE}/预览_P1_首页总览.png"],
        "首页总览：核心 KPI 一屏掌握",
        caption="C 岗贺欢欢交付：预览_P1_首页总览.png"), "L31_p1.jpg")
    frames.append("L31_p1.jpg")

    # ── L32 分区地图（C 岗页面 P2）──────────────────────────────────
    save(render_image_page(
        [f"{CG_PAGE}/预览_P2_分区地图.png"],
        "分区地图：275 个分区按失衡程度着色",
        caption="C 岗贺欢欢交付：预览_P2_分区地图.png"), "L32_p2.jpg")
    frames.append("L32_p2.jpg")

    # ── L33 供需分析（C 岗页面 P3）──────────────────────────────────
    save(render_image_page(
        [f"{CG_PAGE}/预览_P3_供需分析.png"],
        "供需分析：分区级失衡诊断与预测得分",
        caption="C 岗贺欢欢交付：预览_P3_供需分析.png"), "L33_p3.jpg")
    frames.append("L33_p3.jpg")

    # ── L34 电价误差（C 岗页面 P4）──────────────────────────────────
    save(render_image_page(
        [f"{CG_PAGE}/预览_P4_电价误差.png"],
        "电价与误差：TOU / FLAT 分组对照",
        caption="C 岗贺欢欢交付：预览_P4_电价误差.png"), "L34_p4.jpg")
    frames.append("L34_p4.jpg")

    # ── L35 需求预测（C 岗页面 P5）──────────────────────────────────
    save(render_image_page(
        [f"{CG_PAGE}/预览_P5_需求预测.png"],
        "需求预测：实际 vs 预测曲线对比",
        caption="C 岗贺欢欢交付：预览_P5_需求预测.png"), "L35_p5.jpg")
    frames.append("L35_p5.jpg")

    # ── L36 布点建议（C 岗页面 P6）──────────────────────────────────
    save(render_image_page(
        [f"{CG_PAGE}/预览_P6_布点建议.png"],
        "布点建议：扩容优先级与选址决策",
        caption="C 岗贺欢欢交付：预览_P6_布点建议.png"), "L36_p6.jpg")
    frames.append("L36_p6.jpg")

    # ── L37 Postman 实测 ────────────────────────────────────────────
    save(render_image_page(
        ["docs/screenshots/D10_postman/实测响应_09_imbalance.png",
         "docs/screenshots/D10_postman/实测响应_16_cache_stats.png"],
        "Postman 实测：失衡接口响应 与 缓存统计（hitRate 0.333，speedUp 2667ms）",
        caption="仓库图：docs/screenshots/D10_postman/"), "L37_postman.jpg")
    frames.append("L37_postman.jpg")

    # ══ L38 章节卡：总结 ═════════════════════════════════════════════
    save(render_section_card("总结", "四层数仓 · 口径可验证 · 创新算法",
                              "感谢老师观看"), "L38_sec_end.jpg")
    frames.append("L38_sec_end.jpg")

    # ── L39 要点页 ──────────────────────────────────────────────────
    save(render_bullets_page(
        "项目工作小结",
        [
            ("完整四层数据仓库", "ODS → DWD → DWS → ADS 全链路落地，宽转长 + 8 条质量规则清洗"),
            ("指标口径有契约、有独立复算", "docs/contracts/02 指标定义表 + scripts/verify_e_caliber.py 独立复算，可交叉验证"),
            ("供需失衡指数 + 七维聚类选址模型", "I = D − S 份额差口径，7 维特征 KMeans（k=4, seed=42），275 分区分四类"),
            ("Spring Boot 16 接口 + 缓存加速", "AOP 缓存切面 + Redis，16 个接口全部 Postman 实测通过并留档截图"),
        ],
        footer="数据窗口 2022-09 ~ 2023-02（UrbanEV 论文发表时最新可用窗口，含价格维度）"),
        "L39_bullets.jpg")
    frames.append("L39_bullets.jpg")

    # ── L40 结尾页 ──────────────────────────────────────────────────
    save(render_ending_page(
        "谢谢观看",
        "基于 ETL 的城市充电桩数据分析系统的设计与实现",
        ["第 02 组 · Java Web 后端开发技术",
         "彭忠燕 · 苏静 · 姬婷婷 · 杨姗姗 · 贺欢欢",
         "欢迎老师提问"]), "L40_end.jpg")
    frames.append("L40_end.jpg")

    print(f"✓ 生成 {len(frames)} 帧 → {OUT}")
    for f in frames:
        print("  ", f)


if __name__ == "__main__":
    main()
