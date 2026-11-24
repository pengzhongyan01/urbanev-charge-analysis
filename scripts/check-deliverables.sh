#!/usr/bin/env bash
# ==============================================================================
# check-deliverables.sh —— 交付物验收检查
#
# 维护人：A（组长）　|　用途：11/19 起每天跑一次，看谁还差什么
#
# 用法：bash scripts/check-deliverables.sh
# 退出码：0 = 全员齐备，1 = 有人还缺
#
# 它检查每个岗位的「完成标志」里那些能用文件/行数判定的部分。
# 跑不起来的、需要人看的，会列在「需要人工确认」区。
# ==============================================================================
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

GREEN='\033[1;32m'; RED='\033[1;31m'; YELLOW='\033[1;33m'; BLUE='\033[1;34m'; CYAN='\033[1;36m'; NC='\033[0m'
PASS=0; FAIL=0; WARN=0
pass() { echo -e "  ${GREEN}✓${NC} $1"; PASS=$((PASS+1)); }
fail() { echo -e "  ${RED}✗${NC} $1"; FAIL=$((FAIL+1)); }
warn() { echo -e "  ${YELLOW}!${NC} $1"; WARN=$((WARN+1)); }
section() { echo -e "\n${BLUE}$1${NC}"; }

# 组长交付目录的上一级
DELIV_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DELIV_DIR="${UEV_DELIV_DIR:-$DELIV_ROOT/作业内容}"

echo ""
echo "=============================================================="
echo -e " ${BLUE}第 02 组 · 交付物验收${NC}"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================================="
echo -e " 交付目录：$DELIV_DIR"

# ------------------------------------------------------------------------------
section "[A 彭忠燕] 基础设施"
# ------------------------------------------------------------------------------
for f in docker-compose.yml docs/RUNBOOK.md docs/ppt/PPT逐页脚本.md \
         scripts/start_all.sh scripts/stop_all.sh scripts/smoke_test.sh \
         scripts/download_data.sh scripts/verify_data.sh scripts/find_data.sh; do
  if [ -f "$f" ]; then pass "$f"; else fail "$f 缺失"; fi
done
if [ -f "docs/report/第1-2章_初稿.md" ]; then
  pass "报告第一二章初稿"
else
  fail "报告第一二章初稿缺失"
fi

# ------------------------------------------------------------------------------
section "[B 苏静] 数仓与计算"
# ------------------------------------------------------------------------------
for f in hadoop/hive/gen_ddl.py hadoop/mr/WideToLong.java \
         hadoop/mr/DataQualityCheck.java hadoop/mr/PoiZoneJoin.java \
         hadoop/spark/ads_metrics.sql; do
  if [ -f "$f" ]; then pass "$f"; else fail "$f 缺失"; fi
done

