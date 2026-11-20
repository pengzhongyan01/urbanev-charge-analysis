#!/usr/bin/env bash
# ==============================================================================
# check-contracts.sh —— 契约与实现的一致性检查
#
# 目的：防止"文档一套、代码另一套"
#   · 契约里定义的表名，Hive 建表脚本里必须存在
#   · 契约里定义的接口路径，后端 Controller 里必须存在
#   · 契约里定义的指标名，Spark/Hive 脚本里必须出现
#   · 契约文件必须有版本号和变更记录
#
# 用法：bash scripts/check-contracts.sh
# 退出码：0 = 通过，1 = 有问题
# ==============================================================================
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

CONTRACT_DIR="docs/contracts"
ERR=0
OK=0
WARN=0

GREEN='\033[1;32m'; RED='\033[1;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

pass() { echo -e "  ${GREEN}✓${NC} $1"; OK=$((OK+1)); }
fail() { echo -e "  ${RED}✗${NC} $1"; ERR=$((ERR+1)); }
warn() { echo -e "  ${YELLOW}!${NC} $1"; WARN=$((WARN+1)); }

echo ""
echo "--- 契约一致性检查 ---"

# ------------------------------------------------------------------------------
# 检查 1：契约文件是否齐全且有版本号
# ------------------------------------------------------------------------------
echo ""
echo "[1] 契约文件完整性"
REQUIRED=(
  "01-数据字典.md"
  "02-指标定义表.md"
  "03-接口规范.md"
  "04-数仓表结构规范.md"
)
for f in "${REQUIRED[@]}"; do
  path="$CONTRACT_DIR/$f"
  if [ ! -f "$path" ]; then
    fail "$f 不存在"
    continue
  fi
  if ! grep -qE '\*\*版本\*\*\s*[:：]' "$path"; then
    fail "$f 缺少版本号声明（格式：> **版本**：v1.0）"
  elif ! grep -q '变更记录' "$path"; then
    fail "$f 缺少变更记录表"
  elif [ $(wc -c < "$path") -lt 500 ]; then
    warn "$f 内容过少（尚未填写）"
  else
    pass "$f 完整"
  fi
done

