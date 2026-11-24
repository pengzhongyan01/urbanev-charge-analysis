#!/usr/bin/env bash
# =============================================================================
# add_collaborators.sh —— 组长批量给组员开写权限
#
# 用法：
#   bash scripts/add_collaborators.sh 账号1 账号2 ...
#   bash scripts/add_collaborators.sh --list          # 只看当前协作者和待处理邀请
#
# 例：
#   bash scripts/add_collaborators.sh Hehuanhuan-0251 Yangshanshan-0293
#
# 说明：
#   · 仓库是个人账号（pengzhongyan01），加协作者后【对方必须登录 GitHub 点接受】
#     才真正生效 —— 本脚本会打印接受链接
#   · 权限给 write（能推分支、能开 PR），不给 admin
# =============================================================================
set -uo pipefail

REPO="pengzhongyan01/urbanev-charge-analysis"
API="https://api.github.com/repos/$REPO"

RED='\033[1;31m'; GREEN='\033[1;32m'; YELLOW='\033[1;33m'
BLUE='\033[1;34m'; CYAN='\033[1;36m'; NC='\033[0m'

# ── 取 token：优先环境变量，否则问 git 凭据管理器 ───────────────────────────
get_token() {
  if [ -n "${GH_TOKEN:-}" ]; then echo "$GH_TOKEN"; return; fi
  if command -v gh >/dev/null 2>&1; then
    gh auth token 2>/dev/null && return
  fi
  printf 'protocol=https\nhost=github.com\n\n' | git credential fill 2>/dev/null \
    | sed -n 's/^password=//p'
}
TOKEN=$(get_token)
if [ -z "$TOKEN" ]; then
  echo -e "${RED}✗ 拿不到 GitHub token${NC}"
  echo "  设一个环境变量再跑：export GH_TOKEN=ghp_xxx"
  echo "  或用 gh auth login 登录一次。"
  exit 1
fi

api_get() { curl -s -H "Authorization: Bearer $TOKEN" "$1"; }
api_put() { curl -s -o /dev/null -w "%{http_code}" -X PUT -H "Authorization: Bearer $TOKEN" "$1" -d "$2"; }

show_status() {
  echo ""
  echo -e "${BLUE}当前协作者（已接受，权限已生效）${NC}"
  api_get "$API/collaborators" | python -c "
import json,sys
d=json.load(sys.stdin)
if isinstance(d,dict): print('  查询失败：',d.get('message'))
else:
    for c in d: print(f\"  {c['login']:28s} {c.get('role_name')}\")
" 2>/dev/null || echo "  （查询失败）"

  echo ""
  echo -e "${YELLOW}待处理邀请（已发出，等对方点接受）${NC}"
  api_get "$API/invitations" | python -c "
import json,sys
d=json.load(sys.stdin)
if isinstance(d,dict): print('  查询失败：',d.get('message'))
elif not d: print('  （无）')
else:
    for i in d:
        print(f\"  {i['invitee']['login']:28s} {i['permissions']:6s} 过期={i['expired']}\")
" 2>/dev/null || echo "  （查询失败）"
}

# ── 只看状态 ────────────────────────────────────────────────────────────────
if [ "${1:-}" = "--list" ]; then
  show_status
  exit 0
fi

if [ $# -eq 0 ]; then
  echo "用法：bash scripts/add_collaborators.sh <GitHub账号> [更多账号...]"
  echo "      bash scripts/add_collaborators.sh --list    # 只看状态"
  exit 1
fi

# ── 先确认账号真实存在（加错名字会静默失败） ────────────────────────────────
echo ""
echo -e "${BLUE}第一步 · 核对账号是否存在${NC}"
VALID=()
for u in "$@"; do
  CODE=$(api_get "https://api.github.com/users/$u" >/dev/null 2>&1; echo $?)
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "https://api.github.com/users/$u")
  if [ "$HTTP" = "200" ]; then
    echo -e "  ${GREEN}✓${NC} $u"
    VALID+=("$u")
  else
    echo -e "  ${RED}✗${NC} $u —— GitHub 上不存在这个账号，别加错"
  fi
done

if [ ${#VALID[@]} -eq 0 ]; then
  echo ""
  echo -e "${RED}没有可用账号，退出。${NC}"
  exit 1
fi

# ── 逐个授权 ────────────────────────────────────────────────────────────────
echo ""
echo -e "${BLUE}第二步 · 授予 write 权限${NC}"
for u in "${VALID[@]}"; do
  CODE=$(api_put "$API/collaborators/$u" '{"permission":"push"}')
  case "$CODE" in
    201|204) echo -e "  ${GREEN}✓${NC} $u —— 已处理" ;;
    404)     echo -e "  ${RED}✗${NC} $u —— 账号不存在" ;;
    *)       echo -e "  ${RED}✗${NC} $u —— HTTP $CODE" ;;
  esac
done

show_status

echo ""
echo "=============================================================="
echo -e " ${CYAN}还差一步：让组员点接受${NC}"
echo "=============================================================="
echo ""
echo "  个人账号仓库的协作者邀请，必须对方登录 GitHub 点【接受】才生效。"
echo "  把下面这段发到群里，让对应的人照做："
echo ""
echo "  ─────────────────────────────────────────"
echo "  组长已经给你开了仓库写权限，现在需要你点一下接受："
echo ""
echo "  1. 打开 https://github.com/$REPO/invitations"
echo "  2. 点 Accept"
echo ""
echo "     （或右上角头像 → Notifications → Invitations → Accept）"
echo ""
echo "  3. 接受后验证一下："
echo "       bash scripts/doctor_push.sh"
echo "  ─────────────────────────────────────────"
echo ""
echo "  验收标准：doctor_push.sh 显示「有写权限，推送能通」。"
echo ""
