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
echo -e " $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================================="

# ------------------------------------------------------------------------------
section "[1] 数据文件"
if [ -d data/dataset ]; then
  CSV_COUNT=$(ls -1 data/dataset/*.csv 2>/dev/null | wc -l)
  if [ "$CSV_COUNT" -ge 10 ]; then
    pass "data/dataset 有 $CSV_COUNT 个 CSV"
  elif [ "$CSV_COUNT" -gt 0 ]; then
    warn "data/dataset 只有 $CSV_COUNT 个 CSV（预期 11 个）"
  else
    fail "data/dataset 为空"
  fi
else
  fail "data/dataset 目录不存在"
fi

# ------------------------------------------------------------------------------
section "[2] Hadoop 集群"
if command -v docker >/dev/null 2>&1 && [ -f docker-compose.yml ]; then
  JPS=$(docker exec -it hadoop jps 2>/dev/null)
  for proc in NameNode DataNode ResourceManager NodeManager; do
    if echo "$JPS" | grep -q "$proc"; then
      pass "$proc 运行中"
    else
      fail "$proc 未运行"
    fi
  done
else
  warn "无 docker-compose.yml 或 docker 未安装，跳过集群检查"
fi

# ------------------------------------------------------------------------------
section "[3] Hive 四层表"
if command -v hive >/dev/null 2>&1 || (command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' 2>/dev/null | grep -q hadoop); then
  RUN_CMD="docker exec -it hadoop hive -e"
  COUNT_OUT=$($RUN_CMD "SELECT 'ODS',COUNT(*) FROM ev.ods_occupancy
                         UNION ALL SELECT 'DWD',COUNT(*) FROM ev.dwd_zone_hour
                         UNION ALL SELECT 'DWS',COUNT(*) FROM ev.dws_zone_day
                         UNION ALL SELECT 'ADS',COUNT(*) FROM ev.ads_imbalance_index;" 2>/dev/null)
  for layer in ODS DWD DWS ADS; do
    if echo "$COUNT_OUT" | grep -q "$layer"; then
      CNT=$(echo "$COUNT_OUT" | grep "$layer" | awk '{print $NF}')
      if [ "${CNT:-0}" -gt 0 ] 2>/dev/null; then
        pass "$layer 层有数据（$CNT 行）"
      else
        fail "$layer 层无数据"
      fi
    else
      fail "$layer 表不存在"
    fi
  done
  # DWD 应少于 ODS
  ODS_C=$(echo "$COUNT_OUT" | grep ODS | awk '{print $NF}')
  DWD_C=$(echo "$COUNT_OUT" | grep DWD | awk '{print $NF}')
  if [ -n "${ODS_C:-}" ] && [ -n "${DWD_C:-}" ] && [ "$DWD_C" -lt "$ODS_C" ]; then
    pass "清洗有效（DWD $DWD_C < ODS $ODS_C）"
  else
    warn "未验证清洗效果（ODS=$ODS_C, DWD=$DWD_C）"
  fi
else
  warn "无 Hive 环境，跳过"
fi

# ------------------------------------------------------------------------------
section "[4] MySQL 与后端"
if command -v mysql >/dev/null 2>&1; then
  MY_CNT=$(mysql -uroot -p"${MYSQL_ROOT_PASSWORD:-123456}" -N -e \
    "SELECT COUNT(*) FROM ev_ads_imbalance;" 2>/dev/null)
  if [ -n "${MY_CNT:-}" ] && [ "$MY_CNT" -gt 0 ] 2>/dev/null; then
    pass "MySQL ev_ads_imbalance 有 $MY_CNT 行"
  else
    fail "MySQL ADS 表无数据（Sqoop 导出是否完成？）"
  fi
else
  warn "mysql 客户端不可用，跳过"
fi

API_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8080/api/zone/list 2>/dev/null)
if [ "$API_CODE" = "200" ]; then
  pass "后端接口 /api/zone/list 正常"
elif [ "$API_CODE" = "401" ]; then
  pass "后端接口已响应（需登录，正常）"
elif [ "$API_CODE" = "000" ]; then
  fail "后端未响应（8080 端口无服务）"
else
  warn "后端返回 $API_CODE"
fi

# ------------------------------------------------------------------------------
section "[5] 前端页面"
for page in index demand imbalance price forecast advice; do
  if [ -f "frontend/${page}.html" ]; then
    pass "frontend/${page}.html 存在"
  else
    warn "frontend/${page}.html 缺失"
  fi
done
if [ -f frontend/assets/shenzhen.geojson ]; then
  pass "深圳地图 GeoJSON 存在"
else
  fail "深圳地图 GeoJSON 缺失（地图类图表无法显示）"
fi

# ------------------------------------------------------------------------------
section "[6] 契约一致性"
if bash scripts/check-contracts.sh >/dev/null 2>&1; then
  pass "契约与实现一致"
else
  warn "契约检查未通过（详见 scripts/check-contracts.sh 输出）"
fi

# ------------------------------------------------------------------------------
section "[7] 交付物齐备性"
[ -f RUNBOOK.md ] && pass "RUNBOOK.md 存在" || fail "RUNBOOK.md 缺失"
[ -f docs/contracts/01-数据字典.md ] && pass "数据字典存在" || fail "数据字典缺失"
[ -f docs/contracts/02-指标定义表.md ] && pass "指标定义表存在" || fail "指标定义表缺失"
[ -f docs/contracts/03-接口规范.md ] && pass "接口规范存在" || fail "接口规范缺失"
[ -f docs/contracts/04-数仓表结构规范.md ] && pass "数仓规范存在" || fail "数仓规范缺失"

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
