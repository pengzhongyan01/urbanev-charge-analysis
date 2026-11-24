#!/usr/bin/env bash
# ==============================================================================
# build_submission.sh —— 一键组装提交包（A 岗 · 组长）
#
# 用法（在仓库根目录执行）：
#   bash scripts/build_submission.sh              # 生成到 ../../作业内容/彭忠燕/A09_提交包目录与命名/提交包/
#   bash scripts/build_submission.sh --out DIR    # 指定输出目录
#   bash scripts/build_submission.sh --zip        # 顺便打 zip
#
# 做什么：
#   1. 按老师要求的 7 个文件夹结构组装（01.PPT / 02.大作业报告 / 03.视频 /
#      04.实验报告 / 05.源码 / 06.可视化看板 / 07.数据流向架构图）
#   2. 源码目录按 .gitignore 规则剔除 target/ node_modules/ __pycache__/ *.pyc *.jar
#   3. 自动剔除明文口令（把已知口令替换为环境变量占位）
#   4. 生成 MANIFEST.txt（文件清单 + SHA256），评委可校验完整性
#   5. 打印验收清单勾选结果
#
# 命名规范（照老师给的格式）：
#   C_2405_第02组_ Java Web后端开发技术_基于Hadoop与SpringBoot的城市充电桩使用行为分析与充电需求预测系统的设计与实现.zip
# ==============================================================================
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

GREEN='\033[1;32m'; RED='\033[1;31m'; YELLOW='\033[1;33m'; BLUE='\033[1;34m'; NC='\033[0m'

OUT_DIR="../../作业内容/彭忠燕/A09_提交包目录与命名/提交包"
MAKE_ZIP=0
GROUP_NO="02"          # ★ 组号待确认：打 zip 前必须核一次班级通知

while [ $# -gt 0 ]; do
  case "$1" in
    --out) OUT_DIR="$2"; shift 2 ;;
    --zip) MAKE_ZIP=1; shift ;;
    --group) GROUP_NO="$2"; shift 2 ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
done

echo ""
echo -e "${BLUE}==============================================================${NC}"
echo -e " ${BLUE}组装提交包${NC}"
echo -e " 输出目录：$OUT_DIR"
echo -e " 组    号：第 $GROUP_NO 组（★ 请核对班级通知）"
echo -e "${BLUE}==============================================================${NC}"

# ---- 清理旧包 ----
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"/{01.PPT,02.大作业报告,03.视频,04.实验报告,05.源码,06.可视化看板,07.数据流向架构图}

# ────────────────────────────────────────────────────────────────────────────
# 01.PPT
# ────────────────────────────────────────────────────────────────────────────
if [ -f docs/ppt/第02组_城市充电桩数据分析系统_答辩PPT.pptx ]; then
  cp docs/ppt/第02组_城市充电桩数据分析系统_答辩PPT.pptx "$OUT_DIR/01.PPT/"
  cp -r docs/ppt/images "$OUT_DIR/01.PPT/" 2>/dev/null || true
  echo -e "  ${GREEN}✓${NC} 01.PPT"
else
  echo -e "  ${YELLOW}!${NC} 01.PPT —— PPT 文件缺失"
fi

