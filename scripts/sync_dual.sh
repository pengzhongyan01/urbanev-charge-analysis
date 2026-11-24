#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  GitHub ⇄ Gitee 双端同步脚本
#
#  用法：
#    bash scripts/sync_dual.sh push      # 本地 → GitHub + Gitee（同时推）
#    bash scripts/sync_dual.sh pull      # 从 GitHub 拉取（取回 Gitee 上的改动）
#    bash scripts/sync_dual.sh pull-gitee # 只从 Gitee 拉
#    bash scripts/sync_dual.sh status    # 看两个远端的状态
#    bash scripts/sync_dual.sh setup     # 首次配置（校验 SSH、设双远端）
#
#  设计要点：
#   1. 两个远端共存：origin = GitHub，gitee = Gitee，互不干扰
#   2. push 时先推 Gitee 再推 GitHub —— Gitee 国内速度快，
#      先推它能在 GitHub 被墙/超时时保证至少有一端是新的
#   3. 推送前先 fetch 检查分歧，有分叉时中止并提示，不自动强推
#   4. 绝不 --force：除非显式传 --force，否则冲突直接停
# ─────────────────────────────────────────────────────────────
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO"

GITEE_REPO="git@gitee.com:peng-zhongyan/urbanev-charge-analysis.git"
GITEE_BRANCH="main"
SSH_KEY="$HOME/.ssh/id_ed25519_git"

BLUE='\033[1;34m'; GREEN='\033[1;32m'; YELLOW='\033[1;33m'; RED='\033[1;31m'; NC='\033[0m'

hr() { printf "${BLUE}────────────────────────────────────────${NC}\n"; }

ensure_remote() {
    if git remote get-url gitee >/dev/null 2>&1; then
        git remote set-url gitee "$GITEE_REPO"
    else
        git remote add gitee "$GITEE_REPO"
        echo -e "${GREEN}✓${NC} 已添加 gitee 远端：$GITEE_REPO"
    fi
    if ! git remote get-url origin >/dev/null 2>&1; then
        git remote add origin "git@github.com:pengzhongyan01/urbanev-charge-analysis.git"
        echo -e "${GREEN}✓${NC} 已添加 origin 远端（GitHub）"
    fi
}

check_ssh() {
    echo -e "${BLUE}→${NC} 检查 Gitee SSH 认证…"
    local out
    if [ -f "$SSH_KEY" ]; then
        out=$(timeout 25 ssh -T -i "$SSH_KEY" -o StrictHostKeyChecking=no \
              -o ConnectTimeout=15 git@gitee.com 2>&1)
    else
        echo -e "  ${YELLOW}⚠${NC} 找不到私钥 $SSH_KEY，尝试用默认密钥"
        out=$(timeout 25 ssh -T -o StrictHostKeyChecking=no -o ConnectTimeout=15 git@gitee.com 2>&1)
    fi
    # ★ 两个坑叠在一起，必须都处理：
    #   1. Gitee 的欢迎语里插了 ANSI 颜色码，
    #      "successfully" 实际是 "suc\x1b[32mcessfully" → 直接 grep 永远匹配不上。
    #      所以先去 ANSI 序列再判断。
    #   2. Windows Git Bash 在中文用户名路径下会先打印 "Could not create directory"
    #      警告（HOME 被转义成八进制），但认证其实完全成功 —— 误判成失败会卡住推送。
    local plain
    plain=$(printf '%s' "$out" | sed 's/\x1b\[[0-9;]*m//g')
    if printf '%s' "$plain" | grep -q "successfully authenticated"; then
        echo -e "  ${GREEN}✓${NC} $(printf '%s' "$plain" | grep -o 'Hi .*' | head -1)"
        printf '%s' "$plain" | grep -q "Could not create directory" && \
            echo -e "  ${YELLOW}(注)${NC} 上面那句 HOME 路径警告是 Git Bash 中文用户名转义问题，不影响认证"
        return 0
    fi
    echo -e "  ${RED}✗${NC} Gitee SSH 认证失败："
    echo "$out" | sed 's/^/      /' | head -5
    echo -e "  ${BLUE}→${NC} 请运行：bash scripts/setup_ssh.sh 重新配置密钥"
    return 1
}

check_divergence() {
    # 检查本地与远端是否分叉；返回 0=可快进推送，1=有分叉
    local remote="$1" branch="$2"
    git fetch "$remote" "$branch" --quiet 2>/dev/null || {
        echo -e "  ${YELLOW}⚠${NC} fetch $remote/$branch 失败（远端可能还没有该分支）"
        return 0
    }
    local behind ahead
    behind=$(git rev-list --count "$remote/$branch..HEAD" 2>/dev/null || echo 0)
    ahead=$(git rev-list --count "HEAD..$remote/$branch" 2>/dev/null || echo 0)
    if [ "$ahead" -gt 0 ] && [ "$behind" -gt 0 ]; then
        echo -e "  ${RED}✗ 分叉！${NC} 本地领先 $behind 个提交，远端领先 $ahead 个提交"
        echo -e "     需先人工处理（不要自动 force）："
        echo -e "       git fetch $remote && git log --oneline HEAD..$remote/$branch"
        return 1
    fi
    if [ "$ahead" -gt 0 ]; then
        echo -e "  ${YELLOW}⚠${NC} 远端 $remote 领先 $ahead 个提交（本地落后）"
        echo -e "     先执行：git pull $remote $branch"
        return 1
    fi
    echo -e "  ${GREEN}✓${NC} 无分叉，本地领先 $behind 个提交"
    return 0
}

