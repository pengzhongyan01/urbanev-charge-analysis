#!/usr/bin/env bash
# ==============================================================================
# sync.sh —— 每人每天开工第一件事
#
# 作用：把"互相问对方数据"变成"pull 一下就看到"
#   1. 拉取 main 最新内容（含所有人的契约更新）
#   2. 打印本次拉到的契约变更 —— 立刻知道谁改了什么
#   3. 重新加载 Hive 建表 SQL（若有变动）
#   4. 检查本地环境与契约是否一致
#
# 用法：bash scripts/sync.sh
# ==============================================================================
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

CONTRACT_DIR="docs/contracts"
CONTRACT_LOG="docs/contracts/CHANGELOG.md"

RED='\033[1;31m'; GREEN='\033[1;32m'; YELLOW='\033[1;33m'
BLUE='\033[1;34m'; CYAN='\033[1;36m'; NC='\033[0m'

echo ""
echo "=============================================================="
echo -e " ${CYAN}UrbanEV 项目 · 契约同步${NC}"
echo "=============================================================="

# ------------------------------------------------------------------------------
# 1. 记录同步前的契约文件状态
# ------------------------------------------------------------------------------
BEFORE=$(mktemp)
AFTER=$(mktemp)
if [ -d "$CONTRACT_DIR" ]; then
  find "$CONTRACT_DIR" -name "*.md" -type f -exec md5sum {} \; 2>/dev/null | sort > "$BEFORE"
fi

# ------------------------------------------------------------------------------
# 2. 拉取最新内容
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[1/4]${NC} 拉取 main 最新内容..."
git fetch origin 2>/dev/null || git fetch 2>/dev/null

if git rev-parse --verify origin/main >/dev/null 2>&1; then
  REMOTE="origin/main"
else
  REMOTE="main"
fi

BEFORE_SHA=$(git rev-parse HEAD 2>/dev/null || echo "")
git pull --rebase "$REMOTE" 2>&1 | sed 's/^/    /'
AFTER_SHA=$(git rev-parse HEAD 2>/dev/null || echo "")

if [ -n "$BEFORE_SHA" ] && [ "$BEFORE_SHA" != "$AFTER_SHA" ]; then
  echo -e "    ${GREEN}✓${NC} 已更新到最新提交 ${AFTER_SHA:0:8}"
else
  echo -e "    ${GREEN}✓${NC} 已是最新"
fi

# ------------------------------------------------------------------------------
# 3. 对比契约文件，输出变更摘要
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[2/4]${NC} 检测契约变更..."
if [ -d "$CONTRACT_DIR" ]; then
  find "$CONTRACT_DIR" -name "*.md" -type f -exec md5sum {} \; 2>/dev/null | sort > "$AFTER"
fi

CHANGED=0
if ! diff -q "$BEFORE" "$AFTER" >/dev/null 2>&1; then
  CHANGED=1
  echo -e "    ${YELLOW}⚠ 本次同步包含契约变更，请仔细阅读：${NC}"
  echo ""
  # 逐个文件对比
  while IFS= read -r line; do
    file=$(echo "$line" | awk '{print $2}')
    hash=$(echo "$line" | awk '{print $1}')
    if ! grep -q "^$hash" "$BEFORE" 2>/dev/null; then
      echo -e "      ${YELLOW}◆${NC} $(basename "$file")  ${GREEN}有更新${NC}"
      # 显示该文件的版本行和变更记录的最后一条
      if [ -f "$file" ]; then
        ver=$(grep -m1 -oE '版本[^|]*' "$file" 2>/dev/null | head -1)
        [ -n "$ver" ] && echo -e "        ${CYAN}$ver${NC}"
      fi
    fi
  done < "$AFTER"

  echo ""
  echo -e "    ${BLUE}查看完整变更：${NC} git diff HEAD@{1} -- $CONTRACT_DIR"
  echo -e "    ${BLUE}变更历史：${NC}   cat $CONTRACT_LOG"
else
  echo -e "    ${GREEN}✓${NC} 契约无变更"
fi

rm -f "$BEFORE" "$AFTER"

# ------------------------------------------------------------------------------
# 4. 重新加载 Hive 表（若有变动）
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[3/4]${NC} 检查 Hive 建表脚本..."
if [ -d hadoop/hive ]; then
  SQL_COUNT=$(ls -1 hadoop/hive/*.sql 2>/dev/null | wc -l)
  if [ "$SQL_COUNT" -gt 0 ]; then
    echo -e "    发现 ${GREEN}${SQL_COUNT}${NC} 个建表脚本："
    ls -1 hadoop/hive/*.sql 2>/dev/null | while read -r f; do
      echo -e "      ${CYAN}$(basename "$f")${NC}  ($(wc -l < "$f") 行)"
    done
    if command -v hive >/dev/null 2>&1; then
      echo -e "    ${YELLOW}提示${NC}：如结构有变，在集群中执行 ${CYAN}hive -f hadoop/hive/01_ods.sql${NC}"
    fi
  else
    echo -e "    ${YELLOW}尚无建表脚本${NC}"
  fi
fi

# ------------------------------------------------------------------------------
# 5. 契约一致性检查
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[4/4]${NC} 契约一致性检查..."
if bash scripts/check-contracts.sh 2>/dev/null; then
  echo -e "    ${GREEN}✓${NC} 全部检查通过"
else
  echo -e "    ${YELLOW}⚠ 存在待处理项（详见上方输出）${NC}"
fi

# ------------------------------------------------------------------------------
echo ""
echo "=============================================================="
echo -e " ${GREEN}同步完成${NC}  当前分支：$(git branch --show-current)"
echo -e " ${YELLOW}提示${NC}：契约文件在 ${CONTRACT_DIR}/，有疑问先看那里，别急着问人"
echo "=============================================================="
echo ""
