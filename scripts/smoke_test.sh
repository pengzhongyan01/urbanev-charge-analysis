#!/usr/bin/env bash
# ==============================================================================
# smoke_test.sh —— 端到端冒烟测试
#
# 维护人：A（组长）　|　目的：一条命令验证"整套系统是否真的就绪"
#
# 这不是单元测试，是"能不能拿去答辩"的体检。
# 每次提交前跑一次，每次全链路验收跑一次。
#
# 用法：bash scripts/smoke_test.sh
# 退出码：0 = 全部通过，1 = 有失败项
# ==============================================================================
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

GREEN='\033[1;32m'; RED='\033[1;31m'; YELLOW='\033[1;33m'; BLUE='\033[1;34m'; NC='\033[0m'

PASS=0; FAIL=0; WARN=0
pass() { echo -e "  ${GREEN}✓${NC} $1"; PASS=$((PASS+1)); }
fail() { echo -e "  ${RED}✗${NC} $1"; FAIL=$((FAIL+1)); }
warn() { echo -e "  ${YELLOW}!${NC} $1"; WARN=$((WARN+1)); }
section() { echo -e "\n${BLUE}$1${NC}"; }

echo ""
echo "=============================================================="
echo -e " ${BLUE}UrbanEV 项目 · 端到端冒烟测试${NC}"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================================="

# 容器名与库表名常量
NN=uev-namenode
MYSQL_C=uev-mysql
REDIS_C=uev-redis
BE_C=uev-backend

has_docker=0
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  has_docker=1
fi

# 找 Hive 查询方式
run_hive() {
  if [ "$has_docker" -eq 1 ] && docker ps --format '{{.Names}}' 2>/dev/null | grep -q "$NN"; then
    timeout 20 docker exec "$NN" beeline -u jdbc:hive2://hive:10000 -e "$1" 2>/dev/null
  elif command -v beeline >/dev/null 2>&1; then
    timeout 20 beeline -u jdbc:hive2://localhost:10000 -e "$1" 2>/dev/null
  else
    return 1
  fi
}

run_mysql() {
  if [ "$has_docker" -eq 1 ] && docker ps --format '{{.Names}}' 2>/dev/null | grep -q "$MYSQL_C"; then
    timeout 20 docker exec "$MYSQL_C" timeout 20 mysql -uroot -puev123456 uev_charge -N -e "$1" 2>/dev/null
  elif command -v mysql >/dev/null 2>&1; then
    timeout 20 mysql -uroot -puev123456 uev_charge -N -e "$1" 2>/dev/null
  else
    return 1
  fi
}

