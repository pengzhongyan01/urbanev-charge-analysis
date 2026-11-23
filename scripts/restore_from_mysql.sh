#!/usr/bin/env bash
# ==============================================================================
# restore_from_mysql.sh —— 从 MySQL 反向重建 ADS 层 / 恢复数据（无需 129MB 原始数据）
#
# ★ 用途（答辩与复现的关键证据）：
#   评委 / 老师 / 第三方拿到提交包后，不需要下载 129MB 的 UrbanEV 原始 CSV，
#   只需：
#     1) docker compose --profile app up -d mysql      # 起 MySQL
#     2) bash scripts/restore_from_mysql.sh             # 灌入提交包里的数据导出样例
#     3) bash scripts/smoke_test.sh                     # 体检应转绿
#   即可让系统有真实数据可跑，这是"一键复现部署"最有说服力的一环。
#
# 用法：
#   bash scripts/restore_from_mysql.sh                       # 用默认账号密码
#   MYSQL_HOST=127.0.0.1 MYSQL_ROOT_PASSWORD=xxx bash scripts/restore_from_mysql.sh
# ==============================================================================
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

GREEN='\033[1;32m'; RED='\033[1;31m'; YELLOW='\033[1;33m'; BLUE='\033[1;34m'; NC='\033[0m'

DB_NAME="${MYSQL_DB:-uev_charge}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASS="${MYSQL_ROOT_PASSWORD:-uev123456}"
MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
MYSQL_PORT="${MYSQL_PORT:-3306}"

SAMPLE_DIR="05.源码/数据导出样例"
[ -d "$SAMPLE_DIR" ] && SAMPLE_DIR="data/export_samples"

echo ""
echo -e "${BLUE}==============================================================${NC}"
echo -e " ${BLUE}从数据导出样例恢复 MySQL${NC}"
echo -e " 目标：$MYSQL_USER@$MYSQL_HOST:$MYSQL_PORT/$DB_NAME"
echo -e " 样例目录：$SAMPLE_DIR"
echo -e "${BLUE}==============================================================${NC}"

# ---- 找 mysql 客户端 ----
MYSQL_CLI=""
for c in mysql; do
  command -v "$c" >/dev/null 2>&1 && { MYSQL_CLI="$c"; break; }
done
if [ -z "$MYSQL_CLI" ]; then
  for p in "/c/Program Files/MySQL"/*/bin/mysql.exe "D:/mysql01/bin/mysql.exe" "/d/mysql01/bin/mysql.exe"; do
    [ -x "$p" ] && { MYSQL_CLI="$p"; break; }
  done
fi
if [ -z "$MYSQL_CLI" ]; then
  echo -e "  ${RED}✗${NC} 找不到 mysql 客户端。装 MySQL 或用 docker exec 进容器执行。"
  exit 1
fi

run_sql() { "$MYSQL_CLI" -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASS" "$DB_NAME" -e "$1" 2>&1 | grep -v "Using a password"; }

# ---- 1. 建库 ----
echo -e "  ${BLUE}→${NC} 建库 $DB_NAME ..."
"$MYSQL_CLI" -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASS" \
  -e "CREATE DATABASE IF NOT EXISTS \`$DB_NAME\` DEFAULT CHARACTER SET utf8mb4;" 2>&1 | grep -v "Using a password" || true

# ---- 2. 建表（用 db/mysql/01_schema.sql）----
if [ -f db/mysql/01_schema.sql ]; then
  echo -e "  ${BLUE}→${NC} 建表（db/mysql/01_schema.sql）..."
  "$MYSQL_CLI" -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASS" \
    "$DB_NAME" < db/mysql/01_schema.sql 2>&1 | grep -v "Using a password" || true
fi

# ---- 3. 灌数据 ----
if [ ! -d "$SAMPLE_DIR" ]; then
  echo -e "  ${YELLOW}!${NC} 找不到样例目录 $SAMPLE_DIR（尚未导出）"
  exit 0
fi

echo -e "  ${BLUE}→${NC} 导入样例数据 ..."
ok=0; skip=0
for f in "$SAMPLE_DIR"/*.csv; do
  [ -f "$f" ] || continue
  tbl=$(basename "$f" .csv)
  # 表名转小写（MySQL 在 Linux 上表名大小写敏感）
  lower=$(echo "$tbl" | tr 'A-Z' 'a-z')
  # 检查表是否存在
  cnt=$(run_sql "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$DB_NAME' AND table_name='$lower';" | tr -d '[:space:]')
  if [ "$cnt" != "1" ]; then
    echo -e "    ${YELLOW}·${NC} 跳过 $tbl（表中不存在，先建表）"
    skip=$((skip+1)); continue
  fi
  # 关闭唯一键冲突影响，改为 REPLACE 语义先清空
  run_sql "SET FOREIGN_KEY_CHECKS=0; TRUNCATE TABLE \`$lower\`;" >/dev/null
  if "$MYSQL_CLI" --local-infile=1 -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASS" \
       "$DB_NAME" -e "LOAD DATA LOCAL INFILE '$(pwd)/$f' INTO TABLE \`$lower\` \
       CHARACTER SET utf8mb4 FIELDS TERMINATED BY ',' ENCLOSED BY '\"' LINES TERMINATED BY '\n' \
       IGNORE 1 LINES;" 2>&1 | grep -v "Using a password" | grep -qiE "error"; then
    echo -e "    ${YELLOW}·${NC} $tbl 导入失败（列数可能不匹配，跳过）"
    skip=$((skip+1))
  else
    n=$(run_sql "SELECT COUNT(*) FROM \`$lower\`;" | tr -d '[:space:]')
    echo -e "    ${GREEN}✓${NC} $tbl  $n 行"
    ok=$((ok+1))
  fi
done

echo ""
echo -e "  完成：成功 $ok 张，跳过 $skip 张"
echo ""
echo "  验证："
echo "    SELECT COUNT(*) FROM ads_dashboard_kpi;"
echo "    SELECT * FROM ads_imbalance_index ORDER BY rank_no LIMIT 10;"
echo ""
