#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A08 · 答辩 PPT 生成器（15 页）
用法：python scripts/generate_ppt.py
产物：docs/ppt/第02组_城市充电桩数据分析系统_答辩PPT.pptx
版式照参考作业 34 页 PPT 的视觉体系：章节过渡页（大号数字+中英文标题+副标题）
      + 四宫格卡片内容页 + 统一页脚（主讲/制作/数据支持）
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
import copy

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "docs" / "ppt"
OUT.mkdir(parents=True, exist_ok=True)
IMG = REPO / "docs" / "架构图"

# ── 主题 ─────────────────────────────
BG    = RGBColor(0x0B, 0x12, 0x20)
BG2   = RGBColor(0x11, 0x1A, 0x2E)
CARD  = RGBColor(0x16, 0x22, 0x3A)
CARD2 = RGBColor(0x1C, 0x2B, 0x47)
LINE  = RGBColor(0x27, 0x37, 0x55)
T1    = RGBColor(0xEC, 0xF2, 0xFA)
T2    = RGBColor(0xA8, 0xB8, 0xCF)
T3    = RGBColor(0x6E, 0x81, 0x9D)
CYAN  = RGBColor(0x4F, 0xC3, 0xF7)
AMBER = RGBColor(0xFF, 0xB7, 0x4D)
PURP  = RGBColor(0x9C, 0x8C, 0xFF)
GREEN = RGBColor(0x4D, 0xD0, 0xA7)
RED   = RGBColor(0xFF, 0x7B, 0x7B)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

FONT = "微软雅黑"
W, H = 13.333, 7.5

prs = Presentation()
prs.slide_width = Inches(W)
prs.slide_height = Inches(H)
BLANK = prs.slide_layouts[6]


# ── 基础绘制 ─────────────────────────────
def slide():
    s = prs.slides.add_slide(BLANK)
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid(); bg.fill.fore_color.rgb = BG
    bg.line.fill.background(); bg.shadow.inherit = False
    return s


def rect(s, x, y, w, h, fill=None, line=None, lw=1.0, shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.06):
    sp = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid(); sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line; sp.line.width = Pt(lw)
    sp.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try: sp.adjustments[0] = adj
        except Exception: pass
    return sp


def text(s, x, y, w, h, runs, size=16, color=T1, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, lh=1.35, space_after=4):
    """runs: str 或 [(文本, 覆盖属性dict), ...] 或 [str, str, ...] 多段"""
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    if isinstance(runs, str):
        runs = [runs]
    first = True
    for item in runs:
        if isinstance(item, tuple):
            content, ov = item
        else:
            content, ov = item, {}
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = ov.get("align", align)
        p.line_spacing = ov.get("lh", lh)
        p.space_after = Pt(ov.get("space_after", space_after))
        for j, ln in enumerate(str(content).split("\n")):
            if j > 0:
                p = tf.add_paragraph()
                p.alignment = ov.get("align", align)
                p.line_spacing = ov.get("lh", lh)
                p.space_after = Pt(ov.get("space_after", space_after))
            r = p.add_run(); r.text = ln
            f = r.font
            f.name = FONT; f.size = Pt(ov.get("size", size))
            f.bold = ov.get("bold", bold)
            f.color.rgb = ov.get("color", color)
            rPr = r._r.get_or_add_rPr()
            for tag in ("a:latin", "a:ea", "a:cs"):
                e = rPr.find(qn(tag))
                if e is None:
                    e = rPr.makeelement(qn(tag), {}); rPr.append(e)
                e.set("typeface", FONT)
    return tb


def footer(s, no, title, speaker, maker="A", support="—"):
    rect(s, 0, H-0.52, W, 0.012, fill=LINE, shape=MSO_SHAPE.RECTANGLE)
    text(s, 0.55, H-0.42, 7.0, 0.3, f"第 {no} 页　{title}",
         size=10.5, color=T3)
    text(s, W-6.6, H-0.42, 6.05, 0.3,
         f"主讲：{speaker}　制作：{maker}　数据支持：{support}",
         size=10.5, color=T3, align=PP_ALIGN.RIGHT)
    text(s, W-3.2, H-0.74, 2.65, 0.26, "明德至善　博学笃行",
         size=9.5, color=T3, align=PP_ALIGN.RIGHT)


def notes(s, txt):
    s.notes_slide.notes_text_frame.text = txt


def card(s, x, y, w, h, title, lines, accent=CYAN, tsize=13.5, bsize=11):
    rect(s, x, y, w, h, fill=CARD, line=LINE, lw=1.0)
    rect(s, x, y, w, 0.045, fill=accent, shape=MSO_SHAPE.RECTANGLE)
    text(s, x+0.22, y+0.22, w-0.44, 0.4, title, size=tsize, color=accent, bold=True)
    body = []
    for ln in lines:
        body.append((ln, {"size": bsize, "color": T2, "lh": 1.45, "space_after": 3}))
    if body:
        text(s, x+0.22, y+0.72, w-0.44, h-0.9, body)


def placeholder(s, x, y, w, h, label, hint=""):
    """图片占位框：各岗把自己的 PNG 贴进来即可"""
    sp = rect(s, x, y, w, h, fill=CARD2, line=LINE, lw=1.0)
    sp.line.dash_style = 4  # dashed
    text(s, x+0.15, y+h/2-0.32, w-0.3, 0.35, label, size=12, color=CYAN, bold=True, align=PP_ALIGN.CENTER)
    if hint:
        text(s, x+0.15, y+h/2+0.06, w-0.3, 0.6, hint, size=9.5, color=T3, align=PP_ALIGN.CENTER, lh=1.3)
    return sp


def header(s, no, cn, en, subtitle=""):
    rect(s, 0, 0, W, 0.06, fill=CYAN, shape=MSO_SHAPE.RECTANGLE)
    text(s, 0.62, 0.42, 9.0, 0.55, cn, size=27, color=T1, bold=True)
    text(s, 0.62, 1.02, 9.0, 0.32, en, size=12, color=T3)
    if subtitle:
        text(s, 0.62, 1.34, 11.8, 0.34, subtitle, size=12.5, color=CYAN)


def transition(no, num, cn, en, sub, speaker, notes_txt):
    s = slide()
    rect(s, 0, 0, W, 0.06, fill=CYAN, shape=MSO_SHAPE.RECTANGLE)
    text(s, 0.9, 1.35, 3.2, 2.6, f"{num:02d}", size=150, color=CARD2, bold=True)
    rect(s, 0.95, 4.05, 0.9, 0.055, fill=CYAN, shape=MSO_SHAPE.RECTANGLE)
    text(s, 0.95, 4.32, 10.5, 0.85, cn, size=42, color=T1, bold=True)
    text(s, 0.95, 5.22, 10.5, 0.4, en, size=16, color=CYAN)
    text(s, 0.95, 5.72, 10.5, 0.5, sub, size=15, color=T2)
    footer(s, no, f"{num:02d} {cn}", speaker)
    notes(s, notes_txt)
    return s


