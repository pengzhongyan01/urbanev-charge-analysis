#!/usr/bin/env bash
# ==============================================================================
# start_native.sh —— 原生模式启动（不依赖 Docker）
#
# ★ 2026-11-20 补：start_all.sh 的 native 分支一直在调用本脚本，
#   但仓库里从来没有这个文件 → native 模式必崩 "No such file or directory"。
#
# 适用场景：答辩现场 Docker 起不来时的兜底。
# 前提：本机已装 JDK 8/17、Hadoop 3.3.6、Hive 3.1.3、MySQL、Redis。
#
# 维护人：A（组长）
# ==============================================================================
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

GREEN='\033[1;32m'; RED='\033[1;31m'; BLUE='\033[1;34m'; NC='\033[0m'

echo ""
echo -e "${BLUE}==============================================================${NC}"
echo -e " ${BLUE}原生模式启动（非 Docker）${NC}"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo -e "${BLUE}==============================================================${NC}"

# ---- 1. 环境变量 ----
export HADOOP_HOME=${HADOOP_HOME:-/usr/local/hadoop}
export HIVE_HOME=${HIVE_HOME:-/usr/local/hive}
export HADOOP_CONF_DIR=${HADOOP_CONF_DIR:-$HADOOP_HOME/etc/hadoop}
export HIVE_CONF_DIR=${HIVE_CONF_DIR:-$HIVE_HOME/conf}
export PATH=$PATH:$HADOOP_HOME/bin:$HIVE_HOME/bin

for v in HADOOP_HOME HIVE_HOME; do
  val=$(eval echo \$$v)
  if [ ! -d "$val" ]; then
    echo -e "  ${RED}✗${NC} $v 不存在：$val"
    echo "    原生模式需要先装好 Hadoop 与 Hive（见 docs/RUNBOOK.md 第二节）"
    exit 1
  fi
done
echo -e "  ${GREEN}✓${NC} HADOOP_HOME=$HADOOP_HOME"
echo -e "  ${GREEN}✓${NC} HIVE_HOME=$HIVE_HOME"

# ---- 2. 启动 Hadoop 伪分布式 ----
echo -e "  ${BLUE}→${NC} 启动 HDFS / YARN..."
if [ ! -d "$HADOOP_HOME/data/name/current" ]; then
  echo "    首次运行，格式化 NameNode..."
  hdfs namenode -format -force -nonInteractive >/dev/null 2>&1
fi
hdfs --daemon start namenode 2>/dev/null
hdfs --daemon start datanode 2>/dev/null
yarn --daemon start resourcemanager 2>/dev/null
yarn --daemon start nodemanager 2>/dev/null
sleep 8

# ---- 3. 启动 Hive ----
echo -e "  ${BLUE}→${NC} 启动 HiveServer2..."
nohup hiveserver2 > /tmp/hiveserver2.log 2>&1 &
sleep 10

# ---- 4. 启动中间件（若本机已装）----
if command -v mysqld >/dev/null 2>&1; then
  echo -e "  ${BLUE}→${NC} 检测到本机 MySQL，若未运行请手动启动（服务名 mysql）"
else
  echo -e "  ${YELLOW}!${NC} 未检测到 MySQL，请先启动本机 MySQL"
fi

# ---- 5. 验证 ----
echo ""
echo -e "  ${BLUE}→${NC} jps 进程："
jps 2>/dev/null | head -10
echo ""
echo -e "${BLUE}==============================================================${NC}"
echo -e " ${GREEN}原生模式启动完成${NC}"
echo -e "${BLUE}==============================================================${NC}"
echo ""
echo "★ 后续步骤与 Docker 模式一致，见 docs/RUNBOOK.md 第五节"
echo ""
