# -*- coding: utf-8 -*-
r"""
md_to_docx.py —— 把 Markdown 报告初稿转成符合排版规范的 Word 文档（每人一份）

★ 为什么用 Word COM 而不是 python-docx
  python-docx 做不出**自动目录域**（TOC field），而老师明确要求
  「目录页码必须正确」—— 手打目录一旦改内容就全错。
  用 Word COM 调用真实的 Word 引擎，可以：
    · 插入自动目录域（TOC \o "1-3" \h \z \u），打开时 Word 会提示更新
    · 设置中文字体（正文宋体小四、标题三号/四号、行距 1.5、首行缩进 2 字符）
    · 设置页眉「贵州大学本科大作业报告」与页脚「第 X 页」域
    · 自动生成图片题注与图表编号
  排版规格照 A10《写作规范》。

用法：
  python scripts/md_to_docx.py                    # 生成 5 份（每人一份）
  python scripts/md_to_docx.py --out DIR
  python scripts/md_to_docx.py --single 彭忠燕    # 只生成一份
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REPORT = REPO / "docs" / "report"
CHARTS = REPO / "docs" / "charts"

# 五名成员：姓名 → 学号（★ 2026-11-24 组长核实确认，已填真实值）
MEMBERS = [
    ("彭忠燕", "2400770245"),
    ("苏静", "2400770287"),
    ("贺欢欢", "2400770251"),
    ("杨姗姗", "2400770293"),
    ("姬婷婷", "2400770305"),
]

TITLE = "基于 Hadoop 与 Spring Boot 的城市充电桩使用行为分析与充电需求预测系统的设计与实现"
COURSE = "Java Web 后端开发技术"
CLASS = "2405"
GROUP = "第 02 组"
TEACHER = "赵　晨"
MAJOR = "软件工程"
COLLEGE = "示范性软件学院"
DATE = "2026 年 11 月 29 日"

# 章节顺序：(文件名, 起止标记)
# ★ 用「起止标记」按一级标题切分，因为早期初稿把「需求分析」编成了第二章，
#   而按老师给的目录模板，需求分析是第三章、系统开发相关技术是第二章。
#   第 1-2 章初稿里的旧第二章（可行性/功能需求/非功能需求/用例分析）整段剔除，
#   用第 3-4 章初稿里的第三章替代 —— 那版更全（含 14 个用例的完整用例描述表）。
#   标记为 None 表示整篇都要。
CHAPTERS = [
    ("第1-2章_初稿.md", "# 第一章 绪论", "# 第二章 需求分析"),
    ("第2章_初稿.md",   None, None),
    ("第3-4章_初稿.md", None, None),
    ("第5章_初稿.md",   None, None),
    ("第6章_初稿.md",   None, None),
    ("第7章_初稿.md",   None, None),
    ("参考文献与附录.md", None, None),
]


def slice_by_heading(text: str, start: str | None, end: str | None) -> str:
    """按一级标题切分内容

    ★ 切分后还要去掉文件头那一行（「# 报告第X章 · xxx（初稿）」）——
      它也是一级标题，留着会污染自动目录（每个文件多出一条无意义条目）。
    """
    if start:
        i = text.find(start)
        if i < 0:
            text = re.sub(r"^#\s*(报告第.*|参考文献与附录.*)$", "", text, count=1, flags=re.M)
        else:
            j = text.find(end, i + len(start)) if end else -1
            text = text[i:j] if j > 0 else text[i:]
    else:
        # 整篇都要时，也去掉文件头
        text = re.sub(r"^#\s*(报告第.*|参考文献与附录.*)$", "", text, count=1, flags=re.M)
    return text

# 章节文件里的一级标题 → 目录里的章名（用于替换）
TITLE_MAP = {
    "# 报告第一章 · 课题背景与需求分析（初稿）": "",
    "# 报告第三章 · 需求分析与系统概要设计（初稿）": "",
    "# 报告第七章 · 总结与展望（初稿）": "",
    "# 第二章 系统开发相关技术": "# 第二章 系统开发相关技术",
}


# 图题 → 真实图片文件（按语义匹配，缺图不插）
FIG_MAP = {
    # 第四章
    "4-1":  "06_四层数仓规模对比.png",
    "4-2":  "07_系统ER图.png",
    # 第五章（5-6 ~ 5-14 为 E 岗 5.6 节新图，其余沿用）
    "5-1":  "08_Flume采集拓扑图.png",
    "5-2":  "06_四层数仓规模对比.png",
    "5-3":  "10_数据质量实测结果.png",
    "5-4":  "02_分区地图大屏.png",
    "5-5":  "09_接口调用关系与缓存分层图.png",
    "5-6":  "01_24小时供需曲线.png",
    "5-7":  "02_失衡指数_TOP10.png",
    "5-8":  "03_电价标准差_可分性.png",
    "5-9":  "04_TOU_FLAT_占用率对比.png",
    "5-10": "05_需求预测_曲线.png",
    "5-11": "08_肘部法_WCSS.png",
    "5-12": "06_聚类_散点.png",
    "5-13": "07_聚类_雷达.png",
    "5-14": "09_双口径_对比.png",
    "5-15": "01_首页大屏.png",
    "5-17": "06_四层数仓规模对比.png",
    # 第三章
    "3-1":  "06_四层数仓规模对比.png",
    # 附录用
    "6-1":  "05_需求分析用例图.png",
    "7-1":  "04_供需失衡指数TOP20.png",
    "7-2":  "03_24小时供需曲线.png",
}

FIG_DIRS = [CHARTS, REPO / "docs" / "screenshots", REPO / "docs" / "架构图",
            REPO / "docs" / "report" / "images", REPO / "docs" / "ppt" / "images"]


def find_fig(code: str):
    """按图号找到对应图片"""
    name = FIG_MAP.get(code)
    if not name:
        return None
    for d in FIG_DIRS:
        p = d / name
        if p.exists():
            return p
    return None

def strip_meta(text: str) -> str:
    """去掉 Markdown 里的元信息块（主笔/状态/事实源等）"""
    lines = text.splitlines()
    out, i = [], 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("> **主笔") or l.startswith("> **状态") or l.startswith("> **事实源") \
           or l.startswith("> **本章定位") or l.startswith("> **目标字数") or l.startswith("> **交付"):
            while i < len(lines) and (lines[i].startswith(">") or not lines[i].strip()):
                i += 1
            out.append("")
            continue
        out.append(l)
        i += 1
    return "\n".join(out)


def md_to_html(text: str, img_map: dict) -> str:
    """极简 Markdown → HTML（只处理我们报告里实际用到的语法）"""
    text = strip_meta(text)
    lines = text.splitlines()
    html, i = [], 0
    used_figs = set()
    fig_markers = {}
    in_code = False
    code_lang, code_buf = "", []

    def flush_code():
        nonlocal code_buf, code_lang
        if code_buf:
            lang = code_lang or "text"
            html.append(f'<pre class="code"><code class="lang-{lang}">'
                        + "\n".join(code_buf).replace("&", "&amp;").replace("<", "&lt;")
                        + "\n</code></pre>")
        code_buf, code_lang = [], ""

    while i < len(lines):
        l = lines[i]

        # 代码块
        if l.strip().startswith("```"):
            if in_code:
                flush_code(); in_code = False
            else:
                in_code = True; code_lang = l.strip()[3:].strip()
            i += 1
            continue
        if in_code:
            code_buf.append(l); i += 1
            continue

        # 图片 ![](path)
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)", l.strip())
        if m:
            alt, path = m.group(1), m.group(2)
            real = img_map.get(path) or (REPO / path if (REPO / path).exists() else None)
            if real is None:
                # 形如 ./images/01_xxx.png → 依次到 docs/report/images、docs/ppt/images 找
                bn = Path(path).name
                for base in (REPO / "docs" / "report", REPO / "docs" / "ppt"):
                    cand = base / "images" / bn
                    if cand.exists():
                        real = cand; break
            if real and Path(real).exists():
                # ★ 只放占位标记，不放 <img>。
                #   Word 从 HTML 导入本地图片时，路径含非 ASCII 字符会静默丢图
                #   （实测：docx 里没有 word/media 目录，提交给别人就是白板）。
                #   改为「HTML 转换完后再用 COM 按占位符插图」，100% 可控。
                marker = f"@@FIG:{code}@@"
                html.append(f'<p class="figmark">{marker}</p>'
                            f'<p class="fig"><span class="cap">{alt}</span></p>')
                fig_markers[marker] = str(real)
            i += 1
            continue

        # 标题
        m = re.match(r"^(#{1,4})\s+(.*)$", l)
        if m:
            lvl = len(m.group(1)); txt = m.group(2).strip()
            html.append(f"<h{lvl}>{txt}</h{lvl}>")
            i += 1
            continue

        # ★ 图题段落：形如「**图 5-3 六项指标数据质量实测结果图**」
        #   若有对应图片，则在图题前插入该图
        mfig = re.search(r"图\s*([0-9]+-[0-9]+)", l)
        if mfig:
            code = mfig.group(1)
            fp = find_fig(code)
            if fp is not None:
                cap = re.sub(r"[*`]", "", l.strip())
                # ★ 放占位标记而非 <img>：Word 从 HTML 导入本地图片会静默丢图，
                #   改为 HTML 转完后再用 COM 按标记插入，100% 可控。
                marker = f"@@FIG:{code}@@"
                html.append(f'<p class="figmark">{marker}</p>'
                            f'<p class="fig"><span class="cap">{cap}</span></p>')
                fig_markers[marker] = str(fp)
                used_figs.add(code)

        # 水平线
        if re.match(r"^-{3,}$", l.strip()):
            html.append("<hr>"); i += 1
            continue

        # 表格
        if l.strip().startswith("|") and i + 1 < len(lines) and \
           re.match(r"^\s*\|[\s:\-|]+\|\s*$", lines[i + 1]):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
            head, body = cells[0], cells[2:] if len(cells) > 2 else []
            html.append("<table><thead><tr>"
                       + "".join(f"<th>{c}</th>" for c in head) + "</tr></thead><tbody>")
            for r in body:
                html.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
            html.append("</tbody></table>")
            continue

        # 引用
        if l.strip().startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            html.append("<blockquote>" + "<br>".join(buf) + "</blockquote>")
            continue

        # 列表
        m = re.match(r"^\s*([-*]|\d+\.)\s+(.*)$", l)
        if m:
            items = []
            while i < len(lines):
                mm = re.match(r"^\s*([-*]|\d+\.)\s+(.*)$", lines[i])
                if mm:
                    items.append(mm.group(2).strip()); i += 1
                else:
                    break
            html.append("<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>")
            continue

        # 粗体 / 行内代码
        def inline(t):
            t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
            t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
            t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            # 把 &lt;b&gt; 还原
            t = t.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
            t = t.replace("&lt;code&gt;", "<code>").replace("&lt;/code&gt;", "</code>")
            return t

        if l.strip():
            html.append(f"<p>{inline(l.strip())}</p>")
        else:
            html.append("")
        i += 1

    flush_code()
    md_to_html.last_used = used_figs
    md_to_html.last_markers = fig_markers
    return "\n".join(html)


def build_html(chapter_htmls: list[str], member: str, sid: str) -> str:
    """组装完整 HTML（封面 + 目录 + 各章）"""
    names = "　".join(m for m, _ in MEMBERS)
    # ★ 五人学号对照（真实学号，2026-11-24 组长核实）
    sid_rows = "".join(
        f'<tr><td style="border:none;padding:2px 8px 2px 0">{m}</td>'
        f'<td style="border:none;padding:2px 0">{s_}</td></tr>'
        for m, s_ in MEMBERS)
    cover = f"""