# ------------------------------------------------------------------------------
section "[1/7] 数据文件"
# shellcheck source=scripts/find_data.sh
source scripts/find_data.sh
DATA_DIR="${UEV_DATA_DIR:-}"
if [ -n "$DATA_DIR" ] && [ -d "$DATA_DIR" ]; then
  CSV_COUNT=$(ls -1 "$DATA_DIR"/*.csv 2>/dev/null | wc -l)
  if [ "$CSV_COUNT" -ge 12 ]; then
    pass "有 $CSV_COUNT 个 CSV（预期 12 个）"
  elif [ "$CSV_COUNT" -ge 11 ]; then
    warn "只有 $CSV_COUNT 个 CSV（预期 12 个）"
  elif [ "$CSV_COUNT" -gt 0 ]; then
    fail "只有 $CSV_COUNT 个 CSV，数据不完整"
  else
    fail "$DATA_DIR 为空"
  fi

  # 抽查关键文件的行数
  if [ -f "$DATA_DIR/occupancy.csv" ]; then
    OCC_LINES=$(wc -l < "$DATA_DIR/occupancy.csv" | tr -d ' ')
    # wc -l 含表头行，数据行 = 行数 - 1，预期 4344 条数据
    if [ "$OCC_LINES" -eq 4345 ] 2>/dev/null; then
      pass "occupancy.csv 数据行 4344（文件 $OCC_LINES 行，含表头）"
    elif [ "$OCC_LINES" -ge 4343 ] 2>/dev/null; then
      warn "occupancy.csv 行数 $OCC_LINES（预期 4345，含表头）"
    else
      fail "occupancy.csv 行数 $OCC_LINES 异常（预期 4345）"
    fi
  fi
  if [ -f "$DATA_DIR/inf.csv" ]; then
    INF_LINES=$(wc -l < "$DATA_DIR/inf.csv" | tr -d ' ')
    # wc -l 含表头行，数据行 = 行数 - 1，预期 275 个分区
    if [ "$INF_LINES" -eq 276 ] 2>/dev/null; then
      pass "inf.csv 分区数 275（文件 $INF_LINES 行，含表头）"
    elif [ "$INF_LINES" -ge 275 ] 2>/dev/null; then
      warn "inf.csv 行数 $INF_LINES（预期 276，含表头）"
    else
      fail "inf.csv 行数 $INF_LINES 异常（预期 276）"
    fi
  fi
else
  fail "未找到数据目录（执行 bash scripts/download_data.sh）"
fi

# ------------------------------------------------------------------------------
section "[2/7] 容器与集群"
if [ "$has_docker" -eq 1 ]; then
  RUNNING=$(docker ps --format '{{.Names}}' 2>/dev/null)
  for c in "$NN" uev-datanode uev-rm uev-nm "$MYSQL_C" "$REDIS_C"; do
    if echo "$RUNNING" | grep -q "$c"; then
      pass "$c 运行中"
    else
      warn "$c 未运行"
    fi
  done

  if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "$NN"; then
    JPS=$(docker exec "$NN" jps 2>/dev/null)
    for proc in NameNode DataNode; do
      if echo "$JPS" | grep -q "$proc"; then
        pass "$proc 进程正常"
      else
        fail "$proc 进程未启动"
      fi
    done
    # HDFS 可写性
    if docker exec "$NN" hdfs dfs -test -d /uev 2>/dev/null; then
      pass "HDFS /uev 目录可访问"
    else
      warn "HDFS /uev 目录不存在（尚未执行 Flume 采集）"
    fi
  fi
else
  warn "Docker 不可用，跳过容器检查"
fi

# ------------------------------------------------------------------------------
section "[3/7] Hive 四层数仓"
COUNT_OUT=$(run_hive "SELECT 'ODS',COUNT(*) FROM uev_ods.occupancy
                       UNION ALL SELECT 'DWD',COUNT(*) FROM uev_dwd.zone_hour_metric
                       UNION ALL SELECT 'DWS',COUNT(*) FROM uev_dws.zone_day_hour
                       UNION ALL SELECT 'ADS',COUNT(*) FROM uev_ads.imbalance_index;" 2>/dev/null)

if [ -n "$COUNT_OUT" ]; then
  for layer in ODS DWD DWS ADS; do
    CNT=$(echo "$COUNT_OUT" | grep -w "$layer" | awk -F'\t' '{print $NF}' | tr -d ' ')
    if [ -z "$CNT" ]; then
      CNT=$(echo "$COUNT_OUT" | grep "$layer" | awk '{print $NF}' | tr -d ' ')
    fi
    if [ -n "${CNT:-}" ] && [ "$CNT" -gt 0 ] 2>/dev/null; then
      pass "$layer 层有数据（$CNT 行）"
    else
      fail "$layer 层无数据或表不存在"
    fi
  done

  ODS_C=$(echo "$COUNT_OUT" | grep -w "ODS" | awk '{print $NF}' | tr -d ' ')
  DWD_C=$(echo "$COUNT_OUT" | grep -w "DWD" | awk '{print $NF}' | tr -d ' ')
  if [ -n "${ODS_C:-}" ] && [ -n "${DWD_C:-}" ] && [ "$DWD_C" -lt "$ODS_C" ] 2>/dev/null; then
    pass "清洗有效（DWD $DWD_C < ODS $ODS_C）"
  elif [ -n "${ODS_C:-}" ] && [ -n "${DWD_C:-}" ]; then
    warn "未体现清洗效果（ODS=$ODS_C, DWD=$DWD_C）—— 若清洗确实未删行可忽略"
  fi

  # ADS 七张表
  for t in imbalance_index price_elasticity demand_forecast expansion_suggestion \
           dashboard_kpi zone_occupancy hourly_supply_demand; do
    C=$(run_hive "SELECT COUNT(*) FROM uev_ads.$t;" 2>/dev/null | tr -d '[:space:]')
    if [ -n "${C:-}" ] && [ "$C" -gt 0 ] 2>/dev/null; then
      pass "ADS 表 $t 有数据（$C 行）"
    else
      warn "ADS 表 $t 无数据"
    fi
  done
else
  warn "Hive 环境不可用，跳过数仓检查"
fi

# ------------------------------------------------------------------------------
section "[4/7] MySQL 业务表"
MY_CNT=$(run_mysql "SELECT COUNT(*) FROM zone_occupancy;" 2>/dev/null | tr -d '[:space:]')
if [ -n "${MY_CNT:-}" ] && [ "$MY_CNT" -gt 0 ] 2>/dev/null; then
  pass "zone_occupancy 有 $MY_CNT 行"
else
  fail "zone_occupancy 无数据（Sqoop 导出是否完成？）"
fi

for t in dashboard_kpi hourly_supply_demand imbalance_index price_elasticity \
         demand_forecast expansion_suggestion; do
  C=$(run_mysql "SELECT COUNT(*) FROM $t;" 2>/dev/null | tr -d '[:space:]')
  if [ -n "${C:-}" ] && [ "$C" -gt 0 ] 2>/dev/null; then
    pass "$t 有数据（$C 行）"
  else
    warn "$t 无数据"
  fi
done

# ------------------------------------------------------------------------------
section "[4.5/7] Redis 缓存"
# ★ 单独检查 Redis：即使后端没起来，Redis 挂了也必须能第一时间发现
redis_ok=0
if [ "$has_docker" -eq 1 ] && docker ps --format '{{.Names}}' 2>/dev/null | grep -q "$REDIS_C"; then
  if timeout 15 docker exec "$REDIS_C" redis-cli -a uev_redis_pass ping 2>/dev/null | grep -q PONG; then
    pass "Redis 容器响应正常（PING → PONG）"
    redis_ok=1
  else
    fail "Redis 容器无响应"
  fi
elif command -v redis-cli >/dev/null 2>&1; then
  if timeout 15 redis-cli -a uev_redis_pass ping 2>/dev/null | grep -q PONG; then
    pass "Redis 响应正常（PING → PONG）"
    redis_ok=1
  else
    fail "Redis 无响应"
  fi
else
  warn "Redis 不可达（未装 redis-cli 且无容器）"
fi

# ------------------------------------------------------------------------------
section "[5/7] 后端接口"
HEALTH=$(curl -s --max-time 8 http://localhost:8080/api/health 2>/dev/null)
if [ -n "$HEALTH" ]; then
  if echo "$HEALTH" | grep -q '"code":200'; then
    pass "/api/health 正常"
    if echo "$HEALTH" | grep -q '"mysql":"UP"'; then
      pass "MySQL 连接正常"
    else
      fail "MySQL 连接异常"
    fi
    if echo "$HEALTH" | grep -q '"redis":"UP"'; then
      pass "Redis 连接正常"
    else
      fail "Redis 连接异常"
    fi
  else
    fail "/api/health 返回异常"
  fi
else
  fail "后端未响应（8080 端口无服务）"
fi

# ★ 接口清单与 docs/contracts/03-接口规范.md 一一对应（16 个）
#   契约新增的 5 个（clusters / forecast-evaluate / zone detail / weather / advice export）
#   若 D 尚未实现，会报 404 提醒，属正常 —— 实现后自动转绿
API_LIST="/dashboard/kpi /zones/occupancy /charts/hourly /charts/imbalance \
/charts/price-elasticity /charts/forecast /charts/suggestions \
/charts/volume-deviation /charts/poi-correlation /dictionary \
/charts/clusters /charts/forecast-evaluate /weather/list /zones/102/detail"
for api in $API_LIST; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 8 "http://localhost:8080/api$api" 2>/dev/null)
  if [ "$CODE" = "200" ]; then
    pass "$api 返回 200"
  elif [ "$CODE" = "000" ]; then
    fail "$api 无响应"
  else
    fail "$api 返回 $CODE"
  fi
done

# ------------------------------------------------------------------------------
section "[6/7] 前端资源"
[ -f "frontend/index.html" ] && pass "frontend/index.html 存在" || fail "frontend/index.html 缺失"
[ -f "frontend/js/common.js" ] && pass "common.js 存在" || fail "common.js 缺失"
[ -f "frontend/js/app.js" ] && pass "app.js 存在" || fail "app.js 缺失"
[ -f "frontend/css/style.css" ] && pass "style.css 存在" || fail "style.css 缺失"

if [ -f "frontend/js/echarts.min.js" ]; then
  pass "echarts.min.js 已本地化（答辩现场无网可用）"
else
  fail "echarts.min.js 缺失 —— 必须在答辩前本地化，不能依赖 CDN"
fi

if [ -f "frontend/assets/shenzhen_440300_full.json" ]; then
  pass "深圳地图 GeoJSON 存在"
else
  warn "深圳地图 GeoJSON 缺失（应为 frontend/assets/shenzhen_440300_full.json）"
fi

# ------------------------------------------------------------------------------
section "[7/7] 契约一致性与交付物"
if bash scripts/check-contracts.sh >/dev/null 2>&1; then
  pass "契约与实现一致"
else
  warn "契约检查未通过（详见 scripts/check-contracts.sh 输出）"
fi

[ -f "docs/RUNBOOK.md" ] && pass "RUNBOOK.md 存在" || fail "RUNBOOK.md 缺失"
[ -f "docs/contracts/01-数据字典.md" ] && pass "数据字典存在" || fail "数据字典缺失"
[ -f "docs/contracts/02-指标定义表.md" ] && pass "指标定义表存在" || fail "指标定义表缺失"
[ -f "docs/contracts/03-接口规范.md" ] && pass "接口规范存在" || fail "接口规范缺失"
[ -f "docs/contracts/04-数仓表结构规范.md" ] && pass "数仓规范存在" || fail "数仓规范缺失"
[ -f "docs/ppt/PPT逐页脚本.md" ] && pass "PPT 逐页脚本存在" || warn "PPT 逐页脚本缺失"
[ -f "hadoop/mr/WideToLong.java" ] && pass "MR 宽转长作业存在" || warn "MR 作业缺失"
[ -f "hadoop/spark/ads_metrics.sql" ] && pass "Spark 指标 SQL 存在" || warn "Spark SQL 缺失"

# ------------------------------------------------------------------------------
echo ""
echo "=============================================================="
echo -e " ${BLUE}结果${NC}：通过 ${GREEN}$PASS${NC}　警告 ${YELLOW}$WARN${NC}　失败 ${RED}$FAIL${NC}"
if [ "$FAIL" -gt 0 ]; then
  echo -e " ${RED}存在失败项 —— 现在不是能拿去答辩的状态${NC}"
  echo "=============================================================="
  echo ""
  exit 1
fi
echo -e " ${GREEN}全部通过，系统就绪${NC}"
echo "=============================================================="
echo ""
exit 0