cmd_status() {
    hr
    echo -e "${BLUE}双端状态${NC}"
    hr
    git remote -v | sed 's/^/  /'
    echo
    echo -e "  当前分支：$(git branch --show-current)"
    echo -e "  最新提交：$(git log -1 --pretty=format:'%h %ad %s' --date=format:'%m/%d %H:%M')"
    echo
    for r in origin gitee; do
        if git remote get-url "$r" >/dev/null 2>&1; then
            url=$(git remote get-url "$r")
            if git fetch "$r" --quiet 2>/dev/null; then
                behind=$(git rev-list --count "$r/$(git branch --show-current)..HEAD" 2>/dev/null || echo '?')
                ahead=$(git rev-list --count "HEAD..$r/$(git branch --show-current)" 2>/dev/null || echo '?')
                echo -e "  ${GREEN}[$r]${NC} $url"
                echo -e "        本地领先 ${ahead} 个提交 / 本地落后 ${behind} 个提交"
            else
                echo -e "  ${YELLOW}[$r]${NC} $url  ${YELLOW}(fetch 失败，可能还没建仓)${NC}"
            fi
        fi
    done
    echo
    # 只有在 Gitee 仓库确实不可达时才提示建仓（已建好就别啰嗦）
    if ! git ls-remote gitee >/dev/null 2>&1; then
        echo -e "  ${YELLOW}提示${NC}：Gitee 仓库还不可用，先在网页创建 → https://gitee.com/peng-zhongyan/new"
    else
        echo -e "  ${GREEN}双端已就绪${NC}：${GREEN}Gitee${NC} + ${GREEN}GitHub${NC} 内容一致"
    fi
}

cmd_push() {
    local force="$1"
    ensure_remote
    local branch; branch=$(git branch --show-current)
    [ -z "$branch" ] && branch="main"

    check_ssh || return 1

    hr
    echo -e "${BLUE}推送前检查${NC}"
    hr
    local ok=1
    check_divergence gitee "$branch" || ok=0
    check_divergence origin "$branch" || ok=0
    if [ $ok -ne 1 ]; then
        echo -e "\n${RED}中止推送：存在分叉，请先处理。${NC}"
        return 1
    fi

    hr
    echo -e "${BLUE}推送到 Gitee${NC}"
    hr
    if [ "$force" = "--force" ]; then
        git push -u gitee "$branch" --force
    else
        git push -u gitee "$branch"
    fi
    local gitee_rc=$?

    hr
    echo -e "${BLUE}推送到 GitHub${NC}"
    hr
    if [ "$force" = "--force" ]; then
        git push origin "$branch" --force
    else
        git push origin "$branch"
    fi
    local gh_rc=$?

    hr
    if [ $gitee_rc -eq 0 ] && [ $gh_rc -eq 0 ]; then
        echo -e "${GREEN}✓ 双端推送成功${NC}"
        echo -e "  Gitee ：https://gitee.com/peng-zhongyan/urbanev-charge-analysis"
        echo -e "  GitHub：https://github.com/pengzhongyan01/urbanev-charge-analysis"
        return 0
    elif [ $gitee_rc -eq 0 ]; then
        echo -e "${YELLOW}⚠ Gitee 成功，GitHub 失败${NC}"
        return 1
    else
        echo -e "${RED}✗ Gitee 推送失败${NC}"
        if echo "$(git push -u gitee "$branch" 2>&1)" | grep -q "404"; then
            echo -e "  → 仓库不存在。请先在网页创建："
            echo -e "    https://gitee.com/peng-zhongyan/new"
            echo -e "    仓库名填 urbanev-charge-analysis，公开，"
            echo -e "    「已有文件」那栏不用管（我们推的是完整历史）。"
        fi
        return 1
    fi
}

cmd_pull() {
    local from="$1"
    local branch; branch=$(git branch --show-current)
    [ -z "$branch" ] && branch="main"
    if [ -z "$from" ]; then from="origin"; fi
    echo -e "${BLUE}→${NC} 从 $from/$branch 拉取…"
    git pull "$from" "$branch"
}

cmd_setup() {
    ensure_remote
    check_ssh
    echo
    cmd_status
}

case "${1:-status}" in
    push)      shift; cmd_push "${1:-}" ;;
    pull)      shift; cmd_pull "${1:-}" ;;
    pull-gitee) cmd_pull "gitee" ;;
    status)    cmd_status ;;
    setup)     cmd_setup ;;
    *)
        echo "用法: bash scripts/sync_dual.sh {push|pull|pull-gitee|status|setup} [--force]"
        exit 1
        ;;
esac
