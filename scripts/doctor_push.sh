#!/usr/bin/env bash
# =============================================================================
# doctor_push.sh —— 推送失败（403 / Permission denied）一键诊断
#
# 用法：bash scripts/doctor_push.sh
#
# 作用：把「不知道为啥推不上去」变成一行结论 + 一条修复命令
#   1. 报出当前仓库地址、git 身份、认证方式
#   2. 分别探测 SSH 和 HTTPS 两条通道「你是谁」
#   3. 用真实 dry-run 探测写权限（这是唯一权威判据）
#   4. 给出对应的修复动作
#
# 典型场景：组员 push 报
#   remote: Permission to pengzhongyan01/urbanev-charge-analysis.git
#           denied to <某个账号>.
#   → 那个账号对仓库只有 read（公开仓库人人可读），push 需要 write
#   → 组长在仓库 Settings → Collaborators 里加你为 Write，等你点接受
# =============================================================================
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

RED='\033[1;31m'; GREEN='\033[1;32m'; YELLOW='\033[1;33m'
BLUE='\033[1;34m'; CYAN='\033[1;36m'; NC='\033[0m'

echo ""
echo "=============================================================="
echo -e " ${CYAN}推送权限诊断${NC}"
echo "=============================================================="

# ------------------------------------------------------------------------------
# 1. 基本信息
# ------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[1/4] 本地信息${NC}"
echo "  仓库目录：$(pwd)"
REMOTE=$(git remote get-url origin 2>/dev/null)
if [ -z "$REMOTE" ]; then
  echo -e "  ${YELLOW}✗ 没有 origin remote${NC}"
  echo "    修复：git remote add origin git@github.com:pengzhongyan01/urbanev-charge-analysis.git"
  exit 1
fi
echo "  origin   ：$REMOTE"
echo "  git name ：$(git config user.name || echo '(未设置)')"
echo "  git email：$(git config user.email || echo '(未设置)')"

# ------------------------------------------------------------------------------
# 2. SSH 通道：你是谁
# ------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[2/4] SSH 通道身份${NC}"
SSH_OUT=$(ssh -T -o BatchMode=yes -o ConnectTimeout=15 git@github.com 2>&1)
SSH_USER=$(echo "$SSH_OUT" | sed -n 's/^Hi \([^!]*\)!.*/\1/p')
if [ -n "$SSH_USER" ]; then
  echo -e "  ${GREEN}✓ SSH 可用，身份：${SSH_USER}${NC}"
  SSH_OK=1
else
  echo -e "  ${YELLOW}✗ SSH 未通${NC}"
  echo "    $(echo "$SSH_OUT" | head -1)"
  echo "    修复：bash scripts/setup_ssh.sh，然后公钥粘到 https://github.com/settings/ssh/new"
  SSH_OK=0
fi

# ------------------------------------------------------------------------------
# 3. HTTPS 通道：你是谁
# ------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[3/4] HTTPS 通道身份${NC}"
HTTPS_OUT=$(printf 'protocol=https\nhost=github.com\n\n' | git credential fill 2>/dev/null)
HTTPS_USER=$(echo "$HTTPS_OUT" | sed -n 's/^username=//p')
if [ -n "$HTTPS_USER" ]; then
  echo -e "  ${GREEN}✓ 凭据管理器里有账号：${HTTPS_USER}${NC}"
  HTTPS_OK=1
else
  echo -e "  ${YELLOW}✗ 没缓存 HTTPS 凭据${NC}"
  echo "    修复：git push 时用 GitHub 账号 + Personal Access Token 登录"
  HTTPS_OK=0
fi

# ------------------------------------------------------------------------------
# 4. 写权限探针 —— 唯一权威判据
# ------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[4/4] 写权限实测（git push --dry-run）${NC}"
DRY=$(git push --dry-run origin HEAD 2>&1)
if echo "$DRY" | grep -qi "everything up-to-date\|new branch\|up to date"; then
  echo -e "  ${GREEN}✓ 有写权限，推送能通${NC}"
  echo ""
  echo -e "  ${GREEN}${NC}结论：权限没问题，直接推就行"
  echo "  git push origin feat/你的分支"
  exit 0
fi

DENIED=$(echo "$DRY" | sed -n 's/.*denied to \([^ .]*\).*/\1/p')
if [ -n "$DENIED" ]; then
  echo -e "  ${RED}✗ 推送被拒：账号 ${DENIED} 对这个仓库没有写权限${NC}"
  echo ""
  echo "  ${YELLOW}为什么？${NC}"
  echo "    仓库是公开的 → 任何人都能 clone（读）"
  echo "    但 push（写）必须被显式授予 write 权限"
  echo "    ${DENIED} 目前只有 read，所以被 GitHub 挡回 403"
  echo ""
  echo "  ${CYAN}怎么修（两步，5 分钟）${NC}"
  echo "    第 1 步（组长做）：把 ${DENIED} 加为仓库协作者"
  echo "      https://github.com/pengzhongyan01/urbanev-charge-analysis/settings/access"
  echo "      → Collaborators → Add people → 填 ${DENIED} → 权限选 Write → 发送邀请"
  echo ""
  echo "    第 2 步（你做）：登录 GitHub 点接受邀请"
  echo "      https://github.com/pengzhongyan01/urbanev-charge-analysis/invitations"
  echo "      或右上角 Notifications → Invitations → Accept"
  echo ""
  echo "    接受后重新跑本脚本验证，或直接："
  echo "      git push origin feat/你的分支"
else
  echo -e "  ${RED}✗ 推送失败${NC}"
  echo "$DRY" | sed 's/^/    /' | head -8
  echo ""
  echo "  ${YELLOW}如果不是 403 权限问题，看这几条：${NC}"
  echo "    · 第一次推送没建分支 → git push -u origin feat/你的分支"
  echo "    · 分支名不对 → git branch --show-current 看看当前在哪个分支"
  echo "    · 冲突 → git pull --rebase origin main 再推"
  echo "    · SSH 报 Permission denied (publickey) → bash scripts/setup_ssh.sh"
fi

echo ""
exit 1