<div class="cover">
  <div class="c-school">贵州大学</div>
  <div class="c-title">{TITLE}</div>
  <table class="c-info">
    <tr><td>课程名称：</td><td>{COURSE}</td></tr>
    <tr><td>学　　院：</td><td>{COLLEGE}</td></tr>
    <tr><td>专　　业：</td><td>{MAJOR}</td></tr>
    <tr><td>班　　级：</td><td>{CLASS}</td></tr>
    <tr><td>组　　别：</td><td>{GROUP}</td></tr>
    <tr><td>学生姓名：</td><td>{names}</td></tr>
    <tr><td>本报告作者：</td><td>{member}（学号 {sid}）</td></tr>
    <tr><td>指导教师：</td><td>{TEACHER}</td></tr>
  </table>
  <div class="c-sids">
    <div class="c-sids-title">小组成员学号</div>
    <div class="c-sids-grid">{sid_rows}</div>
  </div>
  <div class="c-date">{DATE}</div>
</div>
"""
    toc = """
<div class="toc-page">
  <div class="toc-title">目　　录</div>
  <p class="toc-tip">（在 Word 中按 Ctrl+A 后按 F9，或右键目录 → 更新域 → 更新整个目录，即可生成正确页码）</p>
  <div id="toc-here"></div>
