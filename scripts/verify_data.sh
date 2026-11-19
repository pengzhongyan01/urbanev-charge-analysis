#!/usr/bin/env bash
# ==============================================================================
# verify_data.sh —— 数据完整性校验
#
# 维护人：A（组长）　|　用途：组员下载数据后核对是否完整
#
# 用法：bash scripts/verify_data.sh
# 退出码：0 = 全部通过，1 = 有问题
#
# 它检查三件事：
#   1. 12 个文件是否都在
#   2. 每个文件的行数是否正确
#   3. 每个文件的 SHA256 是否与官方一致
# ==============================================================================
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

# shellcheck source=scripts/find_data.sh
source scripts/find_data.sh

GREEN='\033[1;32m'; RED='\033[1;31m'; YELLOW='\033[1;33m'; BLUE='\033[1;34m'; NC='\033[0m'
PASS=0; FAIL=0; WARN=0
pass() { echo -e "  ${GREEN}✓${NC} $1"; PASS=$((PASS+1)); }
fail() { echo -e "  ${RED}✗${NC} $1"; FAIL=$((FAIL+1)); }
warn() { echo -e "  ${YELLOW}!${NC} $1"; WARN=$((WARN+1)); }

# ---- 期望值：文件名|期望行数|期望 SHA256 ----
EXPECTED="
adj.csv|276|93100d3b042086159387ec069efbaf411b90298cdf8a7ada64de214c6bdb5c00
distance.csv|276|3630642ddce0e4aac440804c134f3424614ce2bd34fc7bcadd1bc1a3de0d303e
duration.csv|4345|3afc79ca193267bca327b04d45b6cf24240f8c93ea94bcbb0a52cc119b8080d1
e_price.csv|4345|0076d03b8e400c3e911789e2c7ffb7dd0d44a4414247ead676b508def95bcef4
inf.csv|276|0699db1069b289caa7f37c7179f482bfe3211711957f8acfe5afc7e1b4dcf2a1
occupancy.csv|4345|264c06c9a68cd296abd11ef0260dff3fcf9feb6ed7775182edfdd6ea77b1900e
poi.csv|712136|b8fd50cbde3b083fc10ce3b423acf60057944e517e90c6f33eb779132f21a1f8
s_price.csv|4345|d125783e042024157f38d1749232696ea2aa893c61fc31672a3c54374498d3dc
volume-11kW.csv|4345|0841f776149120d03bfe9aa04a192a26f28a0f8e89d7752cf59d44672f5b5ee0
volume.csv|4345|a55a095ce75af33c59aece2643d5d71b5cd5a0dc73bb97bc553f0a48f40ace32
weather_airport.csv|4345|ccc9b0056e8f770502d4e05e5cf15cc189af28317629e1b0cb5428ef193ea503
weather_central.csv|4345|da8c16dcc6a25eadc97ca062998b5dbb01efbb4569efdd693ac98fb5bbc6d065
"

echo ""
echo "=============================================================="
echo -e " ${BLUE}UrbanEV 数据完整性校验${NC}"
echo "=============================================================="

if [ -z "${UEV_DATA_DIR:-}" ]; then
  echo -e "\n${RED}✗ 未找到数据目录${NC}"
  echo "  请执行 bash scripts/download_data.sh 下载数据"
  echo "  或设置环境变量 UEV_DATA_DIR 指向数据所在目录"
  echo ""
  exit 1
fi

echo ""
echo "数据目录：$UEV_DATA_DIR"
echo ""

# ---- 检查 1：文件存在性 ----
echo -e "${BLUE}[1/3]${NC} 文件完整性"
MISSING=0
while IFS='|' read -r fname lines sha; do
  [ -z "$fname" ] && continue
  if [ -f "$UEV_DATA_DIR/$fname" ]; then
    pass "$fname 存在"
  else
    fail "$fname 缺失"
    MISSING=$((MISSING+1))
  fi
done <<< "$EXPECTED"

# ---- 检查 2：行数 ----
echo ""
echo -e "${BLUE}[2/3]${NC} 行数校验"
while IFS='|' read -r fname lines sha; do
  [ -z "$fname" ] && continue
  f="$UEV_DATA_DIR/$fname"
  [ -f "$f" ] || continue
  actual=$(wc -l < "$f" 2>/dev/null | tr -d ' ')
  if [ "$actual" = "$lines" ]; then
    pass "$fname 行数 $actual"
  else
    fail "$fname 行数 $actual（应为 $lines）—— 可能下载不完整"
  fi
done <<< "$EXPECTED"

# ---- 检查 3：SHA256 ----
echo ""
echo -e "${BLUE}[3/3]${NC} SHA256 校验"
if command -v sha256sum >/dev/null 2>&1; then
  HASHER="sha256sum"
elif command -v shasum >/dev/null 2>&1; then
  HASHER="shasum -a 256"
else
  warn "系统无 sha256sum 工具，跳过"
  HASHER=""
fi

if [ -n "$HASHER" ]; then
  while IFS='|' read -r fname lines sha; do
    [ -z "$fname" ] && continue
    f="$UEV_DATA_DIR/$fname"
    [ -f "$f" ] || continue
    actual=$($HASHER "$f" 2>/dev/null | awk '{print $1}')
    if [ "$actual" = "$sha" ]; then
      pass "$fname SHA256 一致"
    else
      fail "$fname SHA256 不匹配（文件损坏或被改动）"
    fi
  done <<< "$EXPECTED"
fi

# ---- 汇总 ----
TOTAL=$(echo "$EXPECTED" | grep -c '|')
echo ""
echo "=============================================================="
echo -e " ${BLUE}结果${NC}：通过 ${GREEN}$PASS${NC}　警告 ${YELLOW}$WARN${NC}　失败 ${RED}$FAIL${NC}"
if [ "$FAIL" -gt 0 ]; then
  echo ""
  if [ "$MISSING" -gt 0 ]; then
    echo -e " ${RED}有 $MISSING 个文件缺失${NC} —— 重新执行：bash scripts/download_data.sh"
  else
    echo -e " ${RED}文件不完整或已损坏${NC} —— 重新执行：bash scripts/download_data.sh"
  fi
  echo "=============================================================="
  echo ""
  exit 1
fi
echo -e " ${GREEN}数据完整可用${NC}　（共 $TOTAL 个文件）"
echo "=============================================================="
echo ""
exit 0