# 检查 DDL 是否已生成
if ls hadoop/hive/*.sql >/dev/null 2>&1; then
  pass "已生成建表 SQL（$(ls hadoop/hive/*.sql | wc -l) 个）"
else
  warn "未生成建表 SQL —— 执行 python3 hadoop/hive/gen_ddl.py > ddl_ods.sql"
fi

# 检查 MR 作业能否编译（若有 javac 和 hadoop classpath 则试）
if command -v javac >/dev/null 2>&1; then
  if [ -n "${HADOOP_HOME:-}" ]; then
    TMPD=$(mktemp -d)
    cp hadoop/mr/*.java "$TMPD/" 2>/dev/null
    if javac -cp "$(hadoop classpath 2>/dev/null)" -d "$TMPD" "$TMPD"/*.java 2>/dev/null; then
      pass "MR 作业编译通过"
    else
      warn "MR 作业编译未通过（需 hadoop classpath 环境）"
    fi
    rm -rf "$TMPD"
  else
    warn "未设置 HADOOP_HOME，跳过 MR 编译检查"
  fi
else
  warn "无 javac，跳过 MR 编译检查"
fi

# ------------------------------------------------------------------------------
section "[C 贺欢欢] 可视化"
# ------------------------------------------------------------------------------
for f in frontend/index.html frontend/css/style.css frontend/js/common.js \
         frontend/js/app.js frontend/js/echarts.min.js \
         frontend/assets/shenzhen_440300_full.json; do
  if [ -f "$f" ]; then pass "$f"; else fail "$f 缺失"; fi
done

# ------------------------------------------------------------------------------
section "[D 杨姗姗] 后端"
# ------------------------------------------------------------------------------
for f in backend/pom.xml backend/Dockerfile \
         backend/src/main/resources/application.yml \
         backend/src/main/java/com/uev/UevChargeAnalysisApplication.java \
         backend/src/main/java/com/uev/common/Result.java \
         backend/src/main/java/com/uev/common/GlobalExceptionHandler.java \
         backend/src/main/java/com/uev/config/RedisConfig.java \
         backend/src/main/java/com/uev/controller/HealthController.java \
         db/mysql/01_schema.sql; do
  if [ -f "$f" ]; then pass "$f"; else fail "$f 缺失"; fi
done

# Controller 数量（7 个接口需要至少 2 个 Controller）
CTRL_CNT=$(find backend -name "*Controller.java" 2>/dev/null | wc -l)
if [ "$CTRL_CNT" -ge 2 ]; then
  pass "Controller 数量 $CTRL_CNT（≥2，够放 7 个接口）"
elif [ "$CTRL_CNT" -eq 1 ]; then
  warn "只有 1 个 Controller —— 建议再拆一个（ChartController）"
else
  fail "还没有 Controller 实现"
fi

# ------------------------------------------------------------------------------
section "[E 姬婷婷] 分析与模型"
# ------------------------------------------------------------------------------
if grep -q "待 E 填" docs/contracts/02-指标定义表.md 2>/dev/null; then
  REMAIN=$(grep -c "待 E 填" docs/contracts/02-指标定义表.md)
  warn "指标定义表还有 $REMAIN 处【待 E 填】未回填"
else
  pass "指标定义表已全部回填"
fi
if [ -f "docs/contracts/02-指标定义表.md" ]; then
  pass "指标定义表存在（12 基础 + 3 创新指标）"
else
  fail "指标定义表缺失"
fi

# ------------------------------------------------------------------------------
section "[全体] 交付文件夹素材"
# ------------------------------------------------------------------------------
check_dir() {
  local name="$1"; local desc="$2"
  local d="$DELIV_DIR/$name"
  if [ ! -d "$d" ]; then
    fail "$name 的交付文件夹不存在"
    return
  fi
  local cnt=$(find "$d" -type f ! -name "说明.md" 2>/dev/null | wc -l)
  if [ "$cnt" -gt 0 ]; then
    pass "$name 已交 $cnt 个文件（$desc）"
  else
    warn "$name 文件夹里还没有素材（$desc）"
  fi
}
check_dir "苏静"   "清洗对比表/四层截图/血缘图/Job截图"
check_dir "贺欢欢" "图表PNG/地图/演示脚本/视频"
check_dir "杨姗姗" "接口截图/测试用例/缓存对比"
check_dir "姬婷婷" "创新点图表/预测曲线/建议清单"

# ------------------------------------------------------------------------------
section "[全体] Git 仓库状态"
# ------------------------------------------------------------------------------
if command -v git >/dev/null 2>&1 && [ -d .git ]; then
  CNT=$(git ls-files 2>/dev/null | wc -l)
  pass "已跟踪文件 $CNT 个"
  COMMIT=$(git log --oneline 2>/dev/null | wc -l)
  pass "提交记录 $COMMIT 次"
  DIRTY=$(git status --short 2>/dev/null | wc -l)
  if [ "$DIRTY" -gt 0 ]; then
    warn "有 $DIRTY 个文件未提交 —— 提醒组员 push"
  else
    pass "工作区干净"
  fi
  # 检查是否有大文件误提交
  BIG=$(git ls-files 2>/dev/null | grep -iE '\.(csv|zip|jar)$' | head -3)
  if [ -n "$BIG" ]; then
    fail "仓库里有大文件（应忽略）：$BIG"
  else
    pass "没有大文件被提交"
  fi
else
  warn "不是 Git 仓库或 git 不可用"
fi

# ------------------------------------------------------------------------------
section "[契约] 一致性"
# ------------------------------------------------------------------------------
if bash scripts/check-contracts.sh >/dev/null 2>&1; then
  pass "契约与实现一致（0 失败）"
else
  warn "契约检查有失败项 —— 详见 check-contracts.sh 输出"
fi

# ------------------------------------------------------------------------------
section "[系统] 运行状态"
# ------------------------------------------------------------------------------
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  RUNNING=$(docker ps --format '{{.Names}}' 2>/dev/null | wc -l)
  if [ "$RUNNING" -gt 0 ]; then
    pass "有 $RUNNING 个容器在运行"
  else
    warn "Docker 在运行但没有容器 —— 执行 bash scripts/start_all.sh"
  fi
else
  warn "Docker 不可用，跳过容器检查"
fi

HEALTH=$(curl -s --max-time 5 http://localhost:8080/api/health 2>/dev/null)
if [ -n "$HEALTH" ]; then
  pass "后端已响应"
else
  warn "后端未响应（8080 无服务）"
fi

# ------------------------------------------------------------------------------
section "[人工确认] 这些必须你亲自看"
# ------------------------------------------------------------------------------
cat << 'EOF'
  □ 苏静的 ADS 七张表是否都有数据（跑 smoke_test.sh 看第3项）
  □ 姬婷婷的 MAPE 是否 < 15%（> 25% 要改方法）
  □ 杨姗姗的缓存对比数字是不是实测的（不能编）
  □ 贺欢欢的每张图有没有配一句话结论
  □ 截图是不是本次运行的新截图（不是上周的）
  □ 报告的目录页码是否正确
  □ ★ 随机抽一位组员，照 RUNBOOK 在第二台电脑上跑一遍
EOF

# ------------------------------------------------------------------------------
echo ""
echo "=============================================================="
echo -e " ${BLUE}机器可查部分${NC}：通过 ${GREEN}$PASS${NC}　警告 ${YELLOW}$WARN${NC}　失败 ${RED}$FAIL${NC}"
echo -e " ${YELLOW}人工确认部分见上方清单${NC}"
if [ "$FAIL" -gt 0 ]; then
  echo -e " ${RED}还有 $FAIL 项硬缺失 —— 对应的人还没交${NC}"
  echo "=============================================================="
  echo ""
  exit 1
fi
echo -e " ${GREEN}机器可查部分全部通过${NC}"
echo "=============================================================="
echo ""
exit 0