</div>
"""
    body = "\n".join(chapter_htmls)
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<style>
@page {{ size: A4; margin: 3.0cm 2.0cm 2.5cm 3.0cm; }}
body {{ font-family: "宋体", "SimSun", serif; font-size: 12pt; line-height: 1.5;
        text-align: justify; }}
.cover {{ page-break-after: always; text-align: center; padding-top: 4cm; }}
.c-school {{ font-size: 26pt; font-weight: bold; letter-spacing: 8px; margin-bottom: 2.4cm; }}
.c-title {{ font-size: 18pt; font-weight: bold; line-height: 1.7; margin-bottom: 3cm; }}
.c-info {{ margin: 0 auto; border-collapse: collapse; font-size: 14pt; }}
.c-info td {{ padding: 7px 10px; text-align: left; }}
.c-info td:first-child {{ text-align: right; white-space: nowrap; }}
.c-date {{ margin-top: 1.4cm; font-size: 14pt; }}
.c-sids {{ margin: 0.9cm auto 0 auto; font-size: 12pt; }}
.c-sids-title {{ font-size: 12pt; color: #444; margin-bottom: 4px; }}
.c-sids-grid {{ display: inline-block; text-align: left; }}
.c-sids-grid tr {{ border: none !important; }}
.toc-page {{ page-break-after: always; }}
.toc-title {{ font-size: 16pt; font-weight: bold; text-align: center; margin-bottom: 0.6cm; }}
.toc-tip {{ font-size: 9pt; color: #888; text-align: center; margin-bottom: 0.5cm; }}
h1 {{ font-family: "黑体","SimHei"; font-size: 16pt; text-align: center; margin: 1.6em 0 1em; }}
h2 {{ font-family: "黑体","SimHei"; font-size: 14pt; margin: 1.4em 0 0.7em; }}
h3 {{ font-family: "黑体","SimHei"; font-size: 12pt; margin: 1.1em 0 0.5em; }}
h4 {{ font-size: 12pt; font-weight: bold; margin: 0.9em 0 0.4em; }}
p {{ margin: 0.3em 0; text-indent: 2em; }}
blockquote {{ margin: 0.6em 0 0.6em 2em; padding: 0.3em 0.8em; font-size: 10.5pt;
              color: #444; background: #F5F5F5; text-indent: 0; }}
ul {{ margin: 0.3em 0 0.6em 2em; padding-left: 1.2em; }}
li {{ margin: 0.15em 0; }}
table {{ border-collapse: collapse; width: 100%; margin: 0.7em 0; font-size: 10.5pt; }}
th, td {{ border: 1px solid #666; padding: 4px 7px; text-align: left; vertical-align: top; }}
th {{ background: #EFEFEF; font-weight: bold; }}
code {{ font-family: Consolas, "Courier New", monospace; font-size: 10.5pt; }}
pre.code {{ background: #F7F7F7; border: 1px solid #DDD; border-left: 3px solid #999;
            padding: 8px 12px; margin: 0.7em 0; overflow-x: auto; line-height: 1.35; }}
pre.code code {{ font-size: 9.5pt; white-space: pre; }}
p.fig {{ text-align: center; margin: 0.9em 0; text-indent: 0; }}
p.fig img {{ max-width: 15.5cm; border: 1px solid #CCC; }}
p.fig span.cap {{ display: block; font-size: 10.5pt; color: #333; margin-top: 4px; }}
hr {{ border: none; border-top: 1px solid #CCC; margin: 1.2em 0; }}
</style></head><body>
{cover}
{toc}
{body}
</body></html>"""


