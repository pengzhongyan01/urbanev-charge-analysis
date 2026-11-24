#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  sync_retry.sh —— 双端同步自愈脚本
#
#  用途：GitHub 偶尔会连不上（SSH 被重置 / HTTPS 502），
#        本脚本每 10 分钟重试一次，推成功即停。
#
#  用法：
#    bash scripts/sync_retry.sh              # 前台跑，最多 18 轮（3 小时）
#    bash scripts/sync_retry.sh --bg         # 后台跑（写到 /tmp 的日志）
#    bash scripts/sync_retry.sh --once       # 只试一次
#
#  为什么需要它：
#    2026-11-24 14:50 GitHub SSH 报 "Connection reset by 20.6.7.17 port 22"，
#    HTTPS 报 502 —— 整站不可达。但 Gitee 完全正常。
#    双端镜像的价值在这里体现：**主端挂了不影响组员 clone**。
#    本脚本只负责在 GitHub 恢复后把落后的提交补上。
# ─────────────────────────────────────────────────────────────
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO"

BLUE='\033[1;34m'; GREEN='\033[1;32m'; YELLOW='\033[1;33m'; RED='\033[1;31m'; NC='\033[0m'
LOG="/tmp/uev_sync_retry.log"

MAX=18
ONCE=0
BG=0
for a in "$@"; do
    case "$a" in
        --once) ONCE=1 ;;
        --bg)   BG=1 ;;
    esac
done

log() {
    local msg="[$(date '+%H:%M:%S')] $1"
    echo -e "$msg"
    echo "$msg" >> "$LOG" 2>/dev/null || true
}

# ── 检查某远端是否可达（不改变任何东西）──
reachable() {
    local remote="$1"
    timeout 30 git ls-remote --heads "$remote" >/dev/null 2>&1
}

need_push() {
    local remote="$1"
    local head; head=$(git rev-parse HEAD)
    local rh; rh=$(git rev-parse "$remote/main" 2>/dev/null || echo "")
    [ "$head" != "$rh" ]
}

attempt() {
    local remote="$1"
    local name="$2"
    if ! reachable "$remote"; then
        log "${YELLOW}✗${NC} $name 不可达（网络问题），跳过本轮"
        return 2
    fi
    if ! need_push "$remote"; then
        log "${GREEN}✓${NC} $name 已是最新（$(git rev-parse --short "$remote/main")）"
        return 0
    fi
    log "${BLUE}→${NC} 推送到 $name …"
    if git push "$remote" main 2>&1 | tail -2 | sed 's/^/      /'; then
        if ! need_push "$remote"; then
            log "${GREEN}✓${NC} $name 推送成功 → $(git rev-parse --short HEAD)"
            return 0
        fi
    fi
    log "${RED}✗${NC} $name 推送未完成，稍后重试"
    return 1
}

run() {
    log "${BLUE}=== 开始双端同步自愈 ===${NC}"
    log "  本地 HEAD: $(git rev-parse --short HEAD)"
    log "  待推送：Gitee $(git rev-parse --short gitee/main 2>/dev/null || echo '?') / GitHub $(git rev-parse --short origin/main 2>/dev/null || echo '?')"

    local i=1
    while [ $i -le $MAX ]; do
        log "--- 第 $i 轮 ---"

        # Gitee 优先（国内稳）
        attempt gitee "Gitee"
        local grc=$?

        # GitHub 次之（挂了就等下一轮）
        attempt origin "GitHub"
        local orc=$?

        if [ $grc -eq 0 ] && [ $orc -eq 0 ]; then
            log "${GREEN}=== 双端已同步，退出 ===${NC}"
            return 0
        fi

        [ $ONCE -eq 1 ] && { log "${YELLOW}--once 模式，退出${NC}"; return 1; }
        i=$((i + 1))
        log "  等待 10 分钟后重试…"
        sleep 600
    done
    log "${YELLOW}=== 达到最大重试轮次，退出。稍后手动跑 bash scripts/sync_retry.sh 即可 ===${NC}"
    return 1
}

if [ $BG -eq 1 ]; then
    nohup bash "$0" > /tmp/uev_sync_retry_bg.log 2>&1 &
    echo "已在后台启动，日志：/tmp/uev_sync_retry_bg.log"
    exit 0
fi

run
