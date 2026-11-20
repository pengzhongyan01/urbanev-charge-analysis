#!/usr/bin/env bash
# ==============================================================================
# start_flume.sh —— 启动 Flume 采集 agent
#
# ★ 2026-11-20 重写。原来这个脚本在 uev-namenode 容器里执行 $FLUME_HOME/bin/flume-ng，
#   但 apache/hadoop 镜像**根本不含 Flume**（官方 Dockerfile 只解 hadoop tarball），
#   必然 "flume-ng: No such file or directory"。
#   现在改为：docker-compose.yml 里新增了独立的 flume 服务（基于自建镜像
#   docker/flume/Dockerfile = apache/hadoop + Flume 1.11.0），这里只负责启停与验证。
#
# 维护人：A（组长）
# ==============================================================================
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

GREEN='\033[1;32m'; RED='\033[1;31m'; YELLOW='\033[1;33m'; BLUE='\033[1;34m'; NC='\033[0m'
FLUME_C=uev-flume

echo ""
echo -e "${BLUE}==============================================================${NC}"
echo -e " ${BLUE}启动 Flume 采集 agent${NC}"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo -e "${BLUE}==============================================================${NC}"

# ---- 0. 前置检查 ----
if ! command -v docker >/dev/null 2>&1; then
  echo -e "  ${RED}✗${NC} 未安装 Docker —— Flume 无法启动"
  echo "    Flume 跑在 Docker 容器里（apache/hadoop 镜像不含 Flume，必须自建镜像）"
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo -e "  ${RED}✗${NC} Docker 未运行 —— 请先启动 Docker Desktop"
  exit 1
fi

# ---- 1. 准备容器内数据目录 ----
# ★ 容器内路径固定 /data/urbanev；宿主机实际路径由 find_data.sh 探测
DATA_DIR=""
if [ -f scripts/find_data.sh ]; then
  DATA_DIR=$(bash scripts/find_data.sh 2>/dev/null | grep -oE '/.*UrbanEV' | head -1)
fi
if [ -z "$DATA_DIR" ] || [ ! -d "$DATA_DIR" ]; then
  echo -e "  ${YELLOW}!${NC} 未探测到数据目录，用仓库内 ./data/urbanev"
  DATA_DIR=""
fi
if [ -n "$DATA_DIR" ]; then
  mkdir -p ./data/urbanev
  # 软链接比 bind mount 稳（Windows 上 bind mount 会有权限问题）
  for f in "$DATA_DIR"/*.csv; do
    [ -f "$f" ] || continue
    ln -sf "$f" "./data/urbanev/$(basename "$f")" 2>/dev/null || cp -n "$f" "./data/urbanev/" 2>/dev/null || true
  done
  echo -e "  ${GREEN}✓${NC} 数据目录：$DATA_DIR → ./data/urbanev（已建立软链接）"
else
  echo -e "  ${YELLOW}!${NC} 未找到数据，Flume 会采不到文件。请先跑 scripts/download_data.sh"
fi

# ---- 2. 启动 flume 服务 ----
echo -e "  ${BLUE}→${NC} 启动 flume 服务（首次会构建镜像，需几分钟）..."
if ! docker compose --profile hadoop up -d flume 2>&1 | tail -15; then
  echo -e "  ${RED}✗${NC} flume 服务启动失败"
  exit 1
fi

# ---- 3. 等待 agent 起来 ----
echo -e "  ${BLUE}→${NC} 等待 Flume agent 就绪..."
for i in $(seq 1 20); do
  if docker exec "$FLUME_C" pgrep -f flume-ng >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Flume agent 已就绪（${i}0 秒内）"
    break
  fi
  sleep 3
done
if ! docker exec "$FLUME_C" pgrep -f flume-ng >/dev/null 2>&1; then
  echo -e "  ${RED}✗${NC} Flume agent 未起来，查看日志："
  echo "    docker logs $FLUME_C --tail 50"
  exit 1
fi

# ---- 4. 验证 HDFS 目录 ----
echo -e "  ${BLUE}→${NC} 验证 HDFS 采集目录..."
docker exec uev-namenode hdfs dfs -mkdir -p /uev/raw 2>/dev/null || true
docker exec uev-namenode hdfs dfs -ls /uev/raw/ 2>/dev/null | head -20

echo ""
echo -e "${BLUE}==============================================================${NC}"
echo -e " ${GREEN}Flume 启动完成${NC}"
echo -e "${BLUE}==============================================================${NC}"
echo ""
echo "★ 采集是滚动写入的（rollInterval=300s + 默认 .tmp 后缀），"
echo "  第一次验证请等 5 分钟后再看 hdfs dfs -ls /uev/raw/<表名>/"
echo ""
echo "查看日志：docker logs $FLUME_C --tail 50 -f"
echo "停止采集：docker compose --profile hadoop stop flume"
echo ""
