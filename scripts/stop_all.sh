#!/usr/bin/env bash
# ==============================================================================
# stop_all.sh —— 一键停止全套环境
#
# 维护人：A（组长）
# 用法：bash scripts/stop_all.sh          # 停止但保留数据卷
#        bash scripts/stop_all.sh --clean  # 停止并删除数据卷（会清空 MySQL/HDFS）
# ==============================================================================
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

GREEN='\033[1;32m'; RED='\033[1;31m'; YELLOW='\033[1;33m'; BLUE='\033[1;34m'; NC='\033[0m'

CLEAN=0
[ "${1:-}" = "--clean" ] && CLEAN=1

echo ""
echo "=============================================================="
echo -e " ${BLUE}UrbanEV 项目 · 一键停止${NC}"
echo "=============================================================="

if ! command -v docker >/dev/null 2>&1; then
  echo -e "\n${RED}✗ 未找到 docker 命令${NC}\n"
  exit 1
fi

echo -e "\n${BLUE}[1/3]${NC} 停止容器..."
docker compose --profile full down --remove-orphans 2>&1 | tail -20
echo -e "    ${GREEN}✓${NC} 所有容器已停止"

if [ "$CLEAN" -eq 1 ]; then
  echo -e "\n${YELLOW}[2/3]${NC} 删除数据卷（MySQL 数据、HDFS、Redis 将被清空）..."
  docker compose --profile full down -v 2>&1 | tail -10
  echo -e "    ${GREEN}✓${NC} 数据卷已删除"
else
  echo -e "\n${BLUE}[2/3]${NC} 保留数据卷（下次启动数据还在）"
  echo -e "    ${YELLOW}!${NC} 如需彻底清空，执行：bash scripts/stop_all.sh --clean"
fi

echo -e "\n${BLUE}[3/3]${NC} 检查残留进程..."
# 清理可能残留的本机进程（原生模式部署时产生）
if command -v jps >/dev/null 2>&1; then
  JAVA_PIDS=$(jps 2>/dev/null | grep -E "NameNode|DataNode|ResourceManager|NodeManager|HiveServer2" | awk '{print $1}')
  if [ -n "$JAVA_PIDS" ]; then
    echo -e "    ${YELLOW}!${NC} 发现残留 Hadoop 进程：$JAVA_PIDS"
    echo -e "    ${YELLOW}!${NC} 如需停止本机原生集群，执行：bash scripts/stop_native.sh"
  else
    echo -e "    ${GREEN}✓${NC} 无残留 Hadoop 进程"
  fi
else
  echo -e "    ${YELLOW}!${NC} 未安装 JDK，跳过进程检查"
fi

echo ""
echo "=============================================================="
echo -e " ${GREEN}已停止${NC}"
echo "=============================================================="
echo ""
