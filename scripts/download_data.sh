#!/usr/bin/env bash
# ==============================================================================
# download_data.sh —— 下载 UrbanEV 数据集
#
# 维护人：A（组长）　|　使用方：贺欢欢（C 组）
#
# 数据来源：
#   UrbanEV —— Li Han, Haohao Qu et al. (2023)
#   GitHub: https://github.com/whewhewhenew/UrbanEV
#   论文:   arXiv:2309.05259
#   许可:   CC0（公共领域，可自由使用，引用时注明出处即可）
#
# 用法：bash scripts/download_data.sh          # 下载 1 小时粒度数据（核心，12 个 CSV）
#        bash scripts/download_data.sh --5min   # 额外下载 5 分钟粒度（可选，42MB）
#
# 说明：国内访问 raw.githubusercontent.com 偶尔超时，脚本内置了重试和镜像加速。
# ==============================================================================
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

GREEN='\033[1;32m'; RED='\033[1;31m'; YELLOW='\033[1;33m'; BLUE='\033[1;34m'; CYAN='\033[1;36m'; NC='\033[0m'

# 数据存放位置：优先用已有的探测逻辑，找不到就默认放 data/raw
# shellcheck source=scripts/find_data.sh
source scripts/find_data.sh
RAW_DIR="${UEV_DATA_DIR:-data/raw}"
BASE_URL="https://raw.githubusercontent.com/whewhewhenew/UrbanEV/main/data"
MIRROR_URL="https://ghfast.top/https://raw.githubusercontent.com/whewhewhenew/UrbanEV/main/data"

FILES=(
  "occupancy.csv"
  "duration.csv"
  "volume.csv"
  "volume-11kW.csv"
  "e_price.csv"
  "s_price.csv"
  "inf.csv"
  "adj.csv"
  "distance.csv"
  "poi.csv"
  "weather_airport.csv"
  "weather_central.csv"
)

echo ""
echo "=============================================================="
echo -e " ${BLUE}UrbanEV 数据集下载${NC}"
echo "=============================================================="
echo -e " 来源：https://github.com/whewhewhenew/UrbanEV"
echo -e " 许可：CC0　引用：Li Han, Haohao Qu et al., arXiv:2309.05259 (2023)"
echo ""

mkdir -p "$RAW_DIR"
echo "数据目录: $RAW_DIR"

# ------------------------------------------------------------------------------
# 下载单个文件（带重试 + 镜像加速降级）
# ------------------------------------------------------------------------------
download_one() {
  local fname="$1"
  local target="$RAW_DIR/$fname"
  local url="$BASE_URL/$fname"

  # 已存在且非空则跳过
  if [ -s "$target" ]; then
    local sz=$(stat -c%s "$target" 2>/dev/null || echo 0)
    if [ "$sz" -gt 1000 ]; then
      echo -e "    ${GREEN}✓${NC} $fname 已存在（$((sz/1024/1024))MB），跳过"
      return 0
    fi
  fi

  # 先尝试直连，失败后用镜像
  for attempt in 1 2 3; do
    local code=$(curl -skL --max-time 600 --connect-timeout 20 -w "%{http_code}" -o "$target" "$url" 2>/dev/null)
    local sz=$(stat -c%s "$target" 2>/dev/null || echo 0)
    if [ "$code" = "200" ] && [ "$sz" -gt 1000 ]; then
      echo -e "    ${GREEN}✓${NC} $fname  ($((sz/1024/1024))MB)"
      return 0
    fi
    echo -e "    ${YELLOW}...${NC} $fname 第 $attempt 次尝试失败（http=$code），重试"
    sleep 3
  done

  # 镜像加速
  echo -e "    ${CYAN}→${NC} 尝试镜像加速：ghfast.top"
  code=$(curl -skL --max-time 600 --connect-timeout 20 -w "%{http_code}" -o "$target" "$MIRROR_URL/$fname" 2>/dev/null)
  sz=$(stat -c%s "$target" 2>/dev/null || echo 0)
  if [ "$code" = "200" ] && [ "$sz" -gt 1000 ]; then
    echo -e "    ${GREEN}✓${NC} $fname  ($((sz/1024/1024))MB)  [镜像]"
    return 0
  fi

  echo -e "    ${RED}✗${NC} $fname 下载失败"
  rm -f "$target"
  return 1
}