# ------------------------------------------------------------------------------
# 检查 2：数仓表 —— 契约定义的表是否在 Hive SQL 中建了
# ------------------------------------------------------------------------------
echo ""
echo "[2] 数仓表：契约 → Hive 建表脚本"
if [ -d hadoop/hive ] && ls hadoop/hive/*.sql >/dev/null 2>&1; then
  ALL_SQL=$(cat hadoop/hive/*.sql 2>/dev/null)
  # 从契约文件里提取表名（支持 uev_ads.xxx 与 uev.xxx 两种写法）
  TABLES=$(grep -ohE 'uev_(ods|dwd|dws|ads|dim)_[a-z0-9_]+' "$CONTRACT_DIR"/*.md 2>/dev/null | sort -u)
  for t in $TABLES; do
    if echo "$ALL_SQL" | grep -q "$t"; then
      pass "$t 已在建表脚本中"
    else
      warn "$t 在契约中定义但建表脚本里没有（B 岗尚未产出 DDL）"
    fi
  done
  if [ -z "$TABLES" ]; then
    warn "未从契约中解析到表名"
  fi
else
  if [ -f hadoop/hive/gen_ddl.py ]; then
    pass "DDL 生成脚本存在（hadoop/hive/gen_ddl.py）"
    warn "尚未生成 .sql 文件 —— 执行：python3 hadoop/hive/gen_ddl.py > ddl_ods.sql"
  else
    warn "hadoop/hive 下还没有 DDL 生成脚本或 .sql 文件（B 岗产出）"
  fi
fi

# ------------------------------------------------------------------------------
# 检查 3：接口路径 —— 契约定义的是否在 Controller 里实现
# ------------------------------------------------------------------------------
echo ""
echo "[3] 接口：契约 → 后端 Controller"
if [ -d backend ] && find backend -name "*Controller.java" 2>/dev/null | grep -q .; then
  CTRL=$(cat $(find backend -name "*Controller.java" 2>/dev/null) 2>/dev/null)
  APIS=$(grep -ohE '/api/[a-zA-Z0-9/_{}-]+' "$CONTRACT_DIR/03-接口规范.md" 2>/dev/null | sort -u)
  for a in $APIS; do
    # 去掉可能的路径变量，做宽松匹配
    base=$(echo "$a" | sed 's/{[^}]*}/{}/g')
    # ★ 改为 class 段 + method 段两段匹配：
    #   原写法 cut -d'/' -f1-3 把 /api/dashboard/kpi 截成 /api/dashboard，
    #   而 Controller 里是 @RequestMapping("/api") + @GetMapping("/dashboard/kpi")，
    #   字面量 "/api/dashboard" 从不出现在源码里 → 连已实现的 /api/health 都报未实现。
    _cls=$(echo "$base" | cut -d'/' -f2)
    _mth=$(echo "$base" | cut -d'/' -f3-)
    if echo "$CTRL" | grep -q "/${_cls}" && echo "$CTRL" | grep -q "/${_mth}"; then
      pass "$a 已实现"
    else
      warn "$a 契约中定义但 Controller 中尚未实现（D 岗待完成）"
    fi
  done
  if [ -z "$APIS" ]; then
    warn "接口规范里还没提取到路径"
  fi
else
  warn "backend 下还没有 Controller 文件（D 岗产出）"
fi

# ------------------------------------------------------------------------------
# 检查 4：指标名 —— 契约定义的指标是否在计算脚本里出现
# ------------------------------------------------------------------------------
echo ""
echo "[4] 指标：契约 → 计算脚本"
if [ -d hadoop ] && find hadoop/spark hadoop/mr -name "*.sql" -o -name "*.java" 2>/dev/null | grep -q .; then
  CALC=$(cat $(find hadoop/spark hadoop/mr -name "*.sql" -o -name "*.java" 2>/dev/null) 2>/dev/null)
  METRICS=$(grep -ohE '`[a-z_]{6,}`' "$CONTRACT_DIR/02-指标定义表.md" 2>/dev/null | tr -d '`' | sort -u)
  FOUND=0
  for m in $METRICS; do
    if echo "$CALC" | grep -q "$m"; then
      pass "指标 $m 已出现在计算脚本中"
      FOUND=1
    fi
  done
  if [ "$FOUND" -eq 0 ]; then
    warn "尚未在计算脚本中找到契约指标（B 岗还没实现 ADS 层）"
  fi
else
  warn "hadoop 下还没有计算脚本"
fi

# ------------------------------------------------------------------------------
# 检查 5：数据字典是否覆盖全部 12 个 CSV
# ★ 修正记录（2026-11-20 A）：原注释写「11 个 CSV」，但 FILES 数组实际已是 12 个，
#   属注释与实现不一致，容易让人误以为只需覆盖 11 个。现统一为 12。
# ------------------------------------------------------------------------------
echo ""
echo "[5] 数据字典覆盖度"
FILES=(occupancy duration volume volume-11kW e_price s_price inf poi adj distance weather_airport weather_central)
MISSING=0
for f in "${FILES[@]}"; do
  if grep -qi "$f" "$CONTRACT_DIR/01-数据字典.md" 2>/dev/null; then
    pass "$f 已收录"
  else
    fail "$f 未在数据字典中"
    MISSING=1
  fi
done

# ------------------------------------------------------------------------------
# 检查 6：禁止提交大数据文件
# ------------------------------------------------------------------------------
echo ""
echo "[6] 仓库卫生"
BIG=$(git ls-files 2>/dev/null | grep -iE '\.(csv|zip|parquet|orc|jar)$' | head -5)
if [ -n "$BIG" ]; then
  fail "仓库里有大文件（应进 .gitignore）："
  echo "$BIG" | sed 's/^/       /'
else
  pass "没有大文件被提交"
fi

if git ls-files 2>/dev/null | grep -qiE '(\.env|password|secret)'; then
  fail "疑似提交了密钥文件"
else
  pass "没有密钥文件"
fi

# ------------------------------------------------------------------------------
echo ""
echo "--- 结果：通过 $OK，警告 $WARN，失败 $ERR ---"
if [ "$ERR" -gt 0 ]; then
  echo -e "${RED}有 $ERR 项失败，处理后再合并${NC}"
  exit 1
fi
exit 0
