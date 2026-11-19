#!/usr/bin/env bash
# ==============================================================================
# start_all.sh —— 一键启动全套环境
#
# 维护人：A（组长）　|　目标：任何人执行这一条命令，全套系统就绪
#
# 用法：bash scripts/start_all.sh
#
# 自动降级逻辑（答辩现场的救命功能）：
#   检测到 Docker + 本地缓存大数据镜像 → full 模式（Hadoop+Hive+MySQL+Redis+后端+前端）
#   只有 Docker                      → app 模式（本机已有 Hadoop 时的常态）
#   无 Docker 但有本机 HADOOP_HOME   → native 模式（走 scripts/start_native.sh）
#
# 无论走哪条路，最后都会跑一次 smoke_test.sh 做端到端体检。
# ==============================================================================
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

GREEN='\033[1;32m'; RED='\033[1;31m'; YELLOW='\033[1;33m'; BLUE='\033[1;34m'; CYAN='\033[1;36m'; NC='\033[0m'

echo ""
echo "=============================================================="
echo -e " ${BLUE}UrbanEV 充电桩分析系统 · 一键启动${NC}"
echo "=============================================================="

# ------------------------------------------------------------------------------
# 0. 前置检查
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[0/5]${NC} 前置检查..."
HAS_DOCKER=0
if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    HAS_DOCKER=1
    echo -e "    ${GREEN}✓${NC} Docker 可用"
  else
    echo -e "    ${RED}✗${NC} Docker 已安装但守护进程未启动，请先启动 Docker Desktop"
    exit 1
  fi
else
  echo -e "    ${YELLOW}!${NC} 未检测到 Docker"
fi

HAS_JAVA=0
if command -v java >/dev/null 2>&1; then
  HAS_JAVA=1
  echo -e "    ${GREEN}✓${NC} Java 可用"
else
  echo -e "    ${YELLOW}!${NC} 未检测到 Java"
fi