# ────────────────────────────────────────────────────────────────────────────
# 02.大作业报告 —— 每人一份（老师原文：每人一份，同组可以一样）
# ────────────────────────────────────────────────────────────────────────────
REPORT_SRC="docs/report"
if [ -d "$REPORT_SRC" ]; then
  cp -r "$REPORT_SRC"/*.md "$OUT_DIR/02.大作业报告/" 2>/dev/null || true
  echo -e "  ${GREEN}✓${NC} 02.大作业报告（Markdown 源稿）"
fi
# Word 版（每人一份，5 份）—— 老师要求「每人一份，同组可以一样」
if [ -d "$REPORT_SRC/docx" ]; then
  cp "$REPORT_SRC"/docx/*.docx "$OUT_DIR/02.大作业报告/" 2>/dev/null || true
  echo -e "  ${GREEN}✓${NC} 02.大作业报告/Word 版（$(ls -1 "$OUT_DIR/02.大作业报告"/*.docx 2>/dev/null | wc -l) 份 docx）"
fi

# ────────────────────────────────────────────────────────────────────────────
# 03.视频 / 04.实验报告
# ────────────────────────────────────────────────────────────────────────────
for f in "03.视频/演示视频.mp4" "03.视频/*.mp4"; do
  [ -f "$f" ] && cp "$f" "$OUT_DIR/03.视频/" 2>/dev/null && echo -e "  ${GREEN}✓${NC} 03.视频" && break
done
echo -e "  ${YELLOW}·${NC} 04.实验报告（本次范围外，单独提交）"

# ────────────────────────────────────────────────────────────────────────────
# 05.源码 —— 关键：剔除编译产物与密钥
# ────────────────────────────────────────────────────────────────────────────
echo -e "  ${BLUE}→${NC} 复制源码（剔除 target/ node_modules/ __pycache__/ *.pyc *.jar）..."
mkdir -p "$OUT_DIR/05.源码"
for d in hadoop backend frontend db scripts docker docs; do
  [ -d "$d" ] || continue
  if [ "$d" = "docs" ]; then
    # docs 下只放契约、架构图、RUNBOOK、报告、交付文档；排除截图大目录
    mkdir -p "$OUT_DIR/05.源码/docs"
    for f in RUNBOOK.md CHANGELOG.md README.md; do
      [ -f "docs/$f" ] && cp "docs/$f" "$OUT_DIR/05.源码/docs/"
    done
    cp -r docs/contracts "$OUT_DIR/05.源码/docs/" 2>/dev/null || true
    cp -r docs/架构图 "$OUT_DIR/05.源码/docs/" 2>/dev/null || true
    # ★ 只拷 Markdown 源稿，不拷 docx（正本已在 02.大作业报告，重复一份白占 8.5MB）
    mkdir -p "$OUT_DIR/05.源码/docs/report"
    cp docs/report/*.md "$OUT_DIR/05.源码/docs/report/" 2>/dev/null || true
    [ -d docs/交付 ] && cp -r docs/交付 "$OUT_DIR/05.源码/docs/" 2>/dev/null || true
    # ★ PPT 正本已在 01.PPT，源码目录只留生成脚本，不重复放 pptx 与预览图
    mkdir -p "$OUT_DIR/05.源码/docs/ppt"
    cp docs/ppt/PPT逐页脚本.md docs/ppt/README.md "$OUT_DIR/05.源码/docs/ppt/" 2>/dev/null || true
  else
    cp -r "$d" "$OUT_DIR/05.源码/" 2>/dev/null || true
  fi
done
cp docker-compose.yml "$OUT_DIR/05.源码/" 2>/dev/null || true
cp .env.example "$OUT_DIR/05.源码/" 2>/dev/null || true

# 数据导出样例（每张 MySQL 表前 100 行 CSV）—— 评委会用 restore_from_mysql.sh 回灌
if [ -d "05.源码/数据导出样例" ]; then
  mkdir -p "$OUT_DIR/05.源码/数据导出样例"
  cp "05.源码/数据导出样例"/* "$OUT_DIR/05.源码/数据导出样例/" 2>/dev/null || true
  echo -e "  ${GREEN}✓${NC} 05.源码/数据导出样例（$(ls -1 "$OUT_DIR/05.源码/数据导出样例" | wc -l) 个文件）"
fi

# 剔除垃圾
find "$OUT_DIR/05.源码" -type d -name "target"      -exec rm -rf {} + 2>/dev/null || true
find "$OUT_DIR/05.源码" -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
find "$OUT_DIR/05.源码" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$OUT_DIR/05.源码" -type f -name "*.pyc"  -delete 2>/dev/null || true
find "$OUT_DIR/05.源码" -type f -name "*.jar"  -delete 2>/dev/null || true
find "$OUT_DIR/05.源码" -type f -name "*.class" -delete 2>/dev/null || true
find "$OUT_DIR/05.源码" -type f -name ".DS_Store" -delete 2>/dev/null || true

# 明文口令 → 环境变量占位
echo -e "  ${BLUE}→${NC} 替换明文口令..."
grep -rl "uev123456\|uev_redis_pass" "$OUT_DIR/05.源码" 2>/dev/null | grep -v ".example" | head -20 | while read -r f; do
  sed -i 's/uev123456/${MYSQL_ROOT_PASSWORD:-CHANGE_ME}/g; s/uev_redis_pass/${REDIS_PASSWORD:-CHANGE_ME}/g' "$f" 2>/dev/null || true
  echo "      已处理：${f#$OUT_DIR/05.源码/}"
done

# ────────────────────────────────────────────────────────────────────────────
# 06.可视化看板 / 07.数据流向架构图
# ────────────────────────────────────────────────────────────────────────────
[ -d docs/架构图 ] && cp docs/架构图/*.png "$OUT_DIR/07.数据流向架构图/" 2>/dev/null
echo -e "  ${GREEN}✓${NC} 07.数据流向架构图"

# 大屏 PNG（首页大屏 / 分区地图 / 供需失衡 / 布点建议）
if [ -d docs/screenshots ]; then
  cp docs/screenshots/*.png "$OUT_DIR/06.可视化看板/" 2>/dev/null || true
fi
# 10 张核心图表
if [ -d docs/charts ]; then
  mkdir -p "$OUT_DIR/06.可视化看板/核心图表"
  cp docs/charts/*.png "$OUT_DIR/06.可视化看板/核心图表/" 2>/dev/null || true
fi
if [ -d data/etl_out ]; then
  mkdir -p "$OUT_DIR/06.可视化看板/ADS数据表"
  cp data/etl_out/*.csv "$OUT_DIR/06.可视化看板/ADS数据表/" 2>/dev/null || true
fi
echo -e "  ${GREEN}✓${NC} 06.可视化看板（大屏 $(ls -1 "$OUT_DIR/06.可视化看板"/*.png 2>/dev/null | wc -l) 张 + 核心图表 $(ls -1 "$OUT_DIR/06.可视化看板/核心图表" 2>/dev/null | wc -l) 张 + ADS 表 $(ls -1 "$OUT_DIR/06.可视化看板/ADS数据表" 2>/dev/null | wc -l) 张）"

# ────────────────────────────────────────────────────────────────────────────
# 剔除临时产物
# ────────────────────────────────────────────────────────────────────────────
# ★ Word 转换会留下 _tmp_*.html 和 *.files 目录（含内嵌图 base64，体积巨大），
#   不剔除会让提交包白白多占十几 MB，评委解压时也会莫名其妙。
find "$OUT_DIR" -name "_tmp_*" -delete 2>/dev/null || true
find "$OUT_DIR" -name "*.files" -type d -exec rm -rf {} + 2>/dev/null || true
find "$OUT_DIR" -name "*.html" -path "*report*" -delete 2>/dev/null || true

# ────────────────────────────────────────────────────────────────────────────
# 剔除临时产物
# ────────────────────────────────────────────────────────────────────────────
# ★ Word 转换会留下 _tmp_*.html 和 *.files 目录（含内嵌图 base64，体积巨大），
#   不剔除会让提交包白白多占十几 MB，评委解压时也会莫名其妙。
find "$OUT_DIR" -name "_tmp_*" -delete 2>/dev/null || true
find "$OUT_DIR" -name "*.files" -type d -exec rm -rf {} + 2>/dev/null || true
find "$OUT_DIR" -name "*.html" -path "*report*" -delete 2>/dev/null || true

# ────────────────────────────────────────────────────────────────────────────
# MANIFEST
# ────────────────────────────────────────────────────────────────────────────
echo -e "  ${BLUE}→${NC} 生成 MANIFEST.txt ..."
{
  echo "提交包清单与完整性校验"
  echo "生成时间：$(date '+%Y-%m-%d %H:%M:%S')"
  echo "组号：第 $GROUP_NO 组"
  echo ""
  echo "目录："
  find "$OUT_DIR" -maxdepth 2 -type d | sed "s|$OUT_DIR|.|" | sort
  echo ""
  echo "文件（SHA256）："
  find "$OUT_DIR" -type f ! -name "MANIFEST.txt" -print0 | sort -z | while IFS= read -r -d '' f; do
    printf "%s  %s\n" "$(sha256sum "$f" | cut -d' ' -f1)" "${f#$OUT_DIR/}"
  done
} > "$OUT_DIR/MANIFEST.txt"
echo "     MANIFEST.txt 已生成"

# ────────────────────────────────────────────────────────────────────────────
# 验收清单
# ────────────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BLUE}==============================================================${NC}"
echo -e " ${BLUE}验收清单${NC}"
echo -e "${BLUE}==============================================================${NC}"
chk() { if [ "$2" = "1" ]; then echo -e "  ${GREEN}✓${NC} $1"; else echo -e "  ${RED}✗${NC} $1"; fi; }

chk "01.PPT 存在"                "$([ -f "$OUT_DIR/01.PPT/第02组_城市充电桩数据分析系统_答辩PPT.pptx" ] && echo 1 || echo 0)"
chk "05.源码/backend 有 pom.xml"  "$([ -f "$OUT_DIR/05.源码/backend/pom.xml" ] && echo 1 || echo 0)"
chk "05.源码 无 target/"         "$([ -z "$(find "$OUT_DIR/05.源码" -type d -name target 2>/dev/null)" ] && echo 1 || echo 0)"
chk "05.源码 无 *.jar"          "$([ -z "$(find "$OUT_DIR/05.源码" -type f -name '*.jar' 2>/dev/null)" ] && echo 1 || echo 0)"
chk "05.源码 无 *.pyc"          "$([ -z "$(find "$OUT_DIR/05.源码" -type f -name '*.pyc' 2>/dev/null)" ] && echo 1 || echo 0)"
chk "05.源码 无明文口令"        "$([ -z "$(grep -rl 'uev123456\|uev_redis_pass' "$OUT_DIR/05.源码" 2>/dev/null | grep -v '.example')" ] && echo 1 || echo 0)"
chk "07.架构图 2 张"             "$([ "$(find "$OUT_DIR/07.数据流向架构图" -name '*.png' 2>/dev/null | wc -l)" -ge 2 ] && echo 1 || echo 0)"
chk "MANIFEST.txt 已生成"       "$([ -f "$OUT_DIR/MANIFEST.txt" ] && echo 1 || echo 0)"

TOTAL=$(find "$OUT_DIR" -type f | wc -l)
SIZE=$(du -sh "$OUT_DIR" 2>/dev/null | cut -f1)
echo ""
echo "  文件总数：$TOTAL    总体积：$SIZE"
echo "  输出目录：$OUT_DIR"

# ────────────────────────────────────────────────────────────────────────────
if [ "$MAKE_ZIP" = "1" ]; then
  ZIP_NAME="C_2405_第${GROUP_NO}组_ Java Web后端开发技术_基于Hadoop与SpringBoot的城市充电桩使用行为分析与充电需求预测系统的设计与实现.zip"
  echo ""
  echo -e "  ${BLUE}→${NC} 打包：$ZIP_NAME"
  ( cd "$(dirname "$OUT_DIR")" && zip -qr "$ZIP_NAME" "$(basename "$OUT_DIR")" ) \
    && echo -e "  ${GREEN}✓${NC} zip 已生成：$(dirname "$OUT_DIR")/$ZIP_NAME" \
    || echo -e "  ${YELLOW}!${NC} zip 失败（可能没装 zip 命令，可手动右键压缩）"
fi

echo ""
echo -e "${BLUE}==============================================================${NC}"
echo -e " ${GREEN}提交包组装完成${NC}"
echo -e "${BLUE}==============================================================${NC}"
echo ""
echo "★ 剩余待补（由组员交付后重跑本脚本自动带入）："
echo "  - 02.大作业报告/*.docx      每人一份，5 份（Word 版）"
echo "  - 03.视频/*.mp4             演示视频（可选项）"
echo "  - 06.可视化看板/*.png       ≥4 张大屏截图（C 岗）"
echo "  - 05.源码/数据导出样例/     每张 MySQL 表前 100 行 CSV"
echo ""
