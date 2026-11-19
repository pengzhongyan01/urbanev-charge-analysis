#!/usr/bin/env bash
# ==============================================================================
# start_flume.sh —— 启动 Flume 采集 agent
#
# 维护人：A（组长）　|　交付：11/24
# 用法：bash scripts/start_flume.sh
#
# 前置：data/raw 下已有 CSV；HDFS 可用（docker exec uev-namenode hdfs dfs -mkdir -p /uev/raw）
# ==============================================================================
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

GREEN='\033[1;32m'; RED='\033[1;31m'; YELLOW='\033[1;33m'; BLUE='\033[1;34m'; CYAN='\033[1;36m'; NC='\033[0m'

echo ""
echo "=============================================================="
echo -e " ${BLUE}启动 Flume 采集${NC}"
echo "=============================================================="

# ------------------------------------------------------------------------------
# 1. 检查数据
# ------------------------------------------------------------------------------
DATA_DIR="data/raw"
[ -d "$DATA_DIR" ] || DATA_DIR="data/dataset"
CSV_COUNT=$(ls -1 "$DATA_DIR"/*.csv 2>/dev/null | wc -l)
if [ "$CSV_COUNT" -eq 0 ]; then
  echo -e "\n${RED}✗ ${DATA_DIR} 下没有 CSV${NC}"
  echo -e "  ${YELLOW}→${NC} 先执行 bash scripts/download_data.sh"
  exit 1
fi
echo -e "\n${BLUE}[1/4]${NC} 数据就绪：${CSV_COUNT} 个 CSV"

# ------------------------------------------------------------------------------
# 2. 准备 HDFS 目标目录
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[2/4]${NC} 准备 HDFS 目录..."
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "uev-namenode"; then
  docker exec uev-namenode hdfs dfs -mkdir -p /uev/raw/ 2>&1 | head -3
  docker exec uev-namenode hdfs dfs -chmod 777 /uev/raw 2>&1 | head -3
  echo -e "    ${GREEN}✓${NC} /uev/raw/ 就绪"
else
  echo -e "    ${YELLOW}!${NC} 未检测到 Docker 中的 NameNode，跳过"
  echo -e "       ${YELLOW}→${NC} 若用本机 Hadoop，手动执行：hdfs dfs -mkdir -p /uev/raw/"
fi

# ------------------------------------------------------------------------------
# 3. 分发配置到容器
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[3/4]${NC} 分发配置..."
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "uev-namenode"; then
  docker exec uev-namenode mkdir -p /opt/flume/conf /opt/flume/checkpoint /opt/flume/logs 2>&1 | head -3
  docker cp hadoop/flume/flume-csv-hdfs.conf uev-namenode:/opt/flume/conf/ 2>&1 | head -3
  echo -e "    ${GREEN}✓${NC} 配置已复制到容器"
else
  echo -e "    ${YELLOW}!${NC} Docker 模式不可用，尝试本机模式"
fi

# ------------------------------------------------------------------------------
# 4. 启动 agent
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[4/4]${NC} 启动 agent..."
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "uev-namenode"; then
  docker exec -d uev-namenode bash -c "
    FLUME_HOME=/opt/flume
    \$FLUME_HOME/bin/flume-ng agent \
      --name uev-agent \
      --conf \$FLUME_HOME/conf \
      --conf-file /opt/flume/conf/flume-csv-hdfs.conf \
      > /opt/flume/logs/flume-agent.log 2>&1"
  sleep 6
  if docker exec uev-namenode bash -c "ps aux | grep -q '[f]lume'" 2>/dev/null; then
    echo -e "    ${GREEN}✓${NC} Flume agent 运行中"
  else
    echo -e "    ${RED}✗${NC} Flume agent 启动失败"
    echo -e "       ${YELLOW}→${NC} 查看日志：docker exec uev-namenode tail -30 /opt/flume/logs/flume-agent.log"
    exit 1
  fi
elif [ -n "${FLUME_HOME:-}" ]; then
  "$FLUME_HOME/bin/flume-ng" agent --name uev-agent \
    --conf "$FLUME_HOME/conf" \
    --conf-file hadoop/flume/flume-csv-hdfs.conf \
    > /tmp/flume-agent.log 2>&1 &
  echo -e "    ${GREEN}✓${NC} 本机 Flume 已启动（日志：/tmp/flume-agent.log）"
else
  echo -e "    ${RED}✗${NC} 无法启动：既无 Docker 环境也未设置 FLUME_HOME"
  echo -e "       ${YELLOW}→${NC} 参考 docs/RUNBOOK.md 第三章"
  exit 1
fi

echo ""
echo "=============================================================="
echo -e " ${GREEN}Flume 启动完成${NC}"
echo "=============================================================="
echo ""
echo -e " ${CYAN}验证采集结果${NC}（等 30 秒让数据落盘）："
echo -e "   ${YELLOW}docker exec uev-namenode hdfs dfs -ls /uev/raw/${NC}"
echo -e "   ${YELLOW}docker exec uev-namenode hdfs dfs -cat '/uev/raw/*.csv' | head -5${NC}"
echo ""
echo -e " ${YELLOW}停止采集${NC}：docker exec uev-namenode pkill -f flume"
echo ""
