# Gitee 建仓操作指引（3 步，1 分钟）

> 你的 Gitee 账号：**peng-zhongyan**（SSH 认证已实测通过 ✅）
> 目标仓库：`peng-zhongyan/urbanev-charge-analysis`

---

## 第 1 步：打开新建仓库页面

浏览器打开这个链接（已替你填好用户名）：

```
https://gitee.com/peng-zhongyan/new
```

---

## 第 2 步：填这几项

| 表单项 | 填什么 | 说明 |
|---|---|---|
| **仓库名称** | `urbanev-charge-analysis` | ★ 必须和这个一字不差 |
| **仓库路径** | `peng-zhongyan/urbanev-charge-analysis` | 自动生成，不用改 |
| **描述** | 基于 Hadoop 与 Spring Boot 的城市充电桩使用行为分析与充电需求预测系统 | 可留空 |
| **公开性** | **公开** | 评委会看，别选私有 |
| **设置** | **全部不勾** | 见下方说明 |

> ### ★「已有文件」那一栏不要勾
> 那三项是给「本地只有几个文件、想直接传上去」的人用的。
> 我们是**完整 git 历史**（27 次提交 + 全部文件）推上去，
> 勾了反而会冲突。**初始化仓库时选「不勾」任何一项**，
> 直接点「创建」。

---

## 第 3 步：建好后，告诉我一句

你回复「建好了」即可，**不需要复制任何地址、不需要给我密码或令牌**。

我会立刻执行：

```bash
bash scripts/sync_dual.sh push
```

自动完成：
- 校验 Gitee SSH 认证
- 检查两端有无分叉
- 推送到 Gitee（完整历史，含所有分支）
- 推送到 GitHub
- 刷新状态确认

---

## 建好后你的两个仓库地址

| 端 | 地址 | 用途 |
|---|---|---|
| **Gitee** | `https://gitee.com/peng-zhongyan/urbanev-charge-analysis` | ★ 组员 clone 用这个（国内快） |
| **GitHub** | `https://github.com/pengzhongyan01/urbanev-charge-analysis` | 已有地址，保持不变 |

---

## 推完之后，组员怎么 clone

**推荐 Gitee（国内访问快，答辩现场不容易卡）：**

```bash
git clone git@gitee.com:peng-zhongyan/urbanev-charge-analysis.git
```

**如果他们已经有 GitHub 的 clone：**

```bash
cd urbanev-charge-analysis
git remote set-url origin git@gitee.com:peng-zhongyan/urbanev-charge-analysis.git
```

一条命令就把远端换成 Gitee，不用重新 clone。

---

## 常见问题

**Q：推送会不会覆盖 Gitee 上的东西？**
不会。脚本推送前会自动 fetch 检查 —— 如果 Gitee 上有你手动改过的东西，
脚本会**检测到分叉并中止**，把差异提交列出来让你判断，绝不自动覆盖。

**Q：需要给我 Gitee 密码吗？**
不需要。SSH 认证已经通了（`Hi pengzhongyan(@peng-zhongyan)!`）。

**Q：两个远端会不会冲突？**
不会。`origin` 和 `gitee` 是两个独立的远端名，各推各的，
本地仓库只有一份，提交一次推两个端。

**Q：以后每次提交都要手动推两次吗？**
不用。`bash scripts/sync_dual.sh push` 一条命令推两端。

**Q：如果 Gitee 建仓时不小心勾了「已有文件」？**
建完后跟我说，我用 `--force` 覆盖一次即可（只在这次首次推送时用）。
