# Gitee 双端镜像 —— ✅ 已完成（2026-11-24 08:47）

> 本文件原是「建仓操作指引」，建仓已完成，现转为**使用说明 + 踩坑记录**。

---

## 一、当前状态

| 端 | 地址 | 状态 |
|---|---|---|
| **Gitee** | `https://gitee.com/peng-zhongyan/urbanev-charge-analysis` | ✅ 已推送，167 个文件，与本地完全一致 |
| **GitHub** | `https://github.com/pengzhongyan01/urbanev-charge-analysis` | ✅ 正常 |

- 两个远端都已推：`main` + `develop`
- 本地与 Gitee 差异：**0 个提交**（完全一致）
- SSH 认证：`Hi pengzhongyan(@peng-zhongyan)!` ✅

> ⚠ **注意名字里的连字符**：Gitee 账号叫 `pengzhongyan`，
> 但**仓库路径是 `peng-zhongyan`**（带连字符）。
> 写 clone 命令时必须是 `git@gitee.com:peng-zhongyan/urbanev-charge-analysis.git`，
> 少一个连字符就是 404。

---

## 二、日常操作

```bash
bash scripts/sync_dual.sh push          # 一条命令推两端（先 Gitee 后 GitHub）
bash scripts/sync_dual.sh status        # 看两端各自领先/落后几个提交
bash scripts/sync_dual.sh pull          # 从 GitHub 拉
bash scripts/sync_dual.sh pull-gitee    # 只从 Gitee 拉
bash scripts/sync_dual.sh setup         # 首次配置（校验 SSH + 设双远端）
```

### 组员怎么 clone（推荐 Gitee，国内快）

```bash
git clone git@gitee.com:peng-zhongyan/urbanev-charge-analysis.git
```

已经 clone 过 GitHub 的组员，一条命令换远端、不用重新 clone：

```bash
cd urbanev-charge-analysis
git remote set-url origin git@gitee.com:peng-zhongyan/urbanev-charge-analysis.git
```

---

## 三、★ 实测踩的两个坑（写进 `scripts/sync_dual.sh` 的注释了）

### 坑 1：Gitee 的欢迎语里插了 ANSI 颜色码

`ssh -T git@gitee.com` 的输出实际是：

```
Hi pengzhongyan(@peng-zhongyan)! You've suc[32mcessfully authenticated, ...
                              ↑ 这里有个 ESC[32m（绿色）
```

所以 `grep -q "successfully authenticated"` **永远匹配不上** ——
脚本会误判成「认证失败」并中止推送。

**修法**：判断前先剥掉 ANSI 序列
```bash
plain=$(printf '%s' "$out" | sed 's/\x1b\[[0-9;]*m//g')
```

### 坑 2：Git Bash 中文用户名路径的 HOME 转义警告

Windows Git Bash 下执行 `ssh` 会先打印：

```
Could not create directory '/c/Users/\305\355\326\322\321\340/.ssh' (No such file or directory).
```

中文用户名 `彭忠燕` 被转义成八进制了。但这只是 `ssh` 想把主机密钥写进
`known_hosts` 时的路径问题，**认证本身完全成功**。

如果拿这条警告当失败判据，脚本会永远卡住。

**修法**：判断依据只认 `successfully authenticated`，其余警告照常打印但不中断。

---

## 四、脚本的两个安全设计

1. **绝不自动 `--force`**：推送前自动 `fetch` 检查分叉，
   一旦发现本地与远端各有领先提交，直接中止并列出差异提交，由人工判断。
2. **先推 Gitee 再推 GitHub**：GitHub 超时/被墙时，至少 Gitee 那一端是新的。

---

## 五、常见问题

**Q：推送会不会覆盖 Gitee 上我手动改的东西？**
不会。检测到分叉会中止并提示差异提交。

**Q：需要给 Gitee 密码吗？**
不需要，SSH 认证已通过。

**Q：两个远端会冲突吗？**
不会。`origin` 和 `gitee` 是两个独立远端名，本地只有一份仓库，
提交一次推两个端。

**Q：以后每次提交都要手动推两次吗？**
不用，`bash scripts/sync_dual.sh push` 一条命令搞定。
