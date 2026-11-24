# -*- coding: utf-8 -*-
"""
生成演示视频的全部画面帧（28 个镜头）
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


def main() -> None:
    frames: list[str] = []

    # ── L01 封面 ────────────────────────────────────────────────────────
    save(render_cover(
        "城市充电桩数据分析系统",
        "基于 ETL 的 UrbanEV 数据智能分析系统的设计与实现",
        MEMBERS), "L01_cover.jpg")
    frames.append("L01_cover.jpg")

    # ── L02 章节卡：数据采集 ───────────────────────────────────────────
    save(render_section_card("数据采集", "Flume → Kafka → Sqoop → Hive 四层数仓",
                              "第 02 组 · UrbanEV 充电桩数据分析"), "L02_sec_collect.jpg")
    frames.append("L02_sec_collect.jpg")

    # ── L03 Flume 采集拓扑 ─────────────────────────────────────────────
    save(render_image_page(
        ["docs/charts/08_Flume采集拓扑图.png"],
        "数据采集链路：Flume → Kafka → Sqoop → Hive",
        caption="来源：docs/charts/08_Flume采集拓扑图.png",
        annotations=[{
            "box": (0.30, 0.30, 0.62, 0.62),
            "label": "Flume 采集\n→ Kafka 削峰\n→ Sqoop 入 Hive",
            "label_xy": (1500, 380),
            "arrow": ((0.795, 0.46), (0.625, 0.46)),
        }]), "L03_flume.jpg")
    frames.append("L03_flume.jpg")

    # ── L04 四层数仓 ────────────────────────────────────────────────────
    save(render_image_page(
        ["docs/charts/06_四层数仓规模对比.png"],
        "四层数据仓库：ODS → DWD → DWS → ADS",
        caption="来源：docs/charts/06_四层数仓规模对比.png",
        annotations=[{
            "box": (0.55, 0.20, 0.98, 0.92),
            "label": "ADS 层直接服务\n前端 16 个接口",
            "label_xy": (1420, 250),
            "arrow": ((0.755, 0.42), (0.55, 0.42)),
        }]), "L04_dw.jpg")
    frames.append("L04_dw.jpg")

    # ── L05 四层表格 ────────────────────────────────────────────────────
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
        note="★ 高亮行为关键设计：宽表转长表是后续所有时空分析与 POI 空间连接的基础"), "L05_table.jpg")
    frames.append("L05_table.jpg")

    # ── L06 DWD 宽转长代码页 ───────────────────────────────────────────
    save(render_code_page(
        "scripts/python_etl.py", 117, 133,
        annotations=[{
            "lines": (117, 123),
            "label": "宽转长入口\n字段严格对齐\nuev_dwd.zone_hour_metric",
            "anchor": "a",
        }],
        title="scripts/python_etl.py",
        subtitle="DWD 层 · 宽转长"), "L06_code_dwd.jpg")
    frames.append("L06_code_dwd.jpg")

    # ── L07 章节卡：数据清洗 ───────────────────────────────────────────
    save(render_section_card("数据清洗", "宽转长 + 八条数据质量规则",
                              "核心环节：直接决定分析结论是否可信"), "L07_sec_clean.jpg")
    frames.append("L07_sec_clean.jpg")

    # ── L08 宽转长实现 ─────────────────────────────────────────────────
    save(render_code_page(
        "scripts/python_etl.py", 124, 138,
        annotations=[{
            "lines": (126, 129),
            "label": "行 = 分区\n列 = 时间\n→ 展开成长表",
            "anchor": "a",
        }],
        title="scripts/python_etl.py",
        subtitle="np.repeat / np.tile 构造长表"), "L08_code_long.jpg")
    frames.append("L08_code_long.jpg")

    # ── L09 质量规则：范围校验 ─────────────────────────────────────────
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
        subtitle="数据质量规则 1–4：取值范围校验"), "L09_code_range.jpg")
    frames.append("L09_code_range.jpg")

    # ── L10 去重与零值标记 ─────────────────────────────────────────────
    save(render_code_page(
        "scripts/python_etl.py", 158, 169,
        annotations=[{
            "lines": (162, 165),
            "label": "同分区同时间同指标\n只保留首条",
            "anchor": "a",
        }],
        title="scripts/python_etl.py",
        subtitle="数据质量规则 5–8：去重 / 零值标记 / 时间戳校验"), "L10_code_dup.jpg")
    frames.append("L10_code_dup.jpg")

    # ── L11 数据质量实测 ───────────────────────────────────────────────
    save(render_image_page(
        ["docs/charts/10_数据质量实测结果.png"],
        "数据质量实测结果",
        caption="来源：docs/charts/10_数据质量实测结果.png"), "L11_quality.jpg")
    frames.append("L11_quality.jpg")

    # ── L12 章节卡：核心算法 ───────────────────────────────────────────
    save(render_section_card("核心算法", "供需失衡指数 · 电价弹性 · 七维聚类",
                              "创新点一 / 创新点二 / 创新点三"), "L12_sec_algo.jpg")
    frames.append("L12_sec_algo.jpg")

    # ── L13 公式卡 ─────────────────────────────────────────────────────
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
        "L13_formula.jpg")
    frames.append("L13_formula.jpg")

    # ── L14 TOP-N 矩阵算法 + 聚类 ─────────────────────────────────────
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
        subtitle="创新点① 实现：imb_mat 矩阵上直接取 TOP-N"), "L14_code_topn.jpg")
    frames.append("L14_code_topn.jpg")

    # ── L15 失衡榜 + 布点建议 ──────────────────────────────────────────
    save(render_image_page(
        ["docs/charts/04_供需失衡指数TOP20.png", "docs/charts/09_布点建议优先级分布.png"],
        "失衡指数 TOP20 与布点建议优先级分布",
        caption="来源：docs/charts/04、09"), "L15_imbalance.jpg")
    frames.append("L15_imbalance.jpg")

    # ── L16 章节卡：后端服务 ───────────────────────────────────────────
    save(render_section_card("后端服务", "Spring Boot 3.2.5 + MyBatis + Redis",
                              "16 个接口，全部 Postman 实测通过"), "L16_sec_backend.jpg")
    frames.append("L16_sec_backend.jpg")

    # ── L17 缓存切面 ───────────────────────────────────────────────────
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
        subtitle="AOP 缓存切面：读缓存 → 回源 → 写缓存"), "L17_code_cache.jpg")
    frames.append("L17_code_cache.jpg")

    # ── L18 缓存 key 设计 ──────────────────────────────────────────────
    save(render_code_page(
        "backend/src/main/java/com/uev/aspect/CacheAspect.java", 16, 30,
        annotations=[{
            "lines": (22, 24),
            "label": "QueryParams 含 5 个筛选字段\n→ 改筛选必换 key\n→ 不会拿到旧数据",
            "anchor": "a",
        }],
        title="aspect/CacheAspect.java",
        subtitle="缓存 key 设计：方法名 + 全部入参 MD5"), "L18_code_key.jpg")
    frames.append("L18_code_key.jpg")

    # ── L19 接口清单 ───────────────────────────────────────────────────
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
        note="证据：docs/screenshots/D10_postman/ 共 16 张 Postman 实测响应截图"), "L19_api.jpg")
    frames.append("L19_api.jpg")

    # ── L20 章节卡：运行演示 ───────────────────────────────────────────
    save(render_section_card("运行演示", "可视化大屏 · 实时接口 · 缓存命中",
                              "以下均为真实运行结果"), "L20_sec_demo.jpg")
    frames.append("L20_sec_demo.jpg")

    # ── L21 首页大屏 ───────────────────────────────────────────────────
    save(render_image_page(
        ["docs/screenshots/01_首页大屏.png"],
        "首页大屏：核心 KPI",
        caption="docs/screenshots/01_首页大屏.png"), "L21_dash1.jpg")
    frames.append("L21_dash1.jpg")

    # ── L22 分区地图大屏 ───────────────────────────────────────────────
    save(render_image_page(
        ["docs/screenshots/02_分区地图大屏.png"],
        "分区地图大屏：275 个分区按失衡程度着色",
        caption="docs/screenshots/02_分区地图大屏.png"), "L22_dash2.jpg")
    frames.append("L22_dash2.jpg")

    # ── L23 供需失衡大屏 ───────────────────────────────────────────────
    save(render_image_page(
        ["docs/screenshots/03_供需失衡大屏.png"],
        "供需失衡大屏：24 小时供需曲线",
        caption="docs/screenshots/03_供需失衡大屏.png"), "L23_dash3.jpg")
    frames.append("L23_dash3.jpg")

    # ── L24 布点建议大屏 ───────────────────────────────────────────────
    save(render_image_page(
        ["docs/screenshots/04_布点建议大屏.png"],
        "布点建议大屏：新增充电桩优先级排序",
        caption="docs/screenshots/04_布点建议大屏.png"), "L24_dash4.jpg")
    frames.append("L24_dash4.jpg")

    # ── L25 Postman 实测 ───────────────────────────────────────────────
    save(render_image_page(
        ["docs/screenshots/D10_postman/实测响应_09_imbalance.png",
         "docs/screenshots/D10_postman/实测响应_16_cache_stats.png"],
        "Postman 实测：失衡接口响应 与 缓存统计",
        caption="docs/screenshots/D10_postman/"), "L25_postman.jpg")
    frames.append("L25_postman.jpg")

    # ── L26 章节卡：总结 ───────────────────────────────────────────────
    save(render_section_card("总结", "四层数仓 · 口径可验证 · 创新算法",
                              "感谢老师观看"), "L26_sec_end.jpg")
    frames.append("L26_sec_end.jpg")

    # ── L27 要点页 ─────────────────────────────────────────────────────
    save(render_bullets_page(
        "项目工作小结",
        [
            ("完整四层数据仓库", "ODS → DWD → DWS → ADS 全链路落地，宽转长 + 8 条质量规则清洗"),
            ("指标口径有契约、有独立复算", "docs/contracts/02 指标定义表 + scripts/verify_e_caliber.py 独立复算，可交叉验证"),
            ("供需失衡指数 + 七维聚类选址模型", "I = D − S 份额差口径，7 维特征 KMeans（k=4, seed=42），275 分区分四类"),
            ("Spring Boot 16 接口 + 缓存加速", "AOP 缓存切面 + Redis，16 个接口全部 Postman 实测通过并留档截图"),
        ],
        footer="数据窗口 2022-09 ~ 2023-02（UrbanEV 论文发表时最新可用窗口，含价格维度）"),
        "L27_bullets.jpg")
    frames.append("L27_bullets.jpg")

    # ── L28 结尾页 ─────────────────────────────────────────────────────
    save(render_ending_page(
        "谢谢观看",
        "基于 ETL 的城市充电桩数据分析系统的设计与实现",
        ["第 02 组 · Java Web 后端开发技术",
         "彭忠燕 · 苏静 · 姬婷婷 · 杨姗姗 · 贺欢欢",
         "欢迎老师提问"]), "L28_end.jpg")
    frames.append("L28_end.jpg")

    print(f"✓ 生成 {len(frames)} 帧 → {OUT}")
    for f in frames:
        print("  ", f)


if __name__ == "__main__":
    main()