# ══════════════════════════════════════════════════════════════════
# Word COM 处理
# ══════════════════════════════════════════════════════════════════
PS_SCRIPT = r'''
param([string]$HtmlPath, [string]$DocxPath, [string]$FigMapPath)
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($HtmlPath)
    # 中文字体
    $doc.Content.Font.Name = "宋体"
    $doc.Content.Font.NameFarEast = "宋体"
    $doc.Content.Font.Size = 12
    $doc.Content.ParagraphFormat.LineSpacingRule = 1
    $doc.Content.ParagraphFormat.LineSpacing = 18
    $doc.Content.ParagraphFormat.SpaceAfter = 0
    # 标题样式
    foreach ($i in 1..4) {
        # ★ wdStyleHeading1 = -2，所以 Heading N = -1 - N
        #   （原写成 -2 + $i，i=1 时算出 -1，那是 wdStyleNormal → COMException）
        $st = $doc.Styles.Item(-1 - $i)
        $st.Font.Name = "黑体"
        $st.Font.NameFarEast = "黑体"
        $st.Font.Size = @(16,14,12,12)[$i-1]
        $st.Font.Bold = $true
        $st.ParagraphFormat.Alignment = $(if ($i -eq 1) {1} else {0})
        $st.ParagraphFormat.SpaceBefore = @(18,14,12,10)[$i-1]
        $st.ParagraphFormat.SpaceAfter = @(12,8,6,5)[$i-1]
        $st.ParagraphFormat.LineSpacingRule = 1
        $st.ParagraphFormat.LineSpacing = 18
    }
    # 插入自动目录（把占位 div 换成真正的 TOC 域）
    $rng = $doc.Content
    $f = $rng.Find
    $f.Text = "（在 Word 中按 Ctrl+A 后按 F9"
    if ($f.Execute()) {
        $rng.Text = ""
        $doc.TablesOfContents.Add($rng, $true, 1, 3) | Out-Null
    }
    # 页眉页脚
    $sec = $doc.Sections.Item(1)
    $sec.PageSetup.DifferentFirstPageHeaderFooter = $true
    $hdr = $sec.Headers.Item(1).Range
    $hdr.Text = "贵州大学本科大作业报告"
    $hdr.ParagraphFormat.Alignment = 1
    $hdr.Font.Size = 9
    $hdr.Font.Name = "宋体"
    $ftr = $sec.Footers.Item(1).Range
    $ftr.Text = "第 "
    $ftr.Collapse(0) | Out-Null
    $ftr.Fields.Add($ftr, 33) | Out-Null      # wdFieldPage
    $ftr2 = $sec.Footers.Item(1).Range
    $ftr2.InsertAfter(" 页")
    $ftr2.ParagraphFormat.Alignment = 1
    $ftr2.Font.Size = 9
    $ftr2.Font.Name = "宋体"
    # ★ 按占位符插入图片
    #   HTML 里的 <img> 会被 Word 静默丢弃（路径含中文时尤其明显，
    #   结果 docx 里根本没有 word/media 目录，提交给别人就是白板）。
    #   改为在 HTML 转成 docx 之后，用 InlineShapes.AddPicture 逐张插入。
    if (Test-Path $FigMapPath) {
        $map = Get-Content $FigMapPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $n = 0
        foreach ($prop in $map.PSObject.Properties) {
            $marker = $prop.Name
            $imgPath = $prop.Value
            if (-not (Test-Path $imgPath)) { continue }
            $rng = $doc.Content
            # ★ 同一图题在正文里可能出现多次，必须循环替换直到找不到
            while ($true) {
                $rng = $doc.Content
                $find = $rng.Find
                $find.Text = $marker
                $find.Forward = $true
                $find.Wrap = 0
                if (-not $find.Execute()) { break }
                $rng.Text = ""
                try {
                    $pic = $rng.InlineShapes.AddPicture($imgPath, $false, $true)
                    $pic.Width = 430
                    $pic.Height = [int](430 * $pic.Height / $pic.Width)
                    $pic.Range.ParagraphFormat.Alignment = 1
                    $n++
                } catch {
                    Write-Output "IMGFAIL $marker"
                    break
                }
            }
        }
        Write-Output "IMGS=$n"
    }
    # 目录更新
    foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
    $doc.Fields.Update() | Out-Null
    $doc.SaveAs([ref]$DocxPath, [ref]16)   # wdFormatDocumentDefault = 16
    $pages = $doc.ComputeStatistics(2)    # wdStatisticPages
    $words = $doc.ComputeStatistics(0)    # wdStatisticWords
    Write-Output "PAGES=$pages"
    Write-Output "WORDS=$words"
    $doc.Close([ref]$false)
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
'''


