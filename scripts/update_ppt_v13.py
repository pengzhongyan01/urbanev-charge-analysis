#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
update_ppt_v13.py —— PPT 第 9/10/13 页改为契约 v1.3 口径 + 嵌入 E 岗 9 张素材图

背景
----
第 5 章 5.6 节口径裁决后（契约 02 升 v1.3），PPT 第 9、10、13 页仍是旧口径：
  - P9 创新点②：轮廓系数 0.8132 / TOU 31 / FLAT 244  → 应为 σ>0.05 / TOU 78 / FLAT 197
  - P9 创新点①：DI − D̄ 差值口径 + TOP20 +0.88 时/桩   → 应为份额差 D − S + 56 个供不应求分区
  - P10 创新点③：三模型竞优 20.720%                      → 应为同周期均值×γ + 三层误差分层
  - P10 布点建议：167 分区                               → 应为 56 条建议 / 新增 93 桩
  - P10 创新点④：未写聚类结果                           → 应补 紧张型 27 等四簇规模
  - P13 团队分工：E 岗写「三模型竞优」                    → 应改为契约口径表述

同时把 E 岗（姬婷婷）提供的 9 张 PPT 素材图嵌入对应页，
让答辩现场能直接展示真实图表。

用法
----
    python scripts/update_ppt_v13.py