# ══════════════════════════════════════════════════════════════
#  01 封面
# ══════════════════════════════════════════════════════════════
s = slide()
rect(s, 0, 0, W, 0.09, fill=CYAN, shape=MSO_SHAPE.RECTANGLE)
rect(s, 0, H-0.09, W, 0.09, fill=CYAN, shape=MSO_SHAPE.RECTANGLE)
text(s, 1.0, 0.62, 11.3, 0.35, "明德至善　博学笃行", size=14, color=CYAN, align=PP_ALIGN.CENTER)
text(s, 0.8, 1.55, 11.7, 0.6,
     "基于 Hadoop 与 Spring Boot 的城市充电桩使用行为分析",
     size=30, color=T1, bold=True, align=PP_ALIGN.CENTER)
text(s, 0.8, 2.18, 11.7, 0.6,
     "与充电需求预测系统的设计与实现",
     size=30, color=T1, bold=True, align=PP_ALIGN.CENTER)
text(s, 0.8, 2.98, 11.7, 0.4,
     "Design and Implementation of Urban EV Charging Behavior Analysis and Demand Forecasting System",
     size=12, color=T3, align=PP_ALIGN.CENTER)
rect(s, 4.6, 3.62, 4.15, 0.045, fill=CYAN, shape=MSO_SHAPE.RECTANGLE)

text(s, 1.4, 3.92, 10.5, 0.35, "小组成员", size=13, color=CYAN, bold=True, align=PP_ALIGN.CENTER)
text(s, 1.4, 4.32, 10.5, 0.42,
     "彭忠燕　苏　静　贺欢欢　杨珊珊　姬婷婷",
     size=21, color=T1, bold=True, align=PP_ALIGN.CENTER)
text(s, 1.4, 4.92, 10.5, 0.32,
     "软件工程　2405 班　·　第 02 组　·　主讲人：彭忠燕",
     size=13, color=T2, align=PP_ALIGN.CENTER)
text(s, 1.4, 5.42, 10.5, 0.32, "指导教师：赵　晨", size=13, color=T2, align=PP_ALIGN.CENTER)
text(s, 1.4, 5.95, 10.5, 0.32, "2026 年 11 月", size=13, color=T3, align=PP_ALIGN.CENTER)
text(s, 1.4, 6.62, 10.5, 0.3,
     "数据来源：UrbanEV 开源数据集（CC0 1.0）· 中山大学 / 香港理工大学 · arXiv:2309.05259",
     size=10.5, color=T3, align=PP_ALIGN.CENTER)
notes(s, "开场（约 30 秒）：各位老师好。我们是第 02 组，题目是《基于 Hadoop 与 Spring Boot 的城市充电桩使用行为分析与充电需求预测系统的设计与实现》。\n"
         "我们做的不是一个跑在玩具数据上的 demo：数据是深圳 275 个交通分区、23441 个充电桩、4344 个逐小时真实运营数据，用完整 Hadoop 链路跑通，最后落到一个能回答『哪个分区什么时候桩不够用、该在哪建桩』的决策看板。")

# ══════════════════════════════════════════════════════════════
#  02 目录
# ══════════════════════════════════════════════════════════════
s = slide()
header(s, 2, "目　录", "Contents", "八个部分，20 分钟讲完")
TOC = [
    ("01", "研究背景与意义", "痛点 · 价值 · 定位"),
    ("02", "系统需求分析", "三角色场景 · 用例"),
    ("03", "系统总体设计", "六层架构 · 数据流"),
    ("04", "数据仓库与计算", "Hive 四层 · MR · Spark · Sqoop"),
    ("05", "四个创新指标", "失衡指数 · 电价弹性 · 预测 · 聚类"),
    ("06", "系统实现与演示", "后端 16 接口 · 看板 6 页 10 图"),
    ("07", "系统测试与性能", "用例通过率 · 缓存对比"),
    ("08", "团队分工与总结", "五人分工 · 创新点归纳 · 展望"),
]
for i, (n, t, sub) in enumerate(TOC):
    col, row = i % 4, i // 4
    x = 0.62 + col * 3.10
    y = 2.05 + row * 2.28
    rect(s, x, y, 2.85, 1.92, fill=CARD, line=LINE)
    text(s, x+0.20, y+0.16, 1.2, 0.62, n, size=34, color=CARD2, bold=True)
    text(s, x+0.20, y+0.86, 2.5, 0.4, t, size=14.5, color=T1, bold=True)
    text(s, x+0.20, y+1.30, 2.5, 0.5, sub, size=10.5, color=T3, lh=1.3)
footer(s, 2, "目录", "彭忠燕")
notes(s, "目录（约 15 秒）：按技术链路讲 —— 背景痛点、需求、总体设计、数仓计算、四个创新指标、系统实现、测试性能，最后分工与总结。")

# ══════════════════════════════════════════════════════════════
#  03 过渡页 01
# ══════════════════════════════════════════════════════════════
transition(3, 1, "研究背景与意义", "Research Background and Significance",
            "桩车比失衡是真痛点 —— 我们用真实数据把它量化出来",
            "彭忠燕",
            "（约 1 分钟）先讲为什么这个题目值得做。\n"
            "三个点：① 新能源车增长带来的桩车比失衡是真实痛点 ② 现有研究的空白 —— 大多只做需求预测，很少回答『供给该往哪摆』 ③ 我们的定位：把供需失衡量化到分区×时段粒度，并给出可执行的布点建议。\n"
            "关键数字要说准：275 个分区、23441 个桩、4344 小时。")

# ══════════════════════════════════════════════════════════════
#  04 背景与痛点
# ══════════════════════════════════════════════════════════════
s = slide()
header(s, 4, "研究背景与意义", "Research Background and Significance",
       "真实运营数据里的三个结构性矛盾")
card(s, 0.62, 1.95, 3.86, 2.25, "痛点 ①　总量失衡",
     ["深圳公共充电桩 23,441 个，覆盖 275 个交通分区",
      "分区间供给密度差异达百倍",
      "总量够用 ≠ 分布合理"], CYAN)
card(s, 4.72, 1.95, 3.86, 2.25, "痛点 ②　时空错配",
     ["同一分区，不同时段占用率差异悬殊",
      "夜间闲置与傍晚排队并存",
      "静态规划无法解决时段错配"], AMBER)
