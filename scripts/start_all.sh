#!/usr/bin/env bash
# ==============================================================================
# start_all.sh —— 一键启动全套环境
#
# 维护人：A（组长）　|　目标：任何人执行这一条命令，全套系统就绪
#
# 用法：bash scripts/start_all.sh
# ==============================================================================
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

GREEN='\033[1;32m'; RED='\033[1;31m'; YELLOW='\033[1;33m'; BLUE='\033[1;34m'; NC='\033[0m'

echo ""
echo "=============================================================="
echo -e " ${BLUE}UrbanEV 项目 · 一键启动${NC}"
echo "=============================================================="

# ------------------------------------------------------------------------------
# 0. 前置检查
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[0/6]${NC} 前置检查..."
MISSING=0
for cmd in docker java mvn mysql redis-server; do
  if command -v "$cmd" >/dev/null 2>&1; then
    echo -e "    ${GREEN}✓${NC} $cmd"
  else
    echo -e "    ${RED}✗${NC} $cmd 未安装或不在 PATH"
    MISSING=1
  fi
done
[ "$MISSING" -eq 1 ] && { echo -e "\n${RED}请先补齐缺失的环境${NC}\n"; exit 1; }

# ------------------------------------------------------------------------------
# 1. 数据检查
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[1/6]${NC} 检查数据..."
if [ -d data/dataset ] && [ -n "$(ls -A data/dataset 2>/dev/null)" ]; then
  CSV_COUNT=$(ls -1 data/dataset/*.csv 2>/dev/null | wc -l)
  echo -e "    ${GREEN}✓${NC} data/dataset 下有 ${CSV_COUNT} 个 CSV"
else
  echo -e "    ${YELLOW}!${NC} data/dataset 为空，请先下载 UrbanEV 数据"
  echo -e "       见 README.md 第八节"
fi

# ------------------------------------------------------------------------------
# 2. 启动 Hadoop 集群（Docker Compose）
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[2/6]${NC} 启动 Hadoop 集群..."
if [ -f docker-compose.yml ]; then
  docker compose up -d
  echo -e "    ${GREEN}✓${NC} 容器已启动，等待服务就绪..."
  sleep 20
  HDFS_OK=$(docker exec -it hadoop bash -c "jps" 2>/dev/null | grep -c NameNode)
  if [ "$HDFS_OK" -gt 0 ]; then
    echo -e "    ${GREEN}✓${NC} NameNode 已就绪"
  else
    echo -e "    ${YELLOW}!${NC} NameNode 未就绪，请检查 docker compose logs"
  fi
else
  echo -e "    ${YELLOW}!${NC} 还没有 docker-compose.yml（A 岗产出）"
fi

# ------------------------------------------------------------------------------
# 3. 初始化 Hive 表
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[3/6]${NC} 初始化 Hive 表..."
if ls hadoop/hive/*.sql >/dev/null 2>&1; then
  for f in $(ls hadoop/hive/*.sql | sort); do
    echo -e "    执行 $(basename "$f")"
    docker exec -it hadoop hive -f "/opt/urbanev/$(basename "$f")" 2>/dev/null \
      || echo -e "    ${YELLOW}!${NC} $(basename "$f") 执行失败"
  done
  echo -e "    ${GREEN}✓${NC} 建表完成"
else
  echo -e "    ${YELLOW}!${NC} 还没有建表脚本"
fi

# ------------------------------------------------------------------------------
# 4. 启动 MySQL 与 Redis
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[4/6]${NC} 启动 MySQL 与 Redis..."
if command -v mysqladmin >/dev/null 2>&1; then
  if mysqladmin ping -uroot -p"${MYSQL_ROOT_PASSWORD:-123456}" >/dev/null 2>&1; then
    echo -e "    ${GREEN}✓${NC} MySQL 已运行"
  else
    echo -e "    ${YELLOW}!${NC} MySQL 未运行，请手动启动"
  fi
fi
if command -v redis-cli >/dev/null 2>&1; then
  if redis-cli ping 2>/dev/null | grep -q PONG; then
    echo -e "    ${GREEN}✓${NC} Redis 已运行"
  else
    echo -e "    ${YELLOW}!${NC} Redis 未运行，请手动启动"
  fi
fi

# ------------------------------------------------------------------------------
# 5. 导入 MySQL 表结构
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[5/6]${NC} 导入 MySQL 表结构..."
if ls db/mysql/*.sql >/dev/null 2>&1; then
  for f in $(ls db/mysql/*.sql | sort); do
    mysql -uroot -p"${MYSQL_ROOT_PASSWORD:-123456}" < "$f" 2>/dev/null \
      && echo -e "    ${GREEN}✓${NC} $(basename "$f")" \
      || echo -e "    ${YELLOW}!${NC} $(basename "$f") 导入失败"
  done
else
  echo -e "    ${YELLOW}!${NC} db/mysql 下还没有建表脚本"
fi

# ------------------------------------------------------------------------------
# 6. 启动后端
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[6/6]${NC} 启动后端服务..."
if [ -d backend ] && [ -f backend/pom.xml ]; then
  cd backend
  mvn clean package -DskipTests -q
  JAR=$(ls target/*.jar 2>/dev/null | grep -v original | head -1)
  if [ -n "$JAR" ]; then
    nohup java -jar "$JAR" > ../logs_app.log 2>&1 &
    echo -e "    ${GREEN}✓${NC} 后端启动中，日志：logs_app.log"
    sleep 12
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/zone/list 2>/dev/null | grep -q "200\|401"; then
      echo -e "    ${GREEN}✓${NC} 后端接口已响应"
    else
      echo -e "    ${YELLOW}!${NC} 后端尚未响应，请查看 logs_app.log"
    fi
  else
    echo -e "    ${RED}✗${NC} 打包失败，请检查 backend 工程"
  fi
  cd ..
else
  echo -e "    ${YELLOW}!${NC} backend 工程还没建好（D 岗产出）"
fi

# ------------------------------------------------------------------------------
echo ""
echo "=============================================================="
echo -e " ${GREEN}启动流程结束${NC}"
echo -e " ${BLUE}验证：${NC} bash scripts/smoke_test.sh"
echo -e " ${BLUE}前端：${NC} 用浏览器打开 frontend/index.html"
echo "=============================================================="
echo ""