# ------------------------------------------------------------------------------
# 1. 数据检查（缺失时给出明确指引，而不是静默继续）
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[1/5]${NC} 检查数据..."
# shellcheck source=scripts/find_data.sh
source scripts/find_data.sh
if [ -n "${UEV_DATA_DIR:-}" ]; then
  CSV_COUNT=$(ls -1 "$UEV_DATA_DIR"/*.csv 2>/dev/null | wc -l)
  TOTAL_SIZE=$(du -sh "$UEV_DATA_DIR" 2>/dev/null | cut -f1)
  echo -e "    ${GREEN}✓${NC} 数据目录：$UEV_DATA_DIR"
  echo -e "    ${GREEN}✓${NC} 有 ${CSV_COUNT} 个 CSV（$TOTAL_SIZE）"
else
  echo -e "    ${RED}✗${NC} 未找到数据目录"
  echo -e "       ${YELLOW}→${NC} 执行 ${CYAN}bash scripts/download_data.sh${NC} 下载 UrbanEV 数据集"
  echo -e "       ${YELLOW}→${NC} 或手动把 12 个 CSV 放到 ${CYAN}data/raw/${NC} 或 ${CYAN}大作业/数据/UrbanEV/${NC}"
  echo -e "       ${YELLOW}→${NC} 数据是全组命脉，缺数据后面全部返工"
  exit 1
fi

# ------------------------------------------------------------------------------
# 2. 选择启动模式
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[2/5]${NC} 选择启动模式..."
MODE=""

if [ "$HAS_DOCKER" -eq 1 ]; then
  if docker images --format '{{.Repository}}:{{.Tag}}' 2>/dev/null | grep -q "apache/hadoop"; then
    MODE="full"
    echo -e "    ${GREEN}✓${NC} 检测到本地 Hadoop 镜像 → ${CYAN}full 模式${NC}（Hadoop+Hive+应用全起）"
  elif docker images --format '{{.Repository}}:{{.Tag}}' 2>/dev/null | grep -q "apache/hive"; then
    MODE="full"
    echo -e "    ${GREEN}✓${NC} 检测到本地 Hive 镜像 → ${CYAN}full 模式${NC}"
  elif [ "$HAS_JAVA" -eq 1 ] && [ -n "${HADOOP_HOME:-}" ]; then
    MODE="app"
    echo -e "    ${YELLOW}!${NC} 未缓存大数据镜像，但检测到本机 HADOOP_HOME → ${CYAN}app 模式${NC}"
    echo -e "       ${YELLOW}!${NC} 大数据部分用本机 Hadoop，应用层用 Docker"
  else
    MODE="app"
    echo -e "    ${YELLOW}!${NC} 未缓存大数据镜像 → ${CYAN}app 模式${NC}（MySQL+Redis+后端+前端）"
    echo -e "       ${YELLOW}!${NC} ${CYAN}提示${NC}：首次拉取大镜像约需 1-2GB 流量，若需完整 Hadoop 环境请提前一天执行"
    echo -e "              ${CYAN}docker compose --profile full pull${NC}"
  fi
else
  if [ "$HAS_JAVA" -eq 1 ] && [ -n "${HADOOP_HOME:-}" ]; then
    MODE="native"
    echo -e "    ${GREEN}✓${NC} 无 Docker 但有本机 Hadoop → ${CYAN}native 模式${NC}"
  else
    echo -e "    ${RED}✗${NC} 既无 Docker 也无本机 Hadoop"
    echo -e "       ${YELLOW}→${NC} 二选一：装 Docker Desktop（推荐）或装本机 Hadoop 3.x"
    echo -e "       ${YELLOW}→${NC} 参考 docs/RUNBOOK.md 第二章"
    exit 1
  fi
fi

# ------------------------------------------------------------------------------
# 3. 启动
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[3/5]${NC} 启动服务..."

if [ "$MODE" = "full" ]; then
  echo -e "    ${BLUE}→${NC} docker compose --profile full up -d"
  docker compose --profile full up -d 2>&1 | tail -25
elif [ "$MODE" = "app" ]; then
  echo -e "    ${BLUE}→${NC} docker compose --profile app up -d"
  docker compose --profile app up -d 2>&1 | tail -20
elif [ "$MODE" = "native" ]; then
  echo -e "    ${BLUE}→${NC} bash scripts/start_native.sh"
  bash scripts/start_native.sh 2>&1 | tail -30
fi

# ------------------------------------------------------------------------------
# 4. 等待就绪
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[4/5]${NC} 等待服务就绪（最长 120 秒）..."
READY=0
for i in $(seq 1 60); do
  if curl -sf http://localhost:8080/api/health >/dev/null 2>&1; then READY=1; break; fi
  [ $((i % 15)) -eq 0 ] && echo -e "    ${YELLOW}...${NC} 仍在等待（$((i*2))s）"
  sleep 2
done

if [ "$READY" -eq 1 ]; then
  echo -e "    ${GREEN}✓${NC} 后端已就绪"
else
  echo -e "    ${YELLOW}!${NC} 后端 120 秒内未就绪，继续执行体检以定位问题"
fi

# ------------------------------------------------------------------------------
# 5. 端到端体检
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[5/5]${NC} 端到端体检..."
bash scripts/smoke_test.sh 2>&1 | tail -40

# ------------------------------------------------------------------------------
# 访问信息
# ------------------------------------------------------------------------------
echo ""
echo "=============================================================="
echo -e " ${GREEN}启动完成${NC}"
echo "=============================================================="
echo ""
echo -e "  ${BLUE}前端看板${NC}      http://localhost"
echo -e "  ${BLUE}后端接口${NC}      http://localhost:8080/api"
echo -e "  ${BLUE}健康检查${NC}      http://localhost:8080/api/health"
echo -e "  ${BLUE}MySQL${NC}         localhost:3306  (root / uev123456 / uev_charge)"
echo -e "  ${BLUE}Redis${NC}         localhost:6379  (密码 uev_redis_pass)"
echo ""
if [ "$MODE" = "full" ]; then
  echo -e "  ${BLUE}NameNode UI${NC}    http://localhost:9870"
  echo -e "  ${BLUE}YARN UI${NC}        http://localhost:8088"
  echo -e "  ${BLUE}HiveServer2${NC}    jdbc:hive2://localhost:10000/default"
elif [ "$MODE" = "native" ]; then
  echo -e "  ${BLUE}NameNode UI${NC}    http://localhost:9870"
  echo -e "  ${BLUE}YARN UI${NC}        http://localhost:8088"
fi
echo ""
echo -e "  ${YELLOW}停止系统${NC}：${CYAN}bash scripts/stop_all.sh${NC}"
echo -e "  ${YELLOW}完整体检${NC}：${CYAN}bash scripts/smoke_test.sh${NC}"
echo ""
echo "=============================================================="
echo ""
