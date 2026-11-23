# -*- coding: utf-8 -*-
"""
fill_ppt.py —— 把真实图表贴进答辩 PPT 的占位框

★ 为什么 A 岗自己做
  PPT 第 5/7/8/10/11 页原本是占位框，等 C 岗交图。
  但 C 岗至 11/23 零交付，而图已经由 make_charts.py 用真实 ADS 数据生成好了，
  与其等不如直接贴上 —— 反正数据是真的。

做法：
  1. 打开 docs/ppt/第02组_..._答辩PPT.pptx
  2. 按页查找标题含关键词的形状，替换其下方的占位框（标题里带「〔」的形状）
  3. 插入对应 PNG，按占位框尺寸等比缩放并居中
  4. 保留原有占位说明文字作为图注（移到图下方）

用法：python scripts/fill_ppt.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.util import Emu, Inches, Pt

REPO = Path(__file__).resolve().parent.parent
PPTX = REPO / "docs" / "ppt" / "第02组_城市充电桩数据分析系统_答辩PPT.pptx"
CHARTS = REPO / "docs" / "charts"
SHOTS = REPO / "docs" / "screenshots"

# 页码 → [(占位框关键词, 图片路径, 图注)]
PLAN = {
    5:  [("〔用例图〕", None, "图 5-1 系统用例图（三类角色 / 14 个系统用例）")],
    7:  [("〔", None, "")],
    8:  [("〔血缘图 + 四层 count 截图〕", None, "图 8-1 四层数仓血缘与规模实测")],
    9:  [], 10: [], 11: [],
    12: [("〔", None, "")],
}


def find_placeholder(slide, keyword):
    """找占位区。

    ★ PPT 的占位区是「背景矩形 + 标题文本框 + 说明文本框」三件套：
      背景矩形是真正的占位区（尺寸大），文本框只是它的标签。
      如果直接拿含关键词的文本框当占位区，它的尺寸只有 0.35 英寸高，
      插进去的图会被缩成一小块 —— 这是第一版踩的坑。
    所以：先按关键词定位到标签文本框，再在同区域找尺寸最大的
    AUTO_SHAPE 矩形作为真正的占位区。
    """
    label = None
    for sh in slide.shapes:
        if sh.has_text_frame and keyword in sh.text_frame.text:
            label = sh
            break
    if label is None:
        return None, []
    L, T = label.left, label.top
    # 同区域内的背景矩形：左上角接近、尺寸明显更大
    best, best_area = None, 0
    for sh in slide.shapes:
        if sh.shape_type != 1:            # 1 = AUTO_SHAPE
            continue
        if abs(sh.left - L) > Inches(0.35):
            continue
        if not (T - Inches(1.2) <= sh.top <= T + Inches(0.35)):
            continue
        area = sh.width * sh.height
        if area > best_area:
            best, best_area = sh, area
    if best is None:
        best = label
    # 同区域所有文本框（标题 + 说明）待清理
    siblings = []
    for sh in slide.shapes:
        if sh is best or not sh.has_text_frame:
            continue
        if not sh.text_frame.text.strip():
            continue
        if abs(sh.left - L) > Inches(0.35):
            continue
        if T - Inches(0.1) <= sh.top <= T + Inches(1.6):
            siblings.append(sh)
    return best, siblings


def clean_sibling_labels(slide, ph, old_text):
    """删掉与占位框同区域、且内容是占位说明的文本框。

    PPT 的占位区是「矩形 + 标题文本框 + 说明文本框」三件套，
    只替换矩形会留下两个文字框压在图上，必须一并清掉。
    """
    L, T = ph.left, ph.top
    W, H = ph.width, ph.height
    removed = 0
    for sh in list(slide.shapes):
        if sh is ph or not sh.has_text_frame:
            continue
        txt = sh.text_frame.text.strip()
        if not txt:
            continue
        # 在占位框纵向范围内、且位于占位框左侧同一起始列的文本框
        if not (T - Inches(0.35) <= sh.top <= T + H):
            continue
        if abs(sh.left - L) > Inches(1.2):
            continue
        # 识别为占位说明：含〔 或 含「素材」「草稿」「D-」「C-」等交付指引
        if "〔" in txt or "素材" in txt or "草稿" in txt or "组长负责" in txt \
           or txt.startswith(("D-", "C-", "B-")):
            sh._element.getparent().remove(sh._element)
            removed += 1
    return removed

def replace_with_image(slide, ph, img_path: Path, caption: str = ""):
    """删掉占位框，插入图片（同区域，等比缩放居中），可加图注"""
    left, top, width, height = ph.left, ph.top, ph.width, ph.height
    # 记录占位框里的说明文字作为图注
    old_text = ph.text_frame.text.strip()
    sp = ph._element
    sp.getparent().remove(sp)

    with Image.open(img_path) as im:
        iw, ih = im.size
    box_ratio = width / height
    img_ratio = iw / ih
    if img_ratio > box_ratio:          # 图更宽 → 以宽为准
        new_w = width
        new_h = int(width / img_ratio)
    else:                              # 图更高 → 以高为准
        new_h = height
        new_w = int(height * img_ratio)
    new_left = int(left + (width - new_w) / 2)
    new_top = int(top + (height - new_h) / 2)

    pic = slide.shapes.add_picture(str(img_path), Emu(new_left), Emu(new_top),
                                   width=Emu(new_w), height=Emu(new_h))
    return pic, old_text


def add_caption(slide, left, top, width, text):
    if not text:
        return
    tb = slide.shapes.add_textbox(left, top, width, Inches(0.28))
    tf = tb.text_frame
    tf.text = text
    tf.paragraphs[0].font.size = Pt(10.5)
    tf.word_wrap = True


def main():
    if not PPTX.exists():
        print("[错误] 找不到 PPT:", PPTX)
        return 1
    prs = Presentation(str(PPTX))
    print("=" * 74)
    print(f" 往 PPT 贴图：{PPTX.name}（{len(prs.slides)} 页）")
    print("=" * 74)

    # 第 6 页架构图已在生成时嵌入，跳过
    # 第 9/10 页是创新点公式页，贴对应的分析图
    # 第 11 页系统演示 → 贴大屏
    # (页码, 占位框标题关键词, 图片, 图注)
    plan = [
        (5,  "〔需求分析用例图〕", CHARTS / "05_需求分析用例图.png",
             "图 5-1　系统用例图（三类使用者 · 14 个系统用例）"),
        (8,  "〔血缘图 + 四层 count 截图〕", CHARTS / "06_四层数仓规模对比.png",
             "图 8-1　四层数仓流转与实测规模"),
        (11, "〔首页运营大屏〕", SHOTS / "01_首页大屏.png",
             "图 11-1　系统首页运营大屏"),
        (11, "〔布点扩容建议看板〕", SHOTS / "04_布点建议大屏.png",
             "图 11-2　布点扩容建议看板"),
        (12, "〔测试用例表", CHARTS / "10_数据质量实测结果.png",
             "图 12-1　数据准确性测试：六项指标清洗前后实测"),
    ]

    done = 0
    for page, keyword, img, cap in plan:
        if page > len(prs.slides):
            continue
        slide = prs.slides[page - 1]
        if img is None or not img.exists():
            print(f"  第 {page:2d} 页：跳过（无可用图片）")
            continue
        target, siblings = find_placeholder(slide, keyword)
        if target is None:
            print(f"  第 {page:2d} 页：未找到占位框（关键词 {keyword}）")
            continue
        try:
            pic, old = replace_with_image(slide, target, img, cap)
            # ★ 清掉占位区的标题与说明文本框（否则会压在图上）
            cleaned = 0
            for sh in siblings:
                try:
                    sh._element.getparent().remove(sh._element)
                    cleaned += 1
                except Exception:
                    pass
            done += 1
            print(f"  第 {page:2d} 页：✓ 已贴 {img.name}"
                  f"（清理说明文字 {cleaned} 个）")
        except Exception as e:
            print(f"  第 {page:2d} 页：✗ 失败 {e}")

    prs.save(str(PPTX))
    print()
    print(f" 完成：共贴入 {done} 张图 → {PPTX.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
