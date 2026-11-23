# -*- coding: utf-8 -*-
"""
update_ppt_text.py —— 用实测数字更新 PPT 第 7/9/10 页的文本

★ 为什么
  PPT 第 9/10 页是创新点页，原来只有公式没有数字。
  「创新点」在答辩里靠的是**结论**，而结论必须带数字。
  现在数据已经由 python_etl.py 算出来了，就该填进去。

用法：python scripts/update_ppt_text.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Pt

REPO = Path(__file__).resolve().parent.parent
PPTX = REPO / "docs" / "ppt" / "第02组_城市充电桩数据分析系统_答辩PPT.pptx"
SRC = REPO / "data" / "etl_out"

# 页面 → [(文本框原文片段, 新文本)]
UPDATES = {
    7: [
        ("① occupancy 越界", None),   # 第 7 页下方八类规则，单独处理
    ],
    9: [
        ("需求强度", "需求强度　D(z,t) = duration_h(z,t) / charge_count(z)\n"
                     "全市基准　D̄(t) = Σ_z duration_h(z,t) / Σ_z charge_count(z)\n"
                     "★ 实测：每桩小时均 0.1574 小时（≈9.4 分钟）· 275 分区"),
        ("I > 0", "I > 0 → 需求高于全市同期 → 建议扩容或错峰引导\n"
                  "I < 0 → 供给富余 → 建议调度引流\n"
                  "★ 实测：275 分区均现失衡，TOP20 达 +0.88 时/桩"),
        ("分组依据", "分组依据　按 e_price + s_price 的时序标准差 σ 做 KMeans 二聚类\n"
                     "★ 轮廓系数 0.8132（>0.6，分群成立）\n"
                     "★ TOU 31 区（σ 0.4700）vs FLAT 244 区（σ 0.0349）· 差 13.5 倍"),
        ("TOU 组 vs FLAT", "TOU vs FLAT 对比 24 小时峰谷差与占用率\n"
                           "量化分时电价引导的削峰效果\n"
                           "★ 两组 σ 差 13.5 倍，分群高度可分"),
    ],
    10: [
        ("三模型横向竞优", "★ 三模型横向竞优（统一 MAPE 选优）\n"
                          "朴素基线 lag1　20.720%　← 最优\n"
                          "线性回归　　　　24.628%\n"
                          "随机森林　　　　24.853%\n"
                          "回测 2023-02-15~28，样本 3,850 条\n"
                          "★ 序列接近随机游走，复杂模型不划算"),
        ("Spark MLlib", "KMeans（k=4，seed=42）· 7 维特征\n"
                        "平均/峰值占用率 · 失衡指数\n"
                        "σ_price · 桩数 · POI 数\n"
                        "★ 产出：275 分区 4 类画像 + WCSS 肘部曲线"),
        ("由规则表自动生成", "由规则表自动生成，非人工挑选\n"
                             "紧张型（+30%）/ 潜力型（+20%）\n"
                             "过剩型（调度引流）\n"
                             "★ 实测：167 分区入选，优先级 1/2/3\n"
                             "★ 含类型/数量/优先级/文字依据"),
    ],
}


def set_para_texts(shape, new_text: str):
    """把一个文本框的内容替换为多段（保留原第一段的字体设置）"""
    tf = shape.text_frame
    paras = tf.paragraphs
    # 记下第一段的字体样式
    proto = paras[0]
    size = proto.font.size
    color = None
    try:
        color = proto.font.color.rgb
    except Exception:
        pass
    bold = proto.font.bold
    name = proto.font.name

    lines = new_text.split("\n")
    # 清空
    for p in list(paras)[1:]:
        p._element.getparent().remove(p._element)
    tf.paragraphs[0].text = lines[0]
    for ln in lines[1:]:
        np = tf.add_paragraph()
        np.text = ln
    # 统一应用字体
    for p in tf.paragraphs:
        p.font.size = size or Pt(11)
        if color is not None:
            p.font.color.rgb = color
        p.font.bold = bold
        if name:
            p.font.name = name


def main():
    if not PPTX.exists():
        print("[错误] 找不到 PPT")
        return 1
    prs = Presentation(str(PPTX))
    print("=" * 74)
    print(" 用实测数字更新 PPT 文本")
    print("=" * 74)

    n = 0
    for page, items in UPDATES.items():
        if page > len(prs.slides):
            continue
        slide = prs.slides[page - 1]
        for key, new in items:
            if new is None:
                continue
            hit = False
            for sh in slide.shapes:
                if not sh.has_text_frame:
                    continue
                if key in sh.text_frame.text:
                    set_para_texts(sh, new)
                    hit = True
                    n += 1
                    print(f"  第 {page:2d} 页：✓ 已更新「{key}」")
                    break
            if not hit:
                print(f"  第 {page:2d} 页：! 未找到含「{key}」的文本框")

    # 第 7 页：八类质量规则 → 换成实测结果
    slide7 = prs.slides[6]
    for sh in slide7.shapes:
        if sh.has_text_frame and "① occupancy 越界" in sh.text_frame.text:
            set_para_texts(sh,
                "实测（181 天 / 4,344 小时 / 6 指标 × 1,194,600 行）：\n"
                "① occupancy 越界　　0 条　② volume/duration 负值　0 条　③ 时间戳异常　0 条\n"
                "④ 重复时间戳　　　　0 条　⑤ 全零值段　　32,307~65,365 条（真实业务状态，保留并标记）\n"
                "⑥ 电价负值　　　　　0 条　⑦ 分区坐标缺失　1 条（132 桩，占 0.56%，绘图时剔除）\n"
                "⑧ 连续零值段　　　　已标记 is_zero，不丢弃　★ 结论：原始数据质量优于预期，"
                "越界与重复均为 0")
            n += 1
            print("  第  7 页：✓ 已更新「八类质量规则」为实测结果")
            break

    prs.save(str(PPTX))
    print()
    print(f" 完成：更新 {n} 处 → {PPTX.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
