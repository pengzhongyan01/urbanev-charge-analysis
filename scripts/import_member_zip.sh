#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  组员交付包入库脚本
#
#  用法：
#    bash scripts/import_member_zip.sh <zip路径> <组员姓名>
#
#  例：
#    bash scripts/import_member_zip.sh ~/Downloads/苏静交付.zip 苏静
#
#  作用：
#    1. 解压到临时目录（不覆盖现有文件）
#    2. 按文件名/内容自动判定属于哪个岗位任务（A/B/C/D/E）
#    3. 归档到 作业内容/<组员>/ 对应任务目录
#    4. 刷新交付看板
#
#  ★ 设计原则：绝不覆盖。已存在的同名文件改名加后缀（.dup1/.dup2），
#    保留双方版本，由组长人工判定留哪个。
# ─────────────────────────────────────────────────────────────
set -euo pipefail

ZIP="${1:-}"
MEMBER="${2:-}"

if [ -z "$ZIP" ] || [ -z "$MEMBER" ]; then
    echo "用法: bash scripts/import_member_zip.sh <zip路径> <组员姓名>"
    echo "可用组员: 彭忠燕 苏静 贺欢欢 杨珊珊 姬婷婷"
    exit 1
fi

# 定位作业内容目录（脚本在 urbanev-charge-analysis/scripts/ 下）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
WORK="$(cd "$REPO/.." && pwd)"
DEL="$WORK/作业内容"

if [ ! -f "$ZIP" ]; then
    echo "✗ 找不到 zip：$ZIP"
    exit 1
fi
if [ ! -d "$DEL/$MEMBER" ]; then
    echo "✗ 找不到组员目录：$DEL/$MEMBER"
    echo "  可选：$(ls "$DEL" | tr '\n' ' ')"
    exit 1
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "▶ 解压到临时目录…"
# 中文文件名在 unzip 下可能乱码，用 -O GBK 兜底；失败则退回默认
unzip -qq -o "$ZIP" -d "$TMP" 2>/dev/null || unzip -qq -o "$ZIP" -d "$TMP" -O GBK 2>/dev/null || {
    echo "✗ 解压失败（可能密码保护或格式异常）"; exit 1; }

echo "▶ 解压内容："
find "$TMP" -type f | sed "s|$TMP/|    |" | head -40
echo

# ── 任务归属判定规则（按文件名关键词 → 目标目录）──
# 格式: "关键词1|关键词2|目标子目录"
RULES=(
  "jps|hadoop|集群|HDFS|hdfs|B01|B01_Hadoop集群环境与jps截图"
  "质量规则|质检|dq_|quality|B02|B02_数据质量规则清单"
  "ods|ODS|01_ods|B03|B03_ODS层建表SQL"
  "dwd|DWD|宽转长|WideToLong|B04|B04_DWD层建表与宽转长MR"
  "dws|ads|DWS|ADS|ads_metrics|B05|B05_DWS与ADS层SQL"
  "mapreduce|MR|clean|DataQualityCheck|B06|B06_MapReduce清洗作业"
  "spark|Spark|B07|B07_Spark计算ADS"
  "空间|poi|POI|adj|B08|B08_空间维表加工"
  "sqoop|Sqoop|导出|B09|B09_Sqoop导出到MySQL"
  "view|视图|v_|B10|B10_MySQL视图设计"
  "cluster|聚类|B11|B11_聚类特征宽表与落地表"
  "清洗报告|报告|B12|B12_三份清洗报告"
  "性能|耗时|优化|B13|B13_性能优化与耗时对比"
  "增量|B14|B14_增量抽取机制"
  "调度|schedule|cron|B15|B15_作业调度脚本"
  "表结构说明|B16|B16_数仓表结构说明表"
  "chart|图|echarts|screenshot|截图|C-|C0"
  "controller|service|mapper|api|接口|D-|D0"
  "指标|metric|M1|E-|E0"
  "个人贡献|贡献说明|contribution"
)

# 收集成员目录下的任务文件夹名（用于模糊匹配）
mapfile -t TASKDIRS < <(find "$DEL/$MEMBER" -maxdepth 1 -type d -printf '%f\n' 2>/dev/null | grep -v '^00_' | grep -v '^$' || true)

place_one() {
    local src="$1" target_dir="$2" base
    base="$(basename "$src")"
    mkdir -p "$target_dir"
    local dst="$target_dir/$base"
    if [ -e "$dst" ]; then
        local i=1
        while [ -e "$target_dir/${base%.???}.dup${i}${base##*.}" ]; do i=$((i+1)); done
        dst="$target_dir/${base%.*}.dup${i}.${base##*.}"
        echo "    ⚠ 已存在，改存为 $(basename "$dst")"
    fi
    cp "$src" "$dst"
    echo "    ✓ $(basename "$dst")  →  $(basename "$target_dir")"
}

echo "▶ 按规则归档："
COUNT=0
while IFS= read -r f; do
    rel="${f#$TMP/}"
    placed=0
    for rule in "${RULES[@]}"; do
        IFS='|' read -r k1 k2 target <<< "$rule"
        if [[ "$rel" =~ $k1 ]] || { [ -n "$k2" ] && [[ "$rel" =~ $k2 ]]; }; then
            # 精确匹配成员目录里的任务文件夹，否则建同名目录
            d=""
            for td in "${TASKDIRS[@]}"; do
                if [[ "$td" == "$target" ]] || [[ "$td" == *"$target"* ]]; then d="$td"; break; fi
            done
            [ -z "$d" ] && d="$target"
            place_one "$f" "$DEL/$MEMBER/$d"
            placed=1; COUNT=$((COUNT+1)); break
        fi
    done
    if [ $placed -eq 0 ]; then
        place_one "$f" "$DEL/$MEMBER/00_组员补充材料"
        COUNT=$((COUNT+1))
    fi
done < <(find "$TMP" -type f)

echo
echo "▶ 共入库 $COUNT 个文件"
echo
echo "▶ 刷新交付看板…"
cd "$DEL" && python 检查交付物.py 2>&1 | grep -E "【$MEMBER】" -A 6 | head -8 || true
echo
echo "✔ 完成。请人工核对 $DEL/$MEMBER/ 下新增文件。"
