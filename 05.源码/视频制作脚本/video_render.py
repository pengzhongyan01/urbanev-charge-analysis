# -*- coding: utf-8 -*-
"""
视频画面渲染引擎
================
生成 1920x1080 的演示视频画面：
  - 章节卡（华文行楷 + 宣纸底）
  - IDE 风格代码页（真实源码 + 红框 + 红箭头 + 中文批注）
  - 图表页 / 大屏页（真实项目图片 + 红框标注）
  - 表格页 / 要点页 / 公式卡页

所有内容均来自本仓库真实代码与真实产出图片，不编造。
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(r"D:/一系列作业/java后端/大作业/urbanev-charge-analysis")
OUT = Path(os.environ.get("TEMP", r"C:/Users/彭忠燕/AppData/Local/Temp")) / "uev_video_frames"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1920, 1080
FPS = 30

# ── 字体 ────────────────────────────────────────────────────────────────────
F_KAISHU = r"C:/Windows/Fonts/STXINGKA.TTF"   # 华文行楷（章节卡主标题）
F_KAI = r"C:/Windows/Fonts/simkai.ttf"        # 楷体
F_HEI = r"C:/Windows/Fonts/simhei.ttf"        # 黑体
F_MSYH = r"C:/Windows/Fonts/msyh.ttc"         # 微软雅黑
# 代码用宋体：等宽 + 完整覆盖中文字形（Cascadia Mono 无中文字形，会渲染成方框）
F_MONO = r"C:/Windows/Fonts/simsun.ttc"

_cache: dict = {}


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def f_kaishu(sz: int):
    return font(F_KAISHU, sz)


def f_kai(sz: int):
    return font(F_KAI, sz)


def f_hei(sz: int):
    return font(F_HEI, sz)


def f_msyh(sz: int):
    return font(F_MSYH, sz)


def f_mono(sz: int):
    return font(F_MONO, sz)


# ── 字形兜底 ────────────────────────────────────────────────────────────────
# simhei / simkai 缺少部分符号字形（U+2212 减号、U+2713 对勾会渲染成空心方框）。
# 检测文本中是否存在这些字符，自动改用微软雅黑（字形齐全）。
_MISSING_GLYPH_FONTS = {F_HEI, F_KAI}
_GLYPH_RISK = set("−✓✗✕≥≤→←∈∉±×÷≠∞√∑∏∫µμ")


def safe_font(path: str, sz: int, text: str = "") -> ImageFont.FreeTypeFont:
    """若字体可能缺字形且文本含风险符号，改用微软雅黑。"""
    if path in _MISSING_GLYPH_FONTS and any(ch in _GLYPH_RISK for ch in text):
        return font(F_MSYH, sz)
    return font(path, sz)


# ── 配色 ────────────────────────────────────────────────────────────────────
RED = (255, 59, 48)
RED_DARK = (214, 40, 32)
PAPER = (237, 228, 211)
PAPER_EDGE = (205, 190, 165)
INK = (38, 32, 28)
IDE_BG = (30, 30, 30)
IDE_PANEL = (37, 37, 38)
IDE_TAB = (24, 24, 24)
IDE_BORDER = (60, 60, 60)
WHITE = (255, 255, 255)
GREY = (150, 150, 150)

# 代码语法高亮配色（VS Code Dark+ 近似）
C_KW = (197, 134, 192)
C_STR = (206, 145, 120)
C_COM = (106, 153, 85)
C_FUN = (220, 220, 170)
C_NUM = (181, 206, 168)
C_VAR = (156, 220, 254)
C_OP = (212, 212, 212)
C_TYPE = (78, 201, 176)


# ════════════════════════════════════════════════════════════════════════════
# 基础绘制工具
# ════════════════════════════════════════════════════════════════════════════
def paper_bg() -> Image.Image:
    """宣纸质感背景。"""
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    # 纤维噪点
    noise = Image.effect_noise((W, H), 14).convert("L")
    noise = noise.filter(ImageFilter.GaussianBlur(0.6))
    img = Image.composite(Image.new("RGB", (W, H), (222, 210, 188)), img, noise.point(lambda v: 255 if v > 150 else 0))
    d = ImageDraw.Draw(img)
    # 暗角
    vign = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vign)
    vd.ellipse([-W * 0.35, -H * 0.45, W * 1.35, H * 1.45], fill=255)
    vign = vign.filter(ImageFilter.GaussianBlur(220))
    dark = Image.new("RGB", (W, H), (176, 163, 140))
    img = Image.composite(img, dark, vign)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W - 1, H - 1], outline=PAPER_EDGE, width=3)
    d.rectangle([18, 18, W - 19, H - 19], outline=(219, 206, 182), width=1)
    return img


def text_center(d: ImageDraw.ImageDraw, cx: int, y: int, txt: str, fnt, fill,
                font_path: str = ""):
    if font_path:
        fnt = safe_font(font_path, getattr(fnt, "size", 24), txt)
    bbox = d.textbbox((0, 0), txt, font=fnt)
    d.text((cx - (bbox[2] - bbox[0]) / 2, y), txt, font=fnt, fill=fill)
    return bbox[3] - bbox[1]


def wrap_cn(txt: str, fnt, max_w: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """按像素宽度对中英文混排文本换行。"""
    lines, cur = [], ""
    for ch in txt:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        trial = cur + ch
        if draw.textlength(trial, font=fnt) > max_w and cur:
            lines.append(cur)
            cur = ch
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def draw_arrow(d: ImageDraw.ImageDraw, start: tuple, end: tuple, color=RED, width=7, head=22):
    """实心箭头：从 start 指向 end。"""
    d.line([start, end], fill=color, width=width)
    import math
    ang = math.atan2(end[1] - start[1], end[0] - start[0])
    p1 = (end[0] - head * math.cos(ang - 0.45), end[1] - head * math.sin(ang - 0.45))
    p2 = (end[0] - head * math.cos(ang + 0.45), end[1] - head * math.sin(ang + 0.45))
    d.polygon([end, p1, p2], fill=color)


def drop_shadow(img: Image.Image, offset=(6, 8), blur=14, alpha=90) -> Image.Image:
    """给图片加投影（返回新图）。"""
    alpha_ch = img.convert("RGBA").split()[-1]
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, alpha), (0, 0), alpha_ch)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    base = Image.new("RGBA", img.size, (0, 0, 0, 0))
    base.paste(sh, offset, sh)
    base.alpha_composite(img.convert("RGBA"))
    return base.convert("RGB")


# ════════════════════════════════════════════════════════════════════════════
# 1. 章节卡
# ════════════════════════════════════════════════════════════════════════════
def render_section_card(title: str, subtitle: str = "", tag: str = "") -> Image.Image:
    img = paper_bg()
    d = ImageDraw.Draw(img)
    text_center(d, W // 2, H // 2 - 150, title, f_kaishu(130), INK)
    if subtitle:
        text_center(d, W // 2, H // 2 + 20, subtitle, f_kai(40), (92, 78, 66))
    if tag:
        text_center(d, W // 2, H - 150, tag, f_msyh(26), (140, 124, 108))
    return img


def render_cover(title: str, subtitle: str, members: str) -> Image.Image:
    img = paper_bg()
    d = ImageDraw.Draw(img)
    # 印章
    d.rectangle([W // 2 - 520, 210, W // 2 + 520, 212], fill=(198, 160, 120))
    text_center(d, W // 2, 250, title, f_kaishu(112), INK)
    text_center(d, W // 2, 420, subtitle, f_kai(38), (96, 82, 70))
    d.rectangle([W // 2 - 380, 500, W // 2 + 380, 502], fill=(198, 160, 120))
    text_center(d, W // 2, 560, "Java Web 后端开发技术 · 大作业演示", f_msyh(30), (120, 104, 90))
    text_center(d, W // 2, 700, members, f_msyh(26), (110, 96, 84))
    return img


# ════════════════════════════════════════════════════════════════════════════
# 2. IDE 代码页
# ════════════════════════════════════════════════════════════════════════════
KW = {"def", "return", "if", "else", "elif", "for", "in", "not", "and", "or",
      "import", "from", "class", "None", "True", "False", "with", "as", "try",
      "except", "finally", "lambda", "pass", "break", "continue", "while",
      "public", "private", "protected", "static", "void", "new", "this",
      "final", "abstract", "synchronized", "throw", "throws", "try"}
TYPES = {"int", "long", "double", "float", "boolean", "String", "List", "Map",
         "Set", "Object", "Path", "DataFrame", "np", "pd", "Optional", "Long",
         "Integer", "BigDecimal", "LocalDateTime"}


def _tokenize(line: str) -> list[tuple[str, tuple]]:
    """极简 Java/Python 着色器，返回 (文本, 颜色) 列表。"""
    out = []
    i, n = 0, len(line)
    while i < n:
        ch = line[i]
        if line.startswith("//", i) or line.startswith("#", i):
            out.append((line[i:], C_COM))
            break
        if ch == '"' or ch == "'":
            j = i + 1
            while j < n and line[j] != ch:
                j += 2 if line[j] == "\\" else 1
            out.append((line[i:min(j + 1, n)], C_STR))
            i = j + 1
            continue
        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (line[j].isalnum() or line[j] == "_"):
                j += 1
            word = line[i:j]
            nxt = line[j:j + 1]
            if word in KW:
                out.append((word, C_KW))
            elif word in TYPES or (word[:1].isupper() and len(word) > 1):
                out.append((word, C_TYPE))
            elif nxt == "(":
                out.append((word, C_FUN))
            else:
                out.append((word, C_VAR))
            i = j
            continue
        if ch.isdigit():
            j = i
            while j < n and (line[j].isdigit() or line[j] in "._"):
                j += 1
            out.append((line[i:j], C_NUM))
            i = j
            continue
        if ch in "+-*/%=<>!&|^~()[]{},:;.?":
            out.append((ch, C_OP))
            i += 1
            continue
        out.append((ch, C_OP))
        i += 1
    return out


def render_code_page(
    filepath: str,
    start_line: int,
    end_line: int,
    annotations: list[dict],
    title: str = "",
    subtitle: str = "",
    code_override: list[str] | None = None,
) -> Image.Image:
    """
    annotations 每项：
      {"lines": (a, b),          # 需要框住的源码行号
       "label": "文字",          # 右侧批注（支持 \n 换行）
       "anchor": "a"|"b",        # 箭头指向 lines 的首行(a)或末行(b)，默认 b
       "arrow_from": "label"|"code"   # 箭头起点：标签旁 / 代码框右侧，默认 label
      }
    """
    img = Image.new("RGB", (W, H), IDE_BG)
    d = ImageDraw.Draw(img)

    # 顶部标题栏
    d.rectangle([0, 0, W, 56], fill=IDE_TAB)
    d.rectangle([0, 54, W, 56], fill=(70, 70, 70))
    fname = Path(filepath).name
    parent = Path(filepath).parent.name
    tab_text = f"{parent}/{fname}" if parent else fname
    d.rectangle([0, 0, 560, 56], fill=IDE_PANEL)
    d.text((20, 18), tab_text, font=f_msyh(21), fill=(215, 215, 215))
    d.rectangle([0, 54, 560, 56], fill=RED)
    if title:
        d.text((600, 16), title, font=f_hei(26), fill=(235, 235, 235))
    if subtitle:
        d.text((600 + d.textlength(title, font=f_hei(26)) + 24, 20), subtitle,
               font=f_msyh(19), fill=(150, 150, 150))

    # ── 取源码 ─────────────────────────────────────────────────────────
    if code_override is not None:
        lines = code_override
        first_no = start_line
    else:
        p = ROOT / filepath
        all_lines = p.read_text(encoding="utf-8").splitlines()
        lines = all_lines[start_line - 1:end_line]
        first_no = start_line

    # ── 版面：代码区左 2/3，批注区右 1/3，代码垂直居中 ────────────────
    CODE_X = 96
    LH = 32
    fs = f_mono(20)
    CODE_TOP = 92
    CODE_BOTTOM = H - 48
    n = len(lines)
    block_h = n * LH
    # 若代码过长，占满可用高度
    avail = CODE_BOTTOM - CODE_TOP
    if block_h > avail:
        LH = int(avail // max(n, 1))
        block_h = n * LH
    CODE_Y = CODE_TOP + max(0, (avail - block_h) // 2)

    # 行号 + 代码
    line_y: dict[int, int] = {}
    for idx, ln in enumerate(lines):
        y = CODE_Y + idx * LH
        no = first_no + idx
        line_y[no] = y
        d.text((28, y + 3), str(no), font=f_mono(17), fill=(96, 96, 96))
        x = CODE_X
        for tok, col in _tokenize(ln):
            d.text((x, y), tok, font=fs, fill=col)
            x += d.textlength(tok, font=fs)

    # ── 标注 ───────────────────────────────────────────────────────────
    LABEL_X = 1410          # 批注文字左边界
    BOX_RIGHT = 1370        # 红框右边界
    for ann in annotations:
        a, b = ann["lines"]
        if a not in line_y or b not in line_y:
            continue
        y1 = line_y[a] - 5
        y2 = line_y[b] + LH - 3
        d.rectangle([CODE_X - 16, y1, BOX_RIGHT, y2], outline=RED, width=3)

        label = ann.get("label")
        lx = LABEL_X
        # anchor: "a" 指框首行，"b" 指框末行
        anchor = ann.get("anchor", "b")
        anchor_no = a if anchor == "a" else b
        ly = line_y[anchor_no] - 14
        if label:
            for k, seg in enumerate(label.split("\n")):
                d.text((lx, ly + k * 36), seg,
                       font=safe_font(F_HEI, 24, seg), fill=RED)

        # 箭头：从标签左侧指向框的右边界
        if ann.get("arrow", True):
            tgt_y = line_y[anchor_no] + LH // 2
            src_x = LABEL_X - 24
            src_y = ly + 16
            draw_arrow(d, (src_x, src_y), (BOX_RIGHT + 6, tgt_y), width=6, head=20)

    return img


# ════════════════════════════════════════════════════════════════════════════
# 3. 图片页（图表 / 大屏截图）
# ════════════════════════════════════════════════════════════════════════════
def render_image_page(
    images: list[str],
    title: str,
    caption: str = "",
    annotations: list[dict] | None = None,
    fit: str = "contain",
) -> Image.Image:
    """images: 相对 ROOT 的路径列表。annotations 用归一化坐标 (0-1)。"""
    img = Image.new("RGB", (W, H), IDE_BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 64], fill=IDE_TAB)
    d.text((26, 18), title, font=f_hei(28), fill=(240, 240, 240))
    if caption:
        d.text((W - d.textlength(caption, font=f_msyh(21)) - 30, 22), caption,
               font=f_msyh(21), fill=(140, 140, 140))

    n = len(images)
    gap = 18
    top = 84
    bottom = H - 96 if caption else H - 30
    area_h = bottom - top
    total_w = W - 60
    cell_w = (total_w - gap * (n - 1)) / n

    for i, rel in enumerate(images):
        p = ROOT / rel
        if not p.exists():
            continue
        src = Image.open(p).convert("RGB")
        box_w, box_h = cell_w, area_h
        if fit == "contain":
            sc = min(box_w / src.width, box_h / src.height)
            sz = (max(1, int(src.width * sc)), max(1, int(src.height * sc)))
            src = src.resize(sz, Image.LANCZOS)
        else:
            src = src.resize((int(box_w), int(box_h)), Image.LANCZOS)
        cx = 30 + i * (cell_w + gap) + cell_w / 2
        cy = top + area_h / 2
        canvas = Image.new("RGB", (int(box_w), int(area_h)), (18, 18, 18))
        canvas.paste(src, ((int(box_w) - src.width) // 2, (int(area_h) - src.height) // 2))
        canvas = drop_shadow(canvas, offset=(4, 5), blur=12, alpha=110)
        img.paste(canvas, (int(30 + i * (cell_w + gap)), int(top)))

    # 归一化坐标标注
    if annotations:
        for ann in annotations:
            x1, y1, x2, y2 = ann["box"]  # 0-1 归一化
            bx1, by1 = int(x1 * W), int(y1 * H)
            bx2, by2 = int(x2 * W), int(y2 * H)
            d.rectangle([bx1, by1, bx2, by2], outline=RED, width=4)
            if ann.get("label"):
                lx, ly = ann.get("label_xy", (bx2 + 14, by1))
                for k, seg in enumerate(ann["label"].split("\n")):
                    d.text((lx, ly + k * 34), seg,
                           font=safe_font(F_HEI, 23, seg), fill=RED)
            if ann.get("arrow"):
                (ax1, ay1), (ax2, ay2) = ann["arrow"]
                draw_arrow(d, (int(ax1 * W), int(ay1 * H)), (int(ax2 * W), int(ay2 * H)), width=8, head=26)
    return img


# ════════════════════════════════════════════════════════════════════════════
# 4. 表格页 / 要点页 / 公式页
# ════════════════════════════════════════════════════════════════════════════
def render_table_page(title: str, headers: list[str], rows: list[list[str]],
                      highlight_row: int = -1, note: str = "") -> Image.Image:
    img = Image.new("RGB", (W, H), IDE_BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 64], fill=IDE_TAB)
    d.text((26, 18), title, font=f_hei(28), fill=(240, 240, 240))

    x0, y0 = 70, 120
    ncol = len(headers)
    col_w = (W - 140) / ncol
    row_h = 52
    hfh = 58

    # 表头
    d.rectangle([x0, y0, x0 + col_w * ncol, y0 + hfh], fill=(52, 54, 58))
    for i, h in enumerate(headers):
        d.text((x0 + i * col_w + 18, y0 + 15), h,
               font=safe_font(F_HEI, 24, h), fill=(245, 245, 245))

    for r, row in enumerate(rows):
        ry = y0 + hfh + r * row_h
        if r == highlight_row:
            d.rectangle([x0, ry, x0 + col_w * ncol, ry + row_h], fill=(92, 34, 30))
            d.rectangle([x0, ry, x0 + 6, ry + row_h], fill=RED)
        elif r % 2 == 1:
            d.rectangle([x0, ry, x0 + col_w * ncol, ry + row_h], fill=(40, 40, 42))
        for c, cell in enumerate(row):
            col = (255, 220, 218) if r == highlight_row else (218, 218, 218)
            d.text((x0 + c * col_w + 18, ry + 13), str(cell), font=f_msyh(22), fill=col)
        d.line([x0, ry, x0 + col_w * ncol, ry], fill=(58, 58, 60), width=1)

    bot = y0 + hfh + len(rows) * row_h
    d.line([x0, bot, x0 + col_w * ncol, bot], fill=(58, 58, 60), width=1)
    for i in range(ncol + 1):
        d.line([x0 + i * col_w, y0, x0 + i * col_w, bot], fill=(58, 58, 60), width=1)

    if highlight_row >= 0:
        ry = y0 + hfh + highlight_row * row_h
        d.text((x0 + 6, bot + 26), "▲ 高亮行为关键设计",
               font=safe_font(F_HEI, 22, "▲"), fill=RED)
    if note:
        d.text((x0, H - 70), note, font=f_msyh(21), fill=(140, 140, 140))
    return img


def render_bullets_page(title: str, bullets: list[tuple[str, str]], footer: str = "") -> Image.Image:
    """bullets: [(主标题, 说明)]"""
    img = Image.new("RGB", (W, H), IDE_BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 64], fill=IDE_TAB)
    d.text((26, 18), title, font=f_hei(28), fill=(240, 240, 240))

    y = 132
    for i, (head, sub) in enumerate(bullets):
        d.rectangle([70, y, 96, y + 52], fill=RED)
        d.text((122, y + 2), head, font=safe_font(F_HEI, 31, head), fill=(245, 245, 245))
        d.text((126, y + 52), sub, font=f_msyh(21), fill=(160, 160, 160))
        if i < len(bullets) - 1:
            d.line([122, y + 96, W - 80, y + 96], fill=(56, 56, 58), width=1)
        y += 150
    if footer:
        d.text((70, H - 80), footer, font=f_msyh(21), fill=(140, 140, 140))
    return img


def render_formula_page(title: str, formula: str, explains: list[str],
                        emphasis: str = "", note: str = "") -> Image.Image:
    img = Image.new("RGB", (W, H), IDE_BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 64], fill=IDE_TAB)
    d.text((26, 18), title, font=f_hei(28), fill=(240, 240, 240))

    # 公式区
    d.rounded_rectangle([180, 200, W - 180, 430], radius=18, fill=(38, 38, 40), outline=(78, 78, 82), width=2)
    # 公式：减号用 ASCII 连字符，避免 U+2212 在黑体/楷体下渲染成豆腐块
    text_center(d, W // 2, 248, formula, f_kai(104), (255, 245, 225), font_path=F_KAI)

    y = 500
    for i, ex in enumerate(explains):
        d.rectangle([260, y + 10, 280, y + 30], fill=RED)
        d.text((300, y), ex, font=f_msyh(28), fill=(225, 225, 225))
        y += 66

    if emphasis:
        d.rounded_rectangle([260, y + 24, W - 260, y + 92], radius=10, fill=(92, 34, 30), outline=RED, width=3)
        text_center(d, W // 2, y + 38, emphasis, f_hei(34), (255, 235, 232), font_path=F_HEI)
    if note:
        d.text((70, H - 80), note, font=f_msyh(21), fill=(140, 140, 140))
    return img


def render_ending_page(title: str, sub: str, lines: list[str]) -> Image.Image:
    img = paper_bg()
    d = ImageDraw.Draw(img)
    text_center(d, W // 2, H // 2 - 220, title, f_kaishu(110), INK)
    text_center(d, W // 2, H // 2 - 60, sub, f_kai(40), (96, 82, 70))
    d.rectangle([W // 2 - 300, H // 2 + 10, W // 2 + 300, H // 2 + 12], fill=(198, 160, 120))
    y = H // 2 + 70
    for ln in lines:
        text_center(d, W // 2, y, ln, f_msyh(26), (110, 96, 84))
        y += 46
    return img


def save(img: Image.Image, name: str) -> Path:
    p = OUT / name
    img.save(p, quality=95)
    return p
