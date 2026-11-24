#!/usr/bin/env bash
# ============================================================
# 组员上手脚本 —— 配置 SSH 推送权限
# 用法：bash scripts/setup_ssh.sh
#
# 为什么需要这个：clone 用 HTTPS 就行（公开仓库免授权），
# 但 **push 需要认证**。这个脚本帮你生成 SSH 密钥并配好 git。
# ============================================================
set -e

KEY="$HOME/.ssh/id_ed25519_git"

# ★ 邮箱必须是你自己的，且已验证到你的 GitHub 账号。
#   GitHub 靠邮箱把提交关联到账号 —— 用别人的邮箱，提交就署到别人名下，
#   你的「个人贡献说明」在提交记录里就没有痕迹。
LEADER_EMAIL="15085958265@163.com"

echo "=============================================="
echo " 组员上手 · 配置 Git 推送权限"
echo "=============================================="

# 1. git 身份
if ! git config --global user.email >/dev/null 2>&1; then
  echo "[1/3] ✗ 你的 git 邮箱还没设置。"
  echo ""
  echo "      请先设置成【你自己的、已验证到 GitHub 账号的】邮箱："
  echo "        git config --global user.email \"你的邮箱@example.com\""
  echo ""
  echo "      查自己的 GitHub 邮箱："
  echo "        https://github.com/settings/emails"
  echo "      （GitHub 右上角 → Settings → Emails，能看到 Primary 那个）"
  echo ""
  echo "      ⚠ 不要用组长的邮箱 $LEADER_EMAIL ——"
  echo "        那样你的提交在 GitHub 上会署成别人，个人贡献说明就没证据了。"
  exit 1
fi

CURRENT_EMAIL="$(git config --global user.email)"
if [ "$CURRENT_EMAIL" = "$LEADER_EMAIL" ]; then
  echo "[1/3] ✗ 你现在用的是组长的邮箱，提交会署到别人名下。"
  echo ""
  echo "      请改成你自己的："
  echo "        git config --global user.email \"你的邮箱@example.com\""
  echo "      （在 https://github.com/settings/emails 里查你的 Primary 邮箱）"
  exit 1
fi
echo "[1/3] git email：$CURRENT_EMAIL"

if ! git config --global user.name >/dev/null 2>&1; then
  git config --global user.name "请改成你的名字"
  echo "      ↑ git name 请改：git config --global user.name \"你的名字\""
else
  echo "      git name：$(git config --global user.name)"
fi

# 2. SSH 密钥
if [ -f "$KEY" ]; then
  echo "[2/3] SSH 密钥已存在：$KEY"
else
  mkdir -p "$HOME/.ssh"
  ssh-keygen -t ed25519 -C "$EMAIL" -f "$KEY" -N "" >/dev/null 2>&1
  echo "[2/3] 已生成 SSH 密钥：$KEY"
fi

# 3. 配 core.sshCommand（如果已经在仓库目录里）
if [ -d ".git" ]; then
  git config core.sshCommand "ssh -i $KEY -o IdentitiesOnly=yes"
  echo "[3/3] 本仓库已指向该密钥"
else
  echo "[3/3] 请 cd 进仓库目录后再跑一次本脚本"
fi

echo ""
echo "=============================================="
echo " 还差最后一步：把公钥加到 GitHub"
echo "=============================================="
echo ""
echo "  1. 打开 https://github.com/settings/ssh/new"
echo "  2. Title 随便填，比如「彭忠燕的笔记本」"
echo "  3. Key 里粘贴下面这一整行："
echo "  --------------------------------------------"
cat "$KEY.pub"
echo "  --------------------------------------------"
echo ""
echo "  4. 点 Add SSH key"
echo "  5. 验证：ssh -T git@github.com"
echo "     看到 Hi xxx! You've successfully authenticated 就成功了"
echo ""
echo "  配好后你就能："
echo "    git push origin feat/你的分支"
echo ""
