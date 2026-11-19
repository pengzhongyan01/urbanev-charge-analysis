#!/usr/bin/env bash
# ==============================================================================
# find_data.sh —— 定位 UrbanEV 数据目录（统一出口）
#
# 维护人：A（组长）　|　所有脚本都通过本脚本找数据，不要各自硬编码路径
#
# 数据存放位置（按优先级探测，找到即用）：
#   1. 环境变量 UEV_DATA_DIR
#   2. 仓库内 data/raw/            （组员 clone 仓库后自己放的位置）
#   3. 仓库同级 ../数据/UrbanEV/    （★ 组长本机：大作业/数据/UrbanEV）
#   4. 上两级 ../../数据/UrbanEV/
#   5. 上三级 ../../../数据/UrbanEV/
#   6. 上四级 ../../../../数据/UrbanEV/
#
# 用法：
#   source scripts/find_data.sh && echo "$UEV_DATA_DIR"
#   bash scripts/find_data.sh          # 只打印路径
# ==============================================================================

# ---- 以脚本自身位置为基准算出仓库根目录 ----
_UEV_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_UEV_REPO_ROOT="$(cd "$_UEV_SCRIPT_DIR/.." && pwd)"

# ---- 探测候选路径 ----
_candidates=(
  "${UEV_DATA_DIR:-}"
  "$_UEV_REPO_ROOT/data/raw"
  "$_UEV_REPO_ROOT/data/dataset"
  "$_UEV_REPO_ROOT/../数据/UrbanEV"
  "$_UEV_REPO_ROOT/../数据"
  "$_UEV_REPO_ROOT/../../数据/UrbanEV"
  "$_UEV_REPO_ROOT/../../数据"
  "$_UEV_REPO_ROOT/../../../数据/UrbanEV"
  "$_UEV_REPO_ROOT/../../../数据"
  "$_UEV_REPO_ROOT/../../../../数据/UrbanEV"
  "$_UEV_REPO_ROOT/../../../../数据"
)

UEV_DATA_DIR=""
for _d in "${_candidates[@]}"; do
  [ -z "$_d" ] && continue
  if [ -d "$_d" ] && ls "$_d"/*.csv >/dev/null 2>&1; then
    UEV_DATA_DIR=$(cd "$_d" && pwd)
    break
  fi
done

export UEV_DATA_DIR

# ---- 直接执行时打印结果 ----
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  if [ -n "$UEV_DATA_DIR" ]; then
    echo "$UEV_DATA_DIR"
    echo "CSV 数量: $(ls -1 "$UEV_DATA_DIR"/*.csv 2>/dev/null | wc -l)" >&2
  else
    echo "未找到数据目录" >&2
    echo "已探测的候选位置（基于仓库 $_UEV_REPO_ROOT）:" >&2
    for _d in "${_candidates[@]}"; do
      [ -z "$_d" ] && continue
      echo "  - $_d" >&2
    done
    echo "" >&2
    echo "解决办法（任选其一）：" >&2
    echo "  1. 执行 bash scripts/download_data.sh 自动下载" >&2
    echo "  2. 手动把 12 个 CSV 放到 $  _UEV_REPO_ROOT/data/raw/" >&2
    echo "  3. 设置环境变量：export UEV_DATA_DIR=/你的/数据/路径" >&2
    exit 1
  fi
fi