# ------------------------------------------------------------------------------
# 主流程
# ------------------------------------------------------------------------------
echo -e "${BLUE}[1/3]${NC} 下载核心数据（1 小时粒度，12 个 CSV）..."
FAILED=0
for f in "${FILES[@]}"; do
  download_one "$f" || FAILED=$((FAILED+1))
done

# 可选：5 分钟粒度
if [ "${1:-}" = "--5min" ]; then
  echo -e "\n${BLUE}[2/3]${NC} 下载 5 分钟粒度数据（可选，42MB）..."
  code=$(curl -skL --max-time 900 --connect-timeout 20 -w "%{http_code}" \
         -o "$RAW_DIR/5-minutes.zip" \
         "$BASE_URL/5-minutes.zip" 2>/dev/null)
  sz=$(stat -c%s "$RAW_DIR/5-minutes.zip" 2>/dev/null || echo 0)
  if [ "$code" = "200" ] && [ "$sz" -gt 1000 ]; then
    echo -e "    ${GREEN}✓${NC} 5-minutes.zip  ($((sz/1024/1024))MB)"
    cd "$RAW_DIR" && unzip -o -q 5-minutes.zip && cd .. && echo -e "    ${GREEN}✓${NC} 已解压"
  else
    echo -e "    ${YELLOW}!${NC} 5 分钟粒度下载失败（非必需，跳过）"
  fi
else
  echo -e "\n${BLUE}[2/3]${NC} 跳过 5 分钟粒度（非必需，需要时加 --5min 参数）"
fi

# ------------------------------------------------------------------------------
# 校验
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[3/3]${NC} 校验数据..."
echo ""
printf "  %-22s %10s %10s %s\n" "文件" "行数" "大小" "表头"
printf "  %-22s %10s %10s %s\n" "----------------------" "----------" "----------" "----"

if [ -d "$RAW_DIR" ]; then
  for f in "$RAW_DIR"/*.csv; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    lines=$(wc -l < "$f" 2>/dev/null | tr -d ' ')
    size=$(du -h "$f" 2>/dev/null | cut -f1)
    header=$(head -1 "$f" 2>/dev/null | cut -c1-52)
    printf "  %-22s %10s %10s %s\n" "$bn" "$lines" "$size" "$header"
  done
fi

echo ""
TOTAL=$(du -sh "$RAW_DIR" 2>/dev/null | cut -f1)
COUNT=$(ls -1 "$RAW_DIR"/*.csv 2>/dev/null | wc -l)

if [ "$FAILED" -eq 0 ] && [ "$COUNT" -ge 11 ]; then
  echo "=============================================================="
  echo -e " ${GREEN}下载完成${NC}  共 $COUNT 个 CSV，总计 $TOTAL"
  echo "=============================================================="
  echo ""
  echo -e " 下一步："
  echo -e "   1. ${CYAN}贺欢欢${NC}：基于 data/raw/ 写《数据字典》（docs/contracts/01-数据字典.md）"
  echo -e "   2. ${CYAN}苏静${NC}：先跑 wc -l 看行数，再设计 ODS 建表"
  echo -e ""
  echo -e " ${YELLOW}注意${NC}：data/ 目录已在 .gitignore 中，数据不进 Git。"
  echo -e "       需要共享数据时用网盘/Google Drive，不要 commit。"
  echo ""
  exit 0
else
  echo "=============================================================="
  echo -e " ${YELLOW}部分文件缺失${NC}（成功 $COUNT / 12，失败 $FAILED）"
  echo "=============================================================="
  echo -e " 请重试：bash scripts/download_data.sh"
  echo -e " 若持续失败，请换网络环境或让 C 岗用网盘分发"
  echo ""
  exit 1
fi
