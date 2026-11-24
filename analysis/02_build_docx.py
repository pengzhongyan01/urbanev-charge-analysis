# -*- coding: utf-8 -*-
"""
02_build_docx.py —— 由 第五章初稿.md 生成 Word（.docx）
格式：正文宋体小四(12pt)、首行缩进 2 字符、1.5 倍行距；标题黑体分级；图居中+五号图注；表三线表。
公式：LaTeX 经 matplotlib mathtext 渲染为 300dpi 透明 PNG 后居中嵌入。
输出：../05_报告/第五章初稿_E组_姬婷婷.docx
"""
import os
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MD = os.path.join(BASE, "docs", "report", "第五章_姬婷婷.md")
OUT = os.path.join(BASE, "analysis", "output", "第五章_姬婷婷.docx")
FIG_DIR = os.path.join(BASE, "docs", "report", "images")
MATH_DIR = os.path.join(BASE, "analysis", "output")
os.makedirs(MATH_DIR, exist_ok=True)

SONG, HEI, KAI = "宋体", "黑体", "楷体"
BODY = Pt(12)
CAP = Pt(10.5)
TBL = Pt(10)

doc = Document()
sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(2.5)
sec.left_margin = sec.right_margin = Cm(2.5)

normal = doc.styles["Normal"]
normal.font.name = SONG
normal.font.size = BODY
normal.element.rPr.rFonts.set(qn("w:eastAsia"), SONG)


def _font(run, font=SONG, size=BODY, bold=False):
    run.font.name = font
    run.font.size = size
    run.font.bold = bold
    rpr = run.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.append(rf)
    rf.set(qn("w:eastAsia"), font)
    rf.set(qn("w:ascii"), font)


