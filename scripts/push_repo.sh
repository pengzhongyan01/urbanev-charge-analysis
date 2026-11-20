#!/usr/bin/env bash
# ============================================================
# 首次推送 / 后续推送脚本
# 用法：bash scripts/push_repo.sh
# 作用：自动配置 remote（SSH）+ 推送 main
# ============================================================
set -e

REPO_URL="git@github.com:pengzhongyan01/urbanev-charge-analysis.git"
SSH_KEY="$HOME/.ssh/id_ed25519_git"

echo "=============================================="
echo "  UrbanEV 充电桩大作业 · 推送脚本"
echo "=============================================="

# 1. SSH 钥匙
if [ -f "$SSH_KEY" ]; then
  git config core.sshCommand "ssh -i $SSH_KEY -o IdentitiesOnly=yes"
  echo "[1/3] SSH 钥匙已配置：$SSH_KEY"
else
  echo "[1/3] ⚠ 没找到 $SSH_KEY，退回默认钥匙"
fi

# 2. remote
if git remote get-url origin >/dev/null 2>&1; then
  echo "[2/3] remote origin 已存在：$(git remote get-url origin)"
else
  git remote add origin "$REPO_URL"
  echo "[2/3] remote origin 已添加：$REPO_URL"
fi

# 3. 推送
echo "[3/3] 推送到 main ..."
git push -u origin main

echo ""
echo "=============================================="
echo " ✅ 推送完成"
echo "=============================================="
echo "仓库地址： https://github.com/pengzhongyan01/urbanev-charge-analysis"
echo ""
echo "组员 clone 命令（发群里）："
echo ""
echo "  git clone git@github.com:pengzhongyan01/urbanev-charge-analysis.git"
echo "  cd urbanev-charge-analysis"
echo "  bash scripts/download_data.sh"
echo "  bash scripts/verify_data.sh"
echo ""
