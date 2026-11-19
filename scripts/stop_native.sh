#!/usr/bin/env bash
# ==============================================================================
# stop_native.sh —— 停止本机原生部署的 Hadoop / Hive 进程
#
# 维护人：A（组长）　|　适用：没装 Docker、直接在本机装了 Hadoop 的同学
# 用法：bash scripts/stop_native.sh
# ==============================================================================
set -uo pipefail

GREEN='\033[1;32m'; RED='\033[1;31m'; BLUE='\033[1;34m'; NC='\033[0m'

echo ""
echo "=============================================================="
echo -e " ${BLUE}停止本机 Hadoop / Hive 进程${NC}"
echo "=============================================================="

if ! command -v jps >/dev/null 2>&1; then
  echo -e "\n${RED}✗ 未找到 jps，请确认已安装 JDK 并配置 JAVA_HOME${NC}\n"
  exit 1
fi

# 优先用 Hadoop 自带的 stop 脚本（更干净）
HADOOP_HOME_DIR="${HADOOP_HOME:-}"
if [ -n "$HADOOP_HOME_DIR" ] && [ -x "$HADOOP_HOME_DIR/sbin/stop-all.sh" ]; then
  echo -e "\n${BLUE}[1/3]${NC} 执行 stop-all.sh..."
  "$HADOOP_HOME_DIR/sbin/stop-all.sh" 2>&1 | tail -10
else
  echo -e "\n${BLUE}[1/3]${NC} HADOOP_HOME 未设置，按 PID 逐个停止"
  for PROC in ResourceManager NodeManager NameNode DataNode SecondaryNameNode; do
    PID=$(jps 2>/dev/null | grep "$PROC" | awk '{print $1}')
    if [ -n "$PID" ]; then
      kill "$PID" 2>/dev/null && echo -e "    ${GREEN}✓${NC} $PROC (PID $PID) 已停止"
    fi
  done
fi

# HiveServer2
HS2_PID=$(jps 2>/dev/null | grep -i "HiveServer2" | awk '{print $1}')
if [ -n "$HS2_PID" ]; then
  kill "$HS2_PID" 2>/dev/null && echo -e "    ${GREEN}✓${NC} HiveServer2 (PID $HS2_PID) 已停止"
fi

echo -e "\n${BLUE}[2/3]${NC} 等待进程退出..."
sleep 3
REMAIN=$(jps 2>/dev/null | grep -E "NameNode|DataNode|ResourceManager|NodeManager|HiveServer2" || true)
if [ -n "$REMAIN" ]; then
  echo -e "    ${RED}✗${NC} 仍有残留：$REMAIN"
  echo -e "    ${RED}!${NC} 强制停止：kill -9 $REMAIN"
else
  echo -e "    ${GREEN}✓${NC} 全部进程已退出"
fi

echo -e "\n${BLUE}[3/3]${NC} 清理 Hive 临时锁"
rm -f /tmp/hive/root/*.lock 2>/dev/null || true
echo -e "    ${GREEN}✓${NC} 完成"

echo ""
echo "=============================================================="
echo -e " ${GREEN}本机原生环境已停止${NC}"
echo "=============================================================="
echo ""