def add_runs(p, text, size=BODY, font=SONG, bold=False):
    """处理 **加粗** 与 `代码`，输出多 run。"""
    text = text.replace("`", "")
    parts = re.split(r"(\*\*.*?\*\*)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            r = p.add_run(part[2:-2])
            _font(r, font, size, True)
        else:
            r = p.add_run(part)
            _font(r, font, size, bold)


def body(text, indent=True, size=BODY, align=None, space_after=Pt(3), font=SONG):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.space_before = Pt(0)
    pf.space_after = space_after
    if indent:
        pf.first_line_indent = Pt(24)
    if align is not None:
        p.alignment = align
    add_runs(p, text, size, font)
    return p


def bullet(text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.space_before = Pt(0)
    pf.space_after = Pt(3)
    pf.left_indent = Cm(0.74)
    pf.first_line_indent = Cm(0)
    r = p.add_run("• ")
    _font(r, SONG, BODY)
    add_runs(p, text)
    return p


def heading(text, level):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    if level == 1:
        pf.space_before = Pt(0)
        pf.space_after = Pt(18)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_runs(p, text, Pt(16), HEI)
        p.runs[0].font.bold = True
    elif level == 2:
        pf.space_before = Pt(12)
        pf.space_after = Pt(6)
        add_runs(p, text, Pt(14), HEI)
        p.runs[0].font.bold = True
    else:
        pf.space_before = Pt(9)
        pf.space_after = Pt(4)
        add_runs(p, text, Pt(12), HEI)
        p.runs[0].font.bold = True
    pf.keep_with_next = True
    return p


def caption(text, above=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    pf.space_before = Pt(6 if above else 2)
    pf.space_after = Pt(2 if above else 10)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_runs(p, text, CAP, HEI if above else SONG)
    if above:
        p.runs[0].font.bold = True
    pf.keep_with_next = above
    return p


# ---------- 公式（Word 原生文字排版，可编辑） ----------
MFONT = "Cambria Math"
GREEK_LOWER = "αβγδεζηθικλμνξοπρστυφχψω"
GREEK_UPPER = "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"

F1 = ["D(z,t) = volume(z,t) / Σ_{z′} volume(z′,t)",
      "S(z) = charge_count(z) / Σ_{z′} charge_count(z′)"]
F2 = ["I(z,t) = D(z,t) − S(z)"]
F3 = ["σ_{price}(z) = STDDEV_POP(e_price(z, ·))"]
F4 = ["PEAK(T) = avg{ occupancy(z,t) | 17 ≤ t ≤ 19 }",
      "VALLEY(T) = avg{ occupancy(z,t) | 0 ≤ t ≤ 6 }"]
F5 = ["ELASTICITY(T) = PEAK(T) − VALLEY(T)"]
F6 = ["ŷ(z,h) = v̄(z,·,h) × γ,   γ = v̄_{7d} / v̄_{all}"]
F7 = ["Δn(z) = ⌈ I_{max}(z) × charge_count(z) × 0.3 ⌉"]
F8 = ["X(z) = [ avg_occupancy,   peak_valley_gap,   occupancy_std,"]
F9 = ["avg_duration,   poi_density,   pile_density,   price_std ]"]


def pick_formula(latex):
    L = latex.replace("\\_", "_")
    if "ELASTICITY" in L:
        return F5
    if "PEAK" in L:
        return F4
    if "hat{y}" in L:
        return F6
    if "Delta n(z)" in L:
        return F7
    if "price_std" in L:
        return F9
    if "X(z)" in L:
        return F8
    if "sigma" in L:
        return F3
    if "I(z,t)" in L:
        return F2
    return F1


def _seg(p, text, sub=False):
    if text == "":
        return
    for tok in re.findall(r"[A-Za-z_][A-Za-z_0-9]*|[^A-Za-z_]+", text):
        r = p.add_run(tok)
        _font(r, MFONT, BODY)
        r.font.subscript = sub
        core = tok.strip()
        if len(core) == 1 and (core.isascii() or core in GREEK_LOWER or core in "ŷv̄"):
            if core.isalpha() or core in "ŷv̄":
                r.font.italic = True


def math_block(latex):
    for line in pick_formula(latex):
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.space_before = Pt(3)
        pf.space_after = Pt(3)
        pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for tok in re.split(r"(_{[^{}]*})", line):
            if not tok:
                continue
            if tok.startswith("_{") and tok.endswith("}"):
                _seg(p, tok[2:-1], sub=True)
            else:
                _seg(p, tok, sub=False)


# ---------- 表格 ----------
def set_cell(cell, text, bold=False, size=TBL):
    cell.text = ""
    p = cell.paragraphs[0]
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    pf.space_before = Pt(1)
    pf.space_after = Pt(1)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_runs(p, text.strip(), size, SONG, bold)


def _set_edge(cell, edge, sz=12):
    tcPr = cell._tc.get_or_add_tcPr()
    eb = tcPr.find(qn("w:tcBorders"))
    if eb is None:
        eb = OxmlElement("w:tcBorders")
        tcPr.append(eb)
    tag = "w:" + edge
    el = eb.find(qn(tag))
    if el is None:
        el = OxmlElement(tag)
        eb.append(el)
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), str(sz))
    el.set(qn("w:color"), "000000")


def _clear_borders(cell):
    tcPr = cell._tc.get_or_add_tcPr()
    eb = OxmlElement("w:tcBorders")
    for edge in ("top", "bottom", "left", "right"):
        el = OxmlElement("w:" + edge)
        el.set(qn("w:val"), "nil")
        eb.append(el)
    tcPr.append(eb)


def add_table(rows):
    header, data = rows[0], rows[1:]
    t = doc.add_table(rows=1, cols=len(header))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = True
    for i, h in enumerate(header):
        set_cell(t.rows[0].cells[i], h, bold=True)
    for row in data:
        cells = t.add_row().cells
        for i in range(len(header)):
            set_cell(cells[i], row[i] if i < len(row) else "")
    for r_i, row in enumerate(t.rows):
        for cell in row.cells:
            _clear_borders(cell)
            if r_i == 0:
                _set_edge(cell, "top", 14)
                _set_edge(cell, "bottom", 8)
            if r_i == len(t.rows) - 1:
                _set_edge(cell, "bottom", 14)
    # 表后留白
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    r = p.add_run("")
    _font(r, SONG, Pt(6))


# ---------- 解析 Markdown ----------
def parse(path):
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    items = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue
        if line.startswith("\\["):
            buf = []
            j = i
            while j < len(lines) and "\\]" not in lines[j]:
                buf.append(lines[j])
                j += 1
            if j < len(lines):
                buf.append(lines[j].replace("\\]", ""))
            else:
                buf.append(line.replace("\\[", ""))
            items.append(("math", "\n".join(buf).replace("\\[", "").strip()))
            i = j + 1
            continue
        m = re.match(r"^!\[(.*?)\]\((.*?)\)$", line.strip())
        if m:
            items.append(("img", (m.group(1), m.group(2))))
            i += 1
            continue
        if line.strip().startswith("|"):
            rows = []
            j = i
            while j < len(lines) and lines[j].strip().startswith("|"):
                raw = lines[j].strip().strip("|")
                cells = [c.strip() for c in raw.split("|")]
                if not re.match(r"^:?-{2,}", cells[0].replace(" ", "")):
                    rows.append(cells)
                j += 1
            items.append(("table", rows))
            i = j
            continue
        if line.startswith("### "):
            items.append(("h3", line[4:].strip()))
        elif line.startswith("## "):
            items.append(("h2", line[3:].strip()))
        elif line.startswith("# "):
            items.append(("h1", line[2:].strip()))
        elif line.startswith("> "):
            items.append(("quote", line[2:].strip()))
        elif re.match(r"^- ", line.strip()):
            items.append(("bullet", line.strip()[2:].strip()))
        elif line.strip() == "---":
            items.append(("sep", ""))
        elif line.strip().startswith("表 5-"):
            items.append(("tablecap", line.strip()))
        else:
            items.append(("body", line.strip()))
        i += 1
    return items


def build():
    for kind, val in parse(MD):
        if kind == "h1":
            heading(val, 1)
        elif kind == "h2":
            heading(val, 2)
        elif kind == "h3":
            heading(val, 3)
        elif kind == "body":
            if val.startswith("**本章由") or val.startswith("**本章"):
                body(val, indent=False, align=WD_ALIGN_PARAGRAPH.RIGHT)
            else:
                body(val)
        elif kind == "bullet":
            bullet(val)
        elif kind == "quote":
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
            pf.space_before = Pt(0)
            pf.space_after = Pt(6)
            pf.left_indent = Cm(0.5)
            add_runs(p, val, Pt(10.5), KAI)
        elif kind == "img":
            alt, rel = val
            img_path = os.path.normpath(os.path.join(BASE, "docs", "report", rel))
            if not os.path.exists(img_path):
                img_path = os.path.normpath(os.path.join(BASE, rel))
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.space_before = Pt(8)
            pf.space_after = Pt(2)
            pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(img_path, width=Cm(15.2))
            caption(alt)
        elif kind == "tablecap":
            caption(val, above=True)
        elif kind == "table":
            add_table(val)
        elif kind == "math":
            math_block(val)
        elif kind == "sep":
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
    doc.save(OUT)
    print("saved:", OUT)


build()
