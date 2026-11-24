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
    echo "可用组员: 彭忠燕 苏静 贺欢欢 杨姗姗 姬婷婷"
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
# ★ 中文文件名必须用 Python 的 zipfile 解压：
#   Windows 版 unzip 按本地代码页（GBK）解码，与 zip 内存储的 UTF-8 文件名
#   不一致 → 解出来全是乱码（B01_HadoopÚøåþ¥ñþĻÕóâõ©Äjpsµê¬Õø¥ 这种）。
#   Python 3 的 zipfile 默认按 UTF-8 解码，且能正确还原目录结构。
python - "$ZIP" "$TMP" << 'PYEOF_ZIP'
import sys, zipfile
from pathlib import Path
zpath, dest = Path(sys.argv[1]), Path(sys.argv[2])
try:
    with zipfile.ZipFile(zpath) as z:
        z.extractall(dest)
except Exception as e:
    print(f"✗ 解压失败：{e}")
    sys.exit(1)
PYEOF_ZIP
[ $? -ne 0 ] && { echo "✗ 解压失败（可能密码保护或格式异常）"; exit 1; }

echo "▶ 解压内容："
find "$TMP" -type f | sed "s|$TMP/|    |" | head -40
echo

# ── 任务归属判定规则（按文件名关键词 → 目标目录）──# ★ 规则里的字段分隔符用 "::"（不能用 "|" —— Windows 文件名禁止 "|"，
#   bash 会把它替换成私用区字符 \uf07c，落盘后目录名变成
#   "B01_Hadoop\uf07cB01_Hadoop集群环境与jps截图" 这种垃圾）
RULES=(
  "jps|hadoop|集群|HDFS|hdfs::B01_Hadoop集群环境与jps截图"
  "质量规则|质检|dq_|quality::B02_数据质量规则清单"
  "ods|ODS|01_ods::B03_ODS层建表SQL"
  "dwd|DWD|宽转长|WideToLong::B04_DWD层建表与宽转长MR"
  "dws|ads|DWS|ADS|ads_metrics::B05_DWS与ADS层SQL"
  "mapreduce|MR|clean|DataQualityCheck::B06_MapReduce清洗作业"
  "spark|Spark::B07_Spark计算ADS"
  "空间|poi|POI|adj::B08_空间维表加工"
  "sqoop|Sqoop|导出::B09_Sqoop导出到MySQL"
  "view|视图|v_::B10_MySQL视图设计"
  "cluster|聚类::B11_聚类特征宽表与落地表"
  "清洗报告|报告::B12_三份清洗报告"
  "性能|耗时|优化::B13_性能优化与耗时对比"
  "增量::B14_增量抽取机制"
  "调度|schedule|cron::B15_作业调度脚本"
  "表结构说明::B16_数仓表结构说明表"
  "chart|echarts|screenshot|截图::C00_可视化"
  "controller|service|mapper|接口::D00_后端接口"
  "指标|metric::E00_指标分析"
  "个人贡献|贡献说明|contribution::E00_指标分析"
)

# 收集成员目录下的任务文件夹名（用于模糊匹配）
mapfile -t TASKDIRS < <(find "$DEL/$MEMBER" -maxdepth 1 -type d -printf '%f\n' 2>/dev/null | grep -v '^00_' | grep -v '^$' || true)

place_one() {
    local src="$1" target_dir="$2" base
    base="$(basename "$src")"
    # ★ 保险：目标目录名若含 Windows 非法字符（| < > : " ? *），
    #   落盘会变成私用区字符 \uf07c，目录名会很难看。这里主动换掉。
    #   ★ 注意：绝对不能删 "/" —— target_dir 是完整路径，删了会把整条路径粘成一行。
    target_dir="$(printf '%s' "$target_dir" | tr -d '|<>:"?*' | sed 's/_\{2,\}/_/g')"
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
    # ── 优先级 1：路径里直接带任务号前缀（如 B01_Hadoop.../xxx.png）──
    #   这是最可靠的信号，必须先于关键词匹配
    for td in "${TASKDIRS[@]}"; do
        tcode="${td%%_*}"                       # B01 / C03 / D05 ...
        if [[ "$rel" == *"${tcode}_"* ]] || [[ "$rel" == *"/${tcode}/"* ]]; then
            place_one "$f" "$DEL/$MEMBER/$td"
            placed=1; COUNT=$((COUNT+1)); break
        fi
    done
    [ $placed -eq 1 ] && continue
    # ── 优先级 2：关键词匹配 ──
    for rule in "${RULES[@]}"; do
        # 规则格式: "关键词1|关键词2|关键词3::目标子目录"
        rule_kw="${rule%%::*}"
        target="${rule##*::}"
        IFS='|' read -r -a kws <<< "$rule_kw"
        hit=0
        for kw in "${kws[@]}"; do
            [ -z "$kw" ] && continue
            if [[ "$rel" == *"$kw"* ]]; then hit=1; break; fi
        done
        if [ $hit -eq 1 ]; then
            # 精确匹配成员目录里的任务文件夹，否则建同名目录
            # 先精确匹配，再按「去掉任务号前缀的核心词」模糊匹配
            d=""
            for td in "${TASKDIRS[@]}"; do
                if [[ "$td" == "$target" ]]; then d="$td"; break; fi
            done
            if [ -z "$d" ]; then
                core="${target#*_}"          # 去掉 B01_ 前缀
                core="${core%%_*}"            # 只留核心词
                for td in "${TASKDIRS[@]}"; do
                    if [[ "$td" == *"${core}"* ]]; then d="$td"; break; fi
                done
            fi
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