card(s, 8.82, 1.95, 3.90, 2.25, "痛点 ③　价格无效",
     ["分时电价落地但效果缺量化",
      "不知道引导是否真的削峰",
      "调价决策缺少依据"], PURP)

rect(s, 0.62, 4.48, 12.10, 1.85, fill=CARD, line=LINE)
text(s, 0.86, 4.68, 11.6, 0.4, "本课题的价值", size=15, color=GREEN, bold=True)
text(s, 0.86, 5.12, 11.6, 1.1, [
    ("理论价值　把「充电桩够不够用」从模糊的抱怨，转成可计算、可比较、可检验的分区级指标，并给出统一口径", {"size": 12, "color": T2, "space_after": 6}),
    ("实践价值　输出可直接执行的布点扩容清单（分区 / 建议数量 / 优先级 / 依据 / 预期效果），并量化分时电价的引导效果", {"size": 12, "color": T2, "space_after": 6}),
    ("工程价值　完整 Hadoop 离线数仓链路 + 可复现部署，别人不下载 129MB 原始数据也能一键重建并跑起全系统", {"size": 12, "color": T2}),
])
footer(s, 4, "研究背景与意义", "彭忠燕")
notes(s, "（约 1.5 分钟）三个痛点各 20 秒，重点讲痛点③ —— 这是我们和大部分同类作业的差别：别人停在『预测需求』，我们多问一句『预测出来之后该怎么办』。\n"
         "价值三点快速带过。\n"
         "⚠ 数字必须说准：23,441 个桩、275 个分区、4344 小时。别说成 17532 或 8760。")

# ══════════════════════════════════════════════════════════════
#  05 需求分析
# ══════════════════════════════════════════════════════════════
s = slide()
header(s, 5, "系统需求分析", "System Requirements Analysis",
       "三类使用者，三个真实场景")
ROLES = [
    ("城市运营管理者", CYAN, ["我要知道全市充电桩供给够不够、缺在哪个分区",
                        "哪个分区该扩容、扩多少、优先级如何",
                        "分时电价到底有没有削峰效果"]),
    ("充电站运营方", AMBER, ["我这个站利用率怎么样，是紧张还是过剩",
                      "附近 POI 密度高说明有潜在需求吗",
                      "同类型分区里我的表现算好吗"]),
    ("数据分析师 / 研究者", PURP, ["分区×时段的供需关系怎么量化",
                          "预测模型怎么选、误差有多大",
                          "聚类能不能自动发现分区类型"]),
]
for i, (r, c, items) in enumerate(ROLES):
    x = 0.62 + i * 4.10
    rect(s, x, 1.95, 3.86, 2.55, fill=CARD, line=LINE)
    rect(s, x, 1.95, 3.86, 0.05, fill=c, shape=MSO_SHAPE.RECTANGLE)
    text(s, x+0.24, 2.18, 3.4, 0.4, r, size=15, color=c, bold=True)
    body = [("· " + it, {"size": 11, "color": T2, "lh": 1.5, "space_after": 7}) for it in items]
    text(s, x+0.24, 2.72, 3.4, 1.6, body)

rect(s, 0.62, 4.72, 5.95, 1.62, fill=CARD, line=LINE)
text(s, 0.86, 4.92, 5.5, 0.35, "核心用例（4 个）", size=13.5, color=GREEN, bold=True)
text(s, 0.86, 5.32, 5.5, 0.95, [
    ("UC1　分区供需失衡诊断（运营管理者）", {"size": 11, "color": T2, "space_after": 4}),
    ("UC2　布点扩容建议生成（运营管理者）", {"size": 11, "color": T2, "space_after": 4}),
    ("UC3　充电需求预测与回测（分析师）", {"size": 11, "color": T2, "space_after": 4}),
    ("UC4　分区类型画像发现（分析师）", {"size": 11, "color": T2}),
])
placeholder(s, 6.78, 4.72, 5.94, 1.62, "〔需求分析用例图〕",
            "由 D（杨珊珊）在 A05 交付 D-4 素材\n纸笔草稿即可，组长负责美化后贴入")
footer(s, 5, "系统需求分析", "杨珊珊", "A", "D")
notes(s, "（约 1.5 分钟）三个角色各讲一句需求的原话 —— 带着问题听，比念功能列表强。\n"
         "★ 用例图这里必须贴上，评委看的是你有没有想清楚『谁在什么场景下用』，不是功能有多少。\n"
         "D 同学主讲这一页。")

# ══════════════════════════════════════════════════════════════
#  06 过渡页 03 + 架构图
# ══════════════════════════════════════════════════════════════
s = slide()
header(s, 6, "系统总体设计", "System Overall Architecture",
       "六层架构：采集 → 清洗 → 建模 → 计算 → 服务 → 展示")
if (IMG / "项目架构.png").exists():
    s.shapes.add_picture(str(IMG / "项目架构.png"), Inches(0.62), Inches(1.74), width=Inches(9.02))
else:
    placeholder(s, 0.62, 1.74, 9.02, 4.78, "〔系统架构图〕", "运行 scripts/generate_arch_diagrams.py 生成")
rect(s, 9.86, 1.74, 2.86, 4.78, fill=CARD, line=LINE)
text(s, 10.06, 1.94, 2.5, 0.35, "设计要点", size=13.5, color=CYAN, bold=True)
text(s, 10.06, 2.36, 2.5, 4.0, [
    ("① 契约驱动", {"size": 11, "color": CYAN, "bold": True, "space_after": 2}),
    ("四份契约文件即组内交接物，口径变更走 PR + CHANGELOG", {"size": 9.5, "color": T2, "lh": 1.4, "space_after": 12}),
    ("② 两条路径并行", {"size": 11, "color": CYAN, "bold": True, "space_after": 2}),
    ("B 的离线数仓管道与 E 的探索性分析在 MySQL 汇合，互不阻塞", {"size": 9.5, "color": T2, "lh": 1.4, "space_after": 12}),
    ("③ 视图作契约层", {"size": 11, "color": CYAN, "bold": True, "space_after": 2}),
    ("D 的接口只读视图，ADS 改字段不动接口", {"size": 9.5, "color": T2, "lh": 1.4, "space_after": 12}),
    ("④ 一键复现部署", {"size": 11, "color": CYAN, "bold": True, "space_after": 2}),
    ("Docker Compose + 冒烟测试，别人照 RUNBOOK 能跑起来", {"size": 9.5, "color": T2, "lh": 1.4}),
])
footer(s, 6, "系统总体设计", "彭忠燕", "A", "全体")
notes(s, "（约 1.5 分钟）这页看图讲三个要点，不要逐个方框念。\n"
         "① 契约驱动 —— 这是团队协作机制，也是我们组内互评的加分项\n"
         "② 两条路径汇合 —— 讲清楚为什么不把 E 也塞进 Hive（时间倒挂），体现架构判断\n"
         "③ 视图作契约层 —— 体现分层思维\n"
         "★ 这张图是我们自己画的，版式照参考作业的架构图复刻，可以说明『结构清晰、覆盖完整』。")