"""
from __future__ import annotations

import re
from pathlib import Path

from pptx import Presentation
from pptx.util import Emu, Inches, Pt
from pptx.dml.color import RGBColor

REPO = Path(__file__).resolve().parent.parent
PPTX = REPO / "docs" / "ppt" / "第02组_城市充电桩数据分析系统_答辩PPT.pptx"
EIMG = REPO / "docs" / "ppt" / "images"

INK = RGBColor(0x1F, 0x29, 0x37)
MUT = RGBColor(0x64, 0x74, 0x8B)
BLUE = RGBColor(0x25, 0x63, 0xEB)
RED = RGBColor(0xDC, 0x26, 0x26)
GREEN = RGBColor(0x15, 0x80, 0x3D)
AMBER = RGBColor(0xB4, 0x53, 0x09)
PURPLE = RGBColor(0x7C, 0x3A, 0xED)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

# ★ 契约 v1.3 的实测数字（全部来自 E 岗 analysis/01_analysis.py，A 岗独立复算复核）
P9_REPLACE = [
    # ── 创新点① 卡片 1：公式 + 口径 ──
    ("""需求强度　D(z,t) = duration_h(z,t) / charge_count(z)　全市基准　D̄(t) = Σ_z duration_h(z,t) / Σ_z charge_count(z)　★ 实测：每桩小时均 0.1574 小时（≈9.4 分钟）· 275 分区""",
     """需求份额　D(z,t) = 该分区需求量 / 全市同期需求量　运力份额　S(z) = 该分区桩数 / 全市桩数　★ I(z,t) = D(z,t) − S(z)　★ 275 分区 × 24 时 = 6,600 行　全市单桩每小时仅被占用 9.4 分钟"""),
    # ── 创新点① 卡片 2：判读 + 实测 ──
    ("""I > 0 → 需求高于全市同期 → 建议扩容或错峰引导　I < 0 → 供给富余 → 建议调度引流　★ 实测：275 分区均现失衡，TOP20 达 +0.88 时/桩""",
     """I > 0 → 该区占需求的份额 > 占运力的份额 → 供不应求　I < 0 → 运力相对闲置　★ 实测：仅 56 个分区（20.4%）供不应求，峰值失衡 0.1225（595 区），其余 219 区运力富余"""),
    # ── 创新点② 卡片 1：分组依据 ──
    ("""分组依据　按 e_price + s_price 的时序标准差 σ 做 KMeans 二聚类　★ 轮廓系数 0.8132（>0.6，分群成立）　★ TOU 31 区（σ 0.4700）vs FLAT 244 区（σ 0.0349）· 差 13.5 倍""",
     """分组依据　σ_price = STDDEV_POP(e_price) > 0.05 → 分时电价区（TOU）　★ 实测 TOU 78 区 / FLAT 197 区　★ σ 中位数为 0、分布双峰，0.05 恰在两峰低谷 → 阈值可解释"""),
    # ── 创新点② 卡片 2：弹性结果 ──
    ("""TOU vs FLAT 对比 24 小时峰谷差与占用率　量化分时电价引导的削峰效果　★ 两组 σ 差 13.5 倍，分群高度可分""",
     """TOU vs FLAT 对比 24 小时峰谷占用率差　★ 实测 TOU −0.1185 vs FLAT −0.0510　★ 价差引导拉大了时段差，但两组夜间占用率均高于晚高峰 → 夜间慢充是刚性主体"""),
    # ── 底部总结 ──
    ("""① 归一化消除了分区规模差异 —— 拿『平均充电时长』直接比大小分区没有意义，除以该分区桩数后才可比　② 把『该不该调价』变成一个可以拿数字回答的问题：TOU 组峰谷差比 FLAT 组低多少个百分点　③ 两者互相印证 —— 失衡指数高的分区，正是调价引导潜力最大的分区""",
     """① 份额差消除了分区规模差异 —— 4 桩与 446 桩的分区可公平比较，TOP1 是 1167 区（446 桩，CBD 级）　② 把『该不该调价』变成可回答的问题 —— TOU 组峰谷差比 FLAT 组大 0.0674 个百分点　③ 深圳不是总量缺桩，而是 56 个分区在大流量时段结构性缺桩"""),
]

P10_REPLACE = [
    ("""★ 三模型横向竞优（统一 MAPE 选优）　朴素基线 lag1　20.720%　← 最优　线性回归　　　　24.628%　随机森林　　　　24.853%　回测 2023-02-15~28，样本 3,850 条　★ 序列接近随机游走，复杂模型不划算""",
     """同周期均值 × 趋势因子 γ　前 174 天训练 / 后 7 天回测　★ 三层误差分层披露　全市逐小时 MAPE 5.31%　全市日聚合 WAPE 1.31%　分区逐小时 74.01%　★ volume 经插值补齐，分区级小时 MAPE 系统性偏高 → 如实分层，不藏数"""),
    ("""KMeans（k=4，seed=42）· 7 维特征　平均/峰值占用率 · 失衡指数　σ_price · 桩数 · POI 数　★ 产出：275 分区 4 类画像 + WCSS 肘部曲线""",
     """KMeans（k=4，seed=42）· 7 维特征　平均/峰值占用率 · 失衡指数　σ_price · 桩数 · POI 数　★ 紧张型 27 / 过剩型 128 / 稳定型 79 / 潜力型 41　★ 紧张型平均失衡 0.0226，其余簇近 0 → 与失衡指数互证"""),
    ("""由规则表自动生成，非人工挑选　紧张型（+30%）/ 潜力型（+20%）/ 过剩型（调度引流）　★ 实测：167 分区入选，优先级 1/2/3　★ 含类型/数量/优先级/文字依据""",
     """规则自动生成：⌈峰值失衡 × 现有桩数 × 0.3⌉　★ 实测 56 条建议、合计新增 93 桩（+1.82%）　★ TOP1：595 区 274→285　★ 扩容后均多于现有（100%）　★ 结论：全市靠调度+错峰即可，缺桩的只是少数高失衡分区"""),
    ("""① 失衡指数　回答『哪里供不应求』　→　② 电价弹性　回答『能不能靠调价缓解』　→　③ 需求预测　回答『未来会怎样』　→　④ 聚类画像　回答『这类分区整体该怎么管』　→　布点建议　回答『具体该怎么做』　★ 从规则驱动（①②③）到数据驱动发现未知结构（④），两种思路互补 = 分析维度的完整性""",
     """① 失衡指数　回答『哪里供不应求』　→　② 电价弹性　回答『能不能靠调价缓解』　→　③ 需求预测　回答『未来会怎样』　→　④ 聚类画像　回答『这类分区整体该怎么管』　→　布点建议　回答『具体该怎么做』　★ 从规则驱动（①②③）到数据驱动发现未知结构（④），两种思路互补 = 分析维度的完整性"""),
]

P13_REPLACE = [
    ("""· 《指标定义表》15 项指标口径（组内总闸门）　|　· 四个创新指标：三模型竞优 + 误差评估 + KMeans 聚类　|　· 布点扩容建议规则与清单""",
     """· 《指标定义表》16 项指标口径（组内总闸门）　|　· 四个创新指标：失衡指数 + 电价弹性 + 需求预测 + KMeans 聚类　|　· 布点扩容建议规则与清单 · 报告第五、六章主笔"""),
]

# ★ 关键词定位 → 整框重写（比逐串 replace 可靠：PPT 里空格是全角 U+3000，
#   逐串匹配极易落空；而每个文本框的用途唯一，用关键词定位不会有歧义）
P9_BY_KEYWORD = [
    ("全市基准", "需求份额 D(z,t)　运力份额 S(z)　★ I = D − S\n275 分区 × 24 时 = 6,600 行；单桩每小时仅占用 9.4 分钟"),
    ("I > 0", "I > 0 供不应求　I < 0 运力闲置\n★ 仅 56 个分区（20.4%）供不应求，峰值失衡 0.1225（595 区）"),
    ("分组依据", "σ_price = STDDEV_POP(e_price) > 0.05 → 分时电价区\n★ TOU 78 / FLAT 197；σ 中位数为 0、双峰，阈值可解释"),
    ("TOU vs FLAT", "24 小时峰谷占用率差　★ TOU −0.1185 vs FLAT −0.0510\n★ 价差拉大了时段差，但夜间慢充是刚性主体"),
    ("归一化消除了分区规模差异", "① 份额差消除规模差异 —— 4 桩与 446 桩可公平比较，TOP1 是 1167 区（446 桩，CBD 级）\n② TOU 组峰谷差比 FLAT 组大 0.0674 个百分点　③ 不是总量缺桩，是 56 个分区结构性缺桩"),
]

P10_BY_KEYWORD = [
    ("三模型横向竞优", "同周期均值 × 趋势因子 γ　174 天训练 / 7 天回测\n★ 三层误差分层（不藏数）\n　全市逐小时 MAPE　 5.31%\n　全市日聚合 WAPE　 1.31%\n　分区逐小时　　　74.01%\n★ volume 经插值补齐 → 分区级小时 MAPE 偏高"),
    ("KMeans（k=4", "KMeans（k=4，seed=42）· 7 维特征\n★ 紧张型 27 / 过剩型 128 / 稳定型 79 / 潜力型 41\n★ 紧张型平均失衡 0.0226，其余簇近 0 → 互证成立"),
    ("由规则表自动生成", "规则：⌈峰值失衡 × 现有桩数 × 0.3⌉\n★ 56 条建议、合计新增 93 桩（+1.82%）\n★ TOP1：595 区 274→285，扩容后均多于现有\n★ 全市靠调度+错峰即可，缺桩的只是少数分区"),
]

P13_BY_KEYWORD = [
    ("《指标定义表》15 项指标口径", "· 《指标定义表》16 项指标口径（组内总闸门）\n· 四个创新指标：失衡指数 + 电价弹性 + 需求预测 + KMeans 聚类\n· 布点扩容建议规则与清单 · 报告第五、六章主笔"),
]

# 缩放后插入的图：(页码, 图片文件, 左, 上, 宽, 高)
INSERT_IMGS = [
    (9,  "08_失衡指数_TOP10.png",        Inches(0.90), Inches(5.42), Inches(5.40), Inches(1.50)),
    (9,  "08_TOU_FLAT_占用率对比.png",   Inches(7.06), Inches(5.42), Inches(5.40), Inches(1.50)),
    (10, "09_需求预测_曲线.png",          Inches(0.90), Inches(5.34), Inches(3.40), Inches(1.56)),
    (10, "09b_聚类_散点.png",             Inches(5.00), Inches(5.34), Inches(3.40), Inches(1.56)),
    (10, "09_双口径电量偏差.png",          Inches(9.10), Inches(5.34), Inches(3.40), Inches(1.56)),
]


def iter_text_shapes(slide):
    for sh in slide.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip():
            yield sh


def _norm(t: str) -> str:
    """全角/半角空格归一化 —— PPT 正文用 U+3000，这里同时匹配两种"""
    return t.replace("\u3000", " ")


def replace_text(slide, pairs, page):
    """按关键词定位文本框并整框重写。

    ★ 不用逐串 replace：PPT 正文里的空格是全角 U+3000，
      脚本里写半角会匹配落空。而每个文本框用途唯一，按关键词定位无歧义。
    """
    done = 0
    for sh in iter_text_shapes(slide):
        tf = sh.text_frame
        cur = tf.text
        for kw, newtext in pairs:
            if kw not in cur:
                continue
            # 记录首个 run 的格式
            runs = []
            for p in tf.paragraphs:
                for r in p.runs:
                    try:
                        col = r.font.color.rgb if r.font.color and r.font.color.type is not None else None
                    except Exception:
                        col = None
                    runs.append((r.font.size, r.font.bold, col))
            # 清空所有段，只留第一段
            for p in list(tf.paragraphs[1:]):
                p._element.getparent().remove(p._element)
            p0 = tf.paragraphs[0]
            lines = newtext.split("\n")
            p0.text = lines[0]
            for ln in lines[1:]:
                np = tf.add_paragraph()
                np.text = ln
            # ★ 套回格式 —— 字号必须**显式**给每一段的每个 run。
            #   add_paragraph() 新建的段落不继承原 run 的字号，
            #   会退回文本框默认字号（偏大）→ 溢出卡片。
            size, bold, color = runs[0] if runs else (None, None, None)
            try:
                pt = size.pt if size is not None else 11.0
            except Exception:
                pt = 11.0
            pt = pt - 0.5 if pt > 8 else pt
            for p in tf.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(pt)
                    if bold is not None: r.font.bold = bold
                    if color is not None:
                        try: r.font.color.rgb = color
                        except Exception: pass
            done += 1
            break
    print(f"  第 {page} 页：重写 {done} 个文本框")
    return done


def insert_images(prs):
    for page, name, left, top, width, height in INSERT_IMGS:
        src = EIMG / name
        if not src.exists():
            print(f"  ⚠ 第 {page} 页缺图 {name}")
            continue
        slide = prs.slides[page - 1]
        slide.shapes.add_picture(str(src), left, top, width=width, height=height)
        print(f"  ✓ 第 {page} 页 插入 {name}")


def main():
    if not PPTX.exists():
        print(f"✗ 找不到 PPT：{PPTX}")
        return 1

    prs = Presentation(str(PPTX))
    print(f"共 {len(prs.slides)} 页\n")

    print("【替换文本为契约 v1.3 口径】")
    replace_text(prs.slides[8], P9_BY_KEYWORD, 9)
    replace_text(prs.slides[9], P10_BY_KEYWORD, 10)
    replace_text(prs.slides[12], P13_BY_KEYWORD, 13)

    print("\n【压缩底部总结框，给图腾位置】")
    # 第 9 页底部总结框原本 (0.88,5.08) 11.60x1.20 → 压到 5.02 起、只留 2 行高度
    # ── 第 9 页：底部总结框保留（小标题 + 2 行正文），压扁后给图腾位置 ──
    sl9 = prs.slides[8]
    for sh in sl9.shapes:
        if not sh.has_text_frame:
            continue
        t = sh.text_frame.text
        if "份额差消除规模差异" in t:
            sh.top = Emu(int(4.58 * 914400))
            sh.height = Emu(int(0.76 * 914400))
            print("  第 9 页 底部总结正文压至 4.58~5.34")
        elif t.strip() == "这两个指标解决了什么问题":
            sh.top = Emu(int(4.18 * 914400))
            print("  第 9 页 小标题上移至 4.18")

    # ── 第 10 页：★ 底部「四个指标构成一条完整链路」整块删除 ──
    #   原因：这一段的内容（①→②→③→④ 的链路说明）与三张卡片高度重复，
    #   而三张 E 岗素材图必须占满下半部 —— 页高 7.5 英寸、页脚在 7.08，
    #   放不下第三个文本块。删除冗余比压缩字号更干净。
    sl10 = prs.slides[9]
    removed = 0
    for sh in list(sl10.shapes):
        if not sh.has_text_frame:
            continue
        t = sh.text_frame.text.strip()
        if t == "四个指标构成一条完整链路" or "失衡指数　回答" in t:
            sh._element.getparent().remove(sh._element)
            removed += 1
    print(f"  第 10 页 删除冗余链路文本块 {removed} 个（内容与卡片重复）")

    print("\n【嵌入 E 岗素材图】")
    insert_images(prs)

    prs.save(str(PPTX))
    print(f"\n✓ 已保存：{PPTX.name}")

    # 校验
    print("\n【校验】")
    prs2 = Presentation(str(PPTX))
    pics = 0
    for i, sl in enumerate(prs2.slides, 1):
        n = sum(1 for sh in sl.shapes if sh.shape_type == 13)
        pics += n
    print(f"  总图数 {pics} 张")
    p9 = "\n".join(sh.text_frame.text for sh in iter_text_shapes(prs2.slides[8]))
    p10 = "\n".join(sh.text_frame.text for sh in iter_text_shapes(prs2.slides[9]))
    for old in ("0.8132", "TOU 31", "FLAT 244", "0.4700", "0.88 时/桩", "20.720%", "24.628%", "167 分区"):
        mark = "✗ 残留" if old in p9 + p10 else "✓ 已清"
        print(f"  旧口径 {old:14s} {mark}")
    for new in ("TOU 78", "FLAT 197", "5.31%", "1.31%", "74.01%", "56 条建议", "新增 93 桩", "紧张型 27"):
        print(f"  新口径 {new:14s} {'✓' if new in p9 + p10 else '✗ 未找到'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