def word_convert(html_path: Path, docx_path: Path, markers: dict | None = None) -> dict:
    ps_path = html_path.with_suffix(".ps1")
    ps_path.write_text(PS_SCRIPT, encoding="utf-8-sig")
    # 占位符 → 图片路径 的映射（JSON，供脚本读取）
    map_path = html_path.with_suffix(".figs.json")
    map_path.write_text(json.dumps(markers or {}, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                        "-File", str(ps_path), "-HtmlPath", str(html_path),
                        "-DocxPath", str(docx_path), "-FigMapPath", str(map_path)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    info = {"ok": False, "stdout": r.stdout.strip(), "stderr": r.stderr.strip()[:600]}
    for line in r.stdout.splitlines():
        if line.startswith("PAGES="):
            info["pages"] = int(line.split("=")[1])
        if line.startswith("WORDS="):
            info["words"] = int(line.split("=")[1])
        if line.startswith("IMGS="):
            info["images"] = int(line.split("=")[1])
    info["ok"] = docx_path.exists() and docx_path.stat().st_size > 5000
    for f in (ps_path, map_path):
        try:
            f.unlink()
        except Exception:
            pass
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--single", default=None)
    ap.add_argument("--html-only", action="store_true")
    args = ap.parse_args()

    outdir = Path(args.out) if args.out else REPO / "docs" / "report" / "docx"
    outdir.mkdir(parents=True, exist_ok=True)
    # 临时文件放系统 temp，避免污染仓库（沙箱对中文路径的删除也不友好）
    import tempfile
    tmpdir = Path(tempfile.gettempdir()) / "uev_report_build"
    tmpdir.mkdir(parents=True, exist_ok=True)

    # ── 收集章节 ──
    chapter_srcs = []
    for fname, st, en in CHAPTERS:
        p = REPORT / fname
        if p.exists():
            chapter_srcs.append((p, st, en))
        else:
            print(f"  ! 缺章节文件：{fname}（跳过）")
    if not chapter_srcs:
        print("[错误] 没有可用章节")
        return 1

    # ── 图片映射 ──
    # ★ 关键：Word 从 HTML 导入图片时，本地路径含非 ASCII 字符（中文目录名）
    #   会导致图片**静默丢失**（docx 里没有 word/media，提交给别人就是白板）。
    #   实测踩过这个坑 —— 所以先把图片复制到一个纯 ASCII 的临时目录，
    #   HTML 里引用短 ASCII 路径，Word 才能正确嵌入。
    import tempfile, shutil as _sh
    figdir = Path(tempfile.gettempdir()) / "uev_figs"
    if figdir.exists():
        _sh.rmtree(figdir, ignore_errors=True)
    figdir.mkdir(parents=True, exist_ok=True)
    img_map = {}
    # ★ 必须包含 docs/report/images —— E 岗 5.6 节的 9 张图放在这里
    src_dirs = [CHARTS, REPO / "docs" / "screenshots", REPO / "docs" / "架构图",
                REPO / "docs" / "report" / "images", REPO / "docs" / "ppt" / "images"]
    for sd in src_dirs:
        for f in sd.glob("*.png"):
            safe = re.sub(r"[^A-Za-z0-9_.-]", "_", f.name)
            dst = figdir / safe
            _sh.copy2(f, dst)
            img_map[f.name] = dst
            img_map[f.as_posix()] = dst
    print(f"  · 图片已复制到 ASCII 临时目录：{figdir}（{len(img_map)//2} 张）")

    print("=" * 74)
    print(" Markdown → Word 转换（每人一份）")
    print(f" 章节：{len(chapter_srcs)} 个　输出：{outdir}")
    print("=" * 74)

    chapters_html = []
    all_markers = {}
    for p, st, en in chapter_srcs:
        raw = p.read_text(encoding="utf-8")
        cut = slice_by_heading(raw, st, en)
        if st:
            print(f"  · {p.name}：按标记切分（{st} → {en}），{len(raw)} → {len(cut)} 字符")
        chapters_html.append(md_to_html(cut, img_map))
        all_markers.update(getattr(md_to_html, "last_markers", {}))
    print(f"  · 待插入图片占位符：{len(all_markers)} 个")

    members = [m for m in MEMBERS]
    if args.single:
        members = [(args.single, dict(MEMBERS).get(args.single, "2400770000"))]

    results = []
    for mi, (member, sid) in enumerate(members, 1):
        html = build_html(chapters_html, member, sid)
        # ★ 临时文件名用 ASCII 序号 —— 中文路径经命令行/编码转换会乱码
        html_path = tmpdir / f"member{mi}.html"
        html_path.write_text(html, encoding="utf-8")
        docx_path = outdir / f"{sid}_软工2405班_第02组_{member}_城市充电桩数据分析系统.docx"
        if args.single:
            docx_path = outdir / f"_test_{member}.docx"
        if args.html_only:
            print(f"  {member}: HTML 已生成 {html_path}")
            results.append((member, {"ok": True, "html": str(html_path)}))
            continue
        info = word_convert(html_path, docx_path, all_markers)
        try:
            html_path.unlink()
        except Exception:
            pass
        if info["ok"]:
            print(f"  ✓ {member}: {docx_path.name}")
            print(f"      {info.get('pages','?')} 页 / {info.get('words','?')} 字 / "
                  f"{docx_path.stat().st_size/1024:.0f} KB")
        else:
            print(f"  ✗ {member}: 转换失败")
            if info.get("stderr"):
                print("     ", info["stderr"][:300])
        results.append((member, info))

    # 汇总
    print()
    ok = sum(1 for _, i in results if i.get("ok"))
    print(f" 完成：{ok}/{len(results)} 份 docx 生成")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