# ══════════════════════════════════════════════════════════════
#  07 数据来源与清洗
# ══════════════════════════════════════════════════════════════
s = slide()
header(s, 7, "数据来源与清洗", "Data Source and Cleansing",
       "12 个真实 CSV · 宽表转长表 · 8 类质量规则")
rect(s, 0.62, 1.95, 6.05, 2.52, fill=CARD, line=LINE)
text(s, 0.86, 2.14, 5.6, 0.35, "为什么不用爬虫？（答辩必问）", size=13.5, color=AMBER, bold=True)
text(s, 0.86, 2.55, 5.6, 1.9, [
    ("① 真实性　数据取自 1,682 个公共充电站的运营系统，是真实运营数据，不是前端展示值", {"size": 10.5, "color": T2, "space_after": 5}),
    ("② 可复现　CC0 协议允许自由使用再分发，一份脚本人人可得完全相同的数据集；爬虫受反爬与改版影响不可复现", {"size": 10.5, "color": T2, "space_after": 5}),
    ("③ 合规　公开发布且明确授权，规避服务条款与法律风险", {"size": 10.5, "color": T2, "space_after": 5}),
    ("同时我们实现了 Flume 增量采集链路 —— 若数据源换成需实时采集的场景，现有链路可直接复用", {"size": 10.5, "color": GREEN}),
])
rect(s, 6.92, 1.95, 5.80, 2.52, fill=CARD, line=LINE)
text(s, 7.16, 2.14, 5.35, 0.35, "数据规模（本组实测校验）", size=13.5, color=CYAN, bold=True)
for i, (k, v) in enumerate([("交通分区", "275 个"), ("充电桩总数", "23,441 个"),
                            ("时序长度", "4,344 小时"), ("时间跨度", "181 天 · 逐小时"),
                            ("原始文件", "12 个 CSV"), ("兴趣点 POI", "712,135 条")]):
    cx = 7.16 + (i % 3) * 1.80
    cy = 2.58 + (i // 3) * 0.78
    text(s, cx, cy, 1.75, 0.28, k, size=10, color=T3)
    text(s, cx, cy+0.26, 1.75, 0.35, v, size=14.5, color=T1, bold=True)

rect(s, 0.62, 4.48, 12.10, 1.85, fill=CARD, line=LINE)
text(s, 0.86, 4.66, 11.6, 0.35, "清洗：八类质量规则，先修复后丢弃，逐条记原因", size=13.5, color=GREEN, bold=True)
text(s, 0.86, 5.06, 11.6, 1.15, [
    ("① occupancy 越界(0~100)　② volume / duration 负值　③ 时间戳异常(未来时间 / 乱序)　④ 完全重复行　⑤ 零值语义区分(真实 0 vs 缺失 0)　⑥ 字段缺失　⑦ POI 坐标越界　⑧ 分区编号错位", {"size": 11, "color": T2, "space_after": 7}),
    ("★ 修复优先：能补的先补 —— Haversine 公式补缺失里程、速度表补缺失时长、里程×座位倍率修正票价（参考作业的成熟做法）", {"size": 11, "color": AMBER, "space_after": 7}),
    ("★ 补不了才丢，且每个被丢弃的行都带脏因子单独落隔离表 dq_zone_stat —— 可追溯，不含糊混在一起", {"size": 11, "color": AMBER}),
])
footer(s, 7, "数据来源与清洗", "苏静", "A", "B")
notes(s, "（约 1.5 分钟）\n"
         "先讲数据规模，数字要说准：12 个 CSV、275 分区、23441 桩、4344 小时、181 天。\n"
         "★ 『为什么不用爬虫』这段一定要主动讲 —— 老师给的模板第一步就是爬虫，你不解释等于少了一块。三个理由照念，语速放慢。\n"
         "清洗部分讲『先修复后丢弃』这个思路，这是我们和参考作业共同的亮点。\n"
         "★ 清洗前后对比表在这里（B-1 素材），B 同学主讲这页。")

# ══════════════════════════════════════════════════════════════
#  08 四层数仓
# ══════════════════════════════════════════════════════════════
s = slide()
header(s, 8, "数据仓库与分布式计算", "Data Warehouse and Distributed Computing",
       "Hive 四层数仓 · 3 个 MR 作业 · Spark 计算 · Sqoop 落地")
LAYERS = [
    ("ODS", "贴源保真", "1 张宽表 276 列\nCOUNT(*) = 4344", "#C2410C"),
    ("DWD", "清洗 + 补维度", "长表（分区×小时×指标）\n+ 分区维度表 + 质检表", "#B45309"),
    ("DWS", "轻度汇总", "分区 × 日 × 时汇总\n7 日滚动均值 / 峰谷差", "#0E7C6B"),
    ("ADS", "直接对应图表", "7 张应用表\n一表 = 一图表", "#1D4ED8"),
]
for i, (n, sub, det, c) in enumerate(LAYERS):
    x = 0.62 + i * 3.10
    rect(s, x, 1.95, 2.85, 1.62, fill=CARD, line=LINE)
    rect(s, x, 1.95, 2.85, 0.05, fill=RGBColor.from_string(c[1:]), shape=MSO_SHAPE.RECTANGLE)
    text(s, x+0.20, 2.14, 2.45, 0.4, n, size=19, color=RGBColor.from_string(c[1:]), bold=True)
    text(s, x+0.20, 2.60, 2.45, 0.3, sub, size=11.5, color=T1, bold=True)
    text(s, x+0.20, 2.95, 2.45, 0.55, det, size=10, color=T3, lh=1.35)
    if i < 3:
        text(s, x+2.87, 2.55, 0.25, 0.4, "▶", size=15, color=T3, align=PP_ALIGN.CENTER)
rect(s, 0.62, 3.80, 7.55, 2.68, fill=CARD, line=LINE)
text(s, 0.86, 3.96, 7.1, 0.35, "技术分工：为什么 MR 和 Spark 都要用", size=13.5, color=CYAN, bold=True)
text(s, 0.86, 4.34, 7.1, 2.08, [
    ("MapReduce（3 个作业）　WideToLong 宽表转长 · DataQualityCheck 八类质量检查 · PoiZoneJoin 71 万 POI 空间连接", {"size": 10.5, "color": T2, "space_after": 6}),
    ("Spark SQL　DWS 的 7 日滚动均值、POI 空间聚合、邻接矩阵展开、KMeans 聚类 —— 这几件事用 MR 写要几百行，Spark 几十行搞定", {"size": 10.5, "color": T2, "space_after": 6}),
    ("Sqoop export　ADS 表导出 MySQL uev_charge，配增量 checkpoint 水位，第二次运行自动跳过已导出行", {"size": 10.5, "color": T2, "space_after": 6}),
    ("★ 数据准确性闭环　同一个指标，MySQL 查询值必须等于 Hive 直查值（报告 6.3 节）—— 这是我们严谨性的硬证据", {"size": 10.5, "color": GREEN}),
])
placeholder(s, 8.42, 3.80, 4.30, 2.68, "〔血缘图 + 四层 count 截图〕",
            "B-2 四层表 count 对比\nB-3 血缘流转图\n（能看出 DWD < ODS）")
footer(s, 8, "数据仓库与分布式计算", "苏静", "A", "B")
notes(s, "（约 1.5 分钟）\n"
         "★ 这页是拿『熟练掌握 Hadoop / Spark / Hive』分的关键，一定要讲到『为什么 MR 和 Spark 都要用』—— 不是两个都用显得乱，而是各自解决不同类型的问题。\n"
         "★ 血缘图要能看出 ODS→DWD→DWS→ADS 每层做了什么加工。\n"
         "★ count 截图一定要能看出 DWD < ODS，这是清洗真的做了的证据。\n"
         "B 同学主讲这页。")

# ══════════════════════════════════════════════════════════════
#  09 创新点 ①②
# ══════════════════════════════════════════════════════════════
s = slide()
header(s, 9, "创新指标 ① 与 ②", "Innovation ① Supply-Demand Imbalance & ② Price Elasticity",
       "把「桩够不够用」和「调价有没有用」都量化出来")
rect(s, 0.62, 1.95, 5.95, 2.35, fill=CARD, line=LINE)
rect(s, 0.62, 1.95, 5.95, 0.05, fill=CYAN, shape=MSO_SHAPE.RECTANGLE)
text(s, 0.88, 2.16, 5.45, 0.4, "① 峰谷供需失衡指数", size=16, color=CYAN, bold=True)
text(s, 0.88, 2.62, 5.45, 0.8, [
    ("需求强度　D(z,t) = duration_h(z,t) / charge_count(z)", {"size": 12, "color": T1, "lh": 1.5, "space_after": 5}),
    ("全市基准　D均值(t) = Σduration_h(z,t) / Σcharge_count(z)", {"size": 12, "color": T1, "lh": 1.5, "space_after": 5}),
    ("失衡指数　I(z,t) = D(z,t) − D均值(t)", {"size": 13.5, "color": AMBER, "bold": True}),
])
text(s, 0.88, 3.66, 5.45, 0.75, [
    ("I > 0 → 该分区该时段需求高于全市平均 → 建议扩容或错峰引导", {"size": 10.5, "color": T2, "space_after": 4}),
    ("I < 0 → 供给富余 → 建议车辆调度、错峰引流", {"size": 10.5, "color": T2}),
])
rect(s, 6.78, 1.95, 5.94, 2.35, fill=CARD, line=LINE)
rect(s, 6.78, 1.95, 5.94, 0.05, fill=AMBER, shape=MSO_SHAPE.RECTANGLE)
text(s, 7.04, 2.16, 5.45, 0.4, "② 分时电价弹性分析", size=16, color=AMBER, bold=True)
text(s, 7.04, 2.62, 5.45, 0.75, [
    ("分组依据　按 e_price.csv 的时序标准差 σ_price 反推分时电价区", {"size": 12, "color": T1, "lh": 1.5, "space_after": 5}),
    ("★ 说明　inf.csv 实测无「是否分时电价」标识字段，该判定方法为本组自推导", {"size": 10.5, "color": AMBER, "lh": 1.4}),
])
text(s, 7.04, 3.58, 5.45, 0.8, [
    ("TOU 组 vs FLAT 组对比峰谷差与占用率", {"size": 10.5, "color": T2, "space_after": 4}),
    ("量化分时电价引导的实际削峰效果", {"size": 10.5, "color": T2}),
])
rect(s, 0.62, 4.50, 12.10, 1.85, fill=CARD, line=LINE)
text(s, 0.88, 4.68, 11.6, 0.35, "这两个指标解决了什么问题", size=13.5, color=GREEN, bold=True)
text(s, 0.88, 5.08, 11.6, 1.2, [
    ("① 归一化消除了分区规模差异 —— 拿『平均充电时长』直接比大小分区没有意义，除以该分区桩数后才可比", {"size": 11.5, "color": T2, "space_after": 7}),
    ("② 把『该不该调价』变成一个可以拿数字回答的问题：TOU 组峰谷差比 FLAT 组低多少个百分点", {"size": 11.5, "color": T2, "space_after": 7}),
    ("③ 两者互相印证 —— 失衡指数高的分区，正是调价引导潜力最大的分区", {"size": 11.5, "color": T2}),
])
footer(s, 9, "创新指标 ① 与 ②", "姬婷婷", "A", "E")
notes(s, "（约 2 分钟）★ 你的主讲页，讲慢讲透。\n"
         "① 公式先讲含义再讲式子：D 是『每个桩平均被用多久』，D均值 是全市平均，I 是『这个分区比全市平均高多少』。\n"
         "★ 关键一句：直接比平均时长没有意义，因为大分区天然高，除以桩数才是可比的。\n"
         "② ★ 主动讲『数据集里没有分时电价标识字段，这个判定方法是我们自己推导的』—— 这是加分项，别藏着。\n"
         "结尾讲两个指标互相印证，收在『拿数字回答运营问题』上。")

# ══════════════════════════════════════════════════════════════
#  10 创新点 ③④ + 布点建议
# ══════════════════════════════════════════════════════════════
s = slide()
header(s, 10, "创新指标 ③ 与 ④", "Innovation ③ Demand Forecasting & ④ Zone Clustering",
       "从「预测需求」到「发现分区类型」再到「给出布点建议」")
rect(s, 0.62, 1.95, 3.90, 2.55, fill=CARD, line=LINE)
rect(s, 0.62, 1.95, 3.90, 0.05, fill=PURP, shape=MSO_SHAPE.RECTANGLE)
text(s, 0.86, 2.14, 3.45, 0.4, "③ 充电需求预测", size=15, color=PURP, bold=True)
text(s, 0.86, 2.58, 3.45, 1.8, [
    ("★ 三模型横向竞优", {"size": 11.5, "color": AMBER, "bold": True, "space_after": 3}),
    ("滑动平均 / 同星期同比 / 多元回归", {"size": 10.5, "color": T2, "space_after": 8}),
    ("统一 MAPE 比较后选优 + 竞优对比图", {"size": 10.5, "color": T2, "space_after": 8}),
    ("误差评估四件套", {"size": 11.5, "color": AMBER, "bold": True, "space_after": 3}),
    ("MAPE + MAE + RMSE + 基线对比 + ±1.5σ 区间", {"size": 10.5, "color": T2, "space_after": 8}),
    ("不用 LSTM：可解释性与工程可复现性优先", {"size": 10, "color": T3}),
])
rect(s, 4.72, 1.95, 3.90, 2.55, fill=CARD, line=LINE)
rect(s, 4.72, 1.95, 3.90, 0.05, fill=GREEN, shape=MSO_SHAPE.RECTANGLE)
text(s, 4.96, 2.14, 3.45, 0.4, "④ 分区聚类画像", size=15, color=GREEN, bold=True)
text(s, 4.96, 2.58, 3.45, 1.8, [
    ("Spark MLlib KMeans（k=4，seed=42）", {"size": 10.5, "color": T2, "space_after": 8}),
    ("7 维特征 · StandardScaler 标准化", {"size": 10.5, "color": T2, "space_after": 8}),
    ("★ 肘部法选 k（WCSS 曲线 k=2~6）", {"size": 10.5, "color": T2, "space_after": 8}),
    ("四类：紧张型 / 过剩型 / 稳定型 / 潜力型", {"size": 10.5, "color": T2, "space_after": 8}),
    ("★ 与①互证：紧张型簇平均失衡指数最高", {"size": 10.5, "color": AMBER}),
])
rect(s, 8.82, 1.95, 3.90, 2.55, fill=CARD, line=LINE)
rect(s, 8.82, 1.95, 3.90, 0.05, fill=RED, shape=MSO_SHAPE.RECTANGLE)
text(s, 9.06, 2.14, 3.45, 0.4, "布点扩容建议", size=15, color=RED, bold=True)
text(s, 9.06, 2.58, 3.45, 1.8, [
    ("由规则表自动生成，非人工挑选", {"size": 10.5, "color": T2, "space_after": 8}),
    ("每个分区：建议类型 / 建议数量 / 优先级 / 依据 / 预期效果", {"size": 10.5, "color": T2, "space_after": 8}),
    ("紧张型 → 优先扩容", {"size": 10.5, "color": T2, "space_after": 4}),
    ("过剩型 → 调度引流　潜力型 → 提前布局", {"size": 10.5, "color": T2}),
])
rect(s, 0.62, 4.70, 12.10, 1.62, fill=CARD, line=LINE)
text(s, 0.88, 4.88, 11.6, 0.35, "四个指标构成一条完整链路", size=13.5, color=CYAN, bold=True)
text(s, 0.88, 5.28, 11.6, 0.95, [
    ("① 失衡指数　回答『哪里供不应求』　→　② 电价弹性　回答『能不能靠调价缓解』　→　③ 需求预测　回答『未来会怎样』　→　④ 聚类画像　回答『这类分区整体该怎么管』　→　布点建议　回答『具体该怎么做』", {"size": 11.5, "color": T2, "space_after": 7}),
    ("★ 从规则驱动（①②③）到数据驱动发现未知结构（④），两种思路互补 = 分析维度的完整性", {"size": 11.5, "color": AMBER}),
])
footer(s, 10, "创新指标 ③ 与 ④", "姬婷婷", "A", "E")
notes(s, "（约 2 分钟）★ 你的第二个主讲页。\n"
         "③ ★ 强调『竞优』而不是『我用了某个模型』—— 三个模型都跑了，用 MAPE 比较后选出来，这才叫方法论。\n"
         "★ 被问『为什么不用 LSTM』：「本课题关注需求趋势的可解释性，为增强工程可复现性与结果可审计性采用统计方法，深度学习作为扩展方向已在展望中说明。」\n"
         "④ ★ 这是老师标红『数据分析』最想看到的：三个指标都是我们定义的，第四个是让数据自己告诉我们分区有哪几类。\n"
         "★ 互证是这页的高光：紧张型簇的平均失衡指数显著最高 —— 两种独立方法得到一致结论。\n"
         "结尾把五个环节串成一条链，落到『具体该怎么做』。")

# ══════════════════════════════════════════════════════════════
#  11 系统演示
# ══════════════════════════════════════════════════════════════
s = slide()
header(s, 11, "系统实现与演示", "System Implementation and Demonstration",
       "6 个页面 · 10 张图表 · 7 种图形类型 · 16 个 REST API")
placeholder(s, 0.62, 1.95, 5.95, 2.35, "〔首页运营大屏〕",
            "C-2 素材：首页 KPI 指标卡 + 分区着色地图\n热力图 / 失衡 TOP10 / 电价双曲线 / 预测曲线")
placeholder(s, 6.78, 1.95, 5.94, 2.35, "〔布点扩容建议看板〕",
            "C-2 素材：布点建议清单 + 聚类结果着色地图\n筛选前后对比（证明交互是真的）")
rect(s, 0.62, 4.50, 12.10, 2.02, fill=CARD, line=LINE)
text(s, 0.88, 4.66, 11.6, 0.35, "现场演示动线（2 分 10 秒）", size=13.5, color=GREEN, bold=True)
text(s, 0.88, 5.04, 11.6, 1.42, [
    ("① 首页大屏 20″　看 KPI 指标卡与全市分区热力图 —— 全市桩车比与紧张分区一目了然", {"size": 11, "color": T2, "space_after": 5}),
    ("② 分区详情 25″　点进南山分区，看 24 小时供需曲线与失衡指数 —— 说明『为什么这个分区紧』", {"size": 11, "color": T2, "space_after": 5}),
    ("③ 筛联动 25″　改时段筛选条件，图表跟着变 —— 证明筛选是真联动不是摆设", {"size": 11, "color": T2, "space_after": 5}),
    ("④ 布点建议 30″　展示前 10 条建议清单与导出 —— 落到『具体该怎么做』", {"size": 11, "color": T2, "space_after": 5}),
    ("⑤ 兜底说明 30″　若现场系统异常，播放提前录制的演示视频（本页已内嵌关键截图）", {"size": 10.5, "color": T3}),
])
footer(s, 11, "系统实现与演示", "贺欢欢", "A", "C")
notes(s, "（约 2 分 10 秒）★ 你的主讲页，严格按演示脚本走，别临场发挥。\n"
         "★ 关键：第③步一定要真的改一次筛选条件让图变，评委最爱看这个。\n"
         "★ 万一现场起不来 —— 本页内嵌了 3 张关键截图，直接讲截图，不要慌。\n"
         "C 同学主讲这页。")

# ══════════════════════════════════════════════════════════════
#  12 系统测试与性能
# ══════════════════════════════════════════════════════════════
s = slide()
header(s, 12, "系统测试与性能", "System Testing and Performance",
       "接口功能测试 · 数据准确性测试 · 缓存性能对比")
rect(s, 0.62, 1.95, 3.90, 2.30, fill=CARD, line=LINE)
text(s, 0.86, 2.14, 3.45, 0.35, "接口功能测试", size=14, color=CYAN, bold=True)
text(s, 0.86, 2.54, 3.45, 1.6, [
    ("16 个接口逐个 Postman 实测并截图", {"size": 10.5, "color": T2, "space_after": 7}),
    ("测试用例表 ≥15 条（含实际输出与结论）", {"size": 10.5, "color": T2, "space_after": 7}),
    ("异常降级：参数非法返回友好提示，不抛 500", {"size": 10.5, "color": T2, "space_after": 7}),
    ("★ 全部截图均为本机实跑", {"size": 10.5, "color": GREEN}),
])
rect(s, 4.72, 1.95, 3.90, 2.30, fill=CARD, line=LINE)
text(s, 4.96, 2.14, 3.45, 0.35, "数据准确性测试", size=14, color=PURP, bold=True)
text(s, 4.96, 2.54, 3.45, 1.6, [
    ("同一指标：MySQL 查询值 ≡ Hive 直查值", {"size": 10.5, "color": T2, "space_after": 7}),
    ("两条路径（B 的 ads_* 与 E 的 insight_*）口径必须完全一致", {"size": 10.5, "color": T2, "space_after": 7}),
    ("行数校验：Sqoop 导出行数 = MySQL COUNT(*)", {"size": 10.5, "color": T2, "space_after": 7}),
    ("★ 这是我们严谨性最强的硬证据", {"size": 10.5, "color": GREEN}),
])
rect(s, 8.82, 1.95, 3.90, 2.30, fill=CARD, line=LINE)
text(s, 9.06, 2.14, 3.45, 0.35, "性能与可复现", size=14, color=AMBER, bold=True)
text(s, 9.06, 2.54, 3.45, 1.6, [
    ("Redis 缓存前后响应时间对比（两个毫秒数）", {"size": 10.5, "color": T2, "space_after": 7}),
    ("Spark 作业耗时 / MR 优化前后对比", {"size": 10.5, "color": T2, "space_after": 7}),
    ("第二台电脑从零启动验证通过", {"size": 10.5, "color": T2, "space_after": 7}),
    ("★ 不依赖任何个人绝对路径", {"size": 10.5, "color": GREEN}),
])
placeholder(s, 0.62, 4.48, 12.10, 1.85, "〔测试用例表 + 缓存前后对比数据 + Postman 截图〕",
            "D-2 测试用例表（≥15 条）　D-3 缓存前后毫秒数　D-1 接口 Postman 截图　B-7 作业耗时")
footer(s, 12, "系统测试与性能", "杨珊珊", "A", "D / B")
notes(s, "（约 1.5 分钟）\n"
         "★ 强调两点：① 所有截图都是本机实跑，不是网上找的 ② 我们做了数据准确性测试 —— MySQL 值和 Hive 直查值一致，这是最体现严谨性的一条。\n"
         "★ 缓存对比一定要给具体毫秒数，不要只说『快很多』。\n"
         "D 同学主讲这页。")

# ══════════════════════════════════════════════════════════════
#  13 团队分工
# ══════════════════════════════════════════════════════════════
s = slide()
header(s, 13, "团队分工", "Team Division of Labor",
       "五个人 · 五层技术 · 边界不重叠 · 每层都有可截图可署名的实物交付")
TEAM = [
    ("彭忠燕", "A · 数据接入 + 部署集成 + 报告统稿",
     ["Flume 采集配置、Docker Compose 一键编排", "端到端冒烟测试脚本、RUNBOOK 运行手册", "报告七章统稿、答辩 PPT 全部制作"], CYAN),
    ("苏　静", "B · 数据仓库 + 分布式计算",
     ["Hive 四层数仓（16 张表）", "3 个 MapReduce 作业 + Spark 计算 ADS", "Sqoop 导出 + 4 张 MySQL 视图"], AMBER),
    ("贺欢欢", "C · 可视化呈现",
     ["《数据字典》12 个 CSV 全量字段", "深圳 275 分区地图底图", "10 张图表 / 6 个页面 / 演示视频"], PURP),
    ("杨珊珊", "D · 后端服务",
     ["Spring Boot 16 个 REST API + JWT 鉴权", "MySQL 表设计与索引、Redis 缓存策略", "接口文档、测试用例表、Postman 截图"], GREEN),
    ("姬婷婷", "E · 分析与模型",
     ["《指标定义表》15 项指标口径（组内总闸门）", "四个创新指标：三模型竞优 + 误差评估 + KMeans 聚类", "布点扩容建议规则与清单"], RED),
]
for i, (nm, role, items, c) in enumerate(TEAM):
    x = 0.62 + i * 2.47
    rect(s, x, 1.95, 2.25, 4.10, fill=CARD, line=LINE)
    rect(s, x, 1.95, 2.25, 0.05, fill=c, shape=MSO_SHAPE.RECTANGLE)
    text(s, x+0.18, 2.16, 1.95, 0.4, nm, size=17, color=c, bold=True, align=PP_ALIGN.CENTER)
    text(s, x+0.14, 2.62, 2.05, 0.6, role, size=10, color=T1, align=PP_ALIGN.CENTER, lh=1.3)
    body = [("· " + it, {"size": 9.5, "color": T2, "lh": 1.45, "space_after": 8}) for it in items]
    text(s, x+0.16, 3.38, 1.98, 2.5, body)
text(s, 0.62, 6.25, 12.10, 0.4,
     "★ 分工原则：一层技术一个人，边界不重叠，每层都有可截图、可署名的实物交付物　|　报告逐章署名　|　Git 提交记录带岗位标签",
     size=11, color=AMBER, align=PP_ALIGN.CENTER)
footer(s, 13, "团队分工", "彭忠燕", "A", "全体")
notes(s, "（约 40 秒）不要逐人念，念一句总原则 + 强调『每层都有可截图、可署名的实物』即可。\n"
         "★ 老师明确要求『哪部分哪位同学』，这页 + 报告逐章署名 + Git 提交记录三处呼应，组内互评不吃亏。")

# ══════════════════════════════════════════════════════════════
#  14 总结与展望
# ══════════════════════════════════════════════════════════════
s = slide()
header(s, 14, "总结与展望", "Conclusion and Future Work",
       "六个层面的技术归纳，以及我们还没做完的事")
rect(s, 0.62, 1.95, 7.55, 4.10, fill=CARD, line=LINE)
text(s, 0.88, 2.14, 7.05, 0.35, "总结：六个层面的技术归纳", size=14, color=CYAN, bold=True)
SUM = [
    ("数据接入层", "Flume 增量采集 + SHA256 完整性校验 + 数据目录自动探测", CYAN),
    ("数仓建模层", "Hive 四层 16 张表，宽表转长 + 8 类质量规则 + 脏行隔离表", AMBER),
    ("分析创新层", "4 个创新指标，其中聚类画像实现从规则驱动到数据驱动的跨越", PURP),
    ("服务性能层", "Spring Boot 16 接口 + Redis 缓存 + 视图作契约层的解耦设计", GREEN),
    ("可视化层", "10 张图表 7 种图形类型 + 6 个页面 + 多维筛选联动", RED),
    ("工程化层", "契约驱动协作 + Docker 一键复现 + 冒烟测试 + 双向数据校验", CYAN),
]
for i, (k, v, c) in enumerate(SUM):
    y = 2.60 + i * 0.55
    rect(s, 0.88, y, 0.06, 0.42, fill=c, shape=MSO_SHAPE.RECTANGLE)
    text(s, 1.06, y+0.02, 1.75, 0.35, k, size=12, color=c, bold=True)
    text(s, 2.86, y+0.02, 5.0, 0.4, v, size=11, color=T2)
rect(s, 8.42, 1.95, 4.30, 4.10, fill=CARD, line=LINE)
text(s, 8.66, 2.14, 3.85, 0.35, "展望：还差什么", size=14, color=AMBER, bold=True)
text(s, 8.66, 2.58, 3.85, 3.3, [
    ("① 实时化　当前是离线 T+1 批量链路，Flume 增量机制已就位，接入 Kafka 与 Spark Streaming 即可做到准实时供给与调度决策", {"size": 10.5, "color": T2, "lh": 1.45, "space_after": 10}),
    ("② 预测模型深化　当前用统计方法保证可解释与可复现，后续可引入图神经网络（数据集原论文方向）提升预测精度", {"size": 10.5, "color": T2, "lh": 1.45, "space_after": 10}),
    ("③ 决策闭环　当前输出的是建议清单，后续可接入实际选址与调度执行系统，形成『预测—建议—执行—反馈』闭环", {"size": 10.5, "color": T2, "lh": 1.45, "space_after": 10}),
    ("④ 更多气象与外部特征　当前仅 2 个气象站映射到分区，可接入更多站点与交通流数据提升归因能力", {"size": 10.5, "color": T2, "lh": 1.45}),
])
footer(s, 14, "总结与展望", "彭忠燕", "A", "全体")
notes(s, "（约 1 分钟）总结按六个层面快速过，每个层面一句话。\n"
         "★ 展望要说得诚实且具体 —— 这反而加分。老师原话『保证数量和质量』，不足与改进方向写清楚比藏着好。\n"
         "★ 收尾句：『我们最大的收获不是这个系统本身，而是用契约驱动的方式，让五个人在没有大量会议的情况下做出一件能跑起来的东西。』")

# ══════════════════════════════════════════════════════════════
#  15 致谢
# ══════════════════════════════════════════════════════════════
s = slide()
rect(s, 0, 0, W, 0.09, fill=CYAN, shape=MSO_SHAPE.RECTANGLE)
rect(s, 0, H-0.09, W, 0.09, fill=CYAN, shape=MSO_SHAPE.RECTANGLE)
text(s, 1.0, 2.15, 11.3, 0.8, "请评审老师批评指正", size=42, color=T1, bold=True, align=PP_ALIGN.CENTER)
rect(s, 5.42, 3.12, 2.5, 0.05, fill=CYAN, shape=MSO_SHAPE.RECTANGLE)
text(s, 1.0, 3.52, 11.3, 0.4, "汇报小组：第 02 组", size=17, color=T2, align=PP_ALIGN.CENTER)
text(s, 1.0, 4.02, 11.3, 0.4,
     "彭忠燕　苏　静　贺欢欢　杨珊珊　姬婷婷", size=16, color=T1, align=PP_ALIGN.CENTER)
text(s, 1.0, 4.58, 11.3, 0.4, "指导教师：赵　晨", size=15, color=T2, align=PP_ALIGN.CENTER)
text(s, 1.0, 5.35, 11.3, 0.35, "明德至善　博学笃行", size=15, color=CYAN, align=PP_ALIGN.CENTER)
text(s, 1.0, 5.90, 11.3, 0.3,
     "数据来源：UrbanEV 开源数据集（CC0 1.0）· https://github.com/whewhewhenew/UrbanEV · arXiv:2309.05259",
     size=10.5, color=T3, align=PP_ALIGN.CENTER)
notes(s, "致谢页。\n"
         "★ 问答环节预案（8 问）：\n"
         "1 数据哪来的 → UrbanEV，CC0 协议，GitHub 可查，论文 arXiv:2309.05259\n"
         "2 为什么用 Hadoop → 275 分区 × 4344 小时 × 6 指标，长表化后约 717 万行，叠加 71 万 POI，含宽转长/空间连接/多维聚合三类重计算\n"
         "3 创新点是什么 → 失衡指数 + 电价弹性 + 需求预测与布点建议 + 分区聚类画像\n"
         "4 为什么不用 LSTM → 可解释性与工程可复现性优先，深度学习列入展望\n"
         "5 为什么不用爬虫 → 三理由（真实性/可复现/合规），且已实现 Flume 增量采集\n"
         "6 为什么不用 FineBI → 课程适配性/可扩展性/零授权成本，自建看板覆盖 BI 等价能力\n"
         "7 数据是分区级还是桩级 → 官方清洗后为分区级 275 个，报告中已说明\n"
         "8 各模块谁做的 → 报告逐章署名 + Git 提交记录带岗位标签\n"
         "★ 数字口径统一：275 分区 / 23441 桩 / 4344 小时 / 12 个 CSV / 4 个创新指标 / 16 个 API / 10 张图 / 15 页 PPT")

# ── 保存 ─────────────────────────────
out = OUT / "第02组_城市充电桩数据分析系统_答辩PPT.pptx"
prs.save(str(out))
print(f"✓ 已生成 {out}")
print(f"  页数：{len(prs.slides.__iter__.__self__._sldIdLst)}")
